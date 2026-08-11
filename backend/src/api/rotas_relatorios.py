from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.database import get_db

# Cria o roteador que será importado lá no main.py
router = APIRouter()

@router.get("/tendencias/{codigo_convenio}")
def obter_tendencias_convenio(codigo_convenio: str, db: Session = Depends(get_db)):
    """
    Retorna a evolução temporal financeira de um convênio específico.
    O resultado já sai formatado para facilitar a vida do Chart.js no frontend.
    """
    
    # A query em SQL bruto. O banco faz a força de trabalho (SUM e GROUP BY).
    # Usamos parâmetros nomeados (:convenio) para evitar SQL Injection.
    query = text("""
        SELECT 
            DATE_FORMAT(competencia, '%Y-%m') AS mes_ano,
            SUM(valor_lancado) AS total_lancado,
            SUM(valor_acatado) AS total_acatado
        FROM fato_retornos
        WHERE codigo_convenio = :convenio
        GROUP BY mes_ano
        ORDER BY mes_ano ASC
    """)
    
    # Executa a query no banco
    resultados = db.execute(query, {"convenio": codigo_convenio}).fetchall()
    
    # Se não houver dados, retorna um erro 404 limpo
    if not resultados:
        raise HTTPException(status_code=404, detail="Nenhum dado encontrado para este convênio.")
    
    # Formata a resposta num JSON estruturado para o gráfico (Eixos X e Y)
    dados_grafico = {
        "labels": [],           # Eixo X: ['2026-01', '2026-02', ...]
        "lancado": [],          # Eixo Y (Linha 1)
        "acatado": [],          # Eixo Y (Linha 2)
        "taxa_sucesso": []      # Eixo Y (Percentual)
    }
    
    for linha in resultados:
        dados_grafico["labels"].append(linha.mes_ano)
        
        # Converte Decimal para float para ser aceito no JSON
        lancado = float(linha.total_lancado)
        acatado = float(linha.total_acatado)
        
        dados_grafico["lancado"].append(lancado)
        dados_grafico["acatado"].append(acatado)
        
        # Calcula a taxa de acatamento para o ponto do gráfico (evitando divisão por zero)
        taxa = round((acatado / lancado * 100), 2) if lancado > 0 else 0
        dados_grafico["taxa_sucesso"].append(taxa)
        
    return dados_grafico