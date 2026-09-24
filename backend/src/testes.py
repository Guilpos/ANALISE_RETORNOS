from utils.file_readers import ler_arquivo_seguro
from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_delimitador_ponto, alinhar_tipagem_chaves
import openpyxl
import pandas as pd
import xlrd
import io
import xml.etree.ElementTree as ET

tabela_erros = {
    "ESCC0000": "Processamento realizado com sucesso.", #[cite: 3]
    "ESCC0010": "Ente não cadastrado.", #[cite: 3]
    "ESCC0015": "Número do CPF inválido.", #[cite: 3]
    "ESCC0031": "Consignatário não cadastrado.", #[cite: 3]
    "ESCC0032": "Consignatário não está ativo.", #
    "ESCC0050": "Margem insuficiente.", #[cite: 4]
    "ESCC0054": "Número Único da Averbação inválido.", #[cite: 4]
    "ESCC0082": "Averbação com parcela provisionada. Parcela sem débito na folha de pagamento.", #[cite: 5]
    "ESCC0116": "Encontrados múltiplos registros com a mesma identificação ou matrícula. Realize nova pesquisa incluindo o Órgão.", #[cite: 5]
    "ESCC0144": "Não foi possível cancelar a averbação. Número único da averbação informado não está vinculado a um refinanciamento.", #[cite: 6]
    "ESCC0207": "A requisição excedeu a quantidade de linhas permitidas no resultado. Realize um novo filtro, utilizando outros critérios que possibilitem um resultado de pesquisa menor.", #[cite: 7]
    # Adicione os demais códigos da sua tabela aqui...
}

def processar_portal_exemplo(conteudo_bytes: bytes, conteudo_bytes_2: bytes):    
    # Faz a leitura direta da variável em bytes (ex: b'<?xml version="1.0"...')
    root = ET.fromstring(conteudo_bytes)

    tabela = io.BytesIO(conteudo_bytes_2)

    df_2 = pd.read_excel(tabela, header=None)

    df_2.columns = df_2.iloc[0].astype(str).str.strip()

    df_2 = df_2.iloc[1:].reset_index(drop=True)

    df_2.rename(columns={'Nº AVERBAÇÃO SCC': 'Matrícula', 'VALOR AVERBADO': 'Valor Lançado'}, inplace=True)

    print(f'Amostra de df_2:\n{df_2.head(15)}')

    # Define o mapeamento do namespace
    ns = {'cip': 'http://www.cip-bancos.org.br/ARQ/ASCC024.xsd'}

    linhas = []

    # O root já é o nó raiz da árvore, então iteramos a partir dele
    for grupo in root.findall('.//cip:Grupo_ASCC024RET_Consigrio', ns):
        
        cnpj_ente = grupo.find('cip:CNPJBaseEnte', ns)
        cnpj_ente_text = cnpj_ente.text if cnpj_ente is not None else None

        codigo_encontrado = None
        for elemento in grupo.iter():
            if 'CodErro' in elemento.attrib:
                codigo_encontrado = elemento.attrib['CodErro']
                break # Interrompe a busca após achar o primeiro erro

        consignc = grupo.find('cip:Grupo_ASCC024RET_Consignc', ns)
        
        if consignc is not None:
            cpf = consignc.find('cip:NumCPFServdr', ns)
            ade = consignc.find('cip:NUAvebcSCC', ns)
            contrato = consignc.find('cip:NumContrtoIF', ns)
            controle_cip = consignc.find('cip:NumCtrlCIP', ns)
            data_proc = consignc.find('cip:DtProxProcmntArqDesctFolha', ns)

            linhas.append({
                'CPF': cpf.text if cpf is not None else None,
                'Contrato': contrato.text if contrato is not None else None,
                'ADE_Averbacao': ade.text if ade is not None else None,
                'Controle_CIP': controle_cip.text if controle_cip is not None else None,
                'Data_Processamento': data_proc.text if data_proc is not None else None,
                'CNPJ_Ente': cnpj_ente_text,
                'Cod_Erro': codigo_encontrado
            })

    df = pd.DataFrame(linhas)

    df.rename(columns={"ADE_Averbacao": "Matrícula"}, inplace=True)

    # 2. Criação da Coluna "Crítica" fazendo o PROCV (map) com o dicionário
    # Se o código não estiver no dicionário, preenche com "Erro não catalogado"
    df['Crítica'] = df['Cod_Erro'].map(tabela_erros).fillna('Sucesso / Erro não catalogado')
    
    # Limpeza opcional para quando não há erro (Cod_Erro vem vazio)
    df.loc[df['Cod_Erro'].isnull(), 'Crítica'] = 'Sucesso'

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

    df['Valor Lançado'] = df["Matrícula"].map(df_2.set_index('Matrícula')['Valor Lançado'])

    df.loc[df['Crítica'] == 'Sucesso', 'Valor Acatado'] = df['Valor Lançado']

    # 2. Higienização das colunas padrão
    df['cpf_formatado'] = limpar_cpf(df['CPF'])
    
    # df['Data_formatada'] = limpar_data(df['Data'])

    # 3. Alinhamento Estrito de Tipos para Cruzamento
    # Garante que as chaves de relacionamento estejam exatamente no mesmo tipo (string)
    df['Matricula_formatada'] = alinhar_tipagem_chaves(df, 'Matrícula')

    df['Valor_lancado'] = df['Valor Lançado'].apply(limpar_moeda_universal)

    df['Valor_descontado'] = df['Valor Acatado'].apply(limpar_moeda_universal)

    return df

# Coloque o caminho exato onde você salvou o arquivo de teste
caminho_do_arquivo = r"Z:\Dados\NOVA ESTRUTURA\LANÇAMENTO CARTÕES\TRABALHANDO\2026\09 - Setembro\PREF SAO PAULO\LANÇAMENTOS E RETORNOS\ASCC024_40083667_20260910_00001_RET.xml"
caminho_do_arquivo_2 = r"Z:\Dados\NOVA ESTRUTURA\LANÇAMENTO CARTÕES\TRABALHANDO\2026\09 - Setembro\PREF SAO PAULO\LANÇAMENTOS E RETORNOS\LANÇAMENTO CARTAO PREF. SÃO PAULO - GERAL 09-2026.xlsx"
# Chama a função que criamos passando os bytes simulados

# 2. Leia o arquivo em bytes
with open(caminho_do_arquivo, "rb") as f:
    conteudo_bytes = f.read()

with open(caminho_do_arquivo_2, "rb") as f:
    conteudo_bytes_2 = f.read()

df_teste = processar_portal_exemplo(conteudo_bytes=conteudo_bytes, conteudo_bytes_2=conteudo_bytes_2)

# Exibe o resultado no terminal para você conferir as colunas
print(df_teste.tail(30))
print("\nTipos de dados gerados:")
print(df_teste.dtypes)