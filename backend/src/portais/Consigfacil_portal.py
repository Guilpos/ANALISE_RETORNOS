from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_retorno_consigfacil, alinhar_tipagem_chaves
from utils.validators import validar_matematica_descontos
from utils.analisador import analisar_dados
import pandas as pd

def processar_portal_consigfacil(df_bruto: pd.DataFrame, convenio: str, portal: str) -> pd.DataFrame:
    # 1. Leitura segura (todos os dados nascem como texto bruto)
    df = df_bruto.copy()
    
    # 2. Higienização das colunas padrão
    df['cpf_formatado'] = limpar_cpf(df['CPF'])
    df['Valor_lancado'] = limpar_moeda_retorno_consigfacil(df['Valor Lançado'])
    df['Valor_descontado'] = limpar_moeda_retorno_consigfacil(df['Valor Acatado'])
    # df['Data_formatada'] = limpar_data(df['Data'])

    # 3. Alinhamento Estrito de Tipos para Cruzamento
    # Garante que as chaves de relacionamento estejam exatamente no mesmo tipo (string)
    df['Matricula_formatada'] = alinhar_tipagem_chaves(df, 'Matrícula')
    '''df['cpf_contratos'] = alinhar_tipagem_chaves(df, 'cpf_contratos')'''

    print(df.head(30))

    validar_matematica_descontos(df, col_lancado="Valor_lancado", col_acatado="Valor_descontado")

    # resultado = analisar_dados(df, convenio=convenio, portal=portal)


    return df

# caminho = r"Z:\Dados\NOVA ESTRUTURA\LANÇAMENTO CARTÕES\TRABALHANDO\2026\07 - Julho\PREF JOAO PESSOA\LANÇAMENTO E RETORNO\RETORNO PREF JOAO PESSOA 07.2062.csv"

# arquivo_lido = processar_portal_exemplo(caminho=caminho)

# print(arquivo_lido.head(30))