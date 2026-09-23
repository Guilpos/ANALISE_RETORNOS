from utils.formatters import limpar_cpf, limpar_moeda_universal, alinhar_tipagem_chaves
import pandas as pd

def processar_portal_consigcarioca(df_bruto: pd.DataFrame, convenio: str, portal: str) -> pd.DataFrame:
    df = df_bruto

    df.loc[df['Crítica'] != 'SEM CRÍTICA', 'Crítica'] = df['Descrição da crítica']
    
    df.insert(8, 'Valor Acatado', 0)

    df.loc[df['Crítica'] == 'SEM CRÍTICA', 'Valor Acatado'] = df['Valor Lançado']

    df['Matricula_formatada'] = alinhar_tipagem_chaves(df, 'Matrícula')
    df['cpf_formatado'] = limpar_cpf(df['CPF'])
    
    # --- LÓGICA DE ACATAMENTO ---
    # Aplicação limpa e direta no DataFrame:
    df['Valor_lancado'] = df['Valor Lançado'].apply(limpar_moeda_universal)


    df['Valor_descontado'] = df['Valor Acatado'].apply(limpar_moeda_universal)

    return df
    
