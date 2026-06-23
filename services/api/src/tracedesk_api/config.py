from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TraceDesk API"
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://tracedesk:tracedesk_dev@localhost:5432/tracedesk"
    session_secret: str = "local-development-secret-change-before-deploy"
    web_origin: str = "http://localhost:3000"
    knowledge_dir: Path = Path("knowledge")
    pdf_dir: Path = Path("output/pdf")
    retrieval_report_dir: Path = Path("reports/retrieval")
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_cache_dir: Path = Path(".model-cache/fastembed")
    knowledge_mcp_url: str = "http://localhost:8101/mcp"
    operations_mcp_url: str = "http://localhost:8102/mcp"
    support_mcp_url: str = "http://localhost:8103/mcp"
    mcp_timeout_seconds: float = 8.0
    anthropic_api_key: str | None = None
    claude_router_model: str = "claude-haiku-4-5"
    claude_investigator_model: str = "claude-sonnet-4-5"
    claude_request_timeout_seconds: float = 90.0
    claude_rate_limit_retry_seconds: float = 65.0
    investigation_max_tool_calls: int = 30
    investigation_max_rounds: int = 4
    investigation_specialist_max_rounds: int = 2
    investigation_token_budget: int = 65000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
