from utils.file_readers import ler_arquivo_seguro
from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_retorno_consigfacil, alinhar_tipagem_chaves

def processar_portal_exemplo(caminho: str):
    # 1. Leitura segura (todos os dados nascem como texto bruto)
    convenio = "82"
    df = ler_arquivo_seguro(caminho, "Teste Pref João Pessoa 08-2026.xlsx", convenio)

    # print(f'Como está df antes de filtrar?\n{df.head(10)}\n\n')

    # Use o .iloc (todas as linhas ':', e as colunas nas posições desejadas):
    df_filtrado = df.iloc[:, [2, 3, 7, 16,18]].copy()

    # 2. Atribui os novos nomes na ordem exata dos índices selecionados
    df_filtrado.columns = ['CPF', 'Valor Lançado', 'Crítica', 'Data', 'Valor Acatado']

    df = df_filtrado.copy()
    
    # 2. Higienização das colunas padrão
    df['cpf_formatado'] = limpar_cpf(df['CPF'])
    df['Valor_lancado'] = limpar_moeda_retorno_consigfacil(df['Valor Lançado'])
    df['valor_descontado'] = limpar_moeda_retorno_consigfacil(df['Valor Acatado'])
    df['Data_formatada'] = limpar_data(df['Data'])

    # 3. Alinhamento Estrito de Tipos para Cruzamento
    # Garante que as chaves de relacionamento estejam exatamente no mesmo tipo (string)
    '''df['texto_contratos_sujo'] = alinhar_tipagem_chaves(df, 'texto_contratos_sujo')
    df['cpf_contratos'] = alinhar_tipagem_chaves(df, 'cpf_contratos')'''

    return df

caminho = r"C:\Users\user\Downloads\Teste Pref João Pessoa 08-2026.xlsx"

arquivo_lido = processar_portal_exemplo(caminho=caminho)

print(arquivo_lido.head(30))