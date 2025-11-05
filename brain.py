# brain.py
from langchain_google_genai import ChatGoogleGenerativeAI # <- MUDANÇA
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

class AnaliseDaHistoria(BaseModel):
    """
    Um formulário estruturado para a análise de Bastião sobre
    a história contada pelo usuário.
    """
    
    # A 'description' é crucial. O LangChain a usa para ensinar o LLM
    # o que colocar em cada campo.
    
    historia_editada: str = Field(description="O texto da história, já editado e limpo, em primeira pessoa.")
    
    critica: str = Field(description="Uma crítica curta (uma frase) sobre a profundidade da resposta. O que faltou? Emoções? Detalhes? Datas?")
    
    esta_completo: bool = Field(description="O 'gerente' deve usar isso. 'true' se a história estiver boa o suficiente para salvar, 'false' se for muito curta ou superficial.")
    
    pergunta_complementar: str | None = Field(description="Se 'esta_completo' for 'false', gere uma pergunta gentil e específica para extrair os detalhes que faltam. Se 'true', este campo deve ser 'null'.")

class AnaliseDaHistoria(BaseModel):
    """
    Um formulário estruturado para a análise de Bastião sobre
    a história contada pelo usuário.
    """
    historia_editada: str = Field(description="O texto da história, já editado e limpo, em primeira pessoa.")
    critica: str = Field(description="Uma crítica curta (uma frase) sobre a profundidade da resposta. O que faltou? Emoções? Detalhes? Datas?")
    esta_completo: bool = Field(description="O 'gerente' deve usar isso. 'true' se a história estiver boa o suficiente para salvar, 'false' se for muito curta ou superficial.")
    pergunta_complementar: str | None = Field(description="Se 'esta_completo' for 'false', gere uma pergunta gentil e específica para extrair os detalhes que faltam. Se 'true', este campo deve ser 'null'.")


# 1. O Modelo (LLM): Trocado para o Gemini (Flash é ótimo: rápido e inteligente)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.3,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

llm_com_estrutura = llm.with_structured_output(AnaliseDaHistoria)

# 5. O NOVO PROMPT (A Tarefa)
system_prompt = """
Você é Bastião, um biógrafo e editor literário gentil e curioso.
Sua tarefa é analisar a resposta do usuário à sua pergunta e preencher um formulário de análise.

REGRAS DE ANÁLISE:
1.  **Edite o Texto:** Primeiro, edite a resposta para soar como uma prosa limpa em primeira pessoa (remova 'ums', 'ahs').
2.  **Critique a Profundidade:** A resposta é boa? Uma resposta como "foi legal" é RUIM ('esta_completo' = false). Uma resposta com nomes, lugares e sentimentos é BOA ('esta_completo' = true).
3.  **Gere Perguntas:** Se a resposta for ruim, faça uma pergunta complementar gentil para aprofundar (ex: "O que tornava esse lugar tão legal para o senhor?").

Você DEVE preencher o formulário 'AnaliseDaHistoria' com sua análise.
"""

prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "Minha resposta à sua pergunta é: \n\n{texto_bruto}")
])

analise_chain = prompt_template | llm_com_estrutura

# 5. A Função Principal que nosso bot usará
def analisar_historia(texto_bruto: str) -> AnaliseDaHistoria:
    """
    Recebe um texto bruto e retorna um OBJETO de análise estruturado.
    """
    print(f"--- Invocando Cérebro (Análise Estruturada)... ---")
    try:
        # 'invoke' agora retorna um objeto 'AnaliseDaHistoria', não uma string!
        analise = analise_chain.invoke({"texto_bruto": texto_bruto})
        print(f"--- Análise concluída com sucesso! ---")
        return analise
    except Exception as e:
        print(f"Erro ao invocar o LangChain/Gemini: {e}")
        # Retorna um objeto de erro "padrão" para o gerente lidar
        return AnaliseDaHistoria(
            historia_editada=texto_bruto,
            critica="Falha na análise da IA.",
            esta_completo=False, # Força uma falha segura
            pergunta_complementar="Desculpe, me perdi nos meus pensamentos. Pode repetir o que disse?"
        )