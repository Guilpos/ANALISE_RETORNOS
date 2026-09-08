from utils.file_readers import ler_arquivo_seguro
from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_delimitador_ponto, alinhar_tipagem_chaves
import openpyxl
import pandas as pd
import xlrd

def processar_portal_exemplo(caminho: str):
    # A partir do Pandas 1.3.0:
    df = pd.read_excel(caminho, dtype=str, header=None)

    df.columns = df.iloc[0]

    # Remove a primeira linha (índice 0) que foi usada como molde e reseta o índice
    df = df.iloc[1:].reset_index(drop=True)
    
    print(f'Como está df antes de filtrar?\n{df.head(10)}\n\n')

    # NM_PESSOA|NR_CPF	NR_MATRICULA|VL_PREVISAO_DESCONTO|valor acatado|críticas

    df = df.rename(columns={
        'NR_CPF': 'CPF',
        'NR_MATRICULA': 'Matrícula',
        'VL_PREVISAO_DESCONTO': 'Valor Lançado',
        'valor acatado': 'Valor Acatado',
        'críticas': 'Crítica'
    })


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
    df['Valor_lancado'] = df['Valor_lancado'] / 100


    df['Valor_descontado'] = df['Valor Acatado'].apply(limpar_moeda_universal)

    return df

caminho = r"Z:\Dados\NOVA ESTRUTURA\LANÇAMENTO CARTÕES\TRABALHANDO\2026\08 - Agosto\PREF FLORIANÓPOLIS\LANÇAMENTOS E RETORNOS\RETORNO PREF FLORIANOPOLIS CARTÃO 08-2026.xlsx"

arquivo_lido = processar_portal_exemplo(caminho=caminho)

print(arquivo_lido.head(30))