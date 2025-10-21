"""
Configuration management using Pydantic settings.
Loads from config.yaml and environment variables.
"""
import os
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import yaml


class PathsConfig(BaseModel):
    """File system paths configuration."""
    data_root: Path = Field(default=Path("./data"))
    documents: Path = Field(default=Path("./data/documents"))
    indexes: Path = Field(default=Path("./data/indexes"))
    cache: Path = Field(default=Path("./data/cache"))
    backups: Path = Field(default=Path("./data/backups"))
    artifacts: Path = Field(default=Path("./data/artifacts"))
    database: Path = Field(default=Path("./data/knowledge.db"))


class ServerConfig(BaseModel):
    """Server configuration."""
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = False
    workers: int = 1


class OllamaConfig(BaseModel):
    """Ollama LLM configuration."""
    base_url: str = "http://localhost:11434"
    llm_model: str = "llama3"
    embedding_model: str = "nomic-embed-text"
    temperature: float = 0.7
    timeout: int = 60


class ChunkingConfig(BaseModel):
    """Chunking strategy configuration."""
    method: str = "hierarchical"
    chunk_size: int = 512
    chunk_overlap: int = 100
    min_chunk_size: int = 100
    max_chunk_size: int = 800
    preserve_structure: bool = True


class BM25Config(BaseModel):
    """BM25 indexing configuration."""
    enabled: bool = True
    engine: str = "whoosh"


class VectorConfig(BaseModel):
    """Vector indexing configuration."""
    enabled: bool = True
    engine: str = "chroma"
    dimension: int = 768
    distance_metric: str = "cosine"


class IndexingConfig(BaseModel):
    """Indexing configuration."""
    bm25: BM25Config = Field(default_factory=BM25Config)
    vector: VectorConfig = Field(default_factory=VectorConfig)
    incremental: bool = True
    batch_size: int = 100


class RerankerConfig(BaseModel):
    """Reranker configuration."""
    enabled: bool = False
    model: str = "bge-reranker-mini"
    top_n: int = 5


class SearchConfig(BaseModel):
    """Search and retrieval configuration."""
    top_k: int = 20
    bm25_weight: float = 0.5
    vector_weight: float = 0.5
    reranker: RerankerConfig = Field(default_factory=RerankerConfig)
    merge_adjacent: bool = True
    merge_threshold: float = 0.8


class RAGConfig(BaseModel):
    """RAG configuration."""
    max_context_tokens: int = 4000
    max_output_tokens: int = 1000
    citation_style: str = "numbered"
    min_citations: int = 2
    max_citations: int = 6


class PDFExportConfig(BaseModel):
    """PDF export configuration."""
    engine: str = "weasyprint"
    template: str = "default"
    page_size: str = "A4"
    margin: str = "2cm"


class ExportConfig(BaseModel):
    """Export configuration."""
    default_format: str = "markdown"
    pdf: PDFExportConfig = Field(default_factory=PDFExportConfig)
    cache_ttl: int = 604800  # 7 days


class AuditConfig(BaseModel):
    """Audit configuration."""
    enabled: bool = True
    level: str = "standard"
    log_external_calls: bool = True
    anonymize_queries: bool = True


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "json"
    file: Path = Field(default=Path("./data/app.log"))
    rotation: str = "10 MB"


class SecurityConfig(BaseModel):
    """Security configuration."""
    offline_mode: bool = True
    allow_external_apis: bool = False
    whitelist: List[str] = Field(default_factory=list)
    max_file_size_mb: int = 500


class PerformanceConfig(BaseModel):
    """Performance configuration."""
    max_workers: int = 4
    cache_search_results: bool = True
    cache_ttl: int = 3600
    async_indexing: bool = True


class FeaturesConfig(BaseModel):
    """Feature toggles."""
    graph_rag: bool = False
    asr: bool = False
    ocr: bool = False
    mindmap: bool = True
    study_guide: bool = True


class Config(BaseSettings):
    """
    Main application configuration.
    Loads from config.yaml and environment variables.
    """
    paths: PathsConfig = Field(default_factory=PathsConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    indexing: IndexingConfig = Field(default_factory=IndexingConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)
    audit: AuditConfig = Field(default_factory=AuditConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> "Config":
        """Load configuration from YAML file."""
        yaml_path = Path(yaml_path)
        if not yaml_path.exists():
            return cls()

        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls(**data)

    def ensure_paths(self):
        """Ensure all configured paths exist."""
        for path_name in ["data_root", "documents", "indexes", "cache", "backups", "artifacts"]:
            path = getattr(self.paths, path_name)
            path.mkdir(parents=True, exist_ok=True)


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance."""
    global _config
    if _config is None:
        # Look for config.yaml in current directory or parent
        config_path = Path("config.yaml")
        if not config_path.exists():
            config_path = Path(__file__).parent.parent.parent / "config.yaml"

        _config = Config.from_yaml(config_path) if config_path.exists() else Config()
        _config.ensure_paths()

    return _config


def reload_config():
    """Reload configuration from disk."""
    global _config
    _config = None
    return get_config()
