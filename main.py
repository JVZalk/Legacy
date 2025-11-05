# main.py
import os
import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Nossos arquivos locais
import brain # O cérebro do LangChain/Gemini
from models import SessionLocal, User, StoryChunk, Question, init_db

# --- CONFIGURAÇÃO ---
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# --- LÓGICA DO BOT (Handlers do Telegram) ---

# /start: Cadastra o usuário
async def start_command(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    first_name = update.message.from_user.first_name
    
    db = SessionLocal()
    user = db.query(User).filter(User.chat_id == chat_id).first()
    
    if not user:
        new_user = User(chat_id=chat_id, first_name=first_name, current_question_id=1)
        db.add(new_user)
        db.commit()
        await update.message.reply_text(f"Olá, {first_name}! Bem-vindo ao Projeto Legado. Vou te ajudar a contar suas histórias.")
        
        # Enviar a primeira pergunta
        question = db.query(Question).filter(Question.order == 1).first()
        if question:
            await update.message.reply_text(f"Vamos começar.\n\nPergunta #1: {question.question_text}")
        
    else:
        await update.message.reply_text(f"Bem-vindo de volta, {first_name}!")
    
    db.close()

# Função para lidar com mensagens de TEXTO
async def handle_text(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    texto_bruto = update.message.text
    
    db = SessionLocal()
    user = db.query(User).filter(User.chat_id == chat_id).first()
    
    if not user:
        await update.message.reply_text("Por favor, use /start para começar.")
        db.close()
        return

    # Mensagem de "processando"
    await update.message.reply_text("Recebi sua história! 📝 Estou editando...")

    try:
        # 1. NÃO PRECISA DE WHISPER! Já temos o texto.
        
        # 2. Editar com LangChain (O CÉREBRO)
        historia_editada = brain.editar_historia(texto_bruto)

        # 3. Salvar no Banco de Dados
        new_chunk = StoryChunk(
            user_id=user.id,
            question_id=user.current_question_id,
            raw_transcription=texto_bruto, # Salvamos o texto bruto original
            edited_story=historia_editada
        )
        db.add(new_chunk)
        
        # 4. (Lógica Bônus) Avançar para a próxima pergunta
        user.current_question_id += 1
        db.commit()

        # 5. Responder ao Usuário
        reply = f"Que história fantástica! Editei para ficar mais claro. Veja como ficou:\n\n---\n\n{historia_editada}\n\n---"
        await update.message.reply_text(reply)
        
        # 6. Enviar a nova pergunta
        next_question = db.query(Question).filter(Question.order == user.current_question_id).first()
        if next_question:
            await update.message.reply_text(f"Próxima pergunta: {next_question.question_text}")
        else:
            await update.message.reply_text("Você respondeu todas as perguntas por enquanto! Parabéns!")

    except Exception as e:
        print(f"Erro no handle_text: {e}")
        await update.message.reply_text("Ops, algo deu errado ao processar sua história. Tente novamente.")
    finally:
        db.close()

# --- INICIALIZAÇÃO (Modo Polling) ---
def main():
    """Inicia o bot usando Polling (para testes locais)."""
    print("Inicializando o banco de dados...")
    init_db() # Garante que as tabelas existem
    
    print("Iniciando o bot...")
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Adiciona os handlers
    application.add_handler(CommandHandler("start", start_command))
    
    # Este handler pega todas as mensagens de TEXTO que NÃO são comandos
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Inicia o bot
    print("Bot iniciado! Pressione Ctrl+C para parar.")
    application.run_polling()

if __name__ == "__main__":
    main()