import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session
from utils.file_readers import ler_arquivo_seguro
from utils.formatters import classificar_status_acatamento, gerar_hash_registro

def orquestrar_processamento(conteudo: bytes, nome_arquivo: str, convenio: str, banco: str, tipo_produto: str, competencia: str, db: Session):
    
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