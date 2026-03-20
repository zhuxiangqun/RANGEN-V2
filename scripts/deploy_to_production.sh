#!/bin/bash
# 生产环境部署脚本
# 使用方法: ./deploy_to_production.sh

set -e  # 遇到错误立即退出

echo "🚀 开始生产环境部署..."

# 1. 环境检查
echo "📋 步骤1: 环境检查"
echo "检查Python版本..."
python3 --version

echo "检查系统资源..."
free -h
df -h
nproc

echo "检查网络连接..."
ping -c 3 google.com

# 2. 代码准备
echo "📋 步骤2: 代码准备"
echo "克隆代码仓库..."
git clone <YOUR_REPOSITORY_URL> rangen-system
cd rangen-system

echo "安装依赖..."
pip3 install -r requirements.txt

# 3. 配置环境
echo "📋 步骤3: 配置环境"
echo "创建配置文件..."
cat > config/production_config.json << EOF
{
    "environment": "production",
    "debug": false,
    "log_level": "INFO",
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "rangen_production",
        "user": "rangen_user",
        "password": "YOUR_DB_PASSWORD"
    },
    "redis": {
        "host": "localhost",
        "port": 6379,
        "db": 0
    },
    "api": {
        "host": "0.0.0.0",
        "port": 8080,
        "workers": 4
    }
}
EOF

# 4. 部署执行
echo "📋 步骤4: 部署执行"
echo "启动服务..."
python3 -m src.main --config config/production_config.json &

# 5. 健康检查
echo "📋 步骤5: 健康检查"
sleep 10
echo "检查服务状态..."
curl -f http://localhost:8080/health || exit 1
curl -f http://localhost:8080/api/status || exit 1

echo "✅ 部署完成！"
echo "🌐 服务地址: http://localhost:8080"
echo "📊 监控地址: http://localhost:8080/monitor"
