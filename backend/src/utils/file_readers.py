# utils/file_readers.py
import pandas as pd
from utils.portais_convenios_lista import portal_escolhido, convenio_escolher
from portais import base_portal
import csv
import io

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
            # Transformamos os bytes em um objeto que o Pandas entende como arquivo
            tabela_memoria = io.BytesIO(conteudo_bytes)
            df = pd.read_excel(tabela_memoria, dtype=str, header=None)
            
            # --- AS DUAS LINHAS MÁGICAS QUE FALTAVAM ---
            df = colunas_usadas(modelo=portal, df=df)
            df_resultado = base_portal.decidir_layout_portal(portal=portal, convenio=nome_convenio, arquivo=df)
            
            return df_resultado
            
        except Exception as e:
            raise ValueError(f"Erro ao ler arquivo Excel: {str(e)}")
    
    if caminho_lower.endswith('.txt'):
        try:
            tabela_memoria = io.BytesIO(conteudo_bytes)

            # Ao contrário de Consigfacil, Econsig não terá outro tratamento de dado, ele irá direto para base portal
            if portal == "ECONSIG_1":
                # Aplica a régua posicional exata do layout
                larguras = [10, 11, 50, 10, 10, 9, 1, 100]
                nomes_colunas = ['Matrícula', 'CPF', 'Nome', 'Codigo', 'Valor Lançado', 'Competencia', 'Tipo', 'Crítica']
                
                # skiprows=9 pula o cabeçalho inicial para ler apenas os dados reais[cite: 1]
                df = pd.read_fwf(tabela_memoria, skiprows=12, widths=larguras, names=nomes_colunas, dtype=str)
            if portal == "ECONSIG_2":
                larguras = [10, 8, 10, 8, 100]
                nomes_colunas = ['Matrícula', 'Rubrica', 'Valor Lançado', 'Competencia', 'Crítica']
                df = pd.read_fwf(tabela_memoria, skiprows=12, widths=larguras, names=nomes_colunas, dtype=str)
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

        df['VALOR'] = df['VALOR'].str.replace(',', '.', regex=False).astype(float)
    
        # ['Matrícula', 'CPF', 'Valor Lançado', 'Crítica', 'Valor Acatado']
    
        df.rename(columns={"MATRICULA": "Matrícula", "VALOR": "Valor Lançado", "Retorno_1": "Crítica", "Retorno_3": "Valor Acatado"}, inplace=True)

    if modelo in ["ECONSIG_1", "ECONSIG_2"]:
        pass

    return df