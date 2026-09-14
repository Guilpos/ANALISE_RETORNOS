from utils.file_readers import ler_arquivo_seguro
from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_universal, alinhar_tipagem_chaves
import openpyxl
import pandas as pd
import xlrd
import io
import lxml

def processar_portal_sigrh(df_bruto: pd.DataFrame, convenio: str, portal: str) -> pd.DataFrame:
    df = df_bruto

    df['Matricula_formatada'] = alinhar_tipagem_chaves(df, 'Matrícula')
    df['cpf_formatado'] = limpar_cpf(df['CPF'])
    
    # --- LÓGICA DE ACATAMENTO ---
    # Aplicação limpa e direta no DataFrame:
    df['Valor_lancado'] = df['Valor Lançado'].apply(limpar_moeda_universal)

    df['Valor_lancado'] = df['Valor_lancado'] / 100

    # 4. Atribuição direta dos valores já numéricos (Sobrescreve o que foi limpo acima)
    if "Valor Acatado" in df.columns:
        df["Valor Acatado"] = ''
    df.loc[df['Crítica'] == 'SUCESSO', 'Valor Acatado'] = df['Valor_lancado']


    df['Valor_descontado'] = df['Valor Acatado'].apply(limpar_moeda_universal)
    df['Valor_descontado'] = df['Valor Acatado'].fillna(0)

    return df