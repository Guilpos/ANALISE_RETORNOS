# Arquivo: core/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings  # Importamos o seu novo módulo

# A URL agora vem pronta e protegida da classe Settings
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()