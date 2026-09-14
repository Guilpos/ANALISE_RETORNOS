from utils.file_readers import ler_arquivo_seguro
from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_delimitador_ponto, alinhar_tipagem_chaves
import openpyxl
import pandas as pd
import xlrd
import io
import lxml

def processar_portal_exemplo(conteudo_bytes: bytes) -> pd.DataFrame:

    # 1. Transforma os bytes em um objeto de memória
    tabela_memoria = io.BytesIO(conteudo_bytes)
    
    # 2. O read_html captura a tabela HTML disfarçada de .xls
    # Ele retorna uma lista de tabelas, então pegamos a primeira ([0])
    # Os parâmetros decimal e thousands garantem a conversão segura se o arquivo mudar para padrão BR
    tabelas = pd.read_html(tabela_memoria, header=0, decimal=',', thousands='.')
    df = tabelas[0]
    

    df = df.rename(columns={'Valor_Parcela': 'Valor Lançado', "Motivo_Rejeicao": "Crítica"})
     
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

    df['Valor_lancado'] = df['Valor_lancado'] / 100

    # 4. Atribuição direta dos valores já numéricos (Sobrescreve o que foi limpo acima)
    if "Valor Acatado" in df.columns:
        df["Valor Acatado"] = ''
    df.loc[df['Crítica'] == 'SUCESSO', 'Valor Acatado'] = df['Valor_lancado']


    df['Valor_descontado'] = df['Valor Acatado'].apply(limpar_moeda_universal)
    df['Valor_descontado'] = df['Valor Acatado'].fillna(0)

    return df

# Coloque o caminho exato onde você salvou o arquivo de teste
caminho_do_arquivo = r"C:\RETORNOS\RETORNO GOV SC\RETORNO CAPITAL COMPRA GOV SC 06.2026.xls"
# Chama a função que criamos passando os bytes simulados

# 2. Leia o arquivo em bytes
with open(caminho_do_arquivo, "rb") as f:
    conteudo_bytes = f.read()

df_teste = processar_portal_exemplo(conteudo_bytes=conteudo_bytes)

# Exibe o resultado no terminal para você conferir as colunas
print(df_teste.head(15))
print("\nTipos de dados gerados:")
print(df_teste.dtypes)