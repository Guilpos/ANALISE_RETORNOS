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

    # 1. Limpeza do Valor Lançado (Garantindo leitura segura contra nulos)
    if df['Valor Lançado'].astype(str).str.contains('\.').any():
        df['Valor_lancado'] = limpar_moeda_delimitador_ponto(df['Valor Lançado'].astype(str))
    else:
        df['Valor_lancado'] = limpar_moeda(df['Valor Lançado'].astype(str))

    print('Valor lançado:', df['Valor_lancado'].head(10))

    # 1. Garante que a coluna nasça vazia para todo o arquivo
    if 'Valor Acatado' not in df.columns:
        df['Valor Acatado'] = ""

    # 2. Extração de texto da 'Crítica' (Sem limpar a moeda ainda!)
    mask_margem = df['Crítica'].fillna('').str.contains('MARGEM INSUFICIENTE. SERA INCLUIDO APENAS O VALOR DE')
    if mask_margem.any():
        print('Encontradas críticas de margem insuficiente. Extraindo valores...')
        df['Valor Acatado'] = df.apply(
            lambda row: row['Crítica'].split('VALOR DE ')[1].split(' ')[0] if 'MARGEM INSUFICIENTE' in str(row['Crítica']) else row['Valor Acatado'],
            axis=1
        )

        print('Valores extraídos da crítica:', df.loc[mask_margem, 'Valor Acatado'].head(10))

    # 3. Limpeza do Valor Acatado (Aplica a mesma lógica inteligente do Valor Lançado)
    if df['Valor Acatado'].astype(str).str.contains('\.').any():
        df['Valor_descontado'] = limpar_moeda_delimitador_ponto(df['Valor Acatado'].astype(str))
    else:
        df['Valor_descontado'] = limpar_moeda(df['Valor Acatado'].astype(str))

    # 4. Atribuição direta dos valores já numéricos (Sobrescreve o que foi limpo acima)
    df.loc[df['Crítica'] == 'INCLUSAO VALIDADA.', 'Valor_descontado'] = df['Valor_lancado']

    # Preenche vazios com 0
    df['Valor_descontado'] = df['Valor_descontado'].fillna(0)
    # df['Data_formatada'] = limpar_data(df['Data'])

    # 3. Alinhamento Estrito de Tipos para Cruzamento
    # Garante que as chaves de relacionamento estejam exatamente no mesmo tipo (string)
    df['Matricula_formatada'] = alinhar_tipagem_chaves(df, 'Matrícula')
    '''df['cpf_contratos'] = alinhar_tipagem_chaves(df, 'cpf_contratos')'''

    print(df.head(30))

    validar_matematica_descontos(df, col_lancado="Valor_lancado", col_acatado="Valor_descontado")

    # resultado = analisar_dados(df, convenio=convenio, portal=portal)


    return df