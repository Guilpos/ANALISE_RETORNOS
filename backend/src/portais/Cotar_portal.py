from utils.formatters import limpar_cpf, limpar_moeda_universal, alinhar_tipagem_chaves
from utils.tabelas_cip import tabela_erros_completa
import pandas as pd

def processar_portal_cotar(df_bruto: pd.DataFrame, convenio: str, portal: str) -> pd.DataFrame:
    df = df_bruto

    df['Valor Acatado'] = df['Valor Acatado'].fillna(0)
    
    df['Matricula_formatada'] = alinhar_tipagem_chaves(df, 'Matrícula')
    df['cpf_formatado'] = limpar_cpf(df['CPF'])
    
    # --- LÓGICA DE ACATAMENTO ---
    # Aplicação limpa e direta no DataFrame:
    df['Valor_lancado'] = df['Valor Lançado'].apply(limpar_moeda_universal)


    df['Valor_descontado'] = df['Valor Acatado'].apply(limpar_moeda_universal)

    return df
    