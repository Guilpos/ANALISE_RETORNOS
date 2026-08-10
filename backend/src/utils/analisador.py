import pandas as pd
import numpy as np

import pandas as pd

def analisar_dados(df: pd.DataFrame, convenio: str, portal: str) -> dict:
    """
    Função para analisar os dados do DataFrame e extrair métricas financeiras e operacionais.
    """
    print(f"\nAnalisando dados para o convênio '{convenio}' e portal '{portal}'...\n")

    # [SUGESTÃO EXTRA] Capturar o tamanho total do arquivo para dar contexto às porcentagens
    total_linhas = len(df)

    # 1. Estrutura padronizada de retorno atualizada
    resultados = {
        "convenio": convenio,
        "portal": portal,
        "total_registros_arquivo": total_linhas,
        "colunas_faltantes": [],
        "criticas": {
            "total": 0,
            "taxa_rejeicao_geral_porcentagem": 0.0, 
            "por_tipo": {},
            "porcentagem_por_tipo": {} # Representação (%) de cada crítica dentro do total de erros
        },
        "totais_financeiros": {
            "soma_valor_lancado": 0.0,
            "soma_valor_descontado": 0.0,
            "diferenca_bruta": 0.0,      # Lançado menos Acatado
            "porcentagem_acatada": 0.0   # O quanto do dinheiro esperado realmente entrou
        }
    }

    # 2. Verificação de colunas segura
    colunas_alvo = ["Crítica", "Valor_lancado", "Valor_descontado"]
    colunas_presentes = []

    for coluna in colunas_alvo:
        if coluna in df.columns:
            colunas_presentes.append(coluna)
        else:
            resultados["colunas_faltantes"].append(coluna)
            print(f"A coluna '{coluna}' não se encontra no arquivo.")

    # 3. Análise Operacional (Críticas)
    if "Crítica" in colunas_presentes:
        qtd_criticas = int(df["Crítica"].notna().sum())
        resultados["criticas"]["total"] = qtd_criticas
        
        # [SUGESTÃO EXTRA] Calcula quanto do arquivo inteiro deu problema
        if total_linhas > 0:
            resultados["criticas"]["taxa_rejeicao_geral_porcentagem"] = round((qtd_criticas / total_linhas) * 100, 2)

        # Dicionários de quantidade e porcentagem
        criticas_dict = df["Crítica"].value_counts().to_dict()
        porcentagem_dict = {}
        
        # Se houveram críticas, calcula a representação % de cada tipo
        if qtd_criticas > 0:
            for tipo, quantidade in criticas_dict.items():
                porcentagem_dict[tipo] = round((quantidade / qtd_criticas) * 100, 2)
                
        resultados["criticas"]["por_tipo"] = criticas_dict
        resultados["criticas"]["porcentagem_por_tipo"] = porcentagem_dict
        
        print(f"Quantidade de linhas com críticas: {qtd_criticas} (Aproximadamente {resultados['criticas']['taxa_rejeicao_geral_porcentagem']}% do arquivo)")
        print("\nDetalhamento de críticas:")
        
        for tipo in criticas_dict:
            # Imprime no formato visual: "Ok: 349 (97.5%)"
            print(f"- {tipo}: {criticas_dict[tipo]} ocorrências ({porcentagem_dict[tipo]}%)")
            
    # 4. Análise Financeira
    if "Valor_lancado" in colunas_presentes:
        soma_lancado = round(float(df["Valor_lancado"].sum()), 2)
        resultados["totais_financeiros"]["soma_valor_lancado"] = soma_lancado
        print(f"\nSoma total do Valor Lançado: R$ {soma_lancado}")

    if "Valor_descontado" in colunas_presentes:
        soma_descontado = round(float(df["Valor_descontado"].sum()), 2)
        resultados["totais_financeiros"]["soma_valor_descontado"] = soma_descontado
        print(f"Soma total do Valor Acatado (Descontado): R$ {soma_descontado}")

    # 5. Cruzamento Financeiro (Diferença e Taxa de Sucesso)
    if "Valor_lancado" in colunas_presentes and "Valor_descontado" in colunas_presentes:
        # Diferença Bruta (O quanto de dinheiro ficou pelo caminho)
        diferenca = round(soma_lancado - soma_descontado, 2)
        resultados["totais_financeiros"]["diferenca_bruta"] = diferenca
        
        # Porcentagem de Sucesso de Arrecadação
        porcentagem_acatada = 0.0
        if soma_lancado > 0: # Proteção contra divisão por zero!
            porcentagem_acatada = round((soma_descontado / soma_lancado) * 100, 2)
            
        resultados["totais_financeiros"]["porcentagem_acatada"] = porcentagem_acatada
        
        print(f"\nDiferença bruta não averbada (Lançado - Acatado): R$ {diferenca}")
        print(f"Taxa de Acatamento Financeiro: {porcentagem_acatada}%")

    print("\n" + "-"*40 + "\n")

    return resultados


    
