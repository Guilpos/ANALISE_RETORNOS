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
    portal = portal_escolhido(nome_convenio)
    
    # 1. ARQUIVOS EXCEL (.xlsx, .xls)
    if caminho_lower.endswith('.xlsx') or caminho_lower.endswith('.xls'):
        try:
            # Transformamos os bytes em um objeto que o Pandas entende como arquivo
            tabela_memoria = io.BytesIO(conteudo_bytes)
            return pd.read_excel(tabela_memoria, dtype=str)
        except Exception as e:
            raise ValueError(f"Erro ao ler arquivo Excel: {str(e)}")

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
            df = pd.read_csv(arquivo_memoria, sep=separador, dtype=str, engine='python')
            
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
    return df