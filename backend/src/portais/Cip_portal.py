from utils.formatters import limpar_cpf, limpar_moeda_universal, alinhar_tipagem_chaves
from utils.tabelas_cip import tabela_erros_completa
import pandas as pd

def processar_portal_cip(df_bruto_1: pd.DataFrame, df_bruto_2: pd.DataFrame, convenio: str, portal: str) -> pd.DataFrame:
    """
    Recebe os dois DataFrames gerados, mapeia os valores do Excel para o XML
    e cria as colunas de Crítica e Valor Lançado.
    """
    df_retorno = df_bruto_1
    df_lancamento = df_bruto_2
    
    # 1. Padroniza as colunas chaves
    df_retorno.rename(columns={"ADE_Averbacao": "Matrícula"}, inplace=True)
    
    if 'Nº AVERBAÇÃO SCC' in df_lancamento.columns:
        df_lancamento.rename(columns={'Nº AVERBAÇÃO SCC': 'Matrícula', 'VALOR AVERBADO': 'Valor Lançado'}, inplace=True)
    
    # 2. Cria o dicionário para mapeamento usando o Pandas (Excel -> Dicionário)
    # Garante que as chaves sejam strings padronizadas para não dar erro no cruzamento
    df_lancamento['Matrícula'] = df_lancamento['Matrícula'].astype(str).str.strip()
    df_retorno['Matrícula'] = df_retorno['Matrícula'].astype(str).str.strip()
    
    mapa_valores = df_lancamento.set_index('Matrícula')['Valor Lançado'].to_dict()
    
    # 3. Executa o cruzamento (Traz os valores do Excel para a linha correta do XML)
    df_retorno['Valor Lançado'] = df_retorno['Matrícula'].map(mapa_valores)
    
    # 4. (Opcional) Adiciona aquela lógica do dicionário de críticas
    tabela_erros = tabela_erros_completa
    
    df_retorno['Crítica'] = df_retorno['Cod_Erro'].map(tabela_erros).fillna('Erro não catalogado')
    df_retorno.loc[df_retorno['Cod_Erro'].isnull(), 'Crítica'] = 'Sucesso'

    # 2. Higienização das colunas padrão
    df_retorno['cpf_formatado'] = limpar_cpf(df_retorno['CPF'])

    df_retorno.loc[df_retorno['Crítica'] == 'Sucesso', 'Valor Acatado'] = df_lancamento['Valor Lançado']
    
    # df['Data_formatada'] = limpar_data(df['Data'])

    # 3. Alinhamento Estrito de Tipos para Cruzamento
    # Garante que as chaves de relacionamento estejam exatamente no mesmo tipo (string)
    df_retorno['Matricula_formatada'] = alinhar_tipagem_chaves(df_retorno, 'Matrícula')

    df_retorno['Valor_lancado'] = df_retorno['Valor Lançado'].apply(limpar_moeda_universal)

    df_retorno['Valor_descontado'] = df_retorno['Valor Acatado'].apply(limpar_moeda_universal)
    
    return df_retorno

