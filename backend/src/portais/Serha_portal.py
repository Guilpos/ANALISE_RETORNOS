from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_universal, limpar_moeda_delimitador_ponto, alinhar_tipagem_chaves
from utils.validators import validar_matematica_descontos
from utils.analisador import analisar_dados
import pandas as pd

def processar_portal_serha(df_bruto: pd.DataFrame, convenio: str, portal: str) -> pd.DataFrame:

    df = df_bruto.copy()
    df['Crítica'] = df['Crítica'].replace({
            "000": "CARGA INTEGRAL",
            "001": "CONSIGNANTE - COD. ORÇAMENTARIO INVAL./INEX.",
            "002": "CONSIGNADO - Nº CPF INVAL./INEX.",
            "003": "CONSIGNADO - Nº IPSEMG/MASP/MATRICULA INVAL./INEX.",
            "004": "CONSIGNADO - Nº PROCESSO IPSEMG INVAL./INEX.",
            "005": "CONSIGNATARIO - COD. CREDENCIAMENTO INVAL./INEX.",
            "006": "CONSIGNACAO - COD. INVAL./INEX.",
            "007": "CONSIGNAÇÃO - Nº CONTRATO INVAL./INEX",
            "008": "CONSIGNAÇÃO - TAXA JUROS INVAL./INEX.",
            "009": "CONSIGNAÇÃO - RESERVA MARGEM CARTAO INEX.",
            "010": "SALDO MARGEM CONSIGNAVEL INSUFICIENTE",
            "011": "SALDO LIMITE CONSIGNAVEL INSUFICIENTE",
            "012": "ARQUIVO COM PROBLEMA DE FORMATAÇÃO",
            "013": "MÊS/ANO REFERÊNCIA FL.PAGTO. INVÁLIDO",
            "014": "CONSIGNAÇÃO DUPLICADA P/ CONSIGNADO",
            "015": "CONSIGNATÁRIO NÃO RELACIONADO A CONSIGNAÇÃO",
            "016": "CONSIGNAÇÃO NÃO É DE CARTÃO DE CRÉDITO",
            "017": "VALOR MENOR QUE DEZ REAIS",
            "018": "PARCELA INVÁLIDA",
            "019": "CONSIGNAÇÃO NÃO ENCONTRADA P/ CONSIGNADO",
            "020": "PARCELA INVÁLIDA (DIFERENTE)",
            "021": "CONSIGNADO - RESERVADO P/OUTRO CONSIGNATARIO",
            "022": "CARGA PARCIAL",
            "023": "CONSIGNAÇÃO NÃO É PARCIAL",
            "024": "CONSIGNAÇÃO NÃO É INTEGRAL",
            "025": "CONSIGNACAO - TRAVADO PARA SER ENVIADO PROX. FOLHA",
            "026": "CONSIGNADO BLOQUEADO PARA CARTAO",
            "0": "CARGA INTEGRAL",
            "1": "CONSIGNANTE - COD. ORÇAMENTARIO INVAL./INEX.",
            "2": "CONSIGNADO - Nº CPF INVAL./INEX.",
            "3": "CONSIGNADO - Nº IPSEMG/MASP/MATRICULA INVAL./INEX.",
            "4": "CONSIGNADO - Nº PROCESSO IPSEMG INVAL./INEX.",
            "5": "CONSIGNATARIO - COD. CREDENCIAMENTO INVAL./INEX.",
            "6": "CONSIGNACAO - COD. INVAL./INEX.",
            "7": "CONSIGNAÇÃO - Nº CONTRATO INVAL./INEX",
            "8": "CONSIGNAÇÃO - TAXA JUROS INVAL./INEX.",
            "9": "CONSIGNAÇÃO - RESERVA MARGEM CARTAO INEX.",
            "10": "SALDO MARGEM CONSIGNAVEL INSUFICIENTE",
            "11": "SALDO LIMITE CONSIGNAVEL INSUFICIENTE",
            "12": "ARQUIVO COM PROBLEMA DE FORMATAÇÃO",
            "13": "MÊS/ANO REFERÊNCIA FL.PAGTO. INVÁLIDO",
            "14": "CONSIGNAÇÃO DUPLICADA P/ CONSIGNADO",
            "15": "CONSIGNATÁRIO NÃO RELACIONADO A CONSIGNAÇÃO",
            "16": "CONSIGNAÇÃO NÃO É DE CARTÃO DE CRÉDITO",
            "17": "VALOR MENOR QUE DEZ REAIS",
            "18": "PARCELA INVÁLIDA",
            "19": "CONSIGNAÇÃO NÃO ENCONTRADA P/ CONSIGNADO",
            "20": "PARCELA INVÁLIDA (DIFERENTE)",
            "21": "CONSIGNADO - RESERVADO P/OUTRO CONSIGNATARIO",
            "22": "CARGA PARCIAL",
            "23": "CONSIGNAÇÃO NÃO É PARCIAL",
            "24": "CONSIGNAÇÃO NÃO É INTEGRAL",
            "25": "CONSIGNACAO - TRAVADO PARA SER ENVIADO PROX. FOLHA",
            "26": "CONSIGNADO BLOQUEADO PARA CARTAO",
            })


    # Aplicação limpa e direta no DataFrame:
    df['Valor_lancado'] = df['Valor Lançado'].apply(limpar_moeda_universal)
    df['Valor_lancado'] = df['Valor_lancado'] / 100

    df.insert(7, "Valor Acatado", 0)
    df['Valor Acatado'] = df['Valor Acatado'].astype(float)

    df.loc[df['Crítica'].isin(['000', '0', 'CARGA INTEGRAL']), 'Valor Acatado'] = df['Valor_lancado']

    df['Valor_descontado'] = df['Valor Acatado'].apply(limpar_moeda_universal)

    return df