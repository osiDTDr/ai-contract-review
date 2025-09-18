from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    # LLM 配置
    llm_provider: Literal["openai", "azure", "ollama"] = "openai"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    azure_endpoint: str = ""
    azure_api_key: str = ""
    azure_deployment: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"
    
    # 向量数据库配置
    vector_db: Literal["faiss", "milvus"] = "faiss"
    
    # 嵌入模型配置
    embedding_provider: Literal["openai", "ollama"] = "openai"
    embedding_model: str = "text-embedding-ada-002"
    ollama_embedding_model: str = "nomic-embed-text"
    
    class Config:
        env_file = ".env"

settings = Settings()