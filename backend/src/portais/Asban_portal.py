from utils.formatters import limpar_cpf, limpar_moeda_universal, alinhar_tipagem_chaves
import pandas as pd

def processar_portal_asban(df_bruto: pd.DataFrame, convenio: str, portal: str) -> pd.DataFrame:
    df = df_bruto

    df['Matricula_formatada'] = alinhar_tipagem_chaves(df, 'Matrícula')
    df['cpf_formatado'] = limpar_cpf(df['CPF'])
    
    # --- LÓGICA DE ACATAMENTO ---
    # Aplicação limpa e direta no DataFrame:
    df['Valor_lancado'] = df['Valor Lançado'].apply(limpar_moeda_universal)

    df['Valor_lancado'] = df['Valor_lancado']

    # 4. Atribuição direta dos valores já numéricos (Sobrescreve o que foi limpo acima)
    if "Valor Acatado" in df.columns:
        df["Valor Acatado"] = ''

    df['Crítica'] = df['Crítica'].fillna("")
    df.loc[df['Crítica'] == '', 'Valor Acatado'] = df['Valor_lancado']


    df['Valor_descontado'] = df['Valor Acatado'].apply(limpar_moeda_universal)
    df['Valor_descontado'] = df['Valor Acatado'].fillna(0)

    return df