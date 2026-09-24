# utils/file_readers.py
import pandas as pd
from utils.portais_convenios_lista import portal_escolhido, convenio_escolher
from portais import base_portal
import csv
import xlrd
import io
import xml.etree.ElementTree as ET

def ler_arquivo_inseguro(conteudo_bytes: bytes, nome_arquivo: str, convenio: str) -> pd.DataFrame:
    caminho_lower = nome_arquivo.lower()
    
    # 1. ARQUIVOS EXCEL (.xlsx, .xls) -> LANÇAMENTOS
    if caminho_lower.endswith('.xlsx') or caminho_lower.endswith('.xls'):
        try:
            tabela_memoria = io.BytesIO(conteudo_bytes)
            df = pd.read_excel(tabela_memoria, dtype=str, header=None) # header=0 para pegar nome das colunas
            return df
        except Exception:
            try:
                tabela_memoria = io.BytesIO(conteudo_bytes)
                tabelas = pd.read_html(tabela_memoria, header=None, decimal=',', thousands='.')
                df = tabelas[0]
                return df
            except Exception as erro_final:
                raise ValueError(f"Erro ao ler arquivo Excel/HTML: {str(erro_final)}")

    # 2. ARQUIVOS XML -> RETORNOS
    if caminho_lower.endswith('.xml'):
        try:
            root = ET.fromstring(conteudo_bytes)
            ns = {'cip': 'http://www.cip-bancos.org.br/ARQ/ASCC024.xsd'}
            linhas = []

            for grupo in root.findall('.//cip:Grupo_ASCC024RET_Consigrio', ns):
                cnpj_ente = grupo.find('cip:CNPJBaseEnte', ns)
                cnpj_ente_text = cnpj_ente.text if cnpj_ente is not None else None
        
                codigo_encontrado = None
                for elemento in grupo.iter():
                    if 'CodErro' in elemento.attrib:
                        codigo_encontrado = elemento.attrib['CodErro']
                        break 
        
                consignc = grupo.find('cip:Grupo_ASCC024RET_Consignc', ns)
                if consignc is not None:
                    cpf = consignc.find('cip:NumCPFServdr', ns)
                    ade = consignc.find('cip:NUAvebcSCC', ns)
                    contrato = consignc.find('cip:NumContrtoIF', ns)
                    controle_cip = consignc.find('cip:NumCtrlCIP', ns)
                    
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

