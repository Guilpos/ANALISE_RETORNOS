from utils.file_readers import ler_arquivo_seguro
from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_delimitador_ponto, alinhar_tipagem_chaves
import openpyxl
import pandas as pd
import xlrd
import io

def processar_portal_exemplo(conteudo_bytes: bytes) -> pd.DataFrame:    
    df = pd.read_csv(
        io.BytesIO(conteudo_bytes), 
        header=None,
        encoding='latin-1',
        sep=';'
    )

    df.columns = df.iloc[0].astype(str).str.strip()

    df = df.iloc[1:].reset_index(drop=True)


    df.rename(columns={'matricula': 'Matrícula', 'cpf': 'CPF', 'valor_reserva': 'Valor Lançado', 'motivo_rejeicao': 'Crítica'}, inplace=True)

    df.insert(11, 'Valor Acatado', pd.NA)

    df.loc[df['Crítica'] == 'DESCONTO DUPLICADO', 'Valor Acatado'] = df['Valor Lançado']

    df['Valor Acatado'] = df['Valor Acatado']

    print(f'Amostra de dados:\n{df[['Crítica', 'Valor Lançado', 'Valor Acatado']].tail(15)}')
     
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
    df['Valor_descontado'] = df['Valor_descontado'].fillna(0)

    return df

# Coloque o caminho exato onde você salvou o arquivo de teste
caminho_do_arquivo = r"Z:\Dados\NOVA ESTRUTURA\LANÇAMENTO CARTÕES\TRABALHANDO\2026\08 - Agosto\GOV RN\LANÇAMENTOS E RETORNOS\RETORNO CARTÃO CLICK GOV RN 08.2026.csv"
# Chama a função que criamos passando os bytes simulados

# 2. Leia o arquivo em bytes
with open(caminho_do_arquivo, "rb") as f:
    conteudo_bytes = f.read()

df_teste = processar_portal_exemplo(conteudo_bytes=conteudo_bytes)

# Exibe o resultado no terminal para você conferir as colunas
print(df_teste[['Crítica', 'Valor Lançado', 'Valor Acatado', 'Valor_lancado', 'Valor_descontado']].tail(30))
print("\nTipos de dados gerados:")
print(df_teste.dtypes)