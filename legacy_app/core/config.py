import os
from functools import lru_cache
from pydantic_settings import BaseSettings

# O Pydantic-Settings é inteligente. Ele automaticamente lê
# as variáveis do seu arquivo .env se elas estiverem definidas
# como atributos nesta classe.

class Settings(BaseSettings):
    """
    Configurações globais do aplicativo, lidas do .env
    """
    
    # BANCO DE DADOS
    DATABASE_URL: str
    
    # BOT
    TELEGRAM_TOKEN: str
    
    # SERVIÇOS DE IA
    GOOGLE_API_KEY: str

    class Config:
        # Informa ao Pydantic para carregar do arquivo .env
        env_file = ".env"
        env_file_encoding = 'utf-8'

# -----------------------------------------------------------------
# O "Padrão Singleton"
# -----------------------------------------------------------------
# O @lru_cache garante que a classe 'Settings' seja instanciada
# APENAS UMA VEZ. Não importa quantas vezes importarmos 'get_settings',
# ele sempre retornará o mesmo objeto de configuração em cache.
# Isso evita ler o .env repetidamente.
@lru_cache
def get_settings() -> Settings:
    """Retorna a instância única das configurações."""
    print("Carregando configurações do .env...")
    return Settings()

# Para facilitar a importação em outros módulos,
# podemos expor uma instância global.
settings = get_settings()