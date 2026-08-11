# Estrutura do Módulo `formatters.py`

# Este documento detalha o código fonte para a camada de higienização de dados do projeto. As funções utilizam operações vetorizadas do **Pandas** para máxima performance.

## Código Fonte Recomendado

# Crie o arquivo `utils/formatters.py` e adicione o seguinte código:

# python
import hashlib
import pandas as pd
import numpy as np

def limpar_cpf(cpf_series: pd.Series) -> pd.Series:
    """
    Remove todos os caracteres não numéricos e preenche com zeros à esquerda
    para garantir exatamente 11 dígitos.
    """

    print('Limpar_cpf ativado')
    # Converte para string e remove o que não for número (\D)
    clean_series = cpf_series.astype(str).str.replace(r'\D', '', regex=True)
    
    # Preenche com zero à esquerda, ignorando nulos gerados na extração
    return clean_series.apply(
        lambda x: x.zfill(11) if pd.notna(x) and x != 'nan' and x != '' else np.nan
    )


def limpar_moeda_retorno_consigfacil(valor_series: pd.Series) -> pd.Series:
    """
    Converte strings de moeda (ex: 'R$ 1500.45' ou '1500,45') para float numérico.
    """

    print('limpar_moeda_retorno_consigfacil ativado')
    v = valor_series.astype(str)
    
    # Remove símbolos e espaços
    v = v.str.replace('R$', '', regex=False).str.strip()

    # Preenche valores vazios com 0
    v = v.replace({'': '0', 'nan': '0', np.nan: '0'})
    # print(f'Valores após limpeza: {v.head(10)}')
    # Converte para float (valores não convertíveis viram NaN)
    
    return pd.to_numeric(v, errors='coerce')

def limpar_moeda(valor_series: pd.Series) -> pd.Series:
    """
    Converte strings de moeda (ex: 'R$ 1.500,45' ou '1500,45') para float numérico.
    """
    v = valor_series.astype(str)
    
    # Remove símbolos e espaços
    v = v.str.replace('R$', '', regex=False).str.strip()
    
    # Remove pontos de milhar
    v = v.str.replace('.', '', regex=False)
    
    # Troca vírgula decimal por ponto
    v = v.str.replace(',', '.', regex=False)
    
    # Converte para float (valores não convertíveis viram NaN)
    return pd.to_numeric(v, errors='coerce')

def alinhar_tipagem_chaves(df: pd.DataFrame, coluna: str) -> pd.Series:
    """
    Garante que colunas utilizadas para cruzamento tenham o mesmo tipo estrito (string limpa).
    Isso previne erros silenciosos ao fazer merges/joins no banco de dados.
    """
    if coluna in df.columns:
        return df[coluna].astype(str).str.strip().str.upper()
    return pd.Series(dtype='object')

def limpar_data(valor_series: pd.Series) -> pd.Series:
    """
    Converte strings de data (com ou sem horário/microssegundos) 
    para o formato datetime do Pandas, truncando os microssegundos.
    """
    # 1. Sem o 'format' fixo, ele entende "dd/mm/aaaa" e "dd/mm/aaaa HH:MM:SS.micro"
    datas = pd.to_datetime(valor_series, errors='coerce', dayfirst=True)
    
    # 2. Arredonda/trunca os segundos (se for apenas data "08/07/2026", vira "08/07/2026 00:00:00")
    return datas.dt.floor('s')


def gerar_hash_registro(df: pd.DataFrame) -> pd.Series:
    """
    Gera um hash MD5 único para cada linha baseado nos identificadores disponíveis.
    Protege o banco de dados contra a ingestão duplicada do mesmo arquivo de retorno.
    """
    # 1. Garante que campos nulos não quebrem a concatenação
    cpf_str = df['cpf_formatado'].fillna('SEM_CPF').astype(str)
    mat_str = df['matricula'].fillna('SEM_MAT').astype(str)
    rub_str = df['rubrica'].fillna('SEM_RUB').astype(str)
    comp_str = df['competencia'].astype(str)
    val_str = df['valor_lancado'].astype(str)

    # 2. Concatena os campos em uma única string
    string_base = cpf_str + mat_str + rub_str + comp_str + val_str
    
    # 3. Aplica o algoritmo Hash de forma rápida em toda a coluna
    return string_base.apply(
        lambda x: hashlib.md5(x.encode('utf-8')).hexdigest()
    )

def classificar_acatamento(df: pd.DataFrame, col_lancado: str, col_acatado: str) -> pd.Series:
    """
    Infere o status do retorno baseado estritamente na diferença financeira,
    já que a maioria dos portais não envia código de recusa.
    """
    # Cria uma lista de condições matemáticas
    condicoes = [
        (df[col_acatado] == df[col_lancado]) & (df[col_lancado] > 0),
        (df[col_acatado] < df[col_lancado]) & (df[col_acatado] > 0),
        (df[col_acatado] == 0) | (df[col_acatado].isna())
    ]
    
    # Define as categorias para cada condição
    categorias = [
        'ACATADO INTEGRAL',
        'ACATADO PARCIAL',
        'ZERADO/REJEITADO'
    ]
    
    # Aplica a regra de forma vetorizada no Pandas
    return np.select(condicoes, categorias, default='ANOMALIA/SOBREVALOR')

