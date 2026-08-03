"""LLM 适配层 — OpenAI 兼容客户端（DeepSeek）。

API Key 解析顺序（DR-13 开源预留）：
  请求头 X-API-Key → 环境变量 LLM_API_KEY（.env）→ 明确报错「请配置 API Key」。
无 Key 时禁止假装生成（直接抛错），保证可复现、不幻觉。
"""
from __future__ import annotations

from fastapi import Request
from openai import OpenAI

from config import get_settings

KEY_ERROR = "请配置 API Key（请求头 X-API-Key 或环境变量 LLM_API_KEY）"


def resolve_api_key(request: Request | None = None) -> str:
    """按序解析：请求头 X-API-Key → 环境变量 LLM_API_KEY"""
    if request is not None:
        header_key = request.headers.get("X-API-Key")
        if header_key:
            return header_key
    settings = get_settings()
    if settings.llm_api_key:
        return settings.llm_api_key
    raise ValueError(KEY_ERROR)


def get_llm_client(api_key: str) -> OpenAI:
    settings = get_settings()
    return OpenAI(api_key=api_key, base_url=settings.llm_base_url)


def stream_chat(client: OpenAI, messages: list[dict], model: str | None = None):
    """流式调用 LLM，yield 每个增量文本。"""
    settings = get_settings()
    stream = client.chat.completions.create(
        model=model or settings.llm_model,
        messages=messages,
        stream=True,
        temperature=0.3,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def sync_chat(client: OpenAI, messages: list[dict], model: str | None = None) -> str:
    """同步调用 LLM，返回完整文本。"""
    settings = get_settings()
    resp = client.chat.completions.create(
        model=model or settings.llm_model,
        messages=messages,
        stream=False,
        temperature=0.3,
    )
    return resp.choices[0].message.content or ""
