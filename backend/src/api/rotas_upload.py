from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Query
from typing import List, Optional
import re
from services.processamento_orquestrado import orquestrar_processamento
from sqlalchemy import text, bindparam, inspect as sa_inspect
from sqlalchemy.types import Date, DateTime, TIMESTAMP
from sqlalchemy.orm import Session
from core.database import get_db

router = APIRouter()


@router.post("/upload")
async def receber_upload_retorno(
    arquivos: List[UploadFile] = File(...),
    codigo_convenio: str = Form(...),
    consignataria: str = Form(...),
    produto: str = Form(...),
    competencia: str = Form(...), # NOVO: Para sabermos de qual mês é o arquivo
    db: Session = Depends(get_db) # NOVO: Injeção do banco de dados na rota
):

    if not codigo_convenio or not consignataria or not produto or not competencia:
            raise HTTPException(
                status_code=400, 
                detail="Operação negada: Para adicionar um lote, você deve selecionar Convênio, Consignatária, Produto e Competência Inicial."
            )

    competencia_recebida = competencia # O HTML envia "2026-08"
    
    if competencia_recebida:
        # Colamos o "-01" no final para cravar o primeiro dia do mês
        competencia_padronizada = f"{competencia_recebida}-01"


    query_duplicidade = text("""
        SELECT 1 FROM fato_retornos 
        WHERE codigo_convenio = :conv 
          AND consignataria = :banco 
          AND produto = :prod 
          AND competencia = :comp
        LIMIT 1
    """)
    
    # O .scalar() retorna o valor (1) se encontrar, ou None se não existir nada
    lote_ja_existe = db.execute(query_duplicidade, {
        "conv": codigo_convenio,
        "banco": consignataria,
        "prod": produto,
        "comp": competencia_padronizada
    }).scalar()

    if lote_ja_existe:
        raise HTTPException(
            status_code=409, 
            detail=f"Lote Duplicado: Já existe um arquivo processado para essa combinação de Convênio, Banco, Produto e Competência. Se precisar atualizar os dados, exclua o lote atual primeiro."
        )
    
    
    try:
        # conteudo_em_bytes = await arquivo.read()

        # 1. Lê todos os arquivos de forma assíncrona antes de chamar o orquestrador
        arquivos_para_processar = []
        for arquivo in arquivos:
            conteudo_em_bytes = await arquivo.read()
            arquivos_para_processar.append({
                "conteudo": conteudo_em_bytes,
                "nome_arquivo": arquivo.filename
            })
        
        # Passamos a sessão de banco (db) e a competencia para o orquestrador
        resultado_df = orquestrar_processamento(
            arquivos_lista=arquivos_para_processar, 
            convenio=codigo_convenio,
            banco=consignataria,
            tipo_produto=produto,
            competencia=competencia_padronizada,
            db=db
        )
        
        return {
            "status": "sucesso", 
            "mensagem": f"Arquivo {arquivo.filename} salvo no banco! Linhas inseridas: {len(resultado_df)}"
        }
        
    except Exception as e:
        # Importamos a biblioteca de rastreio nativa do Python
        import traceback 
        
        # Isso vai imprimir o erro gigante e detalhado no seu terminal do VS Code/CMD
        traceback.print_exc() 
        
        # Mantemos o envio do erro para o Swagger/Frontend
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# REGISTRO DE UPLOADS (lê a tabela historico_uploads)
# Um "envio" = Convênio + Consignatária + Produto + Competência. Como o upload bloqueia
# duplicidade (409), cada combinação aparece uma única vez e agrupa todos os arquivos dela.
# =====================================================================
_cache_colunas_historico = {}


def _colunas_historico(db: Session):
    """Descobre as colunas de historico_uploads (e qual guarda a data de processamento)."""
    if "v" in _cache_colunas_historico:
        return _cache_colunas_historico["v"]

    colunas = sa_inspect(db.get_bind()).get_columns("historico_uploads")
    nomes = {c["name"] for c in colunas}

    col_data = None
    for candidato in ("data_processamento", "data_upload", "data_hora", "criado_em",
                      "created_at", "data_criacao", "dt_upload", "data"):
        if candidato in nomes:
            col_data = candidato
            break
    if col_data is None:  # fallback: primeira coluna de data/hora que não seja a competência
        for c in colunas:
            if c["name"] != "competencia" and isinstance(c["type"], (Date, DateTime, TIMESTAMP)):
                col_data = c["name"]
                break

    resultado = {"nomes": nomes, "data": col_data}
    if "competencia" in nomes:  # só guarda em cache quando a tabela já está pronta
        _cache_colunas_historico["v"] = resultado
    return resultado


