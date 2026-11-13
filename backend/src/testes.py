from utils.file_readers import ler_arquivo_seguro
from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_delimitador_ponto, alinhar_tipagem_chaves
from utils.validators import validar_matematica_descontos
from utils.tabelas_cip import tabela_erros_completa
import openpyxl
import pandas as pd
import xlrd
import csv
import io
import xml.etree.ElementTree as ET


def processar_portal_exemplo(conteudo_bytes_1: bytes) -> pd.DataFrame:    
    tabela_memoria = io.BytesIO(conteudo_bytes_1)

    df = pd.read_excel(tabela_memoria, dtype=str, header=None)

    df.columns = df.iloc[3]
    df = df[4:].reset_index(drop=True)

    print(f'Como está df antes de filtrar?\n{df.head(10)}\n\n')

    df.rename(columns={"Vl. Total": "Valor Lançado", "Vl. Lançamento": "Valor Acatado"}, inplace=True)    

    df['Crítica'] = ''    

    df = df[["Matrícula", "CPF", "Valor Lançado", "Crítica", "Valor Acatado"]].copy()

    # 2. Higienização das colunas padrão
    df['cpf_formatado'] = limpar_cpf(df['CPF'])
    # df['Valor_lancado'] = limpar_moeda_delimitador_ponto(df['Valor Lançado'])
    # df['Valor_descontado'] = limpar_moeda_delimitador_ponto(df['Valor Acatado'])

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

    df['Valor_lancado'] = df['Valor Lançado'].apply(limpar_moeda_universal)
    df['Valor_descontado'] = df['Valor Acatado'].apply(limpar_moeda_universal)

    # df['Data_formatada'] = limpar_data(df['Data'])

    # 3. Alinhamento Estrito de Tipos para Cruzamento
    # Garante que as chaves de relacionamento estejam exatamente no mesmo tipo (string)
    df['Matricula_formatada'] = alinhar_tipagem_chaves(df, 'Matrícula')
    '''df['cpf_contratos'] = alinhar_tipagem_chaves(df, 'cpf_contratos')'''

    print(df.head(30))

    validar_matematica_descontos(df, col_lancado="Valor_lancado", col_acatado="Valor_descontado")

        
    '''# OPCIONAL: Se quiser adicionar o Valor Acatado seguindo o padrão que fizemos antes
    if not df.empty:
        df['Valor Acatado'] = '0'
        
        # Criação das máscaras
        sucesso_mask = df['Crítica'].str.contains('Em aberto', case=False, na=False)
        
        # 1. Aloca o valor lançado para os sucessos
        df.loc[sucesso_mask, 'Valor Acatado'] = df.loc[sucesso_mask, 'Valor Lançado']'''
            
        
    # 2. Higienização das colunas padrão
    df['cpf_formatado'] = limpar_cpf(df['CPF'])
    
    # df['Data_formatada'] = limpar_data(df['Data'])

    # 3. Alinhamento Estrito de Tipos para Cruzamento
    # Garante que as chaves de relacionamento estejam exatamente no mesmo tipo (string)
    df['Matricula_formatada'] = alinhar_tipagem_chaves(df, 'Matrícula')
    
    # Aplicação limpa e direta no DataFrame:
    df['Valor_lancado'] = df['Valor Lançado'].apply(limpar_moeda_universal)
    df['Valor_lancado'] = df['Valor_lancado']


    df['Valor_descontado'] = df['Valor Acatado'].apply(limpar_moeda_universal)

    df.to_excel(f'C:\PESSOAL\TESTE PROJETO DE ANALISE DE RETORNOS\GOV SAO PAULO RETORNO TRATADO PELA ANALISE DE RETORNO TESTE.xlsx', index=False)

    return df

# Coloque o caminho exato onde você salvou o arquivo de teste
caminho_do_arquivo_1 = r"Z:\Dados\NOVA ESTRUTURA\LANÇAMENTO CARTÕES\TRABALHANDO\2026\11 - Novembro\PREF ARAPONGAS\LANCAMENTOS E RETORNOS\RETORNO CARTAO PREF ARAPONGAS 11-2026.xlsx"
# Chama a função que criamos passando os bytes simulados

# 2. Leia o arquivo em bytes
with open(caminho_do_arquivo_1, "rb") as f:
    conteudo_bytes_1 = f.read()

df_teste = processar_portal_exemplo(conteudo_bytes_1=conteudo_bytes_1)

# Exibe o resultado no terminal para você conferir as colunas
# print(df_teste.head(30),'\n')
'''
print(df_teste.tail(30))

print('O que está na linha 142:\n', df_teste.iloc[142],'\n')'''

print("\nTipos de dados gerados:")
print(df_teste.dtypes)