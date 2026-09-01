from utils.file_readers import ler_arquivo_seguro
from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_retorno_consigfacil, alinhar_tipagem_chaves
import pandas as pd

def processar_portal_exemplo(caminho: str):
    # 1. Leitura segura (todos os dados nascem como texto bruto)
    convenio = "62"
    df = pd.read_csv(caminho, encoding="ISO-8859-1", sep=";", on_bad_lines="skip", header=None)

    # 1. Atribui os valores da primeira linha (índice 0) aos cabeçalhos
    df.columns = df.iloc[0]

    # 2. Remove a primeira linha dos dados e reseta o índice
    df = df[1:].reset_index(drop=True)

    print(f'Como está df antes de filtrar?\n{df.head(10)}\n\n')

    # 1. Extrai os nomes das colunas reais que estão escondidos na primeira linha (índice 0)
    nomes_colunas_conteudo = df.loc[0, 'Conteudo'].split(';')
    
    # 2. Divide a coluna 'Conteudo' usando o ';' e renomeia com os cabeçalhos extraídos
    df_conteudo = df['Conteudo'].str.split(';', expand=True)
    df_conteudo.columns = nomes_colunas_conteudo
    
    # 3. Divide a coluna 'Retorno'
    # O expand=True cria colunas preenchendo com NaN onde não houver ponto e vírgula
    df_retorno = df['Retorno'].str.split(';', expand=True)
    
    # Renomeia as colunas de retorno dinamicamente (ex: Retorno_1, Retorno_2, Retorno_3)
    df_retorno.columns = [f"Retorno_{i+1}" for i in range(df_retorno.shape[1])]
    
    # 4. Junta as duas partes separadas em um único DataFrame
    # Se quiser manter a coluna 'Linha' original, basta adicionar df[['Linha']] dentro do colchete abaixo
    df_final = pd.concat([df_conteudo, df_retorno], axis=1)
    
    # 5. Remove a primeira linha (índice 0) que foi usada como molde e reseta o índice
    df_final = df_final.iloc[1:].reset_index(drop=True)

    df_final['VALOR'] = df_final['VALOR'].str.replace(',', '.', regex=False).astype(float)

    # ['Matrícula', 'CPF', 'Valor Lançado', 'Crítica', 'Valor Acatado']

    df_final.rename(columns={"MATRICULA": "Matrícula", "VALOR": "Valor Lançado", "Retorno_1": "Crítica", "Retorno_3": "Valor Acatado"}, inplace=True)

    return df_final

caminho = r"C:\PESSOAL\TESTE PROJETO DE ANALISE DE RETORNOS\RETORNO CART GOV PE 08.2026.csv"

arquivo_lido = processar_portal_exemplo(caminho=caminho)

print(arquivo_lido.head(30))