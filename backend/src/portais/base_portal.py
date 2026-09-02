import pandas as pd
from utils.validators import validar_colunas_obrigatorias, validar_matematica_descontos, validar_chaves_nulas, validar_nome_portal_convenio
from portais import Consigfacil_portal, Econsig_portal


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
        },
        "ECONSIG_1": {
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica"]
        },
        "ECONSIG_2": {
            "colunas_obrigatorias": ["Matrícula", "Valor Lançado", "Crítica"]
        }

        # Adicione outros portais e convênios conforme necessário
    }

    # Executa a função que verifica se as colunas obrigatórias estão presentes
    validar_colunas_obrigatorias(arquivo, layouts[portal]["colunas_obrigatorias"], portal)

    
    if portal in layouts:
        if portal in ["CONSIGFACIL_1", "CONSIGFACIL_2"]:
            resultado = Consigfacil_portal.processar_portal_consigfacil(arquivo, convenio=convenio, portal=portal)
        elif portal in ["ECONSIG_1", "ECONSIG_2"]:
            resultado = Econsig_portal.processar_portal_econsig(arquivo, convenio=convenio, portal=portal)
        return resultado
    else:
        raise ValueError(f"Layout não definido para o portal '{portal}' e convênio '{convenio}'.")

