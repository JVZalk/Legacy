# legacy_app/db/models.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# A MUDANÇA MAIS IMPORTANTE:
# Não criamos mais o 'Base', 'engine' ou 'SessionLocal' aqui.
# Apenas importamos o 'Base' que o 'database.py' já criou.
from .database import Base 

class User(Base):
    """
    Modelo do Usuário no banco de dados.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, unique=True, nullable=False, index=True)
    first_name = Column(String(100))
    current_question_id = Column(Integer, default=1) # A 'order' da pergunta
    
    # A NOVA COLUNA QUE PLANEJAMOS:
    user_state = Column(String(50), default='IDLE', nullable=False) 
    # Ex: 'IDLE', 'ANSWERING_Q15', 'REFINING_Q15'
    context_cache = Column(Text, nullable=True)
    # Relacionamento virtual (não cria coluna)
    # Diz ao SQLAlchemy: "A classe 'StoryChunk' tem um atributo 'user'
    # que se refere a mim."
    story_chunks = relationship("StoryChunk", back_populates="user")
    refinement_attempts = Column(Integer, default=0, nullable=False)
            
class Question(Base):
    """
    Modelo das Perguntas pré-definidas (do script 'seed.py').
    """
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(Text, nullable=False)
    category = Column(String(50))
    order = Column(Integer, unique=True, nullable=False)

class StoryChunk(Base):
    """
    Modelo para cada "pedaço" de história contada pelo usuário.
    """
    __tablename__ = "story_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    raw_transcription = Column(Text) # O texto original do usuário
    edited_story = Column(Text)      # A história limpa pela IA (após aprovação)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamento: "Este 'StoryChunk' pertence a um 'User'"
    user = relationship("User", back_populates="story_chunks")