from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Substitua pelas credenciais geradas no TiDB Cloud
# Formato: mysql+pymysql://usuario:senha@host:porta/banco_de_dados
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:suasenha@gateway01.us-east-1.prod.aws.tidbcloud.com:4000/validador_convenios"

# O parâmetro pool_pre_ping=True é vital aqui. Ele testa a conexão 
# antes de cada query, prevenindo travamentos por "broken pipe" em nuvem.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600 # Recicla a conexão a cada hora
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Função geradora que o FastAPI usará para injetar o banco nas rotas
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()