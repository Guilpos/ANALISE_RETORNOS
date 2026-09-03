from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_universal, alinhar_tipagem_chaves
from utils.validators import validar_matematica_descontos
from utils.analisador import analisar_dados
import pandas as pd

def processar_portal_consigx(df_bruto: pd.DataFrame, convenio: str, portal: str) -> pd.DataFrame:
    # 1. Leitura segura (todos os dados nascem como texto bruto)
    df = df_bruto.copy()

    # 4. Atribuição direta dos valores já numéricos (Sobrescreve o que foi limpo acima)
    df['Crítica'] = df['Crítica'].fillna('')  # Preenche valores nulos com string vazia
    df.loc[df['Crítica'] == '', 'Valor Acatado'] = df['Valor Lançado']

    # Aplicação limpa e direta no DataFrame:
    df['Valor_lancado'] = df['Valor Lançado'].apply(limpar_moeda_universal)
    df['Valor_descontado'] = df['Valor Acatado'].apply(limpar_moeda_universal)

    # _________________________________________________________________________________________________________________________________________
    
    # 2. Higienização das colunas padrão
    df['cpf_formatado'] = limpar_cpf(df['CPF'])
    
    # df['Data_formatada'] = limpar_data(df['Data'])

    # 3. Alinhamento Estrito de Tipos para Cruzamento
    # Garante que as chaves de relacionamento estejam exatamente no mesmo tipo (string)
    df['Matricula_formatada'] = alinhar_tipagem_chaves(df, 'Matrícula')
    '''df['cpf_contratos'] = alinhar_tipagem_chaves(df, 'cpf_contratos')'''

    print(df.head())

    validar_matematica_descontos(df, col_lancado="Valor_lancado", col_acatado="Valor_descontado")

    # resultado = analisar_dados(df, convenio=convenio, portal=portal)


    return df