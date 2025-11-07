# legacy_app/db/crud.py
from sqlalchemy.orm import Session
from . import models # Vamos mover/criar 'models.py' aqui em breve
from legacy_app.services.analysis import AnaliseDaHistoria # Importamos o "contrato" do cérebro

# --- Funções de Leitura (Read) ---

def get_user_by_chat_id(db: Session, chat_id: int) -> models.User | None:
    """Busca um usuário pelo seu ID do chat do Telegram."""
    return db.query(models.User).filter(models.User.chat_id == chat_id).first()

def get_question_by_order(db: Session, order_id: int) -> models.Question | None:
    """Busca uma pergunta pela sua ordem."""
    return db.query(models.Question).filter(models.Question.order == order_id).first()

# --- Funções de Escrita (Create / Update) ---

def create_user(db: Session, chat_id: int, first_name: str) -> models.User:
    """Cria um novo usuário no banco."""
    # O estado inicial é 'IDLE' (ocioso) e a primeira pergunta é a 1.
    new_user = models.User(
        chat_id=chat_id, 
        first_name=first_name, 
        current_question_id=1,
        user_state='IDLE', # <- Adicionando o estado que planejamos
        context_cache=None
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user) # Recarrega o 'new_user' com os dados do DB (como o ID)
    return new_user

def create_story_chunk(db: Session, user: models.User, final_story: str) -> models.StoryChunk:
    """
    Salva a história final e APROVADA no banco.
    """
    new_chunk = models.StoryChunk(
        user_id=user.id,
        question_id=user.current_question_id,
        # Nós salvamos a história final em ambas as colunas por simplicidade.
        # Poderíamos ter um "raw_text" que é a concatenação de todas as entradas,
        # mas isso é mais limpo por agora.
        raw_transcription=final_story, 
        edited_story=final_story
    )
    db.add(new_chunk)
    db.commit()
    db.refresh(new_chunk)
    return new_chunk

def set_user_state_idle(db: Session, user: models.User, next_question_id: int) -> models.User:
    """
    Redefine o usuário para o estado 'IDLE' (Ocioso),
    limpa o cache e avança para a próxima pergunta.
    Isso é chamado APÓS uma história ser salva com sucesso.
    """
    user.user_state = 'IDLE'
    user.context_cache = None # Limpa o rascunho
    user.current_question_id = next_question_id
    user.refinement_attempts = 0
    db.commit()
    db.refresh(user)
    return user

def set_user_state_conversing(db: Session, user: models.User, question_id: int) -> models.User:
    """
    Define o usuário para o estado 'CONVERSANDO' sobre uma pergunta.
    Isso é chamado QUANDO uma nova pergunta é feita.
    """
    user.user_state = f'CONVERSANDO_Q{question_id}'
    user.context_cache = "" # Inicializa o rascunho como vazio
    user.refinement_attempts = 0
    db.commit()
    db.refresh(user)
    return user

def update_user_context_cache(db: Session, user: models.User, new_cache_content: str) -> models.User:
    """
    Atualiza o "rascunho em construção" (cache) durante o loop de refinamento.
    """
    user.context_cache = new_cache_content
    db.commit()
    db.refresh(user)
    return user