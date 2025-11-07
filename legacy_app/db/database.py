# legacy_app/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from legacy_app.core.config import settings # Importa nossas configurações!

# 1. O Engine: A "ponte" entre SQLAlchemy e Postgres
# Ele usa a URL que o 'settings' carregou do .env
engine = create_engine(
    settings.DATABASE_URL,
    # 'pool_pre_ping' é uma boa prática para verificar
    # conexões antes de usá-las.
    pool_pre_ping=True 
)

# 2. A Fábrica de Sessões:
# 'SessionLocal' é uma *classe*. Quando a chamamos,
# ela cria uma nova sessão de conversa com o banco.
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

# 3. A Base dos Modelos:
# Este objeto 'Base' é o "registro" central.
# Quando movermos nosso 'models.py', faremos todas as nossas
# classes (User, Question, etc.) herdarem deste 'Base'.
# É assim que o SQLAlchemy sabe quais tabelas criar.
Base = declarative_base()


# 4. Função de Dependência (Padrão FastAPI/Starlette)
# Esta é a função que nossos 'handlers' do bot usarão
# para obter uma sessão de forma segura.
def get_db():
    """
    Função helper para gerenciar o ciclo de vida da sessão do DB.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Cria todas as tabelas no banco de dados.
    Isso importa os modelos 'models.py' para que o 'Base' os conheça.
    """
    # Importamos aqui para evitar problemas de dependência circular
    # e garantir que os modelos sejam carregados antes de 'create_all'
    print("Inicializando o banco de dados e criando tabelas...")
    from . import models 
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas com sucesso (se não existiam).")