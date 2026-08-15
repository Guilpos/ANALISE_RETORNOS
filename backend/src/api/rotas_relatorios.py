from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional 
from sqlalchemy import text
from core.database import get_db

router = APIRouter()
# ... (resto do seu código continua igualzinho)

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

@router.delete("/arquivos/excluir-lote", summary="Exclui dados exatos de um mês")
def excluir_lote_arquivos(
    codigo_convenio: str,
    consignataria: str,
    produto: str,
    competencia_inicio: str, # Usamos o mesmo nome do frontend
    db: Session = Depends(get_db)
):
    # =================================================================
    # 1. TRAVA DE SEGURANÇA (Prevenção contra desastres)
    # =================================================================
    if not codigo_convenio or not consignataria or not produto or not competencia_inicio:
        raise HTTPException(
            status_code=400, 
            detail="Operação negada: Para excluir um lote, você deve selecionar Convênio, Consignatária, Produto e Competência Inicial."
        )

    try:
        # =================================================================
        # 2. EXECUÇÃO CIRÚRGICA DA EXCLUSÃO
        # =================================================================
        query_delete = text("""
            DELETE FROM fato_retornos 
            WHERE codigo_convenio = :conv 
              AND consignataria = :banco 
              AND produto = :prod 
              AND competencia = :comp
        """)
        
        resultado = db.execute(query_delete, {
            "conv": codigo_convenio, 
            "banco": consignataria, 
            "prod": produto, 
            "comp": competencia_inicio
        })
        
        # O SQLAlchemy nos diz exatamente quantas linhas foram evaporadas
        linhas_afetadas = resultado.rowcount
        
        if linhas_afetadas == 0:
            return {"status": "aviso", "mensagem": "Nenhum dado encontrado com esses parâmetros para excluir."}

        db.commit()

        return {
            "status": "sucesso", 
            "mensagem": f"Lote excluído permanentemente! {linhas_afetadas} registros foram apagados."
        }

    except Exception as e:
        db.rollback() # Em caso de erro, desfaz qualquer alteração
        raise HTTPException(status_code=500, detail=f"Falha ao excluir no banco de dados: {str(e)}")


@router.get("/dashboard/resumo", summary="Dados mastigados e filtrados dinamicamente")
def obter_resumo_dashboard(
    codigo_convenio: Optional[str] = None,
    consignataria: Optional[str] = None,
    produto: Optional[str] = None,
    competencia_inicio: Optional[str] = None,
    competencia_fim: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # ==========================================
    # 0. CONSTRUÇÃO DINÂMICA DO FILTRO (WHERE)
    # ==========================================
    filtros_sql = []
    parametros = {}

    if codigo_convenio:
        filtros_sql.append("f.codigo_convenio = :convenio")
        parametros["convenio"] = codigo_convenio
        
    if consignataria:
        filtros_sql.append("f.consignataria = :consignataria")
        parametros["consignataria"] = consignataria
        
    if produto:
        filtros_sql.append("f.produto = :produto")
        parametros["produto"] = produto
        
    if competencia_inicio:
        filtros_sql.append("f.competencia >= :comp_ini")
        parametros["comp_ini"] = competencia_inicio
        
    if competencia_fim:
        filtros_sql.append("f.competencia <= :comp_fim")
        parametros["comp_fim"] = competencia_fim

    # Transforma a lista de filtros em uma string: " AND f.codigo_convenio = :convenio AND ..."
    clausula_where = ""
    if filtros_sql:
        clausula_where = " AND " + " AND ".join(filtros_sql)

    # ==========================================
    # 1. DADOS DOS CARDS (PIZZA E BARRAS)
    # ==========================================
    
    query_pizza = text(f"""
        SELECT 
            f.id_arquivo_origem,
            MAX(h.nome_arquivo_original) as nome_arquivo,
            MAX(f.codigo_convenio) as convenio,
            f.status_acatamento, 
            COUNT(f.id) as quantidade
        FROM fato_retornos f
        LEFT JOIN historico_uploads h ON f.id_arquivo_origem = h.id
        WHERE f.id_arquivo_origem IS NOT NULL {clausula_where}
        GROUP BY f.id_arquivo_origem, f.status_acatamento
    """)
    resultado_pizza = db.execute(query_pizza, parametros).fetchall()

    query_barras = text(f"""
        SELECT 
            f.id_arquivo_origem,
            f.texto_critica_original, 
            COUNT(f.id) as quantidade
        FROM fato_retornos f
        WHERE f.texto_critica_original IS NOT NULL 
          AND f.texto_critica_original != '' 
          AND f.texto_critica_original != 'OK' 
          {clausula_where}
        GROUP BY f.id_arquivo_origem, f.texto_critica_original
    """)
    resultado_barras = db.execute(query_barras, parametros).fetchall()

    cards_arquivos = {}

    for row in resultado_pizza:
        id_arq = row[0]
        nome_arq = row[1] or f"Arquivo {id_arq}"
        status = row[3] if row[3] else "NAO INFORMADO"
        qtd = row[4]

        if id_arq not in cards_arquivos:
            cards_arquivos[id_arq] = {
                "id_arquivo": id_arq,
                "nome_arquivo": nome_arq,
                "grafico_pizza": {"labels": [], "quantidades": []},
                "grafico_barras": {"labels": [], "quantidades": []}
            }
        
        cards_arquivos[id_arq]["grafico_pizza"]["labels"].append(status)
        cards_arquivos[id_arq]["grafico_pizza"]["quantidades"].append(qtd)

    for row in resultado_barras:
        id_arq = row[0]
        critica = row[1]
        qtd = row[2]

        if id_arq in cards_arquivos:
            cards_arquivos[id_arq]["grafico_barras"]["labels"].append(critica)
            cards_arquivos[id_arq]["grafico_barras"]["quantidades"].append(qtd)

    lista_de_cards = list(cards_arquivos.values())

    # ==========================================
    # 2. DADOS DO GRÁFICO GLOBAL (TENDÊNCIA)
    # ==========================================
    query_tendencia = text(f"""
        SELECT 
            DATE_FORMAT(f.competencia, '%m/%Y') as mes_ano, 
            f.status_acatamento, 
            COUNT(f.id) as quantidade
        FROM fato_retornos f
        WHERE f.status_acatamento IS NOT NULL {clausula_where}
        GROUP BY mes_ano, f.status_acatamento
        ORDER BY MIN(f.competencia) ASC
    """)
    resultado_tendencia = db.execute(query_tendencia, parametros).fetchall()

    meses_unicos = []
    linha_aceitos = {}
    linha_rejeitados = {}
    
    for row in resultado_tendencia:
        mes = row[0]
        status = row[1].upper() if row[1] else ""
        qtd = row[2]

        if mes not in meses_unicos:
            meses_unicos.append(mes)
            linha_aceitos[mes] = 0
            linha_rejeitados[mes] = 0

        if "ACATADO" in status and "INTEGRAL" in status:
            linha_aceitos[mes] += qtd
        elif "REJEITADO" in status or "ZERADO" in status:
            linha_rejeitados[mes] += qtd

    dados_tendencia = {
        "labels": meses_unicos,
        "aceitos": [linha_aceitos[mes] for mes in meses_unicos],
        "rejeitados": [linha_rejeitados[mes] for mes in meses_unicos]
    }

    return {
        "cards_arquivos": lista_de_cards,
        "grafico_tendencia": dados_tendencia
    }