from utils.file_readers import ler_arquivo_seguro
from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_delimitador_ponto, alinhar_tipagem_chaves
import openpyxl
import pandas as pd
import xlrd

def processar_portal_exemplo(df: pd.DataFrame) -> pd.DataFrame:

    print(f"PRIMEIRA LINHA\n", df.loc[0][0])
    if "Servidor" in df.loc[0][0]:
        df.columns = df.iloc[0].astype(str).str.strip()
        df = df.iloc[1:].reset_index(drop=True)
    else:
        df.columns = df.iloc[1].astype(str).str.strip()
        df = df.iloc[2:].reset_index(drop=True)
    
    print(f"DEBUG: Como está o DataFrame depois de reorganizar o cabeçalho?\n{df}\n")
    print(f"DEBUG: Colunas de df: {df.columns}")
    # 1. Separar a coluna 'Linha' em múltiplas colunas
    # O expand=True transforma o resultado do split em um novo DataFrame.    
    # Como a string termina com um ';', o split vai criar uma última coluna vazia.
    # Vamos pegar apenas as 6 primeiras colunas que nos interessam:

    # 2. Higienização das colunas padrão
    if 'CPF' not in df.columns:
        df['CPF'] = df['Matrícula'].str.zfill(11)  # Supondo que os primeiros 11 caracteres da matrícula sejam o CPF

    

    df = df.rename(columns={'Valor parcela': 'Valor Lançado', 'Valor ajuste': 'Valor Acatado', "Observação": "Crítica"})

    mask_servidor = df['Servidor'] == 'Servidor'

    df = df.loc[~mask_servidor]

    df = df.iloc[:-1]
     
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
    
    # --- LÓGICA DE ACATAMENTO ---


    # Aplicação limpa e direta no DataFrame:
    df['Valor_lancado'] = df['Valor Lançado'].apply(limpar_moeda_universal)
    df['Valor_lancado'] = df['Valor_lancado']


    df['Valor_descontado'] = df['Valor Acatado'].apply(limpar_moeda_universal)

    return df

# Coloque o caminho exato onde você salvou o arquivo de teste
caminho_do_arquivo = r"Z:\Dados\NOVA ESTRUTURA\LANÇAMENTO CARTÕES\TRABALHANDO\2026\08 - Agosto\PREF CONTAGEM\LANÇAMENTOS E RETORNOS\relatorioAjusteDescontoPREF CONTAGEM 08-2026.xls"
df_tratamento = pd.read_excel(caminho_do_arquivo, header=None)

# Chama a função que criamos passando os bytes simulados
df_teste = processar_portal_exemplo(df_tratamento)

# Exibe o resultado no terminal para você conferir as colunas
print(df_teste.tail(10))
print("\nTipos de dados gerados:")
print(df_teste.dtypes)