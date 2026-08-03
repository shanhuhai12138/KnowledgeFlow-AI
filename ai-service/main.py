"""KnowledgeFlow AI 服务入口（T4.1 骨架）。

启动：uvicorn main:app --reload --port 8000
CORS：允许前端（48080）与后端（Java 转发）访问。
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import agent, chat, ingest, search

app = FastAPI(
    title="KnowledgeFlow AI 服务",
    description="文档分块向量化（/ai/ingest）、语义检索（/ai/search）、问答（/ai/chat，T4.3）",
    version="0.1.0",
)

# CORS：前端（48080）+ 本机任意来源（Java 后端转发请求无 Origin 限制）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:48080",
        "http://127.0.0.1:48080",
        "http://localhost:5173",  # 前端 dev（T3）
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(search.router)
app.include_router(chat.router)
app.include_router(agent.router)


@app.get("/ai/health", tags=["health"])
def health():
    return {"status": "ok", "service": "knowledgeflow-ai"}
