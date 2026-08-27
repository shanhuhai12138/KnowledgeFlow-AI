# KnowledgeFlow AI 服务镜像（pip 清华镜像加速版）
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt  # 代理开启时官方源最快；无代理环境可加 -i https://mirrors.aliyun.com/pypi/simple/
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
