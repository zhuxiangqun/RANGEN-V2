# 🐳 Docker 安装和部署指南

本文档介绍如何使用Docker容器化部署RANGEN系统。Docker部署提供了一致的运行环境，简化了依赖管理，支持快速部署和扩展。

## 📋 目录

1. [概述](#概述)
2. [系统要求](#系统要求)
3. [快速开始](#快速开始)
4. [Docker Compose部署](#docker-compose部署)
5. [自定义配置](#自定义配置)
6. [生产环境部署](#生产环境部署)
7. [维护和监控](#维护和监控)
8. [故障排除](#故障排除)

## 📊 概述

### Docker部署优势

- ✅ **一致性**：在所有环境（开发、测试、生产）中提供一致的运行环境
- ✅ **隔离性**：避免依赖冲突和环境差异
- ✅ **可移植性**：轻松迁移和复制部署
- ✅ **可扩展性**：支持水平扩展和容器编排
- ✅ **简化部署**：一键部署，无需手动安装依赖

### 支持的部署模式

1. **单容器模式**：单个容器运行所有组件
2. **多容器模式**：使用Docker Compose编排多个服务
3. **生产模式**：支持高可用、负载均衡和自动扩缩容
4. **开发模式**：包含热重载和调试功能

## ⚙️ 系统要求

### 硬件要求

| 资源 | 最低要求 | 推荐配置 |
|------|----------|----------|
| CPU | 2核 | 4核或更多 |
| 内存 | 4GB | 8GB或更多 |
| 存储 | 10GB可用空间 | 20GB可用空间 |

### 软件要求

1. **Docker Engine**：20.10.0 或更高版本
2. **Docker Compose**：2.0.0 或更高版本
3. **操作系统**：Linux、macOS、Windows 10/11（WSL2）

### 验证安装

```bash
# 验证Docker安装
docker --version

# 验证Docker Compose安装
docker-compose --version

# 验证Docker运行状态
docker info
```

## 🚀 快速开始

### 方法1：使用预构建镜像（最简单）

```bash
# 1. 拉取最新镜像
docker pull rangen/rangen-v2:latest

# 2. 运行容器
docker run -d \
  --name rangen-api \
  -p 8080:8080 \
  -e ENVIRONMENT=development \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  rangen/rangen-v2:latest
```

### 方法2：从源码构建（自定义配置）

```bash
# 1. 克隆仓库
git clone https://github.com/your-repo/RANGEN.git
cd RANGEN

# 2. 构建Docker镜像
docker build -t rangen:latest .

# 3. 运行容器
docker run -d \
  --name rangen-api \
  -p 8080:8080 \
  -e ENVIRONMENT=development \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  rangen:latest
```

### 方法3：使用Docker Compose（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/your-repo/RANGEN.git
cd RANGEN

# 2. 复制环境变量文件
cp .env.example .env
# 编辑.env文件，配置您的API密钥和其他设置

# 3. 启动完整系统
docker-compose up -d

# 4. 验证部署
docker-compose ps
docker-compose logs -f rangen-api
```

### 访问系统

启动后，通过以下地址访问系统：

- **Web界面**：`http://localhost:8080`
- **API文档**：`http://localhost:8080/docs`
- **健康检查**：`http://localhost:8080/health`

## 🐋 Docker Compose部署

### 完整服务架构

RANGEN的Docker Compose配置包含以下服务：

```yaml
# 服务架构：
# 1. rangen-api: 主API服务
# 2. postgres: PostgreSQL数据库
# 3. redis: Redis缓存
# 4. rabbitmq: RabbitMQ消息队列
# 5. vector-db: 向量数据库（可选）
# 6. monitoring: 监控服务（可选）
```

### 环境变量配置

创建或编辑 `.env` 文件：

```bash
# 基础配置
ENVIRONMENT=development
LOG_LEVEL=INFO
API_PORT=8080

# 数据库配置
POSTGRES_DB=rangen_dev
POSTGRES_USER=rangen
POSTGRES_PASSWORD=rangen123

# Redis配置
REDIS_PASSWORD=redis123

# RabbitMQ配置
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# API密钥配置
DEEPSEEK_API_KEY=sk-...
STEPFLASH_API_KEY=sk-...
LOCAL_MODEL_ENABLED=true

# 监控配置
ENABLE_METRICS=true
ENABLE_TRACING=true
```

### 启动命令

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f rangen-api
docker-compose logs -f postgres
docker-compose logs -f redis

# 停止所有服务
docker-compose down

# 停止并清理数据
docker-compose down -v

# 重新构建并启动
docker-compose up -d --build
```

### 服务健康检查

```bash
# 检查API服务健康状态
curl http://localhost:8080/health

# 检查PostgreSQL连接
docker-compose exec postgres pg_isready -U rangen

# 检查Redis连接
docker-compose exec redis redis-cli ping

# 检查RabbitMQ连接
docker-compose exec rabbitmq rabbitmqctl status
```

## ⚙️ 自定义配置

### 自定义Dockerfile

如果需要对基础镜像进行自定义，可以修改 `Dockerfile`：

```dockerfile
# 使用多阶段构建减小镜像大小
FROM python:3.11-slim AS builder

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
COPY requirements-optional.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-optional.txt

# 生产阶段
FROM python:3.11-slim

WORKDIR /app

# 复制已安装的依赖
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY . .

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV TZ=Asia/Shanghai

# 创建非root用户
RUN useradd -m -u 1000 rangen && \
    chown -R rangen:rangen /app

USER rangen

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 自定义docker-compose.yml

根据您的需求自定义编排配置：

```yaml
# 示例：添加向量数据库服务
vector-db:
  image: qdrant/qdrant:v1.8.1
  container_name: rangen-vector-db
  restart: unless-stopped
  ports:
    - "6333:6333"
  volumes:
    - ./qdrant_storage:/qdrant/storage
  environment:
    QDRANT__SERVICE__GRPC_PORT: 6334
  networks:
    - rangen-network

# 示例：添加监控服务
monitoring:
  image: grafana/grafana:latest
  container_name: rangen-monitoring
  restart: unless-stopped
  ports:
    - "3000:3000"
  volumes:
    - ./grafana_data:/var/lib/grafana
    - ./grafana/provisioning:/etc/grafana/provisioning
  environment:
    GF_SECURITY_ADMIN_PASSWORD: admin
  networks:
    - rangen-network
```

### 数据持久化配置

确保关键数据持久化存储：

```yaml
volumes:
  # PostgreSQL数据卷
  postgres_data:
    driver: local
  # Redis数据卷
  redis_data:
    driver: local
  # 向量数据库数据卷
  qdrant_data:
    driver: local
  # 日志数据卷
  logs_data:
    driver: local
  # 配置数据卷
  config_data:
    driver: local
```

## 🚀 生产环境部署

### 生产配置建议

1. **使用特定版本标签**：避免使用 `latest` 标签
2. **启用TLS/SSL**：加密所有通信
3. **配置资源限制**：防止资源耗尽
4. **设置监控告警**：实时监控系统状态
5. **配置备份策略**：定期备份数据

### 生产环境docker-compose.prod.yml

```yaml
# 生产环境专用配置
version: '3.8'

x-common: &common
  restart: unless-stopped
  networks:
    - rangen-network
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"

services:
  rangen-api:
    <<: *common
    build:
      context: .
      dockerfile: Dockerfile.prod
    image: rangen/rangen-v2:${TAG:-stable}
    container_name: rangen-api-prod
    ports:
      - "443:443"
    environment:
      ENVIRONMENT: production
      LOG_LEVEL: WARNING
      SSL_ENABLED: "true"
      ENABLE_RATE_LIMITING: "true"
    volumes:
      - ./ssl:/app/ssl
      - ./config:/app/config:ro
      - ./logs:/app/logs
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
    healthcheck:
      test: ["CMD", "curl", "-f", "https://localhost:443/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

### 负载均衡和高可用

```yaml
# 使用Nginx作为负载均衡器
nginx:
  image: nginx:alpine
  container_name: rangen-nginx
  restart: unless-stopped
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
    - ./ssl:/etc/nginx/ssl
  depends_on:
    - rangen-api-1
    - rangen-api-2
    - rangen-api-3
  networks:
    - rangen-network

# 多个API实例
rangen-api-1:
  <<: *common
  image: rangen/rangen-v2:${TAG}
  container_name: rangen-api-1
  environment:
    NODE_ID: "api-1"
    ENVIRONMENT: production
  deploy:
    replicas: 1

rangen-api-2:
  <<: *common
  image: rangen/rangen-v2:${TAG}
  container_name: rangen-api-2
  environment:
    NODE_ID: "api-2"
    ENVIRONMENT: production
  deploy:
    replicas: 1

rangen-api-3:
  <<: *common
  image: rangen/rangen-v2:${TAG}
  container_name: rangen-api-3
  environment:
    NODE_ID: "api-3"
    ENVIRONMENT: production
  deploy:
    replicas: 1
```

### 监控和日志收集

```yaml
# ELK堆栈用于日志收集
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.12.0
  container_name: rangen-elasticsearch
  environment:
    - discovery.type=single-node
    - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
  volumes:
    - elasticsearch_data:/usr/share/elasticsearch/data
  ports:
    - "9200:9200"

logstash:
  image: docker.elastic.co/logstash/logstash:8.12.0
  container_name: rangen-logstash
  volumes:
    - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
  ports:
    - "5000:5000"
  depends_on:
    - elasticsearch

kibana:
  image: docker.elastic.co/kibana/kibana:8.12.0
  container_name: rangen-kibana
  environment:
    ELASTICSEARCH_HOSTS: '["http://elasticsearch:9200"]'
  ports:
    - "5601:5601"
  depends_on:
    - elasticsearch
```

## 🔧 维护和监控

### 日常维护

#### 容器管理

```bash
# 查看容器状态
docker ps -a

# 查看容器资源使用
docker stats

# 进入容器shell
docker exec -it rangen-api bash

# 查看容器日志
docker logs -f rangen-api

# 重启容器
docker restart rangen-api

# 停止和删除容器
docker stop rangen-api
docker rm rangen-api
```

#### 镜像管理

```bash
# 查看镜像列表
docker images

# 清理未使用的镜像
docker image prune -a

# 删除特定镜像
docker rmi rangen/rangen-v2:old-version

# 推送镜像到仓库
docker push rangen/rangen-v2:latest
```

#### 数据备份

```bash
# 备份数据库
docker exec rangen-postgres pg_dump -U rangen rangen_dev > backup.sql

# 备份配置
docker cp rangen-api:/app/config ./config_backup/

# 备份日志
docker cp rangen-api:/app/logs ./logs_backup/

# 创建完整系统快照
docker-compose exec rangen-api python scripts/create_backup.py
```

### 系统监控

#### 性能监控

```bash
# 监控容器资源使用
docker stats rangen-api

# 查看容器详细状态
docker inspect rangen-api

# 查看容器进程
docker top rangen-api

# 监控网络流量
docker network inspect rangen-network
```

#### 健康检查

```bash
# 自动健康检查
docker-compose exec rangen-api python scripts/health_check.py

# 检查数据库连接
docker-compose exec postgres psql -U rangen -d rangen_dev -c "SELECT 1"

# 检查缓存连接
docker-compose exec redis redis-cli ping

# 检查消息队列
docker-compose exec rabbitmq rabbitmqctl list_queues
```

#### 日志分析

```bash
# 实时查看日志
docker-compose logs -f --tail=100

# 搜索错误日志
docker-compose logs rangen-api | grep -i error

# 导出日志到文件
docker-compose logs rangen-api > rangen_api_logs.txt

# 分析日志统计
docker-compose exec rangen-api python scripts/analyze_logs.py
```

## 🛠️ 故障排除

### 常见问题

#### 问题1：容器启动失败

**症状**：容器立即退出或无法启动

**解决方案**：
```bash
# 查看详细错误信息
docker logs rangen-api

# 检查端口冲突
netstat -tlnp | grep :8080

# 检查环境变量
docker inspect rangen-api | grep -A 10 "Env"

# 以交互模式运行查看错误
docker run -it --rm rangen/rangen-v2:latest bash
```

#### 问题2：数据库连接失败

**症状**：API服务无法连接数据库

**解决方案**：
```bash
# 检查数据库服务状态
docker-compose ps postgres

# 检查数据库日志
docker-compose logs postgres

# 手动测试数据库连接
docker-compose exec postgres psql -U rangen -d rangen_dev -c "SELECT 1"

# 重启数据库服务
docker-compose restart postgres
```

#### 问题3：内存不足

**症状**：容器因内存不足被杀死

**解决方案**：
```bash
# 查看容器内存限制
docker inspect rangen-api | grep -i memory

# 增加内存限制
docker update --memory 4G --memory-swap 4G rangen-api

# 或者在docker-compose中配置
# rangen-api:
#   deploy:
#     resources:
#       limits:
#         memory: 4G

# 监控内存使用
docker stats --no-stream rangen-api
```

#### 问题4：网络连接问题

**症状**：容器间无法通信

**解决方案**：
```bash
# 检查网络配置
docker network inspect rangen-network

# 测试容器间连接
docker-compose exec rangen-api ping postgres

# 重新创建网络
docker-compose down
docker network prune
docker-compose up -d
```

### 诊断工具

#### Docker诊断命令

```bash
# 系统级诊断
docker system df  # 查看磁盘使用
docker system info  # 查看系统信息
docker system prune  # 清理未使用的资源

# 容器诊断
docker inspect rangen-api  # 查看容器详细信息
docker diff rangen-api  # 查看容器文件系统变化
docker export rangen-api > container.tar  # 导出容器

# 网络诊断
docker network ls
docker network inspect rangen-network
docker network connect/disconnect
```

#### 应用级诊断

```bash
# 进入容器诊断
docker exec -it rangen-api bash

# 检查应用状态
docker exec rangen-api python scripts/check_system_status.py

# 运行健康检查
docker exec rangen-api curl http://localhost:8080/health

# 检查依赖
docker exec rangen-api pip list

# 查看进程
docker exec rangen-api ps aux
```

### 性能优化

#### 镜像优化

```dockerfile
# 使用多阶段构建减小镜像大小
# 使用.alpine基础镜像
# 清理构建缓存和临时文件
```

#### 容器优化

```yaml
# 配置资源限制
resources:
  limits:
    cpus: '2'
    memory: 4G
  reservations:
    cpus: '1'
    memory: 2G

# 配置重启策略
restart: unless-stopped

# 配置健康检查
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

## 📚 相关资源

### 学习资源

- [Docker官方文档](https://docs.docker.com/)
- [Docker Compose文档](https://docs.docker.com/compose/)
- [RANGEN Dockerfile参考](Dockerfile)
- [RANGEN docker-compose参考](docker-compose.yml)

### 工具和扩展

- **Docker Desktop**：桌面版Docker环境
- **Portainer**：Docker容器管理UI
- **Watchtower**：自动更新容器镜像
- **Traefik**：反向代理和负载均衡器

### 最佳实践

1. **安全实践**：使用非root用户，限制容器权限
2. **监控实践**：配置日志收集和性能监控
3. **备份实践**：定期备份容器数据和配置
4. **更新实践**：定期更新基础镜像和应用

## 🎯 下一步

1. **尝试部署**：使用本指南部署RANGEN系统
2. **定制配置**：根据您的需求修改Docker配置
3. **生产部署**：配置生产环境的高可用部署
4. **监控优化**：设置全面的监控和告警系统

如有问题或建议，请查看[文档中心](../../README.md)或[提交GitHub Issue](https://github.com/your-repo/RANGEN/issues)。

祝您部署顺利！🚀