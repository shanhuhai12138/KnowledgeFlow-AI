"""KnowledgeFlow AI 服务配置 — 环境变量驱动。

全部配置可通过环境变量覆盖（大写同名），开发默认值可直接运行：
  QDRANT_URL            Qdrant REST 地址（默认 http://localhost:6333，对应 T1.1 compose）
  QDRANT_COLLECTION     向量集合名（默认 knowledge_segment）
  EMBEDDING_PROVIDER    auto（默认）/ openai / local：
                          auto  → 设置了 OPENAI_API_KEY 用 openai，否则用 local（零依赖降级）
                          openai→ OpenAI text-embedding-3-small（需 API Key）
                          local → 本地 n-gram 特征向量（无需 Key，纯 Python；语义为字面/特征匹配）
  OPENAI_API_KEY        OpenAI API Key（可选）
  OPENAI_BASE_URL       OpenAI 兼容网关地址（可选，如代理/中转）
  EMBEDDING_MODEL       默认 text-embedding-3-small
  EMBEDDING_DIM         向量维度：openai=1536，local=768（切换 provider 时需重建 Qdrant 集合）
  CHUNK_SIZE / CHUNK_OVERLAP  分块参数（默认 1000 / 200，regent 同款）
  TOP_K / THRESHOLD     检索默认 Top-K 与阈值
  LLM_MODEL / LLM_API_KEY      问答模型（T4.3 使用）
"""
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "knowledge_segment"

    # Embedding
    embedding_provider: str = "auto"  # auto / openai / local
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 768  # openai=1536 / local=768

    # 分块（regent 同款参数）
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # 检索
    top_k: int = 5
    threshold: float = 0.0

    # LLM（T4.3 问答；DeepSeek OpenAI 兼容；模型/Key 见 .env：LLM_API_KEY / LLM_MODEL）
    llm_model: str = "deepseek-chat"
    llm_api_key: str | None = None
    llm_base_url: str = "https://api.deepseek.com"

    model_config = {"env_prefix": "", "env_file": ".env", "extra": "ignore"}

    @property
    def effective_provider(self) -> str:
        """auto：有 OpenAI Key 用 openai，否则 local"""
        if self.embedding_provider == "auto":
            return "openai" if self.openai_api_key else "local"
        return self.embedding_provider


@lru_cache
def get_settings() -> Settings:
    return Settings()
