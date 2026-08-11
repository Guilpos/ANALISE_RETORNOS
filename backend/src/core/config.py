# Arquivo: core/config.py
import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env para a memória do sistema
load_dotenv()

class Settings:
    # Busca as chaves ocultas; se não achar, usa um valor padrão vazio ou gera erro
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT", "4000")
    DB_NAME = os.getenv("DB_NAME", "validador_convenios")
    
    # Monta a URL completa de forma dinâmica
    @property
    def DATABASE_URL(self):
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

# Instancia as configurações para serem usadas no resto do projeto
settings = Settings()