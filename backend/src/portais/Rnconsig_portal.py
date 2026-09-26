from utils.formatters import limpar_cpf, limpar_moeda_universal, alinhar_tipagem_chaves
import pandas as pd

def processar_portal_rnconsig(df_bruto: pd.DataFrame, convenio: str, portal: str) -> pd.DataFrame:

    df = df_bruto
    df.insert(11, 'Valor Acatado', pd.NA)
    
    df.loc[df['Crítica'] == 'DESCONTO DUPLICADO', 'Valor Acatado'] = df['Valor Lançado']

    df['Valor Acatado'] = df['Valor Acatado']

    df['Matricula_formatada'] = alinhar_tipagem_chaves(df, 'Matrícula')
    df['cpf_formatado'] = limpar_cpf(df['CPF'])
    
    # --- LÓGICA DE ACATAMENTO ---
    # Aplicação limpa e direta no DataFrame:
    df['Valor_lancado'] = df['Valor Lançado'].apply(limpar_moeda_universal)


    df['Valor_descontado'] = df['Valor Acatado'].apply(limpar_moeda_universal)
    df['Valor_descontado'] = df['Valor_descontado'].fillna(0)

    return df