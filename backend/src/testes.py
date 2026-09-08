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
    
    

    # NM_PESSOA|NR_CPF	NR_MATRICULA|VL_PREVISAO_DESCONTO|valor acatado|críticas

    if 'Critica' in df.columns or 'DS_OBSERVACAO' in df.columns or 'CRITICA' in df.columns:
        df = df.rename(columns={'DS_OBSERVACAO': 'Critica', 'CRITICA': 'Critica'}, errors='ignore')
        # 1. Garante a existência da coluna
        if 'Valor Acatado' not in df.columns:
            df['Valor Acatado'] = '0'

        # 2. Cria a máscara para focar apenas nas linhas de acatamento
        mask = df['Critica'].str.contains('Valor acatado parcialmente|Valor acatado integralmente', case=False, na=False)

        # 3. A MÁGICA: Pega o texto da 'Critica', divide no '|' e pega a última parte (str[-1])
        df.loc[mask, 'Valor Acatado'] = (
            df.loc[mask, 'Critica']
            .astype(str)
            .str.split('|')
            .str[-1]       # Pega o que vier depois do pipe
            .str.strip()   # Remove espaços invisíveis das pontas
        )

        # 4. Garante que quem NÃO foi acatado (~mask) e estiver vazio vire '0'
        vazios_ou_nulos = df['Valor Acatado'].isna() | (df['Valor Acatado'] == '')
        df.loc[~mask & vazios_ou_nulos, 'Valor Acatado'] = '0'

        print(f'DF\n{df.head(-30)}')
        

    df = df.rename(columns={
        'NR_CPF': 'CPF',
        'NR_MATRICULA': 'Matrícula',
        'MATRICULA': 'Matrícula',
        'VL_PREVISAO_DESCONTO': 'Valor Lançado',
        'VL_PARCELA_PREVISTA': 'Valor Lançado',
        'VALOR': 'Valor Lançado',
        'valor acatado': 'Valor Acatado',
        'críticas': 'Crítica',
        'Cpf': 'CPF',
        'CPf': 'CPF',
        'Matricula': 'Matrícula',
        'Valor Informado': 'Valor Lançado',
        'Critica': 'Crítica'
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
    df['Valor_lancado'] = df['Valor_lancado']


    df['Valor_descontado'] = df['Valor Acatado'].apply(limpar_moeda_universal)

    return df

caminho = r"Z:\Dados\NOVA ESTRUTURA\LANÇAMENTO CARTÕES\TRABALHANDO\2026\08 - Agosto\PREF FLORIANÓPOLIS\LANÇAMENTOS E RETORNOS\RETORNO PREF FLORIANOPOLIS COMPRAS 08-2026.xlsx"

arquivo_lido = processar_portal_exemplo(caminho=caminho)

print(arquivo_lido.head(-30))