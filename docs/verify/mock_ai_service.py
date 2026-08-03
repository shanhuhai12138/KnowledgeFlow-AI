# -*- coding: utf-8 -*-
"""T2.4 验收用 mock AI 服务：模拟任务书 T4.0 契约（/ai/search、/ai/chat、/ai/chat/stream SSE）"""
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer


class MockAiHandler(BaseHTTPRequestHandler):

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_POST(self):
        body = self._read_body()
        if self.path == "/ai/search":
            self._json(200, {
                "query": body.get("query", ""),
                "tookMs": 12,
                "results": [
                    {"documentId": "1", "documentName": "开发环境搭建 SOP.md", "page": 3, "score": 95,
                     "content": "开发环境搭建步骤……"},
                    {"documentId": "2", "documentName": "代码规范.md", "page": 8, "score": 82,
                     "content": "代码规范要求……"},
                ],
            })
        elif self.path == "/ai/ingest":
            # T2.5：文档处理（幂等，返回 chunkCount）
            content = body.get("content", "")
            chunk_count = max(1, len(content) // 100 + 1)
            self._json(200, {"documentId": body.get("documentId"), "chunkCount": chunk_count, "vectorCount": chunk_count})
        elif self.path == "/ai/chat":
            self._json(200, {
                "id": "a123", "role": "assistant",
                "content": "根据知识库内容，RAG 是检索增强生成。",
                "sources": [{"documentId": "1", "documentName": "开发环境搭建 SOP.md", "page": 3, "score": 95}],
                "confidence": 88, "rating": None,
                "createdAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
            })
        else:
            self._json(404, {"detail": "not found"})

    def do_GET(self):
        if self.path.startswith("/ai/chat/stream"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            events = [
                ("meta", {"type": "meta", "sessionId": "s1", "message": "什么是RAG？"}),
                ("content", {"type": "content", "delta": "RAG 是"}),
                ("content", {"type": "content", "delta": "检索增强生成。"}),
                ("sources", {"type": "sources", "sources": [{"documentId": "1", "documentName": "开发环境搭建 SOP.md", "page": 3, "score": 95}], "confidence": 88}),
                ("done", {"type": "done", "messageId": "a123"}),
            ]
            for name, data in events:
                self.wfile.write(("event: %s\n" % name).encode())
                self.wfile.write(("data: %s\n\n" % json.dumps(data, ensure_ascii=False)).encode())
                self.wfile.flush()
                time.sleep(0.05)
        else:
            self._json(404, {"detail": "not found"})

    def log_message(self, fmt, *args):
        pass  # 静默


if __name__ == "__main__":
    print("Mock AI service on :8000")
    HTTPServer(("127.0.0.1", 8000), MockAiHandler).serve_forever()
