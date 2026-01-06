
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "SmartFlow Agent Hub"
    API_V1_STR: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-it"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # Database
    DATABASE_URL: str = "sqlite:///./data/sql_app.db"

    # LLM
    OPENAI_API_KEY: str = "e07ae987-1258-4bb5-94bb-277bdc9fc310"
    OPENAI_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    OPENAI_MODEL: str = "deepseek-v3-2-251201"
    
    # Vector DB
    VECTOR_DB_PATH: str = "./data/chroma_db"
    
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

settings = Settings()
