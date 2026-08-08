import pandas as pd

def validar_colunas_obrigatorias(df: pd.DataFrame, colunas_esperadas: list, nome_portal: str):
    """
    Verifica se todas as colunas vitais existem no arquivo antes de iniciar o processamento.
    """
    colunas_presentes = df.columns.tolist()
    colunas_faltantes = [col for col in colunas_esperadas if col not in colunas_presentes]
    
    if colunas_faltantes:
        raise ValueError(
            f"Falha na validação do {nome_portal}. "
            f"O arquivo enviado não possui as seguintes colunas obrigatórias: {colunas_faltantes}. "
            f"Verifique se o layout do portal mudou."
        )

def validar_matematica_descontos(df: pd.DataFrame, col_lancado: str, col_acatado: str):
    """
    Audita a lógica financeira: O valor processado (acatado) não pode exceder o enviado (lançado).
    Retorna um relatório das linhas que violam essa regra.
    """
    # Filtra onde o Acatado é maior que o Lançado (uma anomalia financeira)
    anomalias = df[df[col_acatado] > df[col_lancado]]
    
    if not anomalias.empty:
        qtd_erros = len(anomalias)
        # Em vez de travar o sistema, você pode retornar um log de críticas
        # para exibir esses casos bizarros na tela de visualização HTML.
        return {
            "status": "alerta",
            "mensagem": f"Atenção: Encontradas {qtd_erros} linhas onde o Valor Acatado é maior que o Lançado.",
            "linhas_afetadas": anomalias.index.tolist()
        }
    return {"status": "ok"}

def validar_chaves_nulas(df: pd.DataFrame, coluna_chave: str):
    """
    Evita que o sistema tente gravar no banco de dados registros que não possuem 
    a chave principal (ex: CPF em branco após a formatação).
    """
    nulos = df[df[coluna_chave].isna()]
    
    if not nulos.empty:
        raise ValueError(
            f"Validação de Integridade Falhou: O arquivo contém {len(nulos)} registros "
            f"sem informação na coluna '{coluna_chave}'. A inserção no banco foi abortada."
        )

def validar_nome_portal_convenio (portal: str, convenio: str, lista_portais_convenios: dict):
    """
    Garante que o portal e convênio informados pelo usuário existam na lista de portais válidos.
    """
    if portal not in lista_portais_convenios:
        raise ValueError(f"Portal '{portal}' não encontrado na lista de portais válidos.")
    
    if convenio not in lista_portais_convenios[portal]:
        raise ValueError(
            f"Convênio '{convenio}' não encontrado para o portal '{portal}'. "
            f"Verifique se o convênio está correto ou se o layout do portal mudou."
        )