"""KnowledgeFlow AI 服务入口。

启动：uvicorn main:app --reload --port 8000
CORS：允许来源由环境变量 CORS_ORIGINS 控制，逗号分隔；默认为开发环境地址。
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from routers import agent, chat, ingest, search
import metrics as kf_metrics

app = FastAPI(
    title="KnowledgeFlow AI Service",
    description="文档分块向量化（/ai/ingest）、语义检索（/ai/search）、问答（/ai/chat，SSE）",
    version="1.0.0",
)

# CORS 来源由环境变量控制，生产环境覆盖此列表
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8080,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in _cors_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def _count_requests(request, call_next):
    """按路径累加请求计数（Prometheus /metrics 数据源）。"""
    response = await call_next(request)
    path = request.url.path
    if path == "/ai/ingest":
        kf_metrics.bump("ingest_total")
    elif path == "/ai/search":
        kf_metrics.bump("search_total")
    elif path in ("/ai/chat", "/ai/chat/stream"):
        kf_metrics.bump("chat_total")
    return response

app.include_router(ingest.router)
app.include_router(search.router)
app.include_router(chat.router)
app.include_router(agent.router)


@app.get("/metrics", tags=["health"])
def metrics():
    """Prometheus 文本格式指标（Grafana 全栈监控的 AI 侧数据源）。"""
    return PlainTextResponse(
        kf_metrics.render(), media_type="text/plain; version=0.0.4; charset=utf-8"
    )


@app.get("/ai/health", tags=["health"])
def health():
    return {"status": "ok", "service": "knowledgeflow-ai"}
