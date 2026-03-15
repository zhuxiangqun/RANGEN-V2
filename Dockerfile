# RANGEN深度研究智能体系统Dockerfile
# 基于Python 3.11，支持深度学习和异步架构

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Shanghai

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    wget \
    unzip \
    libffi-dev \
    libssl-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖 (分层构建以利用缓存)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装深度学习相关依赖
RUN pip install --no-cache-dir \
    torch>=2.0.0 \
    torchvision \
    torchaudio \
    transformers \
    sentence-transformers \
    faiss-cpu \
    accelerate \
    datasets \
    && pip install --no-cache-dir \
    aiohttp \
    fastapi \
    uvicorn[standard] \
    pydantic \
    python-multipart \
    && pip install --no-cache-dir \
    psutil \
    pyyaml \
    python-dotenv \
    requests \
    && pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-cov \
    black \
    isort \
    flake8

# 创建非root用户
RUN useradd --create-home --shell /bin/bash rangen && \
    chown -R rangen:rangen /app
USER rangen

# 复制应用代码
COPY --chown=rangen:rangen . .

# 创建必要的目录
RUN mkdir -p logs models data config

# 设置卷挂载点
VOLUME ["/app/logs", "/app/models", "/app/data", "/app/config"]

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["python", "-m", "src.main"]
