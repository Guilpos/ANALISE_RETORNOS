from utils.file_readers import ler_arquivo_seguro
from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_delimitador_ponto, alinhar_tipagem_chaves
import openpyxl
import pandas as pd
import xlrd
import io
import lxml

def processar_portal_exemplo(conteudo_bytes: bytes) -> pd.DataFrame:
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
    
    print(f'Como está a coluna Valor Lançado?\n{df['Valor Lançado'].head(15)}')

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

    df.insert(2, "CPF", "")

    df["CPF"] = df["Matrícula"].astype(str).str.zfill(11)
     
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

    df['Matricula_formatada'] = alinhar_tipagem_chaves(df, 'Matrícula')
    df['cpf_formatado'] = limpar_cpf(df['CPF'])
    
    # --- LÓGICA DE ACATAMENTO ---
    # Aplicação limpa e direta no DataFrame:
    df['Valor_lancado'] = df['Valor Lançado'].apply(limpar_moeda_universal)

    df['Valor_lancado'] = df['Valor_lancado']

    # 4. Atribuição direta dos valores já numéricos (Sobrescreve o que foi limpo acima)
    if "Valor Acatado" in df.columns:
        df["Valor Acatado"] = ''

    df.loc[df["Crítica"].str.contains("ACEITO"), "Valor Acatado"] = df["Valor_lancado"]
    df["Valor Acatado"] = df["Valor Acatado"].fillna(0)

    df['Crítica'] = df['Crítica'].fillna("")
    df.loc[df['Crítica'] == 'Desconto implantado com sucesso', 'Valor Acatado'] = df['Valor_lancado']


    df['Valor_descontado'] = df['Valor Acatado'].apply(limpar_moeda_universal)
    df['Valor_descontado'] = df['Valor Acatado'].fillna(0)

    return df

# Coloque o caminho exato onde você salvou o arquivo de teste
caminho_do_arquivo = r"C:\RETORNOS\RETORNO GOV TO\Output_LANCAMENTO CARTAO GOV TO CAPITAL CCI 08-2026.txt"
# Chama a função que criamos passando os bytes simulados

# 2. Leia o arquivo em bytes
with open(caminho_do_arquivo, "rb") as f:
    conteudo_bytes = f.read()

df_teste = processar_portal_exemplo(conteudo_bytes=conteudo_bytes)

# Exibe o resultado no terminal para você conferir as colunas
print(df_teste.head(15))
print("\nTipos de dados gerados:")
print(df_teste.dtypes)