
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pydantic import Field

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
    OPENAI_MODEL: str = "doubao-seed-1-6-251015"
    ARK_VISION_MODEL: str = "doubao-seed-1-6-vision-250815"
    
    # Vector DB
    VECTOR_DB_PATH: str = "./data/chroma_db"

    # Elasticsearch
    ES_URL: str = "https://es-15gv7mh7.public.tencentelasticsearch.com:9200"
    ES_INDEX_NAME: str = "langchain_demo_index"
    ES_USER: str = "mlm-user"
    ES_PASSWORD: str = "1ZzIFRasdf+pHs8E8d123"
    EMBEDDING_MODEL: str = "doubao-embedding-text-240715"
    
    # Langfuse Monitoring
    LANGFUSE_PUBLIC_KEY: str = "pk-lf-2b899497-e296-47ba-bc20-9701f9c53ec7"
    LANGFUSE_SECRET_KEY: str = "sk-lf-3773953d-57c2-45c6-b0c4-2dc6dd0adc43" # 需替换为真实 Secret Key
    LANGFUSE_HOST: str = "https://langfuse.yingsaidata.tech"

    # Logging
    LOG_DIR: str = "logs"
    LOG_FILE: str = "app.log"
    LOG_LEVEL: str = "INFO"

    # OBS Configuration
    OBS_ENDPOINT: str = Field(default="obs.cn-south-1.myhuaweicloud.com", description="OBS Endpoint")
    OBS_AK: str = Field(default="SFDDLWTCP3BEQUP0JPIK", description="OBS Access Key")
    OBS_SK: str = Field(default="HGqOMwVce3sa0U0fjidtuKLPeKinxzfLFSuBUvYh", description="OBS Secret Key")
    OBS_BUCKET: str = Field(default="donson1203", description="OBS Bucket Name")
    OBS_PUBLIC_BASE_URL: str = Field(default="https://static1203.yingsaidata.com", description="OBS Public Base URL")

    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

settings = Settings()
