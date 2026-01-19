from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # API Settings
    openrouter_api_key: str = Field(..., alias="OPENROUTER_APIKEY")
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    default_model: str = "mistralai/devstral-2512:free"
    
    # Persistence Settings
    database_path: str = "translations_cache.db"
    
    # Processor Settings
    target_tags: list[str] = [
        'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
        'li', 'blockquote', 'dt', 'dd', 'caption'
    ]
    placeholder_fmt: str = "REF_{:06d}"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Instancia global para ser usada en el proyecto
settings = Settings()
