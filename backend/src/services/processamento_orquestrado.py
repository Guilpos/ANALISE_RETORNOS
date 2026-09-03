import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session
from utils.file_readers import ler_arquivo_seguro
from utils.portais_convenios_lista import convenio_escolher, portal_escolhido
from utils.formatters import classificar_status_acatamento, gerar_hash_registro

def orquestrar_processamento(arquivos_lista: list,  convenio: str, banco: str, tipo_produto: str, competencia: str, db: Session):

    # Vamos pegar o codigo que vem em convenio e descobrir qual o nome do convenio e por seguinte descobrir a qual portal ele pertence
    # A sua lógica de escolha de portal!
    nome_convenio = convenio_escolher()[convenio]

    try:
        print('Nome Convenio:', nome_convenio)
    except KeyError:
        print("Convenio não encontrado na lista de convenios.")

    portal = portal_escolhido(nome_convenio)

    # Consigx será o único portal que vai receber múltiplos arquivos, então vamos tratar ele de forma especial
    if portal == "CONSIGX":
        lista_dfs = []
    
        # Processa cada arquivo que chegou na lista
        for arq in arquivos_lista:
            conteudo = arq["conteudo"]
            nome_arquivo = arq["nome_arquivo"]
            
            # Lê o arquivo atual e transforma em DataFrame
            df_temporario = ler_arquivo_seguro(conteudo_bytes=conteudo, nome_arquivo=nome_arquivo, convenio=convenio)
            lista_dfs.append(df_temporario)
            
        # Junta o arquivo de sucesso com o de críticas colocando um embaixo do outro
        df = pd.concat(lista_dfs, ignore_index=True)
    elif portal != "CONSIGX" and len(arquivos_lista) > 1:
        # Se houver mais de um arquivo e o portal não for CONSIGX vamos lançar um erro
        raise ValueError("Apenas um arquivo pode ser enviado para este portal.")
    else:
        # Se for apenas um arquivo, pegamos o primeiro da lista
        conteudo = arquivos_lista[0]["conteudo"]
        nome_arquivo = arquivos_lista[0]["nome_arquivo"]

        # 1. Leitura e Limpeza (A mágica acontece lá nos seus módulos base_portal e Consigfacil_portal)
        df = ler_arquivo_seguro(conteudo_bytes=conteudo, nome_arquivo=nome_arquivo, convenio=convenio)
    
    # 2. Injeção das dimensões da interface
    df['codigo_convenio'] = convenio
    df['consignataria'] = banco.upper().strip()
    df['produto'] = tipo_produto.upper().strip()
    df['competencia'] = competencia 
    
    # 3. Log no historico_uploads
    query_historico = text("""
        INSERT INTO historico_uploads 
        (codigo_convenio, consignataria, produto, nome_arquivo_original, linhas_totais, status_processamento, usuario_upload)
        VALUES (:conv, :banco, :prod, :nome, :linhas, 'PROCESSANDO', 'usuario_teste')
    """)
    
    # 1º: Executamos a query e guardamos o resultado em uma variável
    resultado = db.execute(query_historico, {"conv": convenio, "banco": banco, "prod": tipo_produto, "nome": nome_arquivo, "linhas": len(df)})
    
    # 2º: Pegamos o ID real que acabou de nascer, ANTES de comitar
    id_upload = resultado.lastrowid
    
    # 3º: Agora sim, comitamos e fechamos a transação com segurança
    db.commit()
    
    df['id_arquivo_origem'] = id_upload
    
    # =================================================================
    # 4. ALINHAMENTO DE COLUNAS PARA O BANCO DE DADOS
    # Pegamos as colunas já limpas pelo seu Consigfacil_portal.py e 
    # as renomeamos para o padrão exato da tabela fato_retornos
    # =================================================================
    df = df.rename(columns={
        'Matricula_formatada': 'matricula',
        'cpf_formatado': 'cpf',
        'Valor_lancado': 'valor_lancado',
        'Crítica': 'texto_critica_original', 
        'Valor_descontado': 'valor_acatado'
    })
    

    # Imprime no terminal a lista exata de colunas que o Pandas encontrou
    print("COLUNAS ENCONTRADAS NO ARQUIVO:", df.columns.tolist())
    
    # Como as colunas já estão com os nomes corretos e em float, 
    # apenas rodamos o classificador de status
    df['status_acatamento'] = classificar_status_acatamento(df)

    # =================================================================
    # ATIVAÇÃO DA PROTEÇÃO ANTI-DUPLICIDADE
    # =================================================================
    df['hash_registro'] = gerar_hash_registro(df)
    
    # Removemos colunas antigas/sujas que vieram do portal para não dar erro no banco
    # Manteremos apenas as colunas que de fato existem na tabela do TiDB
    colunas_banco = [
        'matricula', 'cpf', 'valor_lancado', 'texto_critica_original', 
        'valor_acatado', 'codigo_convenio', 'consignataria', 'produto', 
        'competencia', 'id_arquivo_origem', 'status_acatamento'
    ]
    df_para_banco = df[colunas_banco].copy()
    
    try:
        # 5. Gravação no Banco
        df_para_banco.to_sql(name='fato_retornos', con=db.get_bind(), if_exists='append', index=False)
        
        db.execute(text("UPDATE historico_uploads SET status_processamento = 'CONCLUIDO' WHERE id = :id"), {"id": id_upload})
        db.commit()
        
    except Exception as e:
        db.execute(text("UPDATE historico_uploads SET status_processamento = 'ERRO', log_erro = :erro WHERE id = :id"), {"erro": str(e), "id": id_upload})
        db.commit()
        raise e 
    
    return df_para_banco