def ler_arquivo_seguro(conteudo_bytes: bytes, nome_arquivo: str, convenio: str) -> pd.DataFrame:
    """
    Lê o arquivo diretamente da memória (bytes) sem gravar no disco.
    """
    caminho_lower = nome_arquivo.lower()
    
    # A sua lógica de escolha de portal!
    nome_convenio = convenio_escolher()[convenio]

    try:
        print('Nome Convenio:', nome_convenio)
    except KeyError:
        print("Convenio não encontrado na lista de convenios.")

    portal = portal_escolhido(nome_convenio)

    try:
        print('Portal escolhido:', portal)
    except KeyError:
        print("Portal não encontrado na lista de portais.")
    
    # 1. ARQUIVOS EXCEL (.xlsx, .xls)
    if caminho_lower.endswith('.xlsx') or caminho_lower.endswith('.xls'):
        try:
            # TENTATIVA 1: Ler como Excel normal
            tabela_memoria = io.BytesIO(conteudo_bytes)
            df = pd.read_excel(tabela_memoria, dtype=str, header=None)
            
            df = colunas_usadas(modelo=portal, df=df)
            df_resultado = base_portal.decidir_layout_portal(portal=portal, convenio=nome_convenio, arquivo=df)
            return df_resultado
            
        except Exception:
            try:
                # TENTATIVA 2: Se o Excel falhar, tenta ler como HTML disfarçado
                # Precisamos recriar o BytesIO porque a tentativa anterior consumiu a leitura do arquivo original
                tabela_memoria = io.BytesIO(conteudo_bytes)
                tabelas = pd.read_html(tabela_memoria, header=0, decimal=',', thousands='.')
                df = tabelas[0]

                df = colunas_usadas(modelo=portal, df=df)
                df_resultado = base_portal.decidir_layout_portal(portal=portal, convenio=nome_convenio, arquivo=df)
                return df_resultado # O retorno que faltava!

            except Exception as erro_final:
                # TENTATIVA 3: Se as duas falharem, encerra com o erro real
                raise ValueError(f"Erro ao ler arquivo: Não é um Excel nem um HTML válido. Detalhe: {str(erro_final)}")

    if caminho_lower.endswith('.xml'):
        try:
            # Faz a leitura direta da variável em bytes (ex: b'<?xml version="1.0"...')
            root = ET.fromstring(conteudo_bytes)

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
        except Exception as erro_final:
            # TENTATIVA 3: Se as duas falharem, encerra com o erro real
            raise ValueError(f"Erro ao ler arquivo: Não é um XML válido. Detalhe: {str(erro_final)}")
    
    if caminho_lower.endswith('.txt'):
        try:
            tabela_memoria = io.BytesIO(conteudo_bytes)

            # Ao contrário de Consigfacil, Econsig não terá outro tratamento de dado, ele irá direto para base portal
            if portal == "ECONSIG_1":
                # Aplica a régua posicional exata do layout
                larguras = [10, 11, 50, 10, 10, 9, 1, 100]
                nomes_colunas = ['Matrícula', 'CPF', 'Nome', 'Codigo', 'Valor Lançado', 'Competencia', 'Tipo', 'Crítica']

                # Coloque isso antes de chamar o pd.read_fwf ou pd.read_csv
                # print(f"Tamanho do conteúdo detectado: {len(tabela_memoria.getvalue())} caracteres")
                # print(f"Amostra inicial do arquivo:\n{tabela_memoria.getvalue()[:150]}")

                # skiprows=12 pula o cabeçalho inicial para ler apenas os dados reais[cite: 1]
                df = pd.read_fwf(tabela_memoria, skiprows=12, widths=larguras, names=nomes_colunas, dtype=str)
            elif portal == "ECONSIG_2":
                larguras = [10, 8, 10, 8, 100]
                nomes_colunas = ['Matrícula', 'Rubrica', 'Valor Lançado', 'Competencia', 'Crítica']
                df = pd.read_fwf(tabela_memoria, skiprows=12, widths=larguras, names=nomes_colunas, dtype=str)
            elif portal == 'ECONSIG_3':
                # Aplica a régua posicional exata do layout
                larguras = [10, 11, 50, 10, 11, 9, 1, 100]
                nomes_colunas = ['Matrícula', 'CPF', 'Nome', 'Codigo', 'Valor Lançado', 'Competencia', 'Tipo', 'Crítica']

                # Coloque isso antes de chamar o pd.read_fwf ou pd.read_csv
                # print(f"Tamanho do conteúdo detectado: {len(tabela_memoria.getvalue())} caracteres")
                # print(f"Amostra inicial do arquivo:\n{tabela_memoria.getvalue()[:150]}")

                # skiprows=12 pula o cabeçalho inicial para ler apenas os dados reais[cite: 1]
                df = pd.read_fwf(tabela_memoria, skiprows=12, widths=larguras, names=nomes_colunas, dtype=str)
            elif portal == 'ECONSIG_4':
                # Aplica a régua posicional exata do layout
                larguras = [10, 11, 50, 9, 10, 9, 4, 100]
                nomes_colunas = ['Matrícula', 'CPF', 'Nome', 'Codigo', 'Valor Lançado', 'Competencia', 'Tipo', 'Crítica']

                # Coloque isso antes de chamar o pd.read_fwf ou pd.read_csv
                # print(f"Tamanho do conteúdo detectado: {len(tabela_memoria.getvalue())} caracteres")
                # print(f"Amostra inicial do arquivo:\n{tabela_memoria.getvalue()[:150]}")

                # skiprows=12 pula o cabeçalho inicial para ler apenas os dados reais[cite: 1]
                df = pd.read_fwf(tabela_memoria, skiprows=12, widths=larguras, names=nomes_colunas, dtype=str)
            elif portal == 'ECONSIG_5':
                # Aplica a régua posicional exata do layout
                larguras = [20, 11, 50, 17, 10, 9, 1, 100]
                nomes_colunas = ['Matrícula', 'CPF', 'Nome', 'Detalhes', 'Valor Lançado', 'Competencia', 'Tipo', 'Crítica']

                # Coloque isso antes de chamar o pd.read_fwf ou pd.read_csv
                # print(f"Tamanho do conteúdo detectado: {len(tabela_memoria.getvalue())} caracteres")
                # print(f"Amostra inicial do arquivo:\n{tabela_memoria.getvalue()[:150]}")

                # skiprows=12 pula o cabeçalho inicial para ler apenas os dados reais[cite: 1]
                df = pd.read_fwf(tabela_memoria, skiprows=12, widths=larguras, names=nomes_colunas, dtype=str, encoding='latin-1')
            elif portal == 'ECONSIG_6':
                # Aplica a régua posicional exata do layout
                larguras = [12, 11, 50, 9, 10, 9, 1, 100]
                nomes_colunas = ['Matrícula', 'CPF', 'Nome', 'Codigo', 'Valor Lançado', 'Competencia', 'Tipo', 'Crítica']

                # Coloque isso antes de chamar o pd.read_fwf ou pd.read_csv
                # print(f"Tamanho do conteúdo detectado: {len(tabela_memoria.getvalue())} caracteres")
                # print(f"Amostra inicial do arquivo:\n{tabela_memoria.getvalue()[:150]}")

                # skiprows=12 pula o cabeçalho inicial para ler apenas os dados reais[cite: 1]
                df = pd.read_fwf(tabela_memoria, skiprows=12, widths=larguras, names=nomes_colunas, dtype=str)
            elif portal == "ECONSIG_7":
                # Aplica a régua posicional exata do layout
                larguras = [10, 11, 50, 12, 10, 9, 1, 100]
                nomes_colunas = ['Matrícula', 'CPF', 'Nome', 'Codigo', 'Valor Lançado', 'Competencia', 'Tipo', 'Crítica']

                # Coloque isso antes de chamar o pd.read_fwf ou pd.read_csv
                # print(f"Tamanho do conteúdo detectado: {len(tabela_memoria.getvalue())} caracteres")
                # print(f"Amostra inicial do arquivo:\n{tabela_memoria.getvalue()[:150]}")

                # skiprows=12 pula o cabeçalho inicial para ler apenas os dados reais[cite: 1]
                df = pd.read_fwf(tabela_memoria, skiprows=12, widths=larguras, names=nomes_colunas, dtype=str)

            elif portal == 'ECONSIG_8':
                # Aplica a régua posicional exata do layout
                larguras = [20, 11, 50, 11, 10, 9, 1, 100]
                nomes_colunas = ['Matrícula', 'CPF', 'Nome', 'Codigo', 'Valor Lançado', 'Competencia', 'Tipo', 'Crítica']

                # Coloque isso antes de chamar o pd.read_fwf ou pd.read_csv
                # print(f"Tamanho do conteúdo detectado: {len(tabela_memoria.getvalue())} caracteres")
                # print(f"Amostra inicial do arquivo:\n{tabela_memoria.getvalue()[:150]}")

                # skiprows=12 pula o cabeçalho inicial para ler apenas os dados reais[cite: 1]
                df = pd.read_fwf(tabela_memoria, skiprows=12, widths=larguras, names=nomes_colunas, dtype=str, encoding='latin-1')
            elif portal == 'NEOCONSIG':
                # 1. Transformamos os bytes puros em texto legível ignorando possíveis erros de encoding
                texto = conteudo_bytes.decode('utf-8', errors='ignore')

                dados_limpos = []

                # 2. Lê o arquivo linha por linha
                for linha in texto.splitlines():
                    linha = linha.strip()
                    
                    # 3. Filtra: Ignora cabeçalhos e rodapés, focando apenas nos dados reais
                    if linha.startswith('linha('):
                        # O arquivo é separado por tabulações (\t)
                        partes = linha.split('\t')
                        
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
            elif portal == 'VIABILIZE':
                # 1. Lê o arquivo separando pelos pontos e vírgulas (;)
                # Definimos 4 colunas, já que o Valor e a Crítica virão grudados na última
                nomes_colunas = ['Competência', 'Matrícula', 'Rúbrica', 'Valor_Misto']
                
                df = pd.read_csv(
                    io.BytesIO(conteudo_bytes), 
                    sep=';', 
                    names=nomes_colunas, 
                    dtype=str
                )
                
                # 2. Divide a coluna 'Valor_Misto' no PRIMEIRO espaço (n=1)
                # Isso separa o "67.59" do "ACEITO: Parcela criada." e cria duas colunas novas
                df[['Valor Lançado', 'Crítica']] = df['Valor_Misto'].str.split(' ', n=1, expand=True)
            
                
                # 3. Converte o Valor Lançado para decimal puro
                df['Valor Lançado'] = df['Valor Lançado'].astype(float)
                            
                # --- TRATAMENTO DA CRÍTICA ---
                # 4. Cria a máscara para focar apenas nas linhas que foram rejeitadas
                mask_rejeitado = df['Crítica'].str.contains('REJEITADO', case=False, na=False)
                
                # 5. Extrai a palavra que vem depois de 'Motivo:'
                motivos_extraidos = (
                    df.loc[mask_rejeitado, 'Crítica']
                    .str.split('Motivo:')
                    .str[-1]          # Pega a última parte da string (o motivo em si)
                    .str.strip()      # Remove espaços em branco antes ou depois
                    .str.rstrip('.')  # Remove o ponto final (.)
                )
                
                # 6. Sobrescreve a coluna Crítica com o formato exigido apenas para os rejeitados
                df.loc[mask_rejeitado, 'Crítica'] = 'REJEITADO: ' + motivos_extraidos
                
                # Opcional: descarta a coluna mista original, que não é mais necessária
                df = df.drop(columns=['Valor_Misto'])
            else:
                # Leitura genérica para outros TXTs
                df = pd.read_fwf(tabela_memoria, dtype=str)
            
            # --- AS DUAS LINHAS MÁGICAS QUE FALTAVAM ---
            df = colunas_usadas(modelo=portal, df=df)
            df_resultado = base_portal.decidir_layout_portal(portal=portal, convenio=nome_convenio, arquivo=df)
            
            return df_resultado
            
        except Exception as e:
            raise ValueError(f"Erro ao ler arquivo TXT: {str(e)}")

    # 2. ARQUIVOS CSV / TXT
    encodings_comuns = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings_comuns:
        try:
            # Decodificamos os bytes em texto antes de tentar descobrir o separador
            texto = conteudo_bytes.decode(encoding)
            
            # Pegamos uma amostra dos primeiros 4KB para o Sniffer
            amostra = texto[:4096]
            
            try:
                separador = csv.Sniffer().sniff(amostra).delimiter
            except csv.Error:
                separador = ';'
            
            # Criamos o arquivo em memória para o CSV
            arquivo_memoria = io.StringIO(texto)
            df = pd.read_csv(arquivo_memoria, sep=separador, dtype=str, engine='python', header=None)
            
            # O processamento do layout que você já desenhou
            df = colunas_usadas(modelo=portal, df=df)
            df_resultado = base_portal.decidir_layout_portal(portal=portal, convenio=nome_convenio, arquivo=df)
            
            return df_resultado
            
        except UnicodeDecodeError:
            continue # Tenta o próximo encoding
        except Exception as e:
             raise ValueError(f"Erro ao analisar o arquivo de texto: {str(e)}")
             
    raise ValueError("Nenhum encoding suportado conseguiu ler este arquivo.")

