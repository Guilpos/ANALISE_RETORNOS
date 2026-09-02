def convenio_escolher():
    mapa_convenios = {
    "1": "INSS",
    "2": "GOV. PARAÍBA",
    "3": "GOV. MINAS GERAIS - IPSM",
    "4": "GOV. MINAS GERAIS - CBMMG",
    "5": "GOV. MINAS GERAIS - PMMG",
    "6": "GOV. MINAS GERAIS - SEPLAG",
    "7": "GOV. MINAS GERAIS - IPSEMG",
    "8": "GOV. BAHIA",
    "9": "PREF. ARAGUAÍNA",
    "10": "PREF. DUQUE DE CAXIAS",
    "11": "PREF. DUQUE DE CAXIAS - COTAR",
    "12": "PREF. DUQUE DE CAXIAS - IMPDC",
    "13": "PREF. GOIÂNIA",
    "14": "PREVIDÊNCIA SÃO GONÇALO",
    "15": "PREF. RIBEIRÃO PRETO",
    "16": "PREF. TABOÃO DA SERRA",
    "17": "PREVIDÊNCIA SANTOS - IPREV",
    "18": "GOV. ESPÍRITO SANTO",
    "19": "GOV. PARANÁ",
    "20": "GOV. RIO DE JANEIRO",
    "21": "IGEPREV",
    "22": "PREF. BELO HORIZONTE",
    "23": "PREF. AÇAILÂNDIA",
    "24": "PREF. CAMPINAS",
    "25": "PREF. MACAÉ",
    "26": "PREF. SÃO JOSE DE RIBAMAR",
    "27": "PREF. SÃO PAULO-HMSP",
    "28": "PREF. SOBRAL",
    "29": "PREVIPALMAS",
    "30": "PREF. BARBACENA",
    "31": "GOV. ALAGOAS - TJAL",
    "32": "PREF. ANANINDEUA",
    "33": "PREF. ÁGUAS LINDAS DE GOIÁS",
    "34": "PREF. PIRACICABA",
    "35": "PREF. FLORIANÓPOLIS",
    "36": "SEMAE - SERVIÇO MUNICIPAL DE ÁGUA E ESGOTO DE PIRACICABA",
    "37": "PREV. PIRACICABA IPASP",
    "38": "GOV. TOCANTINS e IGEPREV",
    "39": "GOV. SANTA CATARINA",
    "40": "PREF. CONTAGEM",
    "41": "PREF. PLANALTINA",
    "42": "PREF. SÃO PAULO",
    "43": "GOV. SÃO PAULO",
    "44": "GOV. GOIÁS",
    "45": "PREF. SÃO GONÇALO",
    "46": "PREF. SÃO LUÍS",
    "47": "PREF. SOROCABA",
    "48": "PREF. SÃO JOSÉ DO RIO PRETO",
    "49": "PREVIDÊNCIA SÃO JOSÉ DO RIO PRETO",
    "50": "CÂMARA MUNICIPAL DE TERESÓPOLIS",
    "51": "PREF. JUÍZ DE FORA",
    "52": "PREF. RIO DE JANEIRO",
    "53": "PREF. PICOS",
    "54": "PREV. PICOS",
    "55": "PREF. TAUBATÉ",
    "56": "PREF. SANTOS",
    "57": "GOV. CEARÁ",
    "58": "GOV. ALAGOAS",
    "59": "GOV. MARANHÃO",
    "60": "GOV. MATO GROSSO",
    "61": "GOV. PIAUÍ",
    "62": "GOV. PERNAMBUCO",
    "63": "PREF. BAYEUX",
    "64": "PREF. CAJAMAR",
    "65": "PREF. CAMPINA GRANDE",
    "66": "PREF. CAMPO GRANDE",
    "67": "PREF. CUIABÁ",
    "68": "PREF. PORTO VELHO",
    "69": "PREF. IMPERATRIZ MA",
    "70": "PREF. ITU",
    "71": "PREF. JOÃO PESSOA",
    "72": "PREF. JUAZEIRO DO NORTE",
    "73": "PREF. MARABÁ",
    "74": "PREF. NITERÓI",
    "75": "PREF. PAÇO DO LUMIAR",
    "76": "PREF. PALMAS",
    "77": "PREF. RECIFE",
    "78": "PREF. SANTA RITA",
    "79": "PREF. TERESINA",
    "80": "CÂMARA DE TERESÓPOLIS",
    "81": "GOV. RIO GRANDE DO NORTE",
    "82": "PREF. NATAL"
}

    return mapa_convenios

