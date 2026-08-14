from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 1. Importa as duas rotas
from api import rotas_upload, rotas_relatorios

app = FastAPI(title="Validador de Convênios")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Conecta as duas rotas no aplicativo principal
app.include_router(rotas_upload.router, prefix="/api", tags=["Upload de Arquivos"])
app.include_router(rotas_relatorios.router, prefix="/api/relatorios", tags=["Gráficos e Tendências"])

@app.get("/")
def health_check():
    return {"status": "operacional"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)