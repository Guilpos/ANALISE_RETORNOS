from utils.file_readers import ler_arquivo_seguro
from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_delimitador_ponto, alinhar_tipagem_chaves
import openpyxl
import pandas as pd
import xlrd
import csv
import io
import xml.etree.ElementTree as ET


def processar_portal_exemplo(conteudo_bytes_1: bytes, conteudo_bytes_2: bytes) -> pd.DataFrame:    

    colunas_esperadas = ['Matricula', 'Convênio', 'Nome', 'CPF', 'N/S 1', 'N/S 2', 'N/S 3', 'Valor', 'N/S 4', 'Produto', 'Erro', 'Código', 'Data']
    colunas_finais = ['Matricula', 'CPF', 'Valor', 'Erro']

    def preparar_dataframe(conteudo_bytes: bytes) -> pd.DataFrame:
        # header=0 já pega a primeira linha como nome da coluna e resolve o problema dos índices
        # Decodificamos os bytes em texto antes de tentar descobrir o separador
        texto = conteudo_bytes.decode('utf-8')
        
        # Pegamos uma amostra dos primeiros 4KB para o Sniffer
        amostra = texto[:4096]
        
        try:
            separador = csv.Sniffer().sniff(amostra).delimiter
        except csv.Error:
            separador = ';'
        
        # Criamos o arquivo em memória para o CSV
        arquivo_memoria = io.StringIO(texto)
        df = pd.read_csv(arquivo_memoria, sep=separador, dtype=str, engine='python', header=None)
        
        # O Sniffer às vezes falha com caracteres especiais ou padrões confusos no início
        # Se ele leu menos colunas do que deveria (ex: 2 em vez de 13), force o separador ';'
        if len(df.columns) < 5:
            # Reseta o buffer e tenta de novo forçando ponto e vírgula
            arquivo_memoria.seek(0)
            df = pd.read_csv(arquivo_memoria, sep=';', dtype=str, engine='python', header=None)
            
        # Pega a linha 0 e define como cabeçalho
        df.columns = df.iloc[0]
        
        # Sempre exclui a linha 0 original do corpo dos dados para evitar duplicação ou sujeira
        df = df.iloc[1:].reset_index(drop=True)
        
        # Agora aplicamos as regras de negócio
        if "CNPJ" not in df.columns:
            if 'x' in df.columns or 'X' in df.columns:
                # Se o cabeçalho era a linha do 'x', joga fora e pega a linha de baixo
                df.columns = df.iloc[0]
                df = df.iloc[1:].reset_index(drop=True)
            
            # Se a quantidade de colunas bater, renomeia à força para as esperadas
            if len(df.columns) == len(colunas_esperadas):
                df.columns = colunas_esperadas
        else:
            df = df.iloc[1:].reset_index(drop=True)
                
        # Filtra apenas as colunas que importam para o concat final
        # O uso do errors='ignore' protege o script caso a coluna não seja encontrada
        print("Colunas antes do filtro formato lista:", df.columns.tolist(), "\n")
        print("\nColunas antes do filtro sem formato lista:", df.columns, "\n")
        print(f"Comprimento das planilhas: {len(df)}")

        return df[df.columns.intersection(colunas_finais)].copy()

    # Aplica a mesma regra de limpeza padronizada para os dois arquivos
    df_1 = preparar_dataframe(conteudo_bytes_1)
    print(f'df_1 Amostra\n{df_1.head(15)}')
    df_2 = preparar_dataframe(conteudo_bytes_2)
    print(f'df_2 Amostra\n{df_2.head(15)}')

    # Junta os dois DataFrames em um só
    df = pd.concat([df_1, df_2], ignore_index=True)

    # Renomeia para o padrão final
    df.rename(columns={'Matricula': 'Matrícula', 'Valor': 'Valor Lançado', 'Erro': 'Crítica'}, inplace=True)
        

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

        
    # OPCIONAL: Se quiser adicionar o Valor Acatado seguindo o padrão que fizemos antes
    if not df.empty:
        df['Valor Acatado'] = '0'
        
        # Criação das máscaras
        sucesso_mask = df['Crítica'].str.contains('Em aberto', case=False, na=False)
        
        # 1. Aloca o valor lançado para os sucessos
        df.loc[sucesso_mask, 'Valor Acatado'] = df.loc[sucesso_mask, 'Valor Lançado']
            
        
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

    return df

# Coloque o caminho exato onde você salvou o arquivo de teste
caminho_do_arquivo_1 = r"Z:\Dados\NOVA ESTRUTURA\LANÇAMENTO CARTÕES\TRABALHANDO\2026\09 - Setembro\PREF BAURU\RELATÓRIO\RETORNO - GERAL - BAURU - 09.2026.csv"
caminho_do_arquivo_2 = r"Z:\Dados\NOVA ESTRUTURA\LANÇAMENTO CARTÕES\TRABALHANDO\2026\09 - Setembro\PREF BAURU\RELATÓRIO\RETORNO - ERRO - BAURU - 09.2026.csv"
# Chama a função que criamos passando os bytes simulados

# 2. Leia o arquivo em bytes
with open(caminho_do_arquivo_1, "rb") as f:
    conteudo_bytes_1 = f.read()

with open(caminho_do_arquivo_2, "rb") as f:
    conteudo_bytes_2 = f.read()

df_teste = processar_portal_exemplo(conteudo_bytes_1=conteudo_bytes_1, conteudo_bytes_2=conteudo_bytes_2)

# Exibe o resultado no terminal para você conferir as colunas
# print(df_teste.head(30),'\n')
'''
print(df_teste.tail(30))

print('O que está na linha 142:\n', df_teste.iloc[142],'\n')'''

print("\nTipos de dados gerados:")
print(df_teste.dtypes)