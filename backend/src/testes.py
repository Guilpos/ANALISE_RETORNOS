from utils.file_readers import ler_arquivo_seguro
from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_delimitador_ponto, alinhar_tipagem_chaves
import openpyxl
import pandas as pd

def processar_portal_exemplo(caminho: str):
    df = pd.read_excel(caminho,  header=None, dtype=str)
    df.columns = df.iloc[0]

    # Remove a primeira linha (índice 0) que foi usada como molde e reseta o índice
    df = df.iloc[1:].reset_index(drop=True)
    
    print(f'Como está df antes de filtrar?\n{df.head(10)}\n\n')

    if "Critica" not in df.columns:
        df.insert(9, "Critica", "SUCESSO")

    

    if "Valor Acatado" not in df.columns:
        df.insert(5, "Valor Acatado", 0)

    

    # NOME/CPF/MATRICULA/cod_orgao/VALOR/CODIGO DA VERBA/ADE/Critica/Valor/Margem
    df.rename(columns={"MATRICULA": "Matrícula", "Critica": "Crítica", "VALOR": "Valor Lançado"}, inplace=True)

    # Se a crítica for SUCESSO e Valor Acatado estiver vazio, preenche com o Valor Lançado
    df.loc[(df['Crítica'] == 'SUCESSO') & (df['Valor Acatado'].isnull() | (df['Valor Acatado'] == '')), 'Valor Acatado'] = df['Valor Lançado']

    df = df[["Matrícula", "CPF", "Valor Lançado", "Crítica", "Valor Acatado"]].copy()

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

    mask_margem = df['Crítica'].fillna('').str.contains('valor acatado')
        
    if mask_margem.any():
        print('Encontradas críticas de margem insuficiente. Extraindo valores...')
        df['Valor Acatado'] = df.apply(
            lambda row: row['Crítica'].split('valor acatado: ')[1].split(' ')[0].rstrip('.') if 'valor acatado' in str(row['Crítica']) else row['Valor Acatado'],
            axis=1
        )

    # Aplicação limpa e direta no DataFrame:
    df['Valor_lancado'] = df['Valor Lançado'].apply(limpar_moeda_universal)
    df['Valor_descontado'] = df['Valor Acatado'].apply(limpar_moeda_universal)

    return df

caminho = r"Z:\Dados\NOVA ESTRUTURA\LANÇAMENTO CARTÕES\TRABALHANDO\2026\07 - Julho\PREF GOIANIA\LANCAMENTOS E RETORNOS\SUCESSO LANCAMENTO CARTÃO PREF GOIANIA 07-2026.xlsx"

arquivo_lido = processar_portal_exemplo(caminho=caminho)

print(arquivo_lido.head(30))