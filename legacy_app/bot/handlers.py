# legacy_app/bot/handlers.py
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session

# Importa nossas ferramentas de banco de dados (CRUD) e conexão
from legacy_app.db import crud
from legacy_app.db.database import SessionLocal

# Importa o "cérebro" especialista e o "Contrato" de Intenção
from legacy_app.services import analysis
from legacy_app.services.analysis import UserIntent # Importa o Enum

# --- Configuração ---
MAX_REFINEMENT_ATTEMPTS = 3 # A "Rede de Segurança": número de perguntas complementares

# --- Funções Helper ---

def get_db() -> Session:
    """Helper para obter uma sessão de DB limpa."""
    return SessionLocal()

# --- Handler: /start ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lida com o comando /start."""
    chat_id = update.message.chat_id
    first_name = update.message.from_user.first_name
    db = get_db()
    
    try:
        user = crud.get_user_by_chat_id(db, chat_id=chat_id)
        
        if not user:
            # 1. Se não, cria o usuário
            user = crud.create_user(db, chat_id=chat_id, first_name=first_name)
            await update.message.reply_text(
                f"Olá, {first_name}! Bem-vindo ao Projeto Legado. "
                "Eu sou Bastião, e vou te ajudar a contar suas histórias."
            )
        else:
            await update.message.reply_text(f"Bem-vindo de volta, {first_name}!")

        # 2. Verifica se o usuário está 'IDLE' (ocioso)
        if user.user_state == 'IDLE':
            question = crud.get_question_by_order(db, order_id=user.current_question_id)
            if question:
                await update.message.reply_text(
                    f"Vamos começar.\n\nPergunta #{question.order}: {question.question_text}"
                )
                # Define o estado para "CONVERSANDO" e prepara o cache
                crud.set_user_state_conversing(db, user, question_id=question.order)
            else:
                await update.message.reply_text("Você já respondeu todas as perguntas por enquanto!")
        else:
            # Se o usuário der /start no meio de uma conversa, não o interrompa.
            await update.message.reply_text(
                "Parece que já estávamos no meio de uma história. Por favor, continue de onde paramos."
            )
    
    except Exception as e:
        print(f"Erro no /start: {e}")
        await update.message.reply_text("Ops, algo deu errado. Tente novamente.")
    
    finally:
        db.close()

