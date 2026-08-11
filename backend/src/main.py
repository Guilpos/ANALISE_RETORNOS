from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import rotas_relatorios
import uvicorn

# Aqui importaremos os roteadores que criarão as URLs do sistema
# (Vamos criá-los na pasta api/ logo após configurar este arquivo)
# from api import rotas_upload, rotas_relatorios

app = FastAPI(
    title="Validador de Convênios API",
    description="Motor de ingestão e análise de retornos de consignação",
    version="1.0.0"
)

# Configuração essencial para permitir que seu painel HTML converse com o Python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, limitaremos ao domínio do seu site
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# REGISTRO DE ROTAS (A Orquestração)
# Aqui conectamos as pastas e módulos que você já testou
# -------------------------------------------------------------------

# Exemplo de como as rotas serão conectadas (deixarei comentado por enquanto)
# app.include_router(rotas_upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(rotas_relatorios.router, prefix="/api/relatorios", tags=["Relatórios"])

@app.get("/")
def health_check():
    """
    Rota simples para verificar se o servidor está online.
    """
    return {"status": "operacional", "mensagem": "API Validador de Convênios está no ar."}

# O bloco abaixo substitui a necessidade de rodar comandos complexos no terminal
if __name__ == "__main__":
    print("Iniciando o servidor FastAPI...")
    # Executa o servidor na porta 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
