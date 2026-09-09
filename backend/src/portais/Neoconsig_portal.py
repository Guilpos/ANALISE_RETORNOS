from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_universal, limpar_moeda_delimitador_ponto, alinhar_tipagem_chaves
from utils.validators import validar_matematica_descontos
from utils.analisador import analisar_dados
import pandas as pd

def processar_portal_neoconsig(df_bruto: pd.DataFrame, convenio: str, portal: str) -> pd.DataFrame:
    df = df_bruto

    # OPCIONAL: Se quiser adicionar o Valor Acatado seguindo o padrão que fizemos antes
    if not df.empty:
            df['Valor Acatado'] = 0.00
            
            # Criação das máscaras
            sucesso_mask = df['Crítica'].str.contains('Enviado corretamente|Valor no sistema:', case=False, na=False)
            parcial_mask = df['Crítica'].str.contains('Valor acima do limite,', case=False, na=False)
            
            # 1. Aloca o valor lançado para os sucessos
            df.loc[sucesso_mask, 'Valor Acatado'] = df.loc[sucesso_mask, 'Valor Lançado']
            
            # 2. Limpa o texto, remove pontuações e converte para float
            df.loc[parcial_mask, 'Valor Acatado'] = (
                df.loc[parcial_mask, 'Crítica']
                .str.replace('Valor acima do limite, enviado para débito no limite (R$', '', regex=False)
                .str.replace(')', '', regex=False)
                .str.rstrip('.') # O acessor .str é obrigatório aqui
                .str.strip()     # Remove espaços residuais
                .astype(float)   # Transforma a string extraída em número real
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