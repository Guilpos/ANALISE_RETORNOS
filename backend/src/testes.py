from utils.file_readers import ler_arquivo_seguro
from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_delimitador_ponto, alinhar_tipagem_chaves
from utils.tabelas_cip import tabela_erros_completa
import openpyxl
import pandas as pd
import xlrd
import csv
import io
import xml.etree.ElementTree as ET


def processar_portal_exemplo(conteudo_bytes_1: bytes, conteudo_bytes_2: bytes) -> pd.DataFrame:    

    # 2. ARQUIVOS XML -> RETORNOS
    def trata_xml(arquivo_xml):
        try:
            root = ET.fromstring(arquivo_xml)
            ns = {'cip': 'http://www.cip-bancos.org.br/ARQ/ASCC024.xsd'}
            linhas = []

            # 1. Pega os Grupos Pais: tanto os que deram CERTO quanto os que deram ERRADO
            grupos = root.findall('.//cip:Grupo_ASCC024RET_Consigrio', ns) + \
                    root.findall('.//cip:Grupo_ASCC024_Consigrio', ns)
                    
            for grupo in grupos:
                cnpj_ente = grupo.find('.//cip:CNPJBaseEnte', ns)
                cnpj_ente_text = cnpj_ente.text if cnpj_ente is not None else None
                
                # 2. Pega as Consignações (os contratos em si), também somando os de sucesso e os rejeitados
                consignacoes = grupo.findall('.//cip:Grupo_ASCC024RET_Consignc', ns) + \
                            grupo.findall('.//cip:Grupo_ASCC024_Consignc', ns)
                            
                for consignc in consignacoes:
                    cpf = consignc.find('cip:NumCPFServdr', ns)
                    ade = consignc.find('cip:NUAvebcSCC', ns)
                    
                    # 3. O contrato muda de nome dependendo do resultado. Tenta o de sucesso, se não achar tenta o de erro
                    contrato = consignc.find('cip:NumContrtoIF', ns)
                    if contrato is None:
                        contrato = consignc.find('cip:NumContrto', ns)
                        
                    controle_cip = consignc.find('cip:NumCtrlCIP', ns)

                    # 4. Procura o CodErro (se for sucesso, isso vai passar reto e gravar None)
                    codigo_encontrado = None
                    if ade is not None and 'CodErro' in ade.attrib:
                        codigo_encontrado = ade.attrib['CodErro']
                    elif contrato is not None and 'CodErro' in contrato.attrib:
                        codigo_encontrado = contrato.attrib['CodErro']
                    else:
                        for elemento in consignc.iter():
                            if 'CodErro' in elemento.attrib:
                                codigo_encontrado = elemento.attrib['CodErro']
                                break

                    linhas.append({
                        'CPF': cpf.text if cpf is not None else None,
                        'Contrato': contrato.text if contrato is not None else None,
                        'ADE_Averbacao': ade.text if ade is not None else None,
                        'Controle_CIP': controle_cip.text if controle_cip is not None else None,
                        'CNPJ_Ente': cnpj_ente_text,
                        'Cod_Erro': codigo_encontrado
                    })
                    
            return pd.DataFrame(linhas)
        except Exception as erro_final:
            raise ValueError(f"Erro ao ler arquivo XML: {str(erro_final)}")

    xml_tratado = trata_xml(conteudo_bytes_1)
    print('Tamanho da planilha xml_tratado: ', len(xml_tratado))
    df_retorno = xml_tratado

    # 1. ARQUIVOS EXCEL (.xlsx, .xls) -> LANÇAMENTOS
    def trata_xlsx(arquivo_xlsx):
        try:
            tabela_memoria = io.BytesIO(arquivo_xlsx)
            df = pd.read_excel(tabela_memoria, dtype=str) # header=0 para pegar nome das colunas
            return df
        except Exception:
            try:
                tabela_memoria = io.BytesIO(arquivo_xlsx)
                tabelas = pd.read_html(tabela_memoria, decimal=',', thousands='.')
                df = tabelas[0]
                return df
            except Exception as erro_final:
                raise ValueError(f"Erro ao ler arquivo Excel/HTML: {str(erro_final)}")
            
    df_lancamento = trata_xlsx(conteudo_bytes_2)
    
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
    df_retorno['Valor Acatado'] = df_retorno['Matrícula'].map(df_lancamento.set_index('Matrícula')['Valor Lançado'])
    df_retorno.loc[df_retorno['Crítica'] != 'Sucesso', 'Valor Acatado'] = '0'

    print('Amostra de df_retorno\n', df_retorno.head(15))

    df = df_retorno
        

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

        
    '''# OPCIONAL: Se quiser adicionar o Valor Acatado seguindo o padrão que fizemos antes
    if not df.empty:
        df['Valor Acatado'] = '0'
        
        # Criação das máscaras
        sucesso_mask = df['Crítica'].str.contains('Em aberto', case=False, na=False)
        
        # 1. Aloca o valor lançado para os sucessos
        df.loc[sucesso_mask, 'Valor Acatado'] = df.loc[sucesso_mask, 'Valor Lançado']'''
            
        
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

    df.to_excel(f'C:\PESSOAL\TESTE PROJETO DE ANALISE DE RETORNOS\GOV SAO PAULO RETORNO TRATADO PELA ANALISE DE RETORNO TESTE.xlsx', index=False)

    return df

# Coloque o caminho exato onde você salvou o arquivo de teste
caminho_do_arquivo_1 = r"Z:\Dados\NOVA ESTRUTURA\LANÇAMENTO CARTÕES\TRABALHANDO\2026\10 - Outubro\GOV SP\PMESP+SPPREV\LANÇAMENTOS E RETORNOS\RETORNO GOV SP PMESP+SPPREV 10.2026.xml"
caminho_do_arquivo_2 = r"Z:\Dados\NOVA ESTRUTURA\LANÇAMENTO CARTÕES\TRABALHANDO\2026\10 - Outubro\GOV SP\PMESP+SPPREV\LANÇAMENTOS E RETORNOS\LANÇAMENTO GOV SP PMESP+SPPREV 10.2026.xlsx"
# Chama a função que criamos passando os bytes simulados

# 2. Leia o arquivo em bytes
with open(caminho_do_arquivo_1, "rb") as f:
    conteudo_bytes_1 = f.read()

with open(caminho_do_arquivo_2, "rb") as f:
    conteudo_bytes_2 = f.read()

df_teste = processar_portal_exemplo(conteudo_bytes_1=conteudo_bytes_1, conteudo_bytes_2=conteudo_bytes_2)

# Exibe o resultado no terminal para você conferir as colunas
# print(df_teste.head(30),'\n')
'''
print(df_teste.tail(30))

print('O que está na linha 142:\n', df_teste.iloc[142],'\n')'''

print("\nTipos de dados gerados:")
print(df_teste.dtypes)