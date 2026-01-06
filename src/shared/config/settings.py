"""
SmartReviewer - Shared Configuration
Centralized configuration management using pydantic-settings
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class QdrantSettings(BaseSettings):
    """Qdrant Vector Database settings."""
    
    model_config = SettingsConfigDict(env_prefix="QDRANT_")
    
    host: str = Field(default="localhost", description="Qdrant host")
    port: int = Field(default=6333, description="Qdrant REST API port")
    grpc_port: int = Field(default=6334, description="Qdrant gRPC port")
    api_key: str | None = Field(default=None, description="Qdrant API key")
    
    # Collection settings
    collection_documents: str = "documents"
    collection_guidelines: str = "guidelines"
    collection_check_items: str = "check_items"


class Neo4jSettings(BaseSettings):
    """Neo4j Graph Database settings."""
    
    model_config = SettingsConfigDict(env_prefix="NEO4J_")
    
    uri: str = Field(default="bolt://localhost:7687", description="Neo4j URI")
    user: str = Field(default="neo4j", description="Neo4j username")
    password: str = Field(default="smartreviewer_dev", description="Neo4j password")
    database: str = Field(default="neo4j", description="Neo4j database name")
    
    # Connection pool settings
    max_connection_lifetime: int = 3600
    max_connection_pool_size: int = 50


class MinIOSettings(BaseSettings):
    """MinIO Object Storage settings."""
    
    model_config = SettingsConfigDict(env_prefix="MINIO_")
    
    endpoint: str = Field(default="localhost:9000", description="MinIO endpoint")
    access_key: str = Field(default="minioadmin", description="MinIO access key")
    secret_key: str = Field(default="minioadmin123", description="MinIO secret key")
    secure: bool = Field(default=False, description="Use HTTPS")
    
    # Bucket names
    bucket_documents: str = "documents"
    bucket_embeddings: str = "embeddings"
    bucket_ontologies: str = "ontologies"
    bucket_results: str = "results"
    bucket_guidelines: str = "guidelines"


class EmbeddingSettings(BaseSettings):
    """Embedding model settings."""
    
    model_config = SettingsConfigDict(env_prefix="EMBEDDING_")
    
    model_name: str = Field(
        default="intfloat/multilingual-e5-large",
        description="Embedding model name",
    )
    vector_size: int = Field(default=1024, description="Embedding vector dimension")
    batch_size: int = Field(default=32, description="Batch size for embedding")
    max_length: int = Field(default=512, description="Max token length")
    normalize: bool = Field(default=True, description="Normalize embeddings")


class LLMSettings(BaseSettings):
    """LLM/Gennai settings for MCP Sampling."""
    
    model_config = SettingsConfigDict(env_prefix="LLM_")
    
    # MCP Sampling settings (actual LLM is on Host side)
    default_model: str = Field(
        default="gennai-default",
        description="Default model hint for MCP Sampling",
    )
    max_tokens: int = Field(default=4096, description="Max tokens for generation")
    temperature: float = Field(default=0.1, description="Sampling temperature")
    
    # Timeout settings
    timeout_seconds: int = Field(default=120, description="Request timeout")


class ServerSettings(BaseSettings):
    """MCP Server settings."""
    
    model_config = SettingsConfigDict(env_prefix="SERVER_")
    
    name: str = Field(default="smartreviewer", description="Server name")
    port: int = Field(default=8000, description="Server port")
    host: str = Field(default="0.0.0.0", description="Server host")
    
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "console"] = "console"


class Settings(BaseSettings):
    """Main application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # Environment
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    
    # Sub-settings
    qdrant: QdrantSettings = Field(default_factory=QdrantSettings)
    neo4j: Neo4jSettings = Field(default_factory=Neo4jSettings)
    minio: MinIOSettings = Field(default_factory=MinIOSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export settings instance
settings = get_settings()
