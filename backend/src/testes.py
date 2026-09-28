from utils.file_readers import ler_arquivo_seguro
from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_delimitador_ponto, alinhar_tipagem_chaves
import openpyxl
import pandas as pd
import xlrd
import io
import xml.etree.ElementTree as ET


def processar_portal_exemplo(conteudo_bytes: bytes):    

    # tabela = io.BytesIO(conteudo_bytes)

    # 1. Transformamos os bytes puros em texto legível ignorando possíveis erros de encoding
    texto = conteudo_bytes.decode('utf-8', errors='ignore')

    dados_limpos = []

    # 2. Lê o arquivo linha por linha
    for linha in texto.splitlines():
        linha = linha.strip()
        
        # 3. Filtra: Ignora cabeçalhos e rodapés, focando apenas nos dados reais
        if linha.startswith('linha('):
            # O arquivo é separado por tabulações (\t)
            linha_corrigida = linha.replace('cpf:', '\tcpf:').replace('\t\t', '\t')
            partes = linha_corrigida.split('\t')

            # Estrutura esperada:
            # partes[0] = "linha(1)"
            # partes[1] = "mat: 23811"
            # partes[2] = "cpf: 82339929334"
            # partes[3] = "rub: 1005"
            # partes[4] = "ope_id: 207414" (ou "-")
            # partes[5] = "Valor no arquivo: R$ 431.1 "
            # partes[6] = "Enviado corretamente para débito"
            
            try:
                # Removemos os rótulos (ex: "mat: ") e os espaços em branco de cada pedaço
                matricula = partes[1].replace('mat:', '').strip()
                cpf = partes[2].replace('cpf:', '').strip()
                rubrica = partes[3].replace('rub:', '').strip()
                ope_id = partes[4].replace('ope_id:', '').strip()
                valor_str = partes[5].replace('Valor no arquivo: R$', '').strip()
                critica = partes[6].strip()
                
                dados_limpos.append({
                    'Matrícula': matricula,
                    'CPF': cpf,
                    'Rubrica': rubrica,
                    'ID Operação': ope_id,
                    'Valor Lançado': float(valor_str), # Já converte o 431.1 para float
                    'Crítica': critica
                })
            except IndexError:
                # Caso alguma linha venha corrompida, ela não quebra o loop
                continue

    # 4. Transforma a lista de dicionários num DataFrame consolidado
    df = pd.DataFrame(dados_limpos)

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

# Coloque o caminho exato onde você salvou o arquivo de teste
caminho_do_arquivo = r"C:\Users\guilherme.campos.AKRKOPERACIONAL\Downloads\log_LANCAMENTO CARTÃO PREF SÃO LUIS CAPITAL 10.2026.txt"
# Chama a função que criamos passando os bytes simulados

# 2. Leia o arquivo em bytes
with open(caminho_do_arquivo, "rb") as f:
    conteudo_bytes = f.read()

df_teste = processar_portal_exemplo(conteudo_bytes=conteudo_bytes)

# Exibe o resultado no terminal para você conferir as colunas
print(df_teste.tail(30))
print(df_teste.head(30),'\n')
print('O que está na linha 142:\n', df_teste.iloc[142],'\n')

print("\nTipos de dados gerados:")
print(df_teste.dtypes)