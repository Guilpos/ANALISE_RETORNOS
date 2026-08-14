from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from services.processamento_orquestrado import orquestrar_processamento
from sqlalchemy.orm import Session
from core.database import get_db

router = APIRouter()


@router.post("/upload")
async def receber_upload_retorno(
    arquivo: UploadFile = File(...),
    codigo_convenio: str = Form(...),
    consignataria: str = Form(...),
    produto: str = Form(...),
    competencia: str = Form(...), # NOVO: Para sabermos de qual mês é o arquivo
    db: Session = Depends(get_db) # NOVO: Injeção do banco de dados na rota
):
    try:
        conteudo_em_bytes = await arquivo.read()
        
        # Passamos a sessão de banco (db) e a competencia para o orquestrador
        resultado_df = orquestrar_processamento(
            conteudo=conteudo_em_bytes,
            nome_arquivo=arquivo.filename,
            convenio=codigo_convenio,
            banco=consignataria,
            tipo_produto=produto,
            competencia=competencia,
            db=db
        )
        
        return {
            "status": "sucesso", 
            "mensagem": f"Arquivo {arquivo.filename} salvo no banco! Linhas inseridas: {len(resultado_df)}"
        }
        
    except Exception as e:
        # Se algo falhar na gravação, ele avisa a tela
        raise HTTPException(status_code=500, detail=str(e))