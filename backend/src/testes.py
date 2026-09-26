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

    df = df.rename(columns={'Matricula': 'Matrícula', 'Valor a Faturar': 'Valor Lançado', 'Valor a Descontar': 'Valor Acatado', "Mensagem Retorno": "Crítica"})

    df['Valor Acatado'] = df['Valor Acatado'].fillna(0)


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

        
    df['Matricula_formatada'] = alinhar_tipagem_chaves(df, 'Matrícula')
    df['cpf_formatado'] = limpar_cpf(df['CPF'])
    
    # --- LÓGICA DE ACATAMENTO ---
    # Aplicação limpa e direta no DataFrame:
    df['Valor_lancado'] = df['Valor Lançado'].apply(limpar_moeda_universal)


    df['Valor_descontado'] = df['Valor Acatado'].apply(limpar_moeda_universal)

    return df

# Coloque o caminho exato onde você salvou o arquivo de teste
caminho_do_arquivo = r"Z:\Dados\NOVA ESTRUTURA\LANÇAMENTO CARTÕES\TRABALHANDO\2026\09 - Setembro\PREF DUQUE DE CAXIAS + COTAR\COTAR\RETORNO - DUQUE DE CAXIAS - COTAR - CIASPREV - 09.2026.xlsx"
# Chama a função que criamos passando os bytes simulados

# 2. Leia o arquivo em bytes
with open(caminho_do_arquivo, "rb") as f:
    conteudo_bytes = f.read()

df_teste = processar_portal_exemplo(conteudo_bytes=conteudo_bytes)

# Exibe o resultado no terminal para você conferir as colunas
print(df_teste.tail(30))
print("\nTipos de dados gerados:")
print(df_teste.dtypes)