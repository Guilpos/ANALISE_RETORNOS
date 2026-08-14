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