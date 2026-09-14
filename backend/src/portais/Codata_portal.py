from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_universal, limpar_moeda_delimitador_ponto, alinhar_tipagem_chaves
from utils.validators import validar_matematica_descontos
from utils.analisador import analisar_dados
import pandas as pd

def processar_portal_codata(df_bruto: pd.DataFrame, convenio: str, portal: str) -> pd.DataFrame:
    df = df_bruto

    df['Matricula_formatada'] = alinhar_tipagem_chaves(df, 'Matrícula')
    df['cpf_formatado'] = limpar_cpf(df['CPF'])
    
    # --- LÓGICA DE ACATAMENTO ---
    # Aplicação limpa e direta no DataFrame:
    df['Valor_lancado'] = df['Valor Lançado'].apply(limpar_moeda_universal)
    df['Valor_lancado'] = df['Valor_lancado']


    df['Valor_descontado'] = df['Valor Acatado'].apply(limpar_moeda_universal)

    return df
