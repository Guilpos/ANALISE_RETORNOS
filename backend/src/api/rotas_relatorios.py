from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from services.processamento_orquestrado import orquestrar_processamento
from sqlalchemy.orm import Session
from typing import Optional # Essencial para permitir parâmetros opcionais
from sqlalchemy import text
from core.database import get_db

# Cria o roteador que será importado lá no main.py
router = APIRouter()

@router.get("/tendencias/{codigo_convenio}")
def obter_tendencias_convenio(
    codigo_convenio: str, 
    consignataria: Optional[str] = None, # Parâmetro opcional na URL
    produto: Optional[str] = None,       # Parâmetro opcional na URL
    db: Session = Depends(get_db)
):
    """
    Retorna a evolução temporal. Se a consignatária ou o produto forem informados
    na URL, aplica os filtros no banco de dados. Caso contrário, traz o total geral.
    """
    
    # 1. Montamos a base da query e o dicionário inicial de parâmetros
    query_base = """
        SELECT 
            DATE_FORMAT(competencia, '%Y-%m') AS mes_ano,
            SUM(valor_lancado) AS total_lancado,
            SUM(valor_acatado) AS total_acatado
        FROM fato_retornos
        WHERE codigo_convenio = :convenio
    """
    
    parametros = {"convenio": codigo_convenio}
    
    # 2. Adicionamos os filtros dinamicamente SE eles vierem do frontend
    if consignataria:
        query_base += " AND consignataria = :banco"
        parametros["banco"] = consignataria
        
    if produto:
        query_base += " AND produto = :produto"
        parametros["produto"] = produto
        
    # 3. Finalizamos a query com o agrupamento
    query_base += """
        GROUP BY mes_ano
        ORDER BY mes_ano ASC
    """
    
    # Executa no TiDB
    resultados = db.execute(text(query_base), parametros).fetchall()
    
    if not resultados:
        raise HTTPException(status_code=404, detail="Nenhum dado encontrado para os filtros informados.")
    
    # 4. A formatação do JSON continua igualzinho para o Chart.js
    dados_grafico = {
        "labels": [],
        "lancado": [],
        "acatado": [],
        "taxa_sucesso": []
    }
    
    for linha in resultados:
        dados_grafico["labels"].append(linha.mes_ano)
        lancado = float(linha.total_lancado)
        acatado = float(linha.total_acatado)
        
        dados_grafico["lancado"].append(lancado)
        dados_grafico["acatado"].append(acatado)
        
        taxa = round((acatado / lancado * 100), 2) if lancado > 0 else 0
        dados_grafico["taxa_sucesso"].append(taxa)
        
    return dados_grafico

@router.post("/upload")
async def receber_upload_retorno(
    arquivo: UploadFile = File(...),
    codigo_convenio: str = Form(...),
    consignataria: str = Form(...),
    produto: str = Form(...),
    competencia: str = Form(...), # NOVO: Para sabermos de qual mês é o arquivo
    db: Session = Depends(get_db) # NOVO: Injeção do banco de dados na rota
):
    try:
        conteudo_em_bytes = await arquivo.read()
        
        # Passamos a sessão de banco (db) e a competencia para o orquestrador
        resultado_df = orquestrar_processamento(
            conteudo=conteudo_em_bytes,
            nome_arquivo=arquivo.filename,
            convenio=codigo_convenio,
            banco=consignataria,
            tipo_produto=produto,
            competencia=competencia,
            db=db
        )
        
        return {
            "status": "sucesso", 
            "mensagem": f"Arquivo {arquivo.filename} salvo no banco! Linhas inseridas: {len(resultado_df)}"
        }
        
    except Exception as e:
        # Se algo falhar na gravação, ele avisa a tela
        raise HTTPException(status_code=500, detail=str(e))