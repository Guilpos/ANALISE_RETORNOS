from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from typing import List
from services.processamento_orquestrado import orquestrar_processamento
from sqlalchemy import text
from sqlalchemy.orm import Session
from core.database import get_db

router = APIRouter()


@router.post("/upload")
async def receber_upload_retorno(
    arquivos: List[UploadFile] = File(...),
    codigo_convenio: str = Form(...),
    consignataria: str = Form(...),
    produto: str = Form(...),
    competencia: str = Form(...), # NOVO: Para sabermos de qual mês é o arquivo
    db: Session = Depends(get_db) # NOVO: Injeção do banco de dados na rota
):

    if not codigo_convenio or not consignataria or not produto or not competencia:
            raise HTTPException(
                status_code=400, 
                detail="Operação negada: Para adicionar um lote, você deve selecionar Convênio, Consignatária, Produto e Competência Inicial."
            )

    competencia_recebida = competencia # O HTML envia "2026-08"
    
    if competencia_recebida:
        # Colamos o "-01" no final para cravar o primeiro dia do mês
        competencia_padronizada = f"{competencia_recebida}-01"


    query_duplicidade = text("""
        SELECT 1 FROM fato_retornos 
        WHERE codigo_convenio = :conv 
          AND consignataria = :banco 
          AND produto = :prod 
          AND competencia = :comp
        LIMIT 1
    """)
    
    # O .scalar() retorna o valor (1) se encontrar, ou None se não existir nada
    lote_ja_existe = db.execute(query_duplicidade, {
        "conv": codigo_convenio,
        "banco": consignataria,
        "prod": produto,
        "comp": competencia_padronizada
    }).scalar()

    if lote_ja_existe:
        raise HTTPException(
            status_code=409, 
            detail=f"Lote Duplicado: Já existe um arquivo processado para essa combinação de Convênio, Banco, Produto e Competência. Se precisar atualizar os dados, exclua o lote atual primeiro."
        )
    
    
    try:
        # conteudo_em_bytes = await arquivo.read()

        # 1. Lê todos os arquivos de forma assíncrona antes de chamar o orquestrador
        arquivos_para_processar = []
        for arquivo in arquivos:
            conteudo_em_bytes = await arquivo.read()
            arquivos_para_processar.append({
                "conteudo": conteudo_em_bytes,
                "nome_arquivo": arquivo.filename
            })
        
        # Passamos a sessão de banco (db) e a competencia para o orquestrador
        resultado_df = orquestrar_processamento(
            arquivos_lista=arquivos_para_processar, 
            convenio=codigo_convenio,
            banco=consignataria,
            tipo_produto=produto,
            competencia=competencia_padronizada,
            db=db
        )
        
        return {
            "status": "sucesso", 
            "mensagem": f"Arquivo {arquivo.filename} salvo no banco! Linhas inseridas: {len(resultado_df)}"
        }
        
    except Exception as e:
        # Importamos a biblioteca de rastreio nativa do Python
        import traceback 
        
        # Isso vai imprimir o erro gigante e detalhado no seu terminal do VS Code/CMD
        traceback.print_exc() 
        
        # Mantemos o envio do erro para o Swagger/Frontend
        raise HTTPException(status_code=500, detail=str(e))