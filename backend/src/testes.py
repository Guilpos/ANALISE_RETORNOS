from utils.file_readers import ler_arquivo_seguro
from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_delimitador_ponto, alinhar_tipagem_chaves
import openpyxl
import pandas as pd
import xlrd

def processar_portal_exemplo(df: pd.DataFrame) -> pd.DataFrame:

    df.columns = df.iloc[0].astype(str).str.strip()
    df = df.iloc[1:].reset_index(drop=True)
    

    df = df.rename(columns={"cpf": "CPF", "matricula": "Matrícula", 'valor_informado': 'Valor Lançado', 'valor_registrado': 'Valor Acatado', "crÃ­tica": "Crítica"})

     
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
    df['Valor_lancado'] = df['Valor_lancado']


    df['Valor_descontado'] = df['Valor Acatado'].apply(limpar_moeda_universal)

    return df

# Coloque o caminho exato onde você salvou o arquivo de teste
caminho_do_arquivo = r"C:\RETORNOS\GOV PB\RETORNOS_UNIF_GOV_PB_CAPITAL_09-2026.csv"
df_tratamento = pd.read_csv(caminho_do_arquivo, encoding='latin-1', sep=";", header=None)

# Chama a função que criamos passando os bytes simulados
df_teste = processar_portal_exemplo(df_tratamento)

# Exibe o resultado no terminal para você conferir as colunas
print(df_teste.head(15))
print("\nTipos de dados gerados:")
print(df_teste.dtypes)