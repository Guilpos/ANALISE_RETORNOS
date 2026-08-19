import hashlib
import json
import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional 
from sqlalchemy import text
from core.database import get_db
from pydantic import BaseModel
import google.generativeai as genai

router = APIRouter()
# ... (resto do seu código continua igualzinho)

# Configure sua chave de API (O ideal é puxar de um arquivo .env como os dados do seu banco)
CHAVE_API_GOOGLE = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=CHAVE_API_GOOGLE)

# Modelo Pydantic para receber o pacote de dados do Frontend
class DadosInsight(BaseModel):
    resumo_dados: dict

@router.post("/dashboard/gerar-insight", summary="Gera resumo com IA usando cache de Hash")
def gerar_insight_ia(dados: DadosInsight, db: Session = Depends(get_db)):
    
    # ==========================================
    # 1. CRIPTOGRAFIA: CRIANDO A IMPRESSÃO DIGITAL
    # ==========================================
    # Transforma o dicionário em texto puro (sort_keys garante que a ordem não mude o hash)
    string_dados = json.dumps(dados.resumo_dados, sort_keys=True)
    
    # Gera o hash SHA-256 (a impressão digital de 64 caracteres)
    hash_digital = hashlib.sha256(string_dados.encode('utf-8')).hexdigest()

    # ==========================================
    # 2. CONSULTA AO CACHE (TIDB)
    # ==========================================
    query_cache = text("SELECT texto_resumo FROM cache_resumos_ia WHERE hash_dados = :hash")
    resultado_cache = db.execute(query_cache, {"hash": hash_digital}).scalar()

    if resultado_cache:
        # Se achou no banco, devolvemos imediatamente sem gastar créditos!
        return {"status": "cache", "insight": resultado_cache}

    # ==========================================
    # 3. GERAÇÃO COM INTELIGÊNCIA ARTIFICIAL
    # ==========================================
    # Montamos o prompt com instruções claras para a IA agir como analista
    prompt = f"""
    Atue como um analista de dados financeiros focado em retornos de convênios consignados.
    Analise os seguintes dados numéricos de processamento e escreva um parágrafo analítico curto (máximo de 3 linhas).
    Destaque o principal ponto de atenção (como alto volume de rejeições por uma crítica específica) ou o sucesso da operação financeira.
    Não use saudações ("Olá", "Aqui está"), vá direto ao ponto e seja estritamente profissional.
    
    Dados brutos: {string_dados}
    """

    try:
        # Usa o modelo mais rápido e barato do Gemini para tarefas de texto
        modelo = genai.GenerativeModel('gemini-2.5-flash')
        resposta_ia = modelo.generate_content(prompt)
        texto_final = resposta_ia.text.strip()

        # ==========================================
        # 4. SALVANDO NO CACHE PARA O FUTURO
        # ==========================================
        query_insert = text("""
            INSERT INTO cache_resumos_ia (hash_dados, texto_resumo) 
            VALUES (:hash, :texto)
        """)
        db.execute(query_insert, {"hash": hash_digital, "texto": texto_final})
        db.commit()

        return {"status": "novo", "insight": texto_final}

    except Exception as e:
        print(f"Erro na IA: {e}")
        return {
            "status": "erro", 
            "insight": "O resumo inteligente não está disponível no momento devido a uma falha de conexão com a IA."
        }

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

    # PADRONIZAÇÃO AQUI
    competencia_padronizada = f"{competencia_inicio}-01"

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
            "comp": competencia_padronizada
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

    if not codigo_convenio:
            raise HTTPException(
                status_code=400, 
                detail="Operação negada: Para obter o resumo de um convênio, você deve selecionar um Convênio"
            )
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
        # Injeta o -01 direto no parâmetro da query
        parametros["comp_ini"] = f"{competencia_inicio}-01" 
        
    if competencia_fim:
        filtros_sql.append("f.competencia <= :comp_fim")
        # Injeta o -01 direto no parâmetro da query
        parametros["comp_fim"] = f"{competencia_fim}-01"

    # Transforma a lista de filtros em uma string: " AND f.codigo_convenio = :convenio AND ..."
    clausula_where = ""
    if filtros_sql:
        clausula_where = " AND " + " AND ".join(filtros_sql)

    
    # ==========================================
    # 1. CONSTRUÇÃO DO TÍTULO DINÂMICO
    # ==========================================
    partes_titulo = []
    if codigo_convenio:
        partes_titulo.append(codigo_convenio)
    if consignataria:
        partes_titulo.append(consignataria)
    if produto:
        partes_titulo.append(produto)
        
    # Junta as partes com um hífen. Ex: "71 - PREF. JOÃO PESSOA - CAPITAL - Cartão de Crédito"
    titulo_base = " - ".join(partes_titulo) if partes_titulo else "Visão Consolidada"

    # ==========================================
    # 2. LÓGICA DE AGRUPAMENTO (DRILL-DOWN)
    # ==========================================
    # Se preencheu data (início ou fim), separamos os cards por mês. 
    # Se não preencheu, juntamos tudo em um único card chamado 'consolidado'
    quebrar_por_mes = bool(competencia_inicio or competencia_fim)
    
    if quebrar_por_mes:
        coluna_agrupador = "f.competencia"
    else:
        coluna_agrupador = "'consolidado'"

    # ==========================================
    # 3. QUERIES SQL INTELIGENTES
    # ==========================================
    query_pizza = text(f"""
        SELECT 
            {coluna_agrupador} as id_agrupador,
            f.status_acatamento, 
            COUNT(f.id) as quantidade,
            SUM(f.valor_lancado) as valor_financeiro,
            MAX(f.competencia) as competencia_ref
        FROM fato_retornos f
        WHERE 1=1 {clausula_where} 
        GROUP BY {coluna_agrupador}, f.status_acatamento
    """)
    resultado_pizza = db.execute(query_pizza, parametros).fetchall()

    query_barras = text(f"""
        SELECT 
            {coluna_agrupador} as id_agrupador,
            f.texto_critica_original,
            COUNT(f.id) as quantidade
        FROM fato_retornos f
        WHERE f.status_acatamento IN ('ZERADO', 'REJEITADO') 
          AND f.valor_acatado = '0.00'
          AND f.texto_critica_original IS NOT NULL
          AND TRIM(f.texto_critica_original) != ''
          {clausula_where}
        GROUP BY {coluna_agrupador}, f.texto_critica_original
    """)
    resultado_barras = db.execute(query_barras, parametros).fetchall()

    # ==========================================
    # 4. MONTAGEM DOS CARDS (Com o Título Novo)
    # ==========================================
    cards_arquivos = {}

    # --- LAÇO 1: PROCESSA A PIZZA E O FINANCEIRO ---
    for row in resultado_pizza:
        id_agrupador = str(row[0]) 
        status = row[1] if row[1] else "NAO INFORMADO"
        qtd = row[2]
        valor_fin = float(row[3] or 0.0)
        comp_ref = row[4]

        # Define o nome que vai aparecer no topo do card
        if id_agrupador == 'consolidado':
            nome_card = titulo_base
        else:
            # INVERSÃO DE DATA: Transforma '2026-08-01' em '08/2026'
            data_str = str(comp_ref)
            if len(data_str) >= 7:
                ano = data_str[0:4]
                mes = data_str[5:7]
                mes_ano = f"{mes}/{ano}"
            else:
                mes_ano = "Data Indefinida"
                
            nome_card = f"{titulo_base} (Ref: {mes_ano})"

        if id_agrupador not in cards_arquivos:
            cards_arquivos[id_agrupador] = {
                "id_arquivo": id_agrupador, 
                "nome_arquivo": nome_card,  
                "competencia_ref": comp_ref,
                "grafico_pizza": {"labels": [], "quantidades": [], "valores_financeiros": []},
                "grafico_barras": {"labels": [], "quantidades": []}
            }
        
        cards_arquivos[id_agrupador]["grafico_pizza"]["labels"].append(status)
        cards_arquivos[id_agrupador]["grafico_pizza"]["quantidades"].append(qtd)
        cards_arquivos[id_agrupador]["grafico_pizza"]["valores_financeiros"].append(valor_fin)

    # --- LAÇO 2: PROCESSA O GRÁFICO DE BARRAS ---
    for row in resultado_barras:
        id_agrupador = str(row[0])
        critica = row[1] if row[1] else "ERRO DESCONHECIDO"
        qtd = row[2]

        if id_agrupador in cards_arquivos:
            cards_arquivos[id_agrupador]["grafico_barras"]["labels"].append(critica)
            cards_arquivos[id_agrupador]["grafico_barras"]["quantidades"].append(qtd)

    # =================================================================
    # 5. ORDENAÇÃO DOS DADOS (DO MAIOR PARA O MENOR)
    # =================================================================
    for arquivo_id, dados_arq in cards_arquivos.items():
        
        # 1. Ordenar a Pizza e o Resumo Financeiro pelo Valor em Reais
        pizza = dados_arq["grafico_pizza"]
        if len(pizza["labels"]) > 0:
            pizza_ordenada = sorted(
                zip(pizza["labels"], pizza["quantidades"], pizza["valores_financeiros"]), 
                key=lambda x: x[2], 
                reverse=True
            )
            pizza["labels"] = [item[0] for item in pizza_ordenada]
            pizza["quantidades"] = [item[1] for item in pizza_ordenada]
            pizza["valores_financeiros"] = [item[2] for item in pizza_ordenada]

        # 2. Ordenar o Gráfico de Barras pela Quantidade de Inconsistências
        barras = dados_arq["grafico_barras"]
        if len(barras["labels"]) > 0:
            barras_ordenadas = sorted(
                zip(barras["labels"], barras["quantidades"]), 
                key=lambda x: x[1], 
                reverse=True
            )
            barras["labels"] = [item[0] for item in barras_ordenadas]
            barras["quantidades"] = [item[1] for item in barras_ordenadas]

    # Convertendo para lista final que vai pro JavaScript
    lista_de_cards = list(cards_arquivos.values())
    lista_de_cards.sort(key=lambda x: (x["competencia_ref"] or "", x["id_arquivo"]))
    
    # E pronto, é só retornar!
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
    linha_parciais = {}
    
    for row in resultado_tendencia:
        mes = row[0]
        status = row[1].upper() if row[1] else ""
        qtd = row[2]

        if mes not in meses_unicos:
            meses_unicos.append(mes)
            linha_aceitos[mes] = 0
            linha_rejeitados[mes] = 0
            linha_parciais[mes] = 0

        if "ACATADO" in status and "INTEGRAL" in status:
            linha_aceitos[mes] += qtd
        elif "ACATADO" in status and "PARCIAL" in status:
            linha_parciais[mes] += qtd
        elif "REJEITADO" in status or "ZERADO" in status:
            linha_rejeitados[mes] += qtd

    dados_tendencia = {
        "labels": meses_unicos,
        "aceitos": [linha_aceitos[mes] for mes in meses_unicos],
        "parciais": [linha_parciais[mes] for mes in meses_unicos],
        "rejeitados": [linha_rejeitados[mes] for mes in meses_unicos]
    }

    return {
        "cards_arquivos": lista_de_cards,
        "grafico_tendencia": dados_tendencia
    }