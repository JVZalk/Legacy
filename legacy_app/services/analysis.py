# legacy_app/services/analysis.py
from pydantic import BaseModel, Field
from enum import Enum
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from legacy_app.core.config import settings # Importamos nossas configs centrais

# -----------------------------------------------------------------
# 1. O CONTRATO (O "FORMULÁRIO" DO BASTIÃO)
# -----------------------------------------------------------------
# Este Pydantic Model é o nosso "contrato de saída".
# O LLM será forçado a preencher este formulário.

class UserIntent(str, Enum):
    """Padroniza as intenções que o Bastião pode detectar."""
    REFINING = "REFINING"     # O usuário está adicionando informações
    STOPPING = "STOPPING"     # O usuário quer parar/pular esta pergunta
    CONFUSED = "CONFUSED"     # O usuário está confuso com a pergunta

class AnaliseDaHistoria(BaseModel):
    """
    Um formulário estruturado para a análise de Bastião sobre
    a história que está sendo construída.
    """
    historia_editada: str = Field(
        description="A história completa e combinada (anterior + novo texto), já editada em prosa limpa de primeira pessoa."
    )
    
    critica: str = Field(
        description="Uma crítica curta (uma frase) sobre a profundidade da 'historia_editada'. O que faltou? Emoções? Detalhes? Datas?"
    )
    
    esta_completo: bool = Field(
        description="'true' se a 'historia_editada' estiver boa o suficiente para salvar, 'false' se for muito curta, superficial ou se a crítica identificar falhas."
    )
    
    pergunta_complementar: str | None = Field(
        description="Se 'esta_completo' for 'false', gere uma pergunta gentil e específica para extrair os detalhes que faltam. Se 'true', este campo deve ser 'null'."
    )

    user_intent: UserIntent = Field(
        description="A intenção do usuário por trás do 'novo_texto', "
                    "dado o contexto da 'historia_anterior' e da minha última pergunta."
    ) 

# -----------------------------------------------------------------
# 2. O ESPECIALISTA (O LLM)
# -----------------------------------------------------------------
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.3,
    google_api_key=settings.GOOGLE_API_KEY
)

# Vinculamos o LLM ao nosso "Contrato" (AnaliseDaHistoria)
# Agora, o LLM sabe que sua saída DEVE seguir este formato.
llm_com_estrutura = llm.with_structured_output(AnaliseDaHistoria)

# -----------------------------------------------------------------
# 3. O PROMPT (A ALMA DO BASTIÃO)
# -----------------------------------------------------------------
# Este é o prompt mais importante. Ele define a lógica do "Loop Nv3".

system_prompt = """
Você é Bastião, um biógrafo gentil, curioso e com memória.
Sua tarefa é analisar uma conversa em andamento e preencher um formulário de análise.

Você receberá `historia_anterior` (o rascunho) e `novo_texto` (a resposta do usuário).

SUAS TAREFAS:
1.  **Detectar Intenção (MAIS IMPORTANTE):** Qual é a intenção do 'novo_texto'?
    -   `STOPPING`: Se o usuário disser "não me lembro", "não sei", "é só isso", "pular", etc.
    -   `CONFUSED`: Se o usuário parecer confuso com a *sua* pergunta (ex: "o que você quer dizer?").
    -   `REFINING`: Se o usuário estiver fornecendo novas informações para a história.
2.  **Integrar e Editar:** Combine `historia_anterior` e `novo_texto`. Edite a história combinada.
3.  **Criticar:** Analise a história editada. 
    -   Se a intenção for `STOPPING`, a história está automaticamente `completa`.
    -   Caso contrário, avalie a profundidade. A história precisa de detalhes CONCRETOS.
4.  **Gerar Pergunta (A NOVA LÓGICA):**
    -   Se for RUIM (`esta_completo` = false), gere uma `pergunta_complementar` gentil.
    -   **REGRA DE OURO:** Foque em perguntas que buscam **fatos, não abstrações.**
    -   **EVITE:** Perguntas repetitivas sobre "sentimentos", "cheiros" ou "cores". Você pode perguntar sobre sentimentos *uma vez*, mas se o usuário não elaborar, siga em frente.
    -   **PREFIRA (O Cardápio de Perguntas):**
        -   **Pessoas:** "Havia mais alguém com o senhor?"
        -   **Contexto/Data:** "Em que época/ano foi isso?"
        -   **Sequência:** "E o que aconteceu depois disso?"
        -   **Motivação:** "O que o levou a fazer isso?"
        -   **Localização:** "Onde exatamente isso aconteceu?"

Você DEVE preencher o formulário 'AnaliseDaHistoria' com sua análise.
"""

prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", 
     "História Anterior (Rascunho):\n{historia_anterior}\n\n"
     "Novo Texto (O que o usuário acabou de dizer):\n{novo_texto}")
])

# -----------------------------------------------------------------
# 4. A "CHAIN" (A LINHA DE MONTAGEM)
# -----------------------------------------------------------------
# O fluxo é simples: o input do usuário vai para o Prompt,
# que vai para o LLM que sabe como preencher o formulário.
analise_chain = prompt_template | llm_com_estrutura

# -----------------------------------------------------------------
# 5. A FUNÇÃO DE SERVIÇO (O PONTO DE ENTRADA DO "GERENTE")
# -----------------------------------------------------------------
def analisar_e_refinar(historia_anterior: str | None, novo_texto: str) -> AnaliseDaHistoria:
    """
    Combina uma história anterior com um novo texto, edita,
    e critica o resultado.
    Esta é a "célula" de trabalho principal do nosso agente.
    """
    print(f"--- Invocando Cérebro Nv3 (Analisar e Refinar)... ---")
    
    # Garantia de que o 'context_cache' nulo seja tratado como string vazia
    if historia_anterior is None:
        historia_anterior = ""
        
    try:
        # 'invoke' executa a corrente.
        analise = analise_chain.invoke({
            "historia_anterior": historia_anterior,
            "novo_texto": novo_texto
        })
        print(f"--- Análise Nv3 concluída com sucesso! ---")
        return analise
        
    except Exception as e:
        print(f"ERRO CRÍTICO no Cérebro (analysis.py): {e}")
        # Retorno de falha segura. Se a IA falhar, não aprovamos
        # a história e pedimos ao usuário para tentar de novo.
        return AnaliseDaHistoria(
            historia_editada=historia_anterior, # Retorna o rascunho antigo
            critica="Falha interna na análise da IA.",
            esta_completo=False, 
            pergunta_complementar="Peço desculpas, me perdi em meus pensamentos. Você poderia, por favor, repetir o que disse?"
        )