"""轻量进程内指标 — Prometheus 文本格式（零第三方依赖）。

main.py 暴露 /metrics；HTTP 中间件按路径累加请求计数。
后续需要更细粒度指标（直方图/标签维度）时可平滑替换为 prometheus-client。
"""
import platform
import time

START_TIME = time.time()
COUNTERS: dict = {"ingest_total": 0, "search_total": 0, "chat_total": 0}


def bump(name: str, n: int = 1) -> None:
    COUNTERS[name] = COUNTERS.get(name, 0) + n


def render() -> str:
    uptime = round(time.time() - START_TIME, 1)
    lines = [
        "# HELP kf_ai_info AI 服务基本信息",
        "# TYPE kf_ai_info gauge",
        'kf_ai_info{service="knowledgeflow-ai",python_version="%s"} 1' % platform.python_version(),
        "# HELP kf_ai_uptime_seconds AI 服务已运行秒数",
        "# TYPE kf_ai_uptime_seconds gauge",
        "kf_ai_uptime_seconds %s" % uptime,
        "# HELP kf_ai_ingest_total 文档入库累计请求次数",
        "# TYPE kf_ai_ingest_total counter",
        "kf_ai_ingest_total %s" % COUNTERS["ingest_total"],
        "# HELP kf_ai_search_total 检索累计请求次数",
        "# TYPE kf_ai_search_total counter",
        "kf_ai_search_total %s" % COUNTERS["search_total"],
        "# HELP kf_ai_chat_total 问答累计请求次数",
        "# TYPE kf_ai_chat_total counter",
        "kf_ai_chat_total %s" % COUNTERS["chat_total"],
    ]
    return "\n".join(lines) + "\n"
