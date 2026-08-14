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

@router.delete("/excluir/{id_arquivo}", summary="Exclui um arquivo e todos os seus registros")
def excluir_arquivo(id_arquivo: int, db: Session = Depends(get_db)):
    try:
        # 1. Verifica se o arquivo realmente existe no banco
        query_busca = text("SELECT nome_arquivo_original FROM historico_uploads WHERE id = :id")
        arquivo_encontrado = db.execute(query_busca, {"id": id_arquivo}).fetchone()
        
        if not arquivo_encontrado:
            raise HTTPException(status_code=404, detail="Arquivo não encontrado no histórico.")
        
        nome_arquivo = arquivo_encontrado[0]

        # 2. Deleta as milhares de linhas da fato_retornos (Cascata manual)
        query_del_fato = text("DELETE FROM fato_retornos WHERE id_arquivo_origem = :id")
        linhas_afetadas = db.execute(query_del_fato, {"id": id_arquivo}).rowcount
        
        # 3. Deleta o registro "pai" do histórico
        query_del_hist = text("DELETE FROM historico_uploads WHERE id = :id")
        db.execute(query_del_hist, {"id": id_arquivo})
        
        # 4. Salva as alterações de forma definitiva
        db.commit()
        
        return {
            "status": "sucesso",
            "mensagem": f"O arquivo '{nome_arquivo}' foi excluído.",
            "linhas_removidas": linhas_afetadas
        }

    except Exception as e:
        # Se der qualquer erro, desfaz tudo para não corromper o banco
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno ao excluir: {str(e)}")


@router.get("/dashboard/resumo", summary="Dados mastigados e separados por arquivo")
def obter_resumo_dashboard(db: Session = Depends(get_db)):
    
    # ==========================================
    # 1. DADOS DOS CARDS (PIZZA E BARRAS POR ARQUIVO)
    # ==========================================
    
    # Busca a proporção de acatamento agrupada por arquivo
    query_pizza = text("""
        SELECT 
            f.id_arquivo_origem,
            MAX(h.nome_arquivo_original) as nome_arquivo,
            MAX(f.codigo_convenio) as convenio,
            f.status_acatamento, 
            COUNT(f.id) as quantidade
        FROM fato_retornos f
        LEFT JOIN historico_uploads h ON f.id_arquivo_origem = h.id
        WHERE f.id_arquivo_origem IS NOT NULL
        GROUP BY f.id_arquivo_origem, f.status_acatamento
    """)
    resultado_pizza = db.execute(query_pizza).fetchall()

    # Busca as críticas agrupadas por arquivo
    query_barras = text("""
        SELECT 
            id_arquivo_origem,
            texto_critica_original, 
            COUNT(id) as quantidade
        FROM fato_retornos
        WHERE texto_critica_original IS NOT NULL AND texto_critica_original != '' AND texto_critica_original != 'OK'
        GROUP BY id_arquivo_origem, texto_critica_original
    """)
    resultado_barras = db.execute(query_barras).fetchall()

    # Organizando os dados brutos do SQL em um formato de dicionário por arquivo
    cards_arquivos = {}

    for row in resultado_pizza:
        id_arq = row[0]
        nome_arq = row[1] or f"Arquivo {id_arq}"
        status = row[3] if row[3] else "NAO INFORMADO"
        qtd = row[4]

        # Se o arquivo ainda não existe no dicionário, criamos a estrutura dele
        if id_arq not in cards_arquivos:
            cards_arquivos[id_arq] = {
                "id_arquivo": id_arq,
                "nome_arquivo": nome_arq,
                "grafico_pizza": {"labels": [], "quantidades": []},
                "grafico_barras": {"labels": [], "quantidades": []}
            }
        
        # Adicionando os dados da pizza
        cards_arquivos[id_arq]["grafico_pizza"]["labels"].append(status)
        cards_arquivos[id_arq]["grafico_pizza"]["quantidades"].append(qtd)

    # Adicionando os dados das barras nos arquivos corretos
    for row in resultado_barras:
        id_arq = row[0]
        critica = row[1]
        qtd = row[2]

        if id_arq in cards_arquivos:
            cards_arquivos[id_arq]["grafico_barras"]["labels"].append(critica)
            cards_arquivos[id_arq]["grafico_barras"]["quantidades"].append(qtd)

    # Convertendo o dicionário para uma lista simples para o Frontend iterar
    lista_de_cards = list(cards_arquivos.values())

    # ==========================================
    # 2. DADOS DO GRÁFICO GLOBAL (TENDÊNCIA - Mantido igual)
    # ==========================================
    query_tendencia = text("""
        SELECT 
            DATE_FORMAT(competencia, '%m/%Y') as mes_ano, 
            status_acatamento, 
            COUNT(id) as quantidade
        FROM fato_retornos
        WHERE status_acatamento IS NOT NULL
        GROUP BY mes_ano, status_acatamento
        ORDER BY MIN(competencia) ASC
    """)
    resultado_tendencia = db.execute(query_tendencia).fetchall()

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

    # Retorno final: A lista de arquivos (pro meio) e a tendência global (pra direita)
    return {
        "cards_arquivos": lista_de_cards,
        "grafico_tendencia": dados_tendencia
    }