def portal_escolhido(nome_convenio: str) -> list:
    # 1. Mapeamento de todos os portais usando um Dicionário
    portais = {
        "CODATA": ["GOV. PARAÍBA"],
        
        "INSS": ["INSS"],
        
        "SERHA": [
            "GOV. MINAS GERAIS - IPSM", "GOV. MINAS GERAIS - CBMMG", 
            "GOV. MINAS GERAIS - PMMG", "GOV. MINAS GERAIS - SEPLAG", 
            "GOV. MINAS GERAIS - IPSEMG"
        ],
        
        "CONSIGX": [
            "GOV. BAHIA", "PREF. ARAGUAÍNA", "PREF. DUQUE DE CAXIAS", 
            "PREF. DUQUE DE CAXIAS - COTAR", "PREF. DUQUE DE CAXIAS - IMPDC", 
            "PREF. GOIÂNIA", "PREVIDÊNCIA SÃO GONÇALO", "PREF. RIBEIRÃO PRETO", 
            "PREF. TABOÃO DA SERRA", "PREVIDÊNCIA SANTOS - IPREV"
        ],

        "ECONSIG_1": ["PREF. BELO HORIZONTE"],
        
        "ECONSIG": [
            "GOV. ESPÍRITO SANTO", "GOV. PARANÁ", "GOV. RIO DE JANEIRO", 
            "IGEPREV", "PREF. AÇAILÂNDIA", 
            "PREF. CAMPINAS", "PREF. MACAÉ", "PREF. SÃO JOSE DE RIBAMAR", 
            "PREF. SÃO PAULO-HMSP", "PREF. SOBRAL", "PREVIPALMAS", 
            "PREF. BARBACENA", "GOV. ALAGOAS - TJAL"
        ],
        
        "RF1": ["PREF. ANANINDEUA"],
        
        "INFOCONSIG": [
            "PREF. ÁGUAS LINDAS DE GOIÁS", "PREF. PIRACICABA", "PREF. FLORIANÓPOLIS",
            "SEMAE - SERVIÇO MUNICIPAL DE ÁGUA E ESGOTO DE PIRACICABA", "PREV. PIRACICABA IPASP"
        ],
        
        "TO_IGEPREV": ["GOV. TOCANTINS e IGEPREV"],
        
        "SIGRH": ["GOV. SANTA CATARINA"],
        
        "CONSIGI_KONEXIA": ["PREF. CONTAGEM", "PREF. PLANALTINA"],
        
        "CIP": ["PREF. SÃO PAULO", "GOV. SÃO PAULO"],
        
        "NEOCONSIG": ["GOV. GOIÁS", "PREF. SÃO GONÇALO", "PREF. SÃO LUÍS", "PREF. SOROCABA"],
        
        "QUANTUM": [
            "PREF. SÃO JOSÉ DO RIO PRETO", "PREVIDÊNCIA SÃO JOSÉ DO RIO PRETO", 
            "CÂMARA MUNICIPAL DE TERESÓPOLIS", "PREF. JUÍZ DE FORA", "PREF. RIO DE JANEIRO"
        ],
        
        "LINECONSIG": ["PREF. PICOS", "PREV. PICOS"],
        
        "SAFECONSIG": ["PREF. TAUBATÉ", "PREF. SANTOS", "GOV. CEARÁ", "GOV. ALAGOAS"],
        
        "CONSIGFACIL_1": ["GOV. MATO GROSSO",
                          "PREF. TUTÓIA",
                          "PREF. PALMAS",
                          "PREF. CAJAMAR",
                          "PREF. CAMPO GRANDE",
                          "PREF. SUZANO",
                          "PREF. ITU",
                          "PREVIDÊNCIA CAMPO GRANDE IMPCG",
                          "PREF. NATAL",
                          "GOV. PIAUÍ",
                          "GOV. PERNAMBUCO"],

        "CONSIGFACIL_2" : ["PREF. JOÃO PESSOA",
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
    }
    
    # 2. Retorna a lista correspondente tratando letras maiúsculas/minúsculas.
    # O .get() evita que o código quebre se você passar um portal que não existe (retorna [] por padrão).
    # 2. Varre o dicionário para encontrar onde o convênio está
    nome_convenio_limpo = nome_convenio.strip().upper()
    
    for nome_portal, lista_convenios in portais.items():
        if nome_convenio_limpo in lista_convenios:
            return nome_portal
            
    return "PORTAL NÃO MAPEADO"# Retorno de segurança caso não ache
