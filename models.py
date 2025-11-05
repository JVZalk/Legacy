# models.py
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.sql import func
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, unique=True, nullable=False, index=True) # ID do chat do Telegram
    first_name = Column(String(100))
    current_question_id = Column(Integer, ForeignKey("questions.id"), default=1)
    
    # Relacionamentos
    questions = relationship("Question", back_populates="user")
    story_chunks = relationship("StoryChunk", back_populates="user")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(Text, nullable=False)
    category = Column(String(50))
    order = Column(Integer, unique=True) # 1, 2, 3...
    
    user = relationship("User", back_populates="questions")

class StoryChunk(Base):
    __tablename__ = "story_chunks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    raw_transcription = Column(Text) # O texto bruto do Whisper
    edited_story = Column(Text)      # O texto limpo do LangChain/GPT
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamentos
    user = relationship("User", back_populates="story_chunks")
    
# Função helper para criar o banco de dados
def init_db():
    Base.metadata.create_all(bind=engine)

# NÃO ESQUEÇA: Você precisa rodar esta função uma vez para criar as tabelas
# if __name__ == "__main__":
#     init_db()
#     print("Banco de dados inicializado.")