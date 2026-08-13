# syntax=docker/dockerfile:1
## 多阶段构建：先编译后运行
## 使用 Maven 3.9 + JDK 21 编译
## 使用 Eclipse Temurin JDK 21 JRE 运行

FROM maven:3.9-eclipse-temurin-21 AS build

WORKDIR /app

# 拷贝所有源码
COPY . .

# 安装依赖并编译（跳过测试，只编译 yudao-server 模块及其依赖）
RUN --mount=type=cache,target=/root/.m2 mvn install -DskipTests -pl knowledgeflow-server -am -q

## ---- 运行阶段 ----
FROM eclipse-temurin:21-jre

WORKDIR /app

# 从编译阶段拷贝构建产物
COPY --from=build /app/knowledgeflow-server/target/*.jar app.jar

# 设置时区
ENV TZ=Asia/Shanghai

# 设置 JVM 参数
ENV JAVA_OPTS="-Xms512m -Xmx1g -Djava.security.egd=file:/dev/./urandom"

# 暴露端口
EXPOSE 48080

# 启动应用
CMD java ${JAVA_OPTS} -jar app.jar
