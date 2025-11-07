# scripts/seed.py
import sys
import os

# --- A MÁGICA DA CONFIGURAÇÃO DE CAMINHO ---
# Este script está "fora" do nosso aplicativo.
# Para que ele possa importar 'legacy_app.db.models' e outros,
# precisamos adicionar a pasta raiz do projeto ('/projetos/Legacy')
# ao caminho de busca do Python (PYTHONPATH).

# Pega o caminho do diretório onde o script está (/projetos/Legacy/scripts)
script_dir = os.path.dirname(os.path.abspath(__file__))
# Pega o caminho do diretório pai (/projetos/Legacy)
project_root = os.path.dirname(script_dir)
# Adiciona o diretório pai ao sys.path
sys.path.append(project_root)

# Agora podemos importar nossos módulos como se estivéssemos dentro do app
from legacy_app.db.database import SessionLocal, init_db, engine
from legacy_app.db.models import Question, Base

# -----------------------------------------------------------------

# 1. Defina sua lista de perguntas
# (Categoria, Texto, Ordem)
QUESTIONS_TO_ADD = [
    # Infância
    ("Infância", "Qual é a sua lembrança mais antiga?", 1),
    ("Infância", "Como era a casa e o bairro onde você cresceu?", 2),
    ("Infância", "Quem foi seu melhor amigo(a) de infância e o que vocês faziam?", 3),
    ("Infância", "Qual foi a maior travessura que você fez quando criança?", 4),
    
    # Juventude & Carreira
    ("Juventude", "Como você era na escola? Do que mais gostava?", 5),
    ("Carreira", "Qual foi o seu primeiro emprego? Como foi a experiência?", 6),
    ("Carreira", "Como você escolheu sua profissão? Foi um caminho direto?", 7),
    ("Juventude", "Qual foi a maior aventura que você viveu quando jovem?", 8),

    # Família
    ("Família", "Como você conheceu seu cônjuge/parceiro(a)?", 9),
    ("Família", "Qual é a sua lembrança favorita de quando seus filhos eram pequenos?", 10),
    ("Família", "Qual tradição de família é mais importante para você?", 11),

    # Reflexão
    ("Reflexão", "Qual foi o maior desafio que você já superou na vida?", 12),
    ("Reflexão", "Pelo que você é mais grato(a) na vida?", 13),
    ("Reflexão", "Se você pudesse dar um conselho para o seu 'eu' de 20 anos, qual seria?", 14),
    ("Reflexão", "Qual você acha que foi a invenção mais importante durante a sua vida?", 15),
]

def populate_questions():
    """
    Popula o banco de dados com perguntas iniciais,
    evitando duplicatas pela coluna 'order'.
    """
    print("Iniciando a semeadura (seeding) de perguntas...")
    # Usamos o SessionLocal da nossa nova arquitetura
    db = SessionLocal() 
    
    try:
        # Busca todas as 'ordens' que já existem no banco
        current_orders = {q.order for q in db.query(Question.order).all()}
        
        questions_added = 0
        for category, text, order in QUESTIONS_TO_ADD:
            # Só adiciona se a 'ordem' não estiver na lista de ordens atuais
            if order not in current_orders:
                new_question = Question(
                    question_text=text,
                    category=category,
                    order=order
                )
                db.add(new_question)
                questions_added += 1
            
        if questions_added > 0:
            db.commit()
            print(f"Sucesso! {questions_added} novas perguntas foram adicionadas.")
        else:
            print("Nenhuma pergunta nova para adicionar. O banco já está populado.")
            
    except Exception as e:
        print(f"Erro ao popular o banco de dados: {e}")
        db.rollback()
    finally:
        db.close() # Sempre feche a sessão

if __name__ == "__main__":
    # 1. Garante que o Docker (ou Postgres local) esteja rodando.
    
    # 2. Chama a função init_db() do 'database.py'
    #    Isso garante que as tabelas existam antes de tentar popular.
    try:
        # Usamos o 'engine' importado para verificar se o DB está de pé
        # antes de tentar criar as tabelas.
        with engine.connect() as connection:
            print("Conexão com o banco de dados bem-sucedida.")
        
        # Agora chama a função que executa o Base.metadata.create_all()
        init_db() 
    
    except Exception as e:
        print(f"ERRO: Não foi possível conectar ao banco de dados ou criar tabelas.")
        print(f"Detalhe: {e}")
        print("Por favor, garanta que o contêiner Docker do Postgres esteja rodando (`docker-compose up -d`)")
        sys.exit(1) # Sai do script se não puder conectar

    # 3. Popula o banco
    populate_questions()