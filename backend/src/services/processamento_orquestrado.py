import pandas as pd
from utils.file_readers import ler_arquivo_seguro

def orquestrar_processamento(conteudo: bytes, nome_arquivo: str, convenio: str, banco: str, tipo_produto: str):
    
    # 1. Transforma os bytes em um DataFrame, passando o nome do arquivo para ele saber se é CSV ou XLSX
    df = ler_arquivo_seguro(conteudo_bytes=conteudo, nome_arquivo=nome_arquivo, convenio=convenio)
    
    # 2. Injeção das dimensões da interface
    df['codigo_convenio'] = convenio
    df['consignataria'] = banco.upper().strip()
    df['produto'] = tipo_produto.upper().strip()
    
    return df