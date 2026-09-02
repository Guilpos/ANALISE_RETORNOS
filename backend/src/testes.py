from utils.file_readers import ler_arquivo_seguro
from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_retorno_consigfacil, alinhar_tipagem_chaves
import pandas as pd

def processar_portal_exemplo(caminho: str):
    # ABORDAGEM 1: Inferência Automática
    # O pandas tenta adivinhar onde cada coluna começa e termina.
    # skiprows=9 ignora o cabeçalho e header=None evita que a primeira linha de dados vire cabeçalho.
    df_auto = pd.read_fwf(caminho, skiprows=12, header=None)


    # ABORDAGEM 2: Mapeamento Manual de Larguras (Recomendado)
    # Garante que os dados não sejam cortados incorretamente, passando as larguras exatas dos campos.
    # As larguras abaixo foram estimadas contando os caracteres do seu arquivo:
    nomes_colunas = [
        'Matricula',   # 10 caracteres
        'CPF',         # 11 caracteres 
        'Nome',        # 50 caracteres
        'Codigo',      # 10 caracteres
        'Valor',       # 10 caracteres
        'Competencia', # 9 caracteres
        'Tipo',        # 1 caractere
        'Mensagem'     # Restante (ajustado para 100 caracteres de margem)
    ]
    larguras = [10, 11, 50, 10, 10, 9, 1, 100] 

    df_mapeado = pd.read_fwf(
        caminho, 
        skiprows=12, 
        widths=larguras, 
        names=nomes_colunas
    )

    return df_mapeado

caminho = r"C:\Users\user\Downloads\validacao_LAYOUTPREFBELOHORIZONTE08.2026.txt_07-08-2026-170401.txt"

arquivo_lido = processar_portal_exemplo(caminho=caminho)

print(arquivo_lido.head(30))