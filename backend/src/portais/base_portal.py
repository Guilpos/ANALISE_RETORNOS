import pandas as pd
from utils.validators import validar_colunas_obrigatorias, validar_matematica_descontos, validar_chaves_nulas, validar_nome_portal_convenio


def decidir_layout_portal(portal: str, convenio: str, arquivo: pd.DataFrame) -> dict:
    """
    Retorna o layout esperado para o portal e convênio informados.
    """
    # Mapeamento de layouts por portal e convênio
    layouts = {
        "INSS": {
            "colunas_obrigatorias": ["CPF", "NOME", "VALOR_LANCADO", "VALOR_ACATADO"]
        },
        "GOV. PARAÍBA": {
            "colunas_obrigatorias": ["CPF", "NOME", "VALOR_LANCADO", "VALOR_ACATADO"]
        },
        "CONSIGFACIL_1": {
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica", "Valor Acatado"]
        },
        "CONSIGFACIL_2": {
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica", "Valor Acatado"]
        }
        # Adicione outros portais e convênios conforme necessário
    }

    # Executa a função que verifica se as colunas obrigatórias estão presentes
    validar_colunas_obrigatorias(arquivo, layouts[portal]["colunas_obrigatorias"], portal)

    validar_matematica_descontos(arquivo, "Valor Lançado", "Valor Acatado")


    
    if portal in layouts:
        return layouts[portal]
    else:
        raise ValueError(f"Layout não definido para o portal '{portal}' e convênio '{convenio}'.")