# --- Handler: Mensagens de Texto (O "GERENTE") ---

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Lida com todas as mensagens de texto do usuário.
    Este é o "Gerente" que implementa o "Loop de Refinamento".
    """
    chat_id = update.message.chat_id
    raw_text = update.message.text
    db = get_db()
    user_updated = False # Flag para saber se precisamos comitar no final

    try:
        user = crud.get_user_by_chat_id(db, chat_id=chat_id)
        
        # --- Verificações de Guarda ---
        if not user:
            await update.message.reply_text("Por favor, use /start para começar.")
            db.close()
            return
        
        if user.user_state == 'IDLE':
            await update.message.reply_text(
                "Desculpe, não estou esperando uma resposta agora. "
                "Você pode usar /start para vermos a próxima pergunta."
            )
            db.close()
            return
        
        # --- O LOOP DE REFINAMENTO (NV 3.1) ---
        # Se chegamos aqui, o user_state é 'CONVERSANDO_Q...'
        
        # 1. Pega o "rascunho" anterior do banco
        historia_anterior = user.context_cache 
        
        await update.message.reply_text("Hum, deixe-me pensar sobre isso...")

        # 2. Chama o "Cérebro Nv3.1" (agora mais inteligente)
        analise = analysis.analisar_e_refinar(
            historia_anterior=historia_anterior,
            novo_texto=raw_text
        )

        # 3. O GERENTE TOMA A DECISÃO
        
        # --- Cenário 1: "FUGA INTELIGENTE" (O usuário quer parar) ---
        if analise.user_intent == UserIntent.STOPPING:
            print(f"[Usuário {chat_id}] Detectada INTENÇÃO DE FUGA.")
            await update.message.reply_text("Entendido. Sem problemas, vamos seguir em frente.")

            # Salva o que quer que esteja no "rascunho" (cache),
            # DESDE QUE o rascunho não esteja vazio.
            if historia_anterior:
                crud.create_story_chunk(db, user=user, final_story=historia_anterior)
                print(f"[Usuário {chat_id}] História (do cache) APROVADA via fuga.")
            
            # Avança para a próxima pergunta
            next_q_id = user.current_question_id + 1
            user = crud.set_user_state_idle(db, user, next_question_id=next_q_id)
            user_updated = True # O estado do usuário mudou

            # Envia a próxima pergunta
            next_question = crud.get_question_by_order(db, order_id=user.current_question_id)
            if next_question:
                await update.message.reply_text(
                    f"Quando estiver pronto, aqui está a próxima pergunta:\n\n"
                    f"#{next_question.order}: {next_question.question_text}"
                )
                crud.set_user_state_conversing(db, user, question_id=next_question.order)
            else:
                await update.message.reply_text("Você respondeu todas as perguntas! Parabéns!")

        # --- Cenário 2: "FUGA DA REDE DE SEGURANÇA" (Muitas tentativas) ---
        elif user.refinement_attempts >= MAX_REFINEMENT_ATTEMPTS:
            print(f"[Usuário {chat_id}] Atingido MAX_REFINEMENT_ATTEMPTS.")
            await update.message.reply_text("Entendido, acho que temos o suficiente sobre isso. Vamos seguir.")
            
            # Forçamos a aprovação da última história editada
            crud.create_story_chunk(db, user=user, final_story=analise.historia_editada)
            
            # Avança para a próxima pergunta
            next_q_id = user.current_question_id + 1
            user = crud.set_user_state_idle(db, user, next_question_id=next_q_id)
            user_updated = True # O estado do usuário mudou
            
            # ... (código para enviar a próxima pergunta) ...
            next_question = crud.get_question_by_order(db, order_id=user.current_question_id)
            if next_question:
                await update.message.reply_text(
                    f"Quando estiver pronto, aqui está a próxima pergunta:\n\n"
                    f"#{next_question.order}: {next_question.question_text}"
                )
                crud.set_user_state_conversing(db, user, question_id=next_question.order)
            else:
                await update.message.reply_text("Você respondeu todas as perguntas! Parabéns!")

        # --- Cenário 3: "APROVADO" (História está boa) ---
        elif analise.esta_completo:
            print(f"[Usuário {chat_id}] História APROVADA para Q{user.current_question_id}.")
            
            await update.message.reply_text("Entendido! Que ótima história. Anotei aqui:")
            await update.message.reply_text(analise.historia_editada)
            
            crud.create_story_chunk(db, user=user, final_story=analise.historia_editada)
            
            next_q_id = user.current_question_id + 1
            user = crud.set_user_state_idle(db, user, next_question_id=next_q_id)
            user_updated = True # O estado do usuário mudou

            # ... (código para enviar a próxima pergunta) ...
            next_question = crud.get_question_by_order(db, order_id=user.current_question_id)
            if next_question:
                await update.message.reply_text(
                    f"Quando estiver pronto, aqui está a próxima pergunta:\n\n"
                    f"#{next_question.order}: {next_question.question_text}"
                )
                crud.set_user_state_conversing(db, user, question_id=next_question.order)
            else:
                await update.message.reply_text("Você respondeu todas as perguntas! Parabéns!")

        # --- Cenário 4: "REPROVADO" (Continuar o loop) ---
        else: # (analise.esta_completo == false E user_intent != STOPPING)
            print(f"[Usuário {chat_id}] História REFINANDO para Q{user.current_question_id}.")
            
            # Incrementa o contador da "rede de segurança"
            user.refinement_attempts += 1
            user_updated = True # O estado do usuário mudou
            
            # Atualiza o rascunho (cache)
            crud.update_user_context_cache(db, user, new_cache_content=analise.historia_editada)
            
            # Envia a pergunta complementar (o estado NÃO muda)
            await update.message.reply_text(analise.pergunta_complementar)
            
    except Exception as e:
        print(f"ERRO CRÍTICO no handle_text: {e}")
        await update.message.reply_text("Ops, algo deu muito errado ao processar sua história. Vamos tentar de novo.")
        # Tenta redefinir o estado do usuário para 'IDLE' para destravar
        if 'user' in locals():
            crud.set_user_state_idle(db, user, next_question_id=user.current_question_id)
            user_updated = True
    
    finally:
        # Commit centralizado
        # Todas as nossas funções 'crud' que mudam o estado (exceto 'create_story_chunk')
        # precisam de um commit. Vamos fazer isso aqui para garantir.
        # Edição: Movi o commit para dentro das funções crud para ser mais atômico.
        # Mas uma boa prática é garantir que o db seja fechado.
        db.close()