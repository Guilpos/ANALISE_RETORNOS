from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_universal, limpar_moeda_delimitador_ponto, alinhar_tipagem_chaves
from utils.validators import validar_matematica_descontos
from utils.analisador import analisar_dados
import pandas as pd

def processar_portal_neoconsig(df_bruto: pd.DataFrame, convenio: str, portal: str) -> pd.DataFrame:
    df = df_bruto

    # OPCIONAL: Se quiser adicionar o Valor Acatado seguindo o padrão que fizemos antes
    if not df.empty:
        df['Valor Acatado'] = 0.00
        # Se a crítica for "Enviado corretamente", acata o valor lançado
        sucesso_mask = df['Crítica'].str.contains('Enviado corretamente', case=False, na=False)
        df.loc[sucesso_mask, 'Valor Acatado'] = df.loc[sucesso_mask, 'Valor Lançado']
        
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