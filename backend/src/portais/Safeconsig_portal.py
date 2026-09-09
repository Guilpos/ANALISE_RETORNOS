from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_universal, limpar_moeda_delimitador_ponto, alinhar_tipagem_chaves
from utils.validators import validar_matematica_descontos
from utils.analisador import analisar_dados
import pandas as pd

def processar_portal_safeconsig(df_bruto: pd.DataFrame, convenio: str, portal: str) -> pd.DataFrame:
    df = df_bruto

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
        
    # Aplicação limpa e direta no DataFrame:
    df['Valor_lancado'] = df['Valor Lançado'].apply(limpar_moeda_universal)
    df['Valor_lancado'] = df['Valor_lancado']


    df['Valor_descontado'] = df['Valor Acatado'].apply(limpar_moeda_universal)

    return df