from utils.file_readers import ler_arquivo_seguro
from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_delimitador_ponto, alinhar_tipagem_chaves
import openpyxl
import pandas as pd
import xlrd

def processar_portal_exemplo(df: pd.DataFrame) -> pd.DataFrame:

    df.columns = df.iloc[1]
    df = df.iloc[2:].reset_index(drop=True)
    # 1. Separar a coluna 'Linha' em múltiplas colunas
    # O expand=True transforma o resultado do split em um novo DataFrame.
    df_separado = df['Linha'].str.split(';', expand=True)
    
    # Como a string termina com um ';', o split vai criar uma última coluna vazia.
    # Vamos pegar apenas as 6 primeiras colunas que nos interessam:
    df_separado = df_separado.iloc[:, :6]
    df_separado.columns = ['Matrícula', 'CPF', 'Valor Lançado', 'Serviço', 'Competência', 'Nome']
    
    # 2. Juntar as novas colunas com as colunas originais (removendo a velha 'Linha')
    df = pd.concat([df_separado, df.drop(columns=['Linha'])], axis=1)
    
    # 3. Limpar o 'Valor Lançado' (trocar vírgula por ponto e converter para float)
    df['Valor Lançado'] = df['Valor Lançado'] # .str.replace(',', '.', regex=False).astype(float)
    
    # 4. Criar a coluna 'Valor Acatado' partindo do zero
    df['Valor Acatado'] = ''
    
    # --- LÓGICA DE ACATAMENTO ---
    
    # A) Tratamento do SUCESSO TOTAL
    mask_sucesso = df['Critica'].str.strip() == 'SUCESSO'
    df.loc[mask_sucesso, 'Valor Acatado'] = df.loc[mask_sucesso, 'Valor Lançado']
    
    # B) Tratamento do SUCESSO PARCIAL
    # Identifica as linhas que contêm a palavra "PARCIAL" na crítica
    mask_parcial = df['Critica'].str.contains('SUCESSO PARCIAL', na=False, case=False)
    
    # Extrai dinamicamente apenas o número que vem depois do "R$"
    df.loc[mask_parcial, 'Valor Acatado'] = (
        df.loc[mask_parcial, 'Critica']
        .str.split('R\$')                     # Corta o texto exatamente no 'R$'
        .str[-1]                              # Pega a última parte (onde ficou o número)
        .str.strip()                          # Remove espaços sobrando
    )
        
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

    # Aplicação limpa e direta no DataFrame:
    df['Valor_lancado'] = df['Valor Lançado'].apply(limpar_moeda_universal)
    df['Valor_lancado'] = df['Valor_lancado']


    df['Valor_descontado'] = df['Valor Acatado'].apply(limpar_moeda_universal)

    return df

# Coloque o caminho exato onde você salvou o arquivo de teste
caminho_do_arquivo = r"Z:\Dados\NOVA ESTRUTURA\LANÇAMENTO CARTÕES\TRABALHANDO\2026\08 - Agosto\GOV CE\LANÇAMENTOS E RETORNOS\Linhas Processadas_GOV CE 08-2026.xlsx"

df_tratamento = pd.read_excel(caminho_do_arquivo, header=None)

# Chama a função que criamos passando os bytes simulados
df_teste = processar_portal_exemplo(df_tratamento)

# Exibe o resultado no terminal para você conferir as colunas
print(df_teste.head(-30))
print("\nTipos de dados gerados:")
print(df_teste.dtypes)