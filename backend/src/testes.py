from utils.file_readers import ler_arquivo_seguro
from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_delimitador_ponto, alinhar_tipagem_chaves
import openpyxl
import pandas as pd
import xlrd

def processar_portal_exemplo(caminho: str):
    df = pd.read_excel(caminho,  header=None, dtype=str, engine='xlrd')
    df.columns = df.iloc[4]

    # Remove a primeira linha (índice 0) que foi usada como molde e reseta o índice
    df = df.iloc[5:].reset_index(drop=True)

    # Remover colunas vazias
    df = df.dropna(axis=1, how='all')
    
    print(f'Como está df antes de filtrar?\n{df.head(10)}\n\n')

    

    if "Valor Acatado" not in df.columns:
        df.insert(5, "Valor Acatado", 0)
        df['Valor Acatado'] = df['Valor Acatado'].astype(str)

    

    # NOME/CPF/MATRICULA/cod_orgao/VALOR/CODIGO DA VERBA/ADE/Critica/Valor/Margem
    df.rename(columns={"Descrição da crítica": "Crítica", "Valor": "Valor Lançado"}, inplace=True)

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

    # 4. Atribuição direta dos valores já numéricos (Sobrescreve o que foi limpo acima)
    df['Crítica'] = df['Crítica'].fillna('')  # Preenche valores nulos com string vazia
    df.loc[df['Crítica'] == '', 'Valor Acatado'] = df['Valor Lançado']

    # Aplicação limpa e direta no DataFrame:
    df['Valor_lancado'] = df['Valor Lançado'].apply(limpar_moeda_universal)
    df['Valor_descontado'] = df['Valor Acatado'].apply(limpar_moeda_universal)

    return df

caminho = r"Z:\Dados\NOVA ESTRUTURA\LANÇAMENTO CARTÕES\TRABALHANDO\2026\08 - Agosto\PREF+PREV JUIZ DE FORA\LANÇAMENTOS E RETORNOS\RETORNO PREF JUIZ DE FORA 08-2026.xls"

arquivo_lido = processar_portal_exemplo(caminho=caminho)

print(arquivo_lido.head(30))