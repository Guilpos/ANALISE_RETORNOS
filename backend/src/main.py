from utils.file_readers import ler_arquivo_seguro
from utils.formatters import limpar_cpf, limpar_data, limpar_moeda_retorno_consigfacil, alinhar_tipagem_chaves
from utils.validators import validar_colunas_obrigatorias, validar_matematica_descontos, validar_chaves_nulas, validar_nome_portal_convenio
from utils.portais_convenios_lista import convenio_escolher, portal_escolhido
from portais import base_portal
print('Escolha o convênio desejado:\n')
print("1 - INSS\n2 - GOV. PARAÍBA\n3 - GOV. MINAS GERAIS - IPSM\n4 - GOV. MINAS GERAIS - CBMMG\n5 - GOV. MINAS GERAIS - PMMG\n6 - GOV. MINAS GERAIS - SEPLAG\n" \
        "7 - GOV. MINAS GERAIS - IPSEMG\n8 - GOV. BAHIA\n9 - PREF. ARAGUAÍNA\n10 - PREF. DUQUE DE CAXIAS\n11 - PREF. DUQUE DE CAXIAS - COTAR\n12 - PREF. DUQUE DE CAXIAS - IMPDC\n " \
        "13 - PREF. GOIÂNIA\n14 - PREVIDÊNCIA SÃO GONÇALO\n15 - PREF. RIBEIRÃO PRETO\n16 - PREF. TABOÃO DA SERRA\n17 - PREVIDÊNCIA SANTOS - IPREV\n18 - GOV. ESPÍRITO SANTO\n19 - GOV. PARANÁ\n" \
        "20 - GOV. RIO DE JANEIRO\n21 - IGEPREV\n22 - PREF. BELO HORIZONTE\n23 - PREF. AÇAILÂNDIA\n24 - PREF. CAMPINAS\n25 - PREF. MACAÉ\n26 - PREF. SÃO JOSE DE RIBAMAR\n27 - PREF. SÃO PAULO-HMSP\n" \
        "28 - PREF. SOBRAL\n29 - PREVIPALMAS\n30 - PREF. BARBACENA\n31 - GOV. ALAGOAS - TJAL\n32 - PREF. ANANINDEUA\n33 - PREF. ÁGUAS LINDAS DE GOIÁS\n34 - PREF. PIRACICABA\n35 - PREF. FLORIANÓPOLIS\n" \
        "36 - SEMAE - SERVIÇO MUNICIPAL DE ÁGUA E ESGOTO DE PIRACICABA\n37 - PREV. PIRACICABA IPASP\n38 - GOV. TOCANTINS e IGEPREV\n39 - GOV. SANTA CATARINA\n40 - PREF. CONTAGEM\n " \
        "41 - PREF. PLANALTINA\n42 - PREF. SÃO PAULO\n43 - GOV. SÃO PAULO\n44 - GOV. GOIÁS\n45 - PREF. SÃO GONÇALO\n46 - PREF. SÃO LUÍS\n47 - PREF. SOROCABA\n48 - PREF. SÃO JOSÉ DO RIO PRETO\n " \
        "49 - PREVIDÊNCIA SÃO JOSÉ DO RIO PRETO\n50 - CÂMARA MUNICIPAL DE TERESÓPOLIS\n51 - PREF. JUÍZ DE FORA\n52 - PREF. RIO DE JANEIRO\n53 - PREF. PICOS\n54 - PREV. PICOS\n" \
        "55 - PREF. TAUBATÉ\n56 - PREF. SANTOS\n57 - GOV. CEARÁ\n58 - GOV. ALAGOAS\n59 - GOV. MARANHÃO\n60 - GOV. MATO GROSSO\n61 - GOV. PIAUÍ\n62 - GOV. PERNAMBUCO\n63 - PREF. BAYEUX\n64 - PREF. CAJAMAR\n" \
        "65 - PREF. CAMPINA GRANDE\n66 - PREF. CAMPO GRANDE\n67 - PREF. CUIABÁ\n68 - PREF. PORTO VELHO\n69 - PREF. IMPERATRIZ MA\n70 - PREF. ITU\n71 - PREF. JOÃO PESSOA\n72 - PREF. JUAZEIRO DO NORTE\n" \
        "73 - PREF. MARABÁ\n74 - PREF. NITERÓI\n75 - PREF. PAÇO DO LUMIAR\n76 - PREF. PALMAS\n77 - PREF. RECIFE\n78 - PREF. SANTA RITA\n79 - PREF. TERESINA\n80 - CÂMARA DE TERESÓPOLIS\n81 - GOV. RIO GRANDE DO NORTE\n82 - PREF. NATAL"
        
    )

mapa_convenios = convenio_escolher()

while True:
    print('Escolha o convênio desejado:\n')
    
    # Gera o menu na tela dinamicamente
    for numero, nome in mapa_convenios.items():
        print(f"{numero} - {nome}")
        
    convenio_escolhido = input("\nDigite o número correspondente ao convênio desejado: ")
    
    try:
        # A mágica acontece aqui: busca direta no dicionário sem nenhum 'if'
        nome_convenio = mapa_convenios[convenio_escolhido]
        
        # NOVA LINHA: Descobre o portal usando a função que criamos
        nome_portal = portal_escolhido(nome_convenio=nome_convenio)
        
        print(f"\nSucesso! Você selecionou o convênio: {nome_convenio}")
        print(f"Este convênio pertence ao portal: {nome_portal}")
        break  # Sai do loop após uma escolha válida
        
    except KeyError:
        # Se o usuário digitar "99" ou "A", o dicionário não acha a chave e cai aqui
        print("\n[ERRO] Opção inválida. Por favor, escolha um número válido da lista.\n")


# Inserção do arquivo
while True:
    try:
        caminho_arquivo = input("\nDigite o caminho completo do arquivo a ser processado\nFormatos aceitos(.txt, .csv, .xlsx): ")
        
        # Agora você pode passar tanto o convenio quanto o portal para a sua função de leitura, se precisar!
        arquivo_lido = ler_arquivo_seguro(caminho_arquivo=caminho_arquivo, convenio=nome_convenio, portal=nome_portal)

        break
        
    except Exception as e:
        print(f"\n[ERRO] Falha ao ler o arquivo: {e}\n")
        continue  # Volta para o início do loop para tentar novamente

resultado = base_portal.decidir_layout_portal(portal=nome_portal, convenio=nome_convenio, arquivo=arquivo_lido)

print("\nAnálise concluída com sucesso! Aqui está um resumo dos resultados:\n")
print(resultado)
