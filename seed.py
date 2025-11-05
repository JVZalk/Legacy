# seed.py
from models import SessionLocal, Question, engine, Base

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
    ("Família", "Como você conheceu [nome do cônjuge/parceiro(a)]?", 9),
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
    db = SessionLocal()
    
    try:
        current_orders = {q.order for q in db.query(Question.order).all()}
        
        questions_added = 0
        for category, text, order in QUESTIONS_TO_ADD:
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
        db.close()

if __name__ == "__main__":
    # Garante que as tabelas existam antes de tentar popular
    Base.metadata.create_all(bind=engine)
    
    # Popula o banco
    populate_questions()