import pandas as pd
import csv

consigfacil_1 = ["GOV. MATO GROSSO",
                "PREF. TUTÓIA",
                "PREF. PALMAS",
                "PREF. CAJAMAR",
                "PREF. CAMPO GRANDE",
                "PREF. SUZANO",
                "PREF. ITU",
                "PREVIDÊNCIA CAMPO GRANDE IMPCG",
                "PREF. NATAL",
                "GOV. PIAUÍ",
                "GOV. PERNAMBUCO"]

consigfacil_2 = ["PREF. JOÃO PESSOA",
                "PREF. CAMPINA GRANDE",
                "PREF. TERESINA",
                "PREF. JUAZEIRO DO NORTE",
                "PREF. BAYEUX",
                "PREVIDÊNCIA CAMPINA GRANDE IPSEM",
                "PREF. NITERÓI",
                "PREF. RECIFE",
                "PREF. PAÇO DO LUMIAR",
                "PREF. PORTO VELHO - IPAM",
                "PREF. PORTO VELHO",
                "PREF. SANTA RITA",
                "PREF. MARABÁ",
                "PREF. IMPERATRIZ MA",
                "GOV. MARANHÃO"]

def ler_arquivo_seguro(caminho_arquivo: str, convenio: str) -> pd.DataFrame:
    """
    Lê arquivos XLSX, XLS, CSV e TXT de forma segura, garantindo
    que todos os dados nasçam como texto bruto (dtype=str).
    Para CSV/TXT, descobre automaticamente o encoding e o separador.
    """
    # Padroniza para letras minúsculas para facilitar a comparação
    caminho_lower = caminho_arquivo.lower()
    
    # ==========================================
    # 1. TRATAMENTO PARA ARQUIVOS EXCEL
    # ==========================================
    if caminho_lower.endswith('.xlsx') or caminho_lower.endswith('.xls'):
        try:
            # Importante: dtype=str garante que zeros à esquerda (como em CPFs) não sumam
            df = pd.read_excel(caminho_arquivo, dtype=str)
            return df
        except Exception as e:
            raise ValueError(f"Erro ao ler o arquivo Excel: {str(e)}")

    # ==========================================
    # 2. TRATAMENTO PARA ARQUIVOS CSV / TXT
    # ==========================================
    encodings_comuns = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings_comuns:
        try:
            with open(caminho_arquivo, 'r', encoding=encoding) as arquivo:
                amostra = arquivo.read(4096)
                
                try:
                    separador = csv.Sniffer().sniff(amostra).delimiter
                except csv.Error:
                    # Fallback seguro caso o sniffer não consiga identificar
                    separador = ';'
                
                arquivo.seek(0)
                
                # Importante: dtype=str força que tudo seja lido como texto bruto
                df = pd.read_csv(arquivo, sep=separador, dtype=str, engine='python')

                if convenio in consigfacil_2:
                    df_filtrado = df.iloc[:, [3, 7, 16, 18]].copy()

                    # 2. Atribui os novos nomes na ordem exata dos índices selecionados
                    df_filtrado.columns = ['CPF', 'Valor Lançado', 'Crítica', 'Valor Acatado']

                    df = df_filtrado.copy()
                
                return df
                
        except UnicodeDecodeError:
            # Ignora o erro e passa para a próxima tentativa da lista
            continue
            
        except Exception as e:
            raise ValueError(f"Erro estrutural ao ler o arquivo de texto: {str(e)}")
            
    # Se o loop terminar e não retornar o DataFrame
    raise ValueError(
        f"Falha ao ler {caminho_arquivo}. Nenhum dos encodings testados funcionou. "
        "Verifique se o arquivo não está corrompido ou compactado."
    )