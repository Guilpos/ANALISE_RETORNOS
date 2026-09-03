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

    if "Valor Acatado" not in df.columns:
        df.insert(5, "Valor Acatado", 0)

    # NOME/CPF/MATRICULA/cod_orgao/VALOR/CODIGO DA VERBA/ADE/Critica/Valor/Margem
    df.rename(columns={"MATRICULA": "Matrícula", "VALOR": "Valor Lançado"}, inplace=True)

    df = df[["Matrícula", "CPF", "Valor Lançado", "Critica", "Valor Acatado"]].copy()

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
    df['Valor_descontado'] = df['Valor Acatado'].apply(limpar_moeda_universal)

    return df

caminho = r"C:\PESSOAL\TESTE PROJETO DE ANALISE DE RETORNOS\Critica_LANÇAMENTO CARTÃO PREF RIBEIRAO PRETO 07.2026_20260710_1152.xlsx"

arquivo_lido = processar_portal_exemplo(caminho=caminho)

print(arquivo_lido.head())