def colunas_usadas(modelo, df: pd.DataFrame) -> pd.DataFrame:
    # (Sem alterações, sua lógica está correta e funcional)
    if modelo == "CONSIGFACIL_2":
        df_filtrado = df.iloc[:, [2, 3, 7, 16, 18]].copy()
        df_filtrado.columns = ['Matrícula', 'CPF', 'Valor Lançado', 'Crítica', 'Valor Acatado']
        df = df_filtrado.copy()
        
    if modelo == "CONSIGFACIL_1":
        # 1. Extrai os nomes das colunas reais que estão escondidos na primeira linha (índice 0)
        # Atribui os valores da primeira linha (índice 0) aos cabeçalhos
        df.columns = df.iloc[0]
    
        # 2. Remove a primeira linha dos dados e reseta o índice
        df = df[1:].reset_index(drop=True)
        print(f'Como está df antes de filtrar?\n{df.head(10)}\n\n')

        nomes_colunas_conteudo = df.loc[0, 'Conteudo'].split(';')
        
        # 2. Divide a coluna 'Conteudo' usando o ';' e renomeia com os cabeçalhos extraídos
        df_conteudo = df['Conteudo'].str.split(';', expand=True)
        df_conteudo.columns = nomes_colunas_conteudo
        
        # 3. Divide a coluna 'Retorno'
        # O expand=True cria colunas preenchendo com NaN onde não houver ponto e vírgula
        df_retorno = df['Retorno'].str.split(';', expand=True)
        
        # Renomeia as colunas de retorno dinamicamente (ex: Retorno_1, Retorno_2, Retorno_3)
        df_retorno.columns = [f"Retorno_{i+1}" for i in range(df_retorno.shape[1])]
        
        # 4. Junta as duas partes separadas em um único DataFrame
        # Se quiser manter a coluna 'Linha' original, basta adicionar df[['Linha']] dentro do colchete abaixo
        df = pd.concat([df_conteudo, df_retorno], axis=1)
        
        # 5. Remove a primeira linha (índice 0) que foi usada como molde e reseta o índice
        df = df.iloc[1:].reset_index(drop=True)

        # df['VALOR'] = df['VALOR'].str.replace(',', '.', regex=False).astype(float)
    
        # ['Matrícula', 'CPF', 'Valor Lançado', 'Crítica', 'Valor Acatado']
    
        df.rename(columns={"MATRICULA": "Matrícula", "VALOR": "Valor Lançado", "Retorno_1": "Crítica", "Retorno_3": "Valor Acatado"}, inplace=True)

    if modelo in ["NEOCONSIG", "ECONSIG_1", "ECONSIG_2", "ECONSIG_3", "ECONSIG_4", "ECONSIG_5", "ECONSIG_6", "ECONSIG_7", "ECONSIG_8"]:
        pass

    if modelo in ["CONSIGX"]:
        # 1. Extrai os nomes das colunas reais que estão escondidos na primeira linha (índice 0)
        # Atribui os valores da primeira linha (índice 0) aos cabeçalhos
        df.columns = df.iloc[0]

        # Remove a primeira linha (índice 0) que foi usada como molde e reseta o índice
        df = df.iloc[1:].reset_index(drop=True)

        print(f'Como está df antes de filtrar?\n{df.head(10)}\n\n')

        if "Valor Acatado" not in df.columns:
            df.insert(5, "Valor Acatado", 0)

        if "Critica" not in df.columns:
            df.insert(9, "Critica", "SUCESSO")

        # NOME/CPF/MATRICULA/cod_orgao/VALOR/Valor Acatado/Folha Inclusao/CODIGO DA VERBA/ADE/Observações/Margem
        # NOME/CPF/MATRICULA/cod_orgao/VALOR/CODIGO DA VERBA/ADE/Critica/Valor/Margem
        df.rename(columns={"MATRICULA": "Matrícula", "Critica": "Crítica", "VALOR": "Valor Lançado"}, inplace=True)

        df = df[["Matrícula", "CPF", "Valor Lançado", "Crítica", "Valor Acatado"]].copy()

    if modelo == 'QUANTUM':
        df.columns = df.iloc[4]
        
        # Remove a primeira linha (índice 0) que foi usada como molde e reseta o índice
        df = df.iloc[5:].reset_index(drop=True)
    
        # Remover colunas vazias
        df = df.dropna(axis=1, how='all')
        
        print(f'Como está df antes de filtrar?\n{df.head(10)}\n\n')
    
        
    
        if "Valor Acatado" not in df.columns:
            df.insert(5, "Valor Acatado", 0)
            df['Valor Acatado'] = df['Valor Acatado'].astype(str)
    
        
    
        # NOME/CPF/MATRICULA/cod_orgao/VALOR/CODIGO DA VERBA/ADE/Critica/Valor/Margem
        df.rename(columns={"Descrição da crítica": "Crítica", "Valor": "Valor Lançado"}, inplace=True)
    
        
    
        df = df[["Matrícula", "CPF", "Valor Lançado", "Crítica", "Valor Acatado"]].copy()

    if modelo == 'SERHA':
        for column in df.columns:
                if column in ['x', 'X']:
                    df.columns = df.iloc[1]
        
        # Remove a primeira linha (índice 0) que foi usada como molde e reseta o índice
        df = df.iloc[2:].reset_index(drop=True)
    
        # Remover colunas vazias
        df = df.dropna(axis=1, how='all')
        
        print(f'Como está df antes de filtrar?\n{df.head(10)}\n\n')
    
        df.columns = ["Consignante", "CPF", "Matrícula", "N_Processo", "Consignatario", "Consignacao", "Valor Lançado", "Contrato", "Taxa", "MesAno", "Crítica"]

    if modelo == 'INFOCONSIG':
        df.columns = df.iloc[0]
        
        # Remove a primeira linha (índice 0) que foi usada como molde e reseta o índice
        df = df.iloc[1:].reset_index(drop=True)
        
        print(f'Como está df antes de filtrar?\n{df.head(10)}\n\n')
    
        # NM_PESSOA|NR_CPF	NR_MATRICULA|VL_PREVISAO_DESCONTO|valor acatado|críticas
        # Servidor|CPf|Matricula|Valor Informado|Parcela|Mês	Prazo|Critica

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
    if modelo == 'SAFECONSIG':
        df.columns = df.iloc[1].astype(str).str.strip()
        df = df.iloc[2:].reset_index(drop=True)
        print(f"DEBUG: Como está o DataFrame depois de reorganizar o cabeçalho?\n{df}\n")
        print(f"DEBUG: Colunas de df: {df.columns}")
        # 1. Separar a coluna 'Linha' em múltiplas colunas
        # O expand=True transforma o resultado do split em um novo DataFrame.
        df_separado = df['Linha'].str.split(';', expand=True)
        
        # Como a string termina com um ';', o split vai criar uma última coluna vazia.
        # Vamos pegar apenas as 6 primeiras colunas que nos interessam:
        df_separado = df_separado.iloc[:, :6]
        df_separado.columns = ['Matrícula', 'CPF', 'Valor Lançado', 'Serviço', 'Competência', 'Nome']
        
        # 2. Juntar as novas colunas com as colunas originais (removendo a velha 'Linha')
        df = pd.concat([df_separado, df.drop(columns=['Linha'])], axis=1)

        df = df.rename(columns={"Critica": "Crítica"})

    if modelo == 'KONEXIA':
         if "Servidor" in df.loc[0][0]:
             df.columns = df.iloc[0].astype(str).str.strip()
             df = df.iloc[1:].reset_index(drop=True)
         else:
             df.columns = df.iloc[1].astype(str).str.strip()
             df = df.iloc[2:].reset_index(drop=True)
        
         print(f"DEBUG: Como está o DataFrame depois de reorganizar o cabeçalho?\n{df}\n")
         print(f"DEBUG: Colunas de df: {df.columns}")
         # 1. Separar a coluna 'Linha' em múltiplas colunas
          # O expand=True transforma o resultado do split em um novo DataFrame.    
         # Como a string termina com um ';', o split vai criar uma última coluna vazia.
         # Vamos pegar apenas as 6 primeiras colunas que nos interessam:
    
         # 2. Higienização das colunas padrão
         if 'CPF' not in df.columns:
            df['CPF'] = df['Matrícula'].str.zfill(11)  # Supondo que os primeiros 11 caracteres da matrícula sejam o CPF
    
        
    
         df = df.rename(columns={'Valor parcela': 'Valor Lançado', 'Valor ajuste': 'Valor Acatado', "Observação": "Crítica"})

    if modelo == "CODATA":
        df.columns = df.iloc[0].astype(str).str.strip()
        df = df.iloc[1:].reset_index(drop=True)
            
        
        df = df.rename(columns={"cpf": "CPF", "matricula": "Matrícula", 'valor_informado': 'Valor Lançado', 'valor_registrado': 'Valor Acatado', "crÃ­tica": "Crítica"})

    if modelo == "SIGRH":
        df = df.rename(columns={'Valor_Parcela': 'Valor Lançado', "Motivo_Rejeicao": "Crítica"})

    if modelo == 'ASBAN':
        df.columns = df.iloc[0].astype(str).str.strip()
        
        df = df.iloc[1:].reset_index(drop=True)
        
    
        df = df.rename(columns={'Valor': 'Valor Lançado', "Motivo do Erro": "Crítica"})

    if modelo == 'CODIUB':
        df.columns = df.iloc[0].astype(str).str.strip()
        
        df = df.iloc[1:].reset_index(drop=True)
    
        df_mensagem = df['Mensagem']
    
        # 1. Divide a coluna 'Obs' em 3 novas colunas usando o '|' como separador
        # O expand=True força o resultado a virar colunas no DataFrame
        df[['Matrícula_Sujo', 'CPF_Sujo', 'Valor_Sujo']] = df['Obs'].str.split('|', expand=True)
        
        # 2. Limpa a coluna Matrícula (Remove o texto "Matrícula:" e espaços)
        df['Matrícula'] = df['Matrícula_Sujo'].str.replace('Matrícula:', '', case=False).str.strip()
        
        # 3. Limpa a coluna CPF (Remove o texto "CPF:" e espaços)
        df['CPF'] = df['CPF_Sujo'].str.replace('CPF:', '', case=False).str.strip()
    
        df['Valor Lançado'] = df['Valor_Sujo']
            
        # 5. Descarta as colunas temporárias e a original (opcional)
        df = df.drop(columns=['Obs', 'Matrícula_Sujo', 'CPF_Sujo', 'Valor_Sujo'])
    
        df = df.rename(columns={"Mensagem": "Crítica"})

    if modelo == 'CONSIGCARIOCA':
        df.columns = df.iloc[4].astype(str).str.strip()
        
        df = df.iloc[5:].reset_index(drop=True)
    
    
        df.rename(columns={'Valor': 'Valor Lançado', 'Situação': 'Crítica'}, inplace=True)

    if modelo == 'RNCONSIG':
        df.columns = df.iloc[0].astype(str).str.strip()
        
        df = df.iloc[1:].reset_index(drop=True)
    
    
        df.rename(columns={'matricula': 'Matrícula', 'cpf': 'CPF', 'valor_reserva': 'Valor Lançado', 'motivo_rejeicao': 'Crítica'}, inplace=True)

    if modelo == 'CIP':
        df_1 = df if 'Controle_CIP' in df.columns else None
        if df_1 is None:
            raise ValueError("df_1 está vázio")
        
        df_2 = df if 'VALOR AVERBADO' in df.columns else None
        if df_2 is None:
            raise ValueError("df_2 está vázio")

        df_2.rename(columns={'Nº AVERBAÇÃO SCC': 'Matrícula', 'VALOR AVERBADO': 'Valor Lançado'}, inplace=True)

        df_1.rename(columns={"ADE_Averbacao": "Matrícula"}, inplace=True)
        df_1['Valor Lançado'] = df_1["Matrícula"].map(df_2.set_index('Matrícula')['Valor Lançado'])


    return df