@router.get("/upload/registro", summary="Registro de uploads (mais recentes primeiro)")
def listar_registro_uploads(
    busca: Optional[str] = None,
    convenios: Optional[List[str]] = Query(None),       # códigos que o front achou a partir de um nome digitado
    consignatarias: Optional[List[str]] = Query(None),  # valores de banco que o front achou a partir do nome
    produtos: Optional[List[str]] = Query(None),        # valores de produto que o front achou a partir do nome
    limite: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    info = _colunas_historico(db)
    if "competencia" not in info["nomes"]:
        raise HTTPException(
            status_code=503,
            detail="A tabela historico_uploads ainda não tem a coluna 'competencia'. Execute o script SQL de atualização.",
        )
    col_data = info["data"]

    condicoes_base = ["status_processamento = 'CONCLUIDO'", "competencia IS NOT NULL"]
    params = {}
    listas = []

    termo = (busca or "").strip().lower()
    if termo:
        ors = []
        like_geral = [
            "LOWER(nome_arquivo_original) LIKE :termo ESCAPE '!'",
            "LOWER(consignataria) LIKE :termo ESCAPE '!'",
            "LOWER(produto) LIKE :termo ESCAPE '!'",
        ]
        escapado = termo.replace("!", "!!").replace("%", "!%").replace("_", "!_")
        params["termo"] = f"%{escapado}%"

        m_comp = re.fullmatch(r"(\d{1,2})[./\-](\d{4}|\d{2})", termo)
        if re.fullmatch(r"\d+", termo):
            # "2" deve achar o convênio 2 (e não 12, 20, 22...). Só com 3+ dígitos busca também nos textos.
            ors.append("codigo_convenio = :exato")
            params["exato"] = termo
            if len(termo) >= 3:
                ors += like_geral
            if re.fullmatch(r"20\d{2}", termo):  # ano: "2026" acha todas as competências de 2026
                ors.append("(competencia >= :ano_ini AND competencia < :ano_fim)")
                params["ano_ini"] = f"{termo}-01-01"
                params["ano_fim"] = f"{int(termo) + 1}-01-01"
        elif m_comp and 1 <= int(m_comp.group(1)) <= 12:
            ano = m_comp.group(2) if len(m_comp.group(2)) == 4 else "20" + m_comp.group(2)
            ors.append("competencia = :comp")
            params["comp"] = f"{ano}-{int(m_comp.group(1)):02d}-01"
            ors.append("LOWER(nome_arquivo_original) LIKE :termo ESCAPE '!'")
        else:
            ors.append("LOWER(CAST(codigo_convenio AS CHAR)) LIKE :termo ESCAPE '!'")
            ors += like_geral
            for nome_lista, valores, coluna in (("lc", convenios, "codigo_convenio"),
                                                ("lb", consignatarias, "consignataria"),
                                                ("lp", produtos, "produto")):
                if valores:
                    ors.append(f"{coluna} IN :{nome_lista}")
                    params[nome_lista] = valores[:80]
                    listas.append(nome_lista)
        condicoes_base.append("(" + " OR ".join(ors) + ")")

    where = " AND ".join(condicoes_base)
    chaves_sql = "codigo_convenio, consignataria, produto, competencia"

    def preparar(sql):
        q = text(sql)
        for nome in listas:
            q = q.bindparams(bindparam(nome, expanding=True))
        return q

    total = db.execute(
        preparar(f"SELECT COUNT(*) FROM (SELECT 1 FROM historico_uploads WHERE {where} GROUP BY {chaves_sql}) t"),
        params,
    ).scalar() or 0

    # 1) Página de envios (paginamos por ENVIO, nunca por arquivo)
    chaves = db.execute(
        preparar(f"""
            SELECT {chaves_sql}, MAX(id) AS ultimo
            FROM historico_uploads
            WHERE {where}
            GROUP BY {chaves_sql}
            ORDER BY ultimo DESC
            LIMIT :limite OFFSET :offset
        """),
        {**params, "limite": limite, "offset": offset},
    ).fetchall()
    if not chaves:
        return {"total": total, "itens": []}

    # 2) Todos os arquivos desses envios (mesmo os que não bateram com a busca)
    blocos, p2 = [], {}
    for i, c in enumerate(chaves):
        blocos.append(f"(codigo_convenio = :c{i} AND consignataria = :b{i} AND produto = :p{i} AND competencia = :m{i})")
        p2.update({f"c{i}": c[0], f"b{i}": c[1], f"p{i}": c[2], f"m{i}": c[3]})

    campo_data = f", `{col_data}`" if col_data else ", NULL"
    linhas = db.execute(
        text(f"""
            SELECT id, codigo_convenio, consignataria, produto, competencia,
                   nome_arquivo_original, linhas_totais{campo_data}
            FROM historico_uploads
            WHERE status_processamento = 'CONCLUIDO' AND ({' OR '.join(blocos)})
            ORDER BY id ASC
        """),
        p2,
    ).fetchall()

    por_envio = {}
    for r in linhas:
        k = (str(r[1]), str(r[2]), str(r[3]), str(r[4])[:10])
        e = por_envio.get(k)
        if e is None:
            e = por_envio[k] = {
                "id": r[0], "codigo_convenio": str(r[1]), "consignataria": r[2], "produto": r[3],
                "competencia": str(r[4])[:7],          # "AAAA-MM"
                "linhas": 0, "criado_em": None, "arquivos": [],
            }
        e["id"] = max(e["id"], r[0])
        e["linhas"] += int(r[6] or 0)
        if r[5] and r[5] not in e["arquivos"]:
            e["arquivos"].append(r[5])
        if r[7] is not None:
            iso = r[7].isoformat() if hasattr(r[7], "isoformat") else str(r[7]).replace(" ", "T")
            if e["criado_em"] is None or iso > e["criado_em"]:
                e["criado_em"] = iso

    itens = []
    for c in chaves:
        k = (str(c[0]), str(c[1]), str(c[2]), str(c[3])[:10])
        if k in por_envio:
            itens.append(por_envio[k])
    return {"total": total, "itens": itens}
