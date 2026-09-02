from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_delimitador_ponto, limpar_moeda, alinhar_tipagem_chaves
from utils.validators import validar_matematica_descontos
from utils.analisador import analisar_dados
import pandas as pd

def processar_portal_econsig(df_bruto: pd.DataFrame, convenio: str, portal: str) -> pd.DataFrame:
    # 1. Leitura segura (todos os dados nascem como texto bruto)
    df = df_bruto.copy()
    
    # 2. Higienização das colunas padrão
    if 'CPF' not in df.columns:
        df['CPF'] = df['Matrícula'].str.zfill(11)  # Supondo que os primeiros 11 caracteres da matrícula sejam o CPF
    df['cpf_formatado'] = limpar_cpf(df['CPF'])

    # Verificar se o delimitador de casa decimal de Valor Lançado e Valor Acatado é ponto ou vírgula
    if df['Valor Lançado'].str.contains('\.').any():
        df['Valor_lancado'] = limpar_moeda_delimitador_ponto(df['Valor Lançado'])
    else:
        df['Valor_lancado'] = limpar_moeda(df['Valor Lançado'])

    df.loc[df['Crítica'] == 'INCLUSAO VALIDADA', 'Valor Acatado'] = df['Valor Lançado']
    df['Valor Acatado'] = df['Valor Acatado'].fillna(0)    

    df['Valor_descontado'] = limpar_moeda_delimitador_ponto(df['Valor Acatado'])
    # df['Data_formatada'] = limpar_data(df['Data'])

    # 3. Alinhamento Estrito de Tipos para Cruzamento
    # Garante que as chaves de relacionamento estejam exatamente no mesmo tipo (string)
    df['Matricula_formatada'] = alinhar_tipagem_chaves(df, 'Matrícula')
    '''df['cpf_contratos'] = alinhar_tipagem_chaves(df, 'cpf_contratos')'''

    print(df.head(30))

    validar_matematica_descontos(df, col_lancado="Valor_lancado", col_acatado="Valor_descontado")

    # resultado = analisar_dados(df, convenio=convenio, portal=portal)


    return df