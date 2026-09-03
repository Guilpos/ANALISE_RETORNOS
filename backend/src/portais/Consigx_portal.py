from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_universal, alinhar_tipagem_chaves
from utils.validators import validar_matematica_descontos
from utils.analisador import analisar_dados
import pandas as pd

def processar_portal_consigx(df_bruto: pd.DataFrame, convenio: str, portal: str) -> pd.DataFrame:
    # 1. Leitura segura (todos os dados nascem como texto bruto)
    df = df_bruto.copy()

    # Se a crítica for SUCESSO e Valor Acatado estiver vazio, preenche com o Valor Lançado
    df.loc[(df['Crítica'] == 'SUCESSO') & (df['Valor Acatado'].isnull() | (df['Valor Acatado'] == '')), 'Valor Acatado'] = df['Valor Lançado']
    
    # 2. Higienização das colunas padrão
    df['cpf_formatado'] = limpar_cpf(df['CPF'])
    # 1. Limpeza do Valor Lançado (Garantindo leitura segura contra nulos)
    # Aplicação limpa e direta no DataFrame:
    df['Valor_lancado'] = df['Valor Lançado'].apply(limpar_moeda_universal)

    # 2. Extração de texto da 'Crítica' (Sem limpar a moeda ainda!)
    mask_margem = df['Crítica'].fillna('').str.contains('valor acatado')
    
    if mask_margem.any():
        print('Encontradas críticas de margem insuficiente. Extraindo valores...')
        df['Valor Acatado'] = df.apply(
            lambda row: row['Crítica'].split('valor acatado: ')[1].split(' ')[0].rstrip('.') if 'valor acatado' in str(row['Crítica']) else row['Valor Acatado'],
            axis=1
        )
    df['Valor_descontado'] = df['Valor Acatado'].apply(limpar_moeda_universal)
    # df['Data_formatada'] = limpar_data(df['Data'])

    # 3. Alinhamento Estrito de Tipos para Cruzamento
    # Garante que as chaves de relacionamento estejam exatamente no mesmo tipo (string)
    df['Matricula_formatada'] = alinhar_tipagem_chaves(df, 'Matrícula')
    '''df['cpf_contratos'] = alinhar_tipagem_chaves(df, 'cpf_contratos')'''

    print(df.head())

    validar_matematica_descontos(df, col_lancado="Valor_lancado", col_acatado="Valor_descontado")

    # resultado = analisar_dados(df, convenio=convenio, portal=portal)


    return df