"""Embedding 适配层 — 可切换实现（项目书 §4.2 约定）。

- OpenAIEmbedder：OpenAI text-embedding-3-small（1536 维，需 API Key）
- LocalHashEmbedder：零依赖 n-gram 特征向量（768 维，无需 Key；中文按单字/双字、英文按词做特征哈希）

get_embedder() 按配置返回实现（auto：有 Key 用 OpenAI，否则本地降级）。
"""
from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod
from typing import List

from config import get_settings


class BaseEmbedder(ABC):
    dim: int

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        ...

    def embed_query(self, query: str) -> List[float]:
        return self.embed_texts([query])[0]


class OpenAIEmbedder(BaseEmbedder):
    """OpenAI embedding（text-embedding-3-small，1536 维）。"""

    dim = 1536

    def __init__(self):
        from openai import OpenAI
        settings = get_settings()
        kwargs = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            kwargs["base_url"] = settings.openai_base_url
        self.client = OpenAI(**kwargs)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        settings = get_settings()
        resp = self.client.embeddings.create(model=settings.embedding_model, input=texts)
        return [item.embedding for item in resp.data]


# 中文字符 / 英文单词 / 数字
_ZH = re.compile(r"[\u4e00-\u9fff]")
_WORD = re.compile(r"[a-zA-Z0-9]+")


class LocalHashEmbedder(BaseEmbedder):
    """本地 n-gram 特征哈希向量（零依赖降级方案）。

    中文按单字+双字、英文按词作特征，哈希到固定维度并 L2 归一化。
    相同/高重合文本得到相近向量（余弦 ≈ 点积），满足链路验收；语义泛化弱于模型向量。
    """

    dim = 768

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        # 中文单字 + 双字特征
        zh_chars = _ZH.findall(text)
        for i, ch in enumerate(zh_chars):
            vec[self._hash(ch) % self.dim] += 1.0
            if i + 1 < len(zh_chars):
                vec[self._hash(ch + zh_chars[i + 1]) % self.dim] += 1.0
        # 英文/数字词（含字符 trigram）
        for word in _WORD.findall(text.lower()):
            vec[self._hash("w:" + word) % self.dim] += 1.0
            for n in (2, 3):
                for i in range(len(word) - n + 1):
                    vec[self._hash("g:" + word[i:i + n]) % self.dim] += 1.0
        # L2 归一化
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    @staticmethod
    def _hash(s: str) -> int:
        return int(hashlib.md5(s.encode("utf-8")).hexdigest()[:8], 16)


def get_embedder() -> BaseEmbedder:
    settings = get_settings()
    provider = settings.effective_provider
    if provider == "openai":
        return OpenAIEmbedder()
    if provider == "local":
        return LocalHashEmbedder()
    raise ValueError(f"不支持的 embedding provider: {provider}")
