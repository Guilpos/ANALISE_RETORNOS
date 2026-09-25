from utils.file_readers import ler_arquivo_seguro
from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_delimitador_ponto, alinhar_tipagem_chaves
import openpyxl
import pandas as pd
import xlrd
import io
import xml.etree.ElementTree as ET


def processar_portal_exemplo(conteudo_bytes: bytes):    

    tabela = io.BytesIO(conteudo_bytes)

    df = pd.read_excel(tabela, header=None)

    df.columns = df.iloc[0].astype(str).str.strip()

    df = df.iloc[1:].reset_index(drop=True)

    print(f'Como está df antes de filtrar?\n{df.head(10)}\n\n')

    if "Valor Acatado" not in df.columns and "VALOR_ACATADO" not in df.columns:
        df.insert(5, "Valor Acatado", 0)

    if "Critica" not in df.columns and "OBSERVACAO" not in df.columns:
        df.insert(9, "Critica", "SUCESSO")

    # NOME/CPF/MATRICULA/cod_orgao/VALOR/Valor Acatado/Folha Inclusao/CODIGO DA VERBA/ADE/Observações/Margem
    # NOME/CPF/MATRICULA/cod_orgao/VALOR/CODIGO DA VERBA/ADE/Critica/Valor/Margem
    df.rename(columns={"MATRICULA": "Matrícula", "Critica": "Crítica", "OBSERVACAO": "Crítica", "VALOR": "Valor Lançado", "VALOR_IMPORTADO": "Valor Lançado", "VALOR_ACATADO": "Valor Acatado"}, inplace=True, errors='ignore')

    df['Crítica'] = df['Crítica'].fillna("SUCESSO")

    df = df[["Matrícula", "CPF", "Valor Lançado", "Crítica", "Valor Acatado", "ADE"]].copy()


    print(f'Amostra de df:\n{df.head(15)}')


    def limpar_moeda_universal(valor):
        valor_str = str(valor).strip()
        
        # Ignora nulos
        if valor_str.lower() in ['nan', 'none', '']:
            return 0.00 
            
        # Se tiver vírgula (Padrão BR: 1.000,00 ou 50,45)
        if ',' in valor_str:
            # Remove o ponto de milhar e converte a vírgula decimal para ponto
            valor_str = valor_str.replace('.', '').replace(',', '.')
        
        # Converte para float de forma segura
        try:
            return float(valor_str)
        except ValueError:
            return 0.00

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

    df = df.drop_duplicates(subset="ADE", keep='first')

    return df

# Coloque o caminho exato onde você salvou o arquivo de teste
caminho_do_arquivo = r"Z:\Dados\NOVA ESTRUTURA\LANÇAMENTO CARTÕES\TRABALHANDO\2026\09 - Setembro\PREF GOIANIA\LANCAMENTOS E RETORNOS\Critica_LANCAMENTO CARTÃO PREF GOIANIA 09-2026.xlsx"
# Chama a função que criamos passando os bytes simulados

# 2. Leia o arquivo em bytes
with open(caminho_do_arquivo, "rb") as f:
    conteudo_bytes = f.read()

df_teste = processar_portal_exemplo(conteudo_bytes=conteudo_bytes)

# Exibe o resultado no terminal para você conferir as colunas
print(df_teste.tail(30))
print("\nTipos de dados gerados:")
print(df_teste.dtypes)