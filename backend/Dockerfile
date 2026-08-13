# KnowledgeFlow 后端镜像 — 多阶段构建（maven 构建 → JRE 运行）
# 构建：docker compose build backend（或 docker build -f backend/Dockerfile backend）

# ---- 构建阶段 ----
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /app
COPY . .
# --mount=type=cache 缓存 /root/.m2，源码变更后仅重编译不重下依赖
RUN --mount=type=cache,target=/root/.m2 mvn install -DskipTests -pl knowledgeflow-server -am -q

# ---- 运行阶段 ----
FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /app/knowledgeflow-server/target/*.jar app.jar
ENV TZ=Asia/Shanghai
ENV JAVA_OPTS="-Xms512m -Xmx1g -Djava.security.egd=file:/dev/./urandom"
EXPOSE 48080
CMD ["sh", "-c", "java ${JAVA_OPTS} -jar app.jar"]
