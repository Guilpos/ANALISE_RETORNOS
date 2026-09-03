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


def limpar_moeda_delimitador_ponto(valor_series: pd.Series) -> pd.Series:
    """
    Converte strings de moeda (ex: 'R$ 1500.45' ou '1500,45') para float numérico.
    """

    print('limpar_moeda_delimitador_ponto ativado')
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

def limpar_moeda_universal(valor_series: pd.Series) -> pd.Series:
    valor_str = str(valor_series).strip()

    valor_str = valor_str.replace('R$', '').replace(' ', '')
    
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


import hashlib
import pandas as pd

def gerar_hash_registro(df: pd.DataFrame) -> pd.Series:
    """
    Gera um hash MD5 único por linha, combinando os dados do servidor,
    as dimensões do formulário e a posição exata da linha no arquivo original.
    """
    # 1. Dados do Servidor e Financeiro
    cpf_str = df['cpf'].fillna('SEM_CPF').astype(str)
    mat_str = df['matricula'].fillna('SEM_MAT').astype(str)
    val_str = df['valor_lancado'].astype(str)
    
    # 2. Dimensões do Formulário (Garante distinção entre Bancos e Produtos diferentes)
    conv_str = df['codigo_convenio'].astype(str)
    consig_str = df['consignataria'].astype(str)
    prod_str = df['produto'].astype(str)
    comp_str = df['competencia'].astype(str)
    
    # 3. Solução para Empréstimos Gêmeos 
    # (Adiciona o número da linha original do arquivo. Assim, duas parcelas 
    # idênticas para a mesma pessoa no mesmo banco geram hashes diferentes)
    linha_str = df.index.astype(str)

    # 4. Concatenação Absoluta
    string_base = (
        conv_str + consig_str + prod_str + comp_str + 
        cpf_str + mat_str + val_str + linha_str
    )
    
    # 5. Aplicação vetorizada do Hash
    return string_base.apply(
        lambda x: hashlib.md5(x.encode('utf-8')).hexdigest()
    )

# [Suas funções limpar_cpf, limpar_moeda_delimitador_ponto e limpar_moeda ficam aqui]

def classificar_status_acatamento(df: pd.DataFrame) -> pd.Series:
    """
    Compara o valor lançado com o valor acatado (já em float) e 
    retorna a string de status para salvar no banco de dados.
    """
    condicoes = [
        # Se o acatado for igual ao lançado e maior que zero
        (df['valor_acatado'] == df['valor_lancado']) & (df['valor_lancado'] > 0),
        
        # Se o acatado for menor que o lançado, mas maior que zero
        (df['valor_acatado'] < df['valor_lancado']) & (df['valor_acatado'] > 0),
        
        # Se veio zerado, nulo, ou menor/igual a zero
        (df['valor_acatado'] == 0) | (df['valor_acatado'].isna())
    ]
    
    categorias = [
        'ACATADO INTEGRAL',
        'ACATADO PARCIAL',
        'ZERADO/REJEITADO'
    ]
    
    # default abrange anomalias (ex: descontou a mais do que foi pedido)
    return np.select(condicoes, categorias, default='ANOMALIA/SOBREVALOR')

