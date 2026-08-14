from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional 
from sqlalchemy import text
from core.database import get_db
from pydantic import BaseModel

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