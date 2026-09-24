import pandas as pd
from utils.validators import validar_colunas_obrigatorias, validar_matematica_descontos, validar_chaves_nulas, validar_nome_portal_convenio
from portais import Consigfacil_portal, Econsig_portal, Consigx_portal, Quantum_portal, Serha_portal, \
Infoconsig_portal, Neoconsig_portal, Safeconsig_portal, Konexia_portal, Codata_portal, Sigrh_portal, \
Asban_portal, Codiub_portal, Viabilize_portal, Consigcarioca_portal, Rnconsig_portal


def decidir_layout_portal(portal: str, convenio: str, arquivo: pd.DataFrame) -> dict:
    """
    Retorna o layout esperado para o portal e convênio informados.
    """
    # Mapeamento de layouts por portal e convênio
    layouts = {
        "INSS": {
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica", "Valor Acatado"]
        },
        "CODATA": {
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica", "Valor Acatado"]
        },
        "CONSIGFACIL_1": {
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica", "Valor Acatado"]
        },
        "CONSIGFACIL_2": {
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica", "Valor Acatado"]
        },
        "CONSIGX": {
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica"]
        },
        "QUANTUM":{
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica"]
        },
        "SERHA": {
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica"]
        },
        "INFOCONSIG": {
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica"]
        },
        "NEOCONSIG":{
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica"]
        },
        "SAFECONSIG":{
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica"]
        },
        "KONEXIA": {
            "colunas_obrigatorias": ["Matrícula", "Valor Lançado", "Crítica"]
        },
        "SIGRH": {
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica"],
        },
        "ASBAN": {
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica"],
        },
        "CODIUB": {
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica"],
        },
        "VIABILIZE": {
            "colunas_obrigatorias": ["Matrícula", "Valor Lançado", "Crítica"]
        },
        'CONSIGCARIOCA': {
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica"]
        },
        'RNCONSIG': {
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica"]
        },
        'CIP': {
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica"]
        },
        "ECONSIG_1": {
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica"]
        },
        "ECONSIG_2": {
            "colunas_obrigatorias": ["Matrícula", "Valor Lançado", "Crítica"]
        },
        "ECONSIG_3": {
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica"]
        },
        "ECONSIG_4": {
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica"]
        },
        "ECONSIG_5": {
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica"]
        },
        "ECONSIG_6": {
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica"]
        },
        "ECONSIG_7": {
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica"]
        },

        "ECONSIG_8": {
            "colunas_obrigatorias": ["CPF", "Valor Lançado", "Crítica"]
        },

        # Adicione outros portais e convênios conforme necessário
    }

    # Executa a função que verifica se as colunas obrigatórias estão presentes
    validar_colunas_obrigatorias(arquivo, layouts[portal]["colunas_obrigatorias"], portal)

    
    if portal in layouts:
        if portal in ["CONSIGFACIL_1", "CONSIGFACIL_2"]:
            resultado = Consigfacil_portal.processar_portal_consigfacil(arquivo, convenio=convenio, portal=portal)
        elif portal in ["ECONSIG_1", "ECONSIG_2", "ECONSIG_3", "ECONSIG_4", "ECONSIG_5", "ECONSIG_6", "ECONSIG_7", "ECONSIG_8"]:
            resultado = Econsig_portal.processar_portal_econsig(arquivo, convenio=convenio, portal=portal)
        elif portal == "CONSIGX":
            resultado = Consigx_portal.processar_portal_consigx(arquivo, convenio=convenio, portal=portal)
        elif portal == "QUANTUM":
            resultado = Quantum_portal.processar_portal_consigx(arquivo, convenio=convenio, portal=portal)
        elif portal == "SERHA":
            resultado = Serha_portal.processar_portal_serha(arquivo, convenio=convenio, portal=portal)
        elif portal == 'INFOCONSIG':
            resultado = Infoconsig_portal.processar_portal_infoconsig(arquivo, convenio=convenio, portal=portal)
        elif portal == 'NEOCONSIG':
            resultado = Neoconsig_portal.processar_portal_neoconsig(arquivo, convenio=convenio, portal=portal)
        elif portal == 'SAFECONSIG':
            resultado = Safeconsig_portal.processar_portal_safeconsig(arquivo, convenio=convenio, portal=portal)
        elif portal == 'KONEXIA':
            resultado = Konexia_portal.processar_portal_konexia(arquivo, convenio=convenio, portal=portal)
        elif portal == 'CODATA':
            resultado = Codata_portal.processar_portal_codata(arquivo, convenio=convenio, portal=portal)
        elif portal == 'SIGRH':
            resultado = Sigrh_portal.processar_portal_sigrh(arquivo, convenio=convenio, portal=portal)
        elif portal == 'ASBAN':
            resultado = Asban_portal.processar_portal_asban(arquivo, convenio=convenio, portal=portal)
        elif portal == 'CODIUB':
            resultado = Codiub_portal.processar_portal_codiub(arquivo, convenio=convenio, portal=portal)
        elif portal == 'VIABILIZE':
            resultado = Viabilize_portal.processar_portal_viabilize(arquivo, convenio=convenio, portal=portal)
        elif portal == 'CONSIGCARIOCA':
            resultado = Consigcarioca_portal.processar_portal_consigcarioca(arquivo, convenio=convenio, portal=portal)
        elif portal == 'RNCONSIG':
            resultado = Rnconsig_portal.processar_portal_rnconsig(arquivo, convenio=convenio, portal=portal)
        elif portal == 'CIP':
            resultado = arquivo
        return resultado
    else:
        raise ValueError(f"Layout não definido para o portal '{portal}' e convênio '{convenio}'.")

