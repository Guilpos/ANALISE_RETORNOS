# Estrutura do Módulo `formatters.py`

# Este documento detalha o código fonte para a camada de higienização de dados do projeto. As funções utilizam operações vetorizadas do **Pandas** para máxima performance.

## Código Fonte Recomendado

# Crie o arquivo `utils/formatters.py` e adicione o seguinte código:

# python
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

