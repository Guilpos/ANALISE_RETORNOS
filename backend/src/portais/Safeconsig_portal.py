from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_universal, limpar_moeda_delimitador_ponto, alinhar_tipagem_chaves
from utils.validators import validar_matematica_descontos
from utils.analisador import analisar_dados
import pandas as pd

def processar_portal_safeconsig(df_bruto: pd.DataFrame, convenio: str, portal: str) -> pd.DataFrame:

    df = df_bruto
    
    # 3. Limpar o 'Valor Lançado' (trocar vírgula por ponto e converter para float)
    df['Valor Lançado'] = df['Valor Lançado'] # .str.replace(',', '.', regex=False).astype(float)
    
    # 4. Criar a coluna 'Valor Acatado' partindo do zero
    df['Valor Acatado'] = ''
    
    # --- LÓGICA DE ACATAMENTO ---
    
    # A) Tratamento do SUCESSO TOTAL
    mask_sucesso = df['Crítica'].str.strip() == 'SUCESSO'
    df.loc[mask_sucesso, 'Valor Acatado'] = df.loc[mask_sucesso, 'Valor Lançado']
    
    # B) Tratamento do SUCESSO PARCIAL
    # Identifica as linhas que contêm a palavra "PARCIAL" na crítica
    mask_parcial = df['Crítica'].str.contains('SUCESSO PARCIAL', na=False, case=False)
    
    # Extrai dinamicamente apenas o número que vem depois do "R$"
    df.loc[mask_parcial, 'Valor Acatado'] = (
        df.loc[mask_parcial, 'Crítica']
        .str.split('R\$')                     # Corta o texto exatamente no 'R$'
        .str[-1]                              # Pega a última parte (onde ficou o número)
        .str.strip()                          # Remove espaços sobrando
    )

    # 2. Higienização das colunas padrão
    df['cpf_formatado'] = limpar_cpf(df['CPF'])
    
    # df['Data_formatada'] = limpar_data(df['Data'])

    # 3. Alinhamento Estrito de Tipos para Cruzamento
    # Garante que as chaves de relacionamento estejam exatamente no mesmo tipo (string)
    df['Matricula_formatada'] = alinhar_tipagem_chaves(df, 'Matrícula')
        
    # Aplicação limpa e direta no DataFrame:
    df['Valor_lancado'] = df['Valor Lançado'].apply(limpar_moeda_universal)
    df['Valor_lancado'] = df['Valor_lancado']


    df['Valor_descontado'] = df['Valor Acatado'].apply(limpar_moeda_universal)

    return df