# KnowledgeFlow 前端镜像 — 多阶段构建（node 构建 → nginx 托管）
# 构建上下文为仓库根：docker compose build frontend（context: .，dockerfile: frontend/Dockerfile）

# ---- 构建阶段 ----
FROM node:20-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci || npm install
COPY frontend/ .
ARG VITE_API_BASE=/
ENV VITE_API_BASE=$VITE_API_BASE
RUN npm run build

# ---- 运行阶段（nginx 托管 dist + 反代） ----
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
