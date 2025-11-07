# legacy_app/bot/app.py
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Importa nossas configurações centrais e os handlers
from legacy_app.core.config import settings
from . import handlers

# Importa a função de inicialização do banco
from legacy_app.db.database import init_db

def main():
    """
    Função principal para construir e iniciar o bot de Telegram
    usando o modo 'polling'.
    """
    
    # 1. Garante que o banco e as tabelas existam
    # (Não precisa mais do 'seed.py' aqui, só do 'init_db')
    try:
        init_db()
    except Exception as e:
        print(f"ERRO: Não foi possível inicializar o banco de dados: {e}")
        print("Verifique se o Docker está rodando.")
        return # Sai se não puder conectar ao DB

    print("Bot iniciando...")
    
    # 2. Cria o aplicativo do bot usando o Token
    application = Application.builder().token(settings.TELEGRAM_TOKEN).build()

    # 3. Registra os "handlers" (comandos e lógica)
    # Diz ao bot: "Quando você receber o comando /start, 
    # chame a função 'start_command' do handlers.py"
    application.add_handler(CommandHandler("start", handlers.start_command))
    
    # "Quando receber qualquer mensagem de texto que NÃO seja um comando,
    # chame a função 'handle_text' do handlers.py"
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_text))

    # 4. Inicia o bot
    print("Bot iniciado e 'ouvindo' por mensagens (Polling)...")
    application.run_polling()

# Nota: Não há 'if __name__ == "__main__"' aqui.
# Este arquivo será chamado pelo 'run.py'.