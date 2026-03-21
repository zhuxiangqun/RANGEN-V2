#!/usr/bin/env python3
"""
生产环境部署指南
详细说明如何部署优化后的系统到生产环境
"""

import asyncio
import logging
import os
import json
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductionDeploymentGuide:
    """生产环境部署指南"""
    
    def __init__(self):
        self.deployment_steps = self._initialize_deployment_steps()
        self.environment_checklist = self._initialize_environment_checklist()
        self.deployment_commands = self._initialize_deployment_commands()
    
    def _initialize_deployment_steps(self):
        """初始化部署步骤"""
        return [
            {
                "step": 1,
                "title": "环境准备",
                "description": "准备生产环境的基础设施和配置",
                "tasks": [
                    "检查服务器资源",
                    "配置网络环境",
                    "准备数据库",
                    "配置监控系统"
                ]
            },
            {
                "step": 2,
                "title": "代码准备",
                "description": "准备部署的代码和配置文件",
                "tasks": [
                    "代码审查和测试",
                    "配置文件准备",
                    "环境变量配置",
                    "依赖包准备"
                ]
            },
            {
                "step": 3,
                "title": "部署执行",
                "description": "执行实际的部署操作",
                "tasks": [
                    "备份当前版本",
                    "部署新版本",
                    "执行健康检查",
                    "验证功能正常"
                ]
            },
            {
                "step": 4,
                "title": "监控验证",
                "description": "部署后的监控和验证",
                "tasks": [
                    "性能监控",
                    "错误监控",
                    "用户反馈收集",
                    "系统稳定性验证"
                ]
            }
        ]
    
    def _initialize_environment_checklist(self):
        """初始化环境检查清单"""
        return {
            "服务器资源": {
                "CPU": "至少8核心",
                "内存": "至少16GB",
                "磁盘": "至少100GB可用空间",
                "网络": "稳定的网络连接"
            },
            "软件环境": {
                "操作系统": "Linux (Ubuntu 20.04+ / CentOS 8+)",
                "Python": "Python 3.8+",
                "数据库": "PostgreSQL 12+ / MySQL 8+",
                "缓存": "Redis 6+",
                "消息队列": "RabbitMQ 3.8+ / Apache Kafka"
            },
            "安全配置": {
                "防火墙": "配置必要的端口开放",
                "SSL证书": "配置HTTPS",
                "用户权限": "最小权限原则",
                "日志审计": "启用安全日志"
            }
        }
    
    def _initialize_deployment_commands(self):
        """初始化部署命令"""
        return {
            "环境检查": [
                "python -c \"import sys; print(f'Python版本: {sys.version}')\"",
                "free -h",
                "df -h",
                "nproc",
                "curl -I http://localhost:8080/health"
            ],
            "代码部署": [
                "git clone <repository_url>",
                "cd rangen-system",
                "pip install -r requirements.txt",
                "python setup.py install"
            ],
            "服务启动": [
                "sudo systemctl start rangen-api",
                "sudo systemctl start rangen-worker",
                "sudo systemctl start rangen-monitor"
            ],
            "健康检查": [
                "curl http://localhost:8080/health",
                "curl http://localhost:8080/api/status",
                "curl http://localhost:8080/health/db"
            ]
        }
    
    def show_deployment_guide(self):
        """显示部署指南"""
        print("🚀 生产环境部署指南")
        print("=" * 80)
        
        # 显示部署步骤
        print("\n📋 部署步骤:")
        for step in self.deployment_steps:
            print(f"\n{step['step']}. {step['title']}")
            print(f"   描述: {step['description']}")
            print("   任务:")
            for task in step['tasks']:
                print(f"     • {task}")
        
        # 显示环境检查清单
        print("\n🔍 环境检查清单:")
        for category, items in self.environment_checklist.items():
            print(f"\n  {category}:")
            for item, requirement in items.items():
                print(f"    • {item}: {requirement}")
        
        # 显示部署命令
        print("\n⚙️ 部署命令:")
        for category, commands in self.deployment_commands.items():
            print(f"\n  {category}:")
            for command in commands:
                print(f"    $ {command}")
    
    def create_deployment_script(self, output_path: str = "deploy_to_production.sh"):
        """创建部署脚本"""
        script_content = """#!/bin/bash
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
sleep get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit"))
echo "检查服务状态..."
curl -f http://localhost:8080/health || exit 1
curl -f http://localhost:8080/api/status || exit 1

echo "✅ 部署完成！"
echo "🌐 服务地址: http://localhost:8080"
echo "📊 监控地址: http://localhost:8080/monitor"
"""
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            # 设置执行权限
            os.chmod(output_path, 0o755)
            
            logger.info(f"部署脚本已创建: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"创建部署脚本失败: {e}")
            return False
    
    def create_docker_compose(self, output_path: str = "docker-compose.production.yml"):
        """创建Docker Compose配置"""
        docker_compose_content = """version: '3.8'

services:
  rangen-api:
    image: rangen-system:latest
    container_name: rangen-api
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis
    networks:
      - rangen-network

  rangen-worker:
    image: rangen-system:latest
    container_name: rangen-worker
    restart: unless-stopped
    command: ["python", "-m", "src.worker"]
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis
    networks:
      - rangen-network

  postgres:
    image: postgres:13
    container_name: rangen-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_DB=rangen_production
      - POSTGRES_USER=rangen_user
      - POSTGRES_PASSWORD=YOUR_DB_PASSWORD
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - rangen-network

  redis:
    image: redis:6-alpine
    container_name: rangen-redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - rangen-network

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
      - rangen-api
    networks:
      - rangen-network

volumes:
  postgres_data:
  redis_data:

networks:
  rangen-network:
    driver: bridge
"""
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(docker_compose_content)
            
            logger.info(f"Docker Compose配置已创建: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"创建Docker Compose配置失败: {e}")
            return False
    
    def create_nginx_config(self, output_path: str = "nginx.conf"):
        """创建Nginx配置"""
        nginx_config = """events {
    worker_connections 1024;
}

http {
    upstream rangen_api {
        server rangen-api:8080;
    }

    server {
        listen 80;
        server_name your-domain.com;
        
        # 重定向到HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # 安全头
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options DENY always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-XSS-Protection "1; mode=block" always;

        location / {
            proxy_pass http://rangen_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # 超时设置
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # 健康检查
        location /health {
            proxy_pass http://rangen_api/health;
            access_log off;
        }

        # 静态文件
        location /static/ {
            alias /app/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
"""
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(nginx_config)
            
            logger.info(f"Nginx配置已创建: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"创建Nginx配置失败: {e}")
            return False
    
    def create_systemd_service(self, output_path: str = "rangen-api.service"):
        """创建systemd服务配置"""
        service_content = """[Unit]
Description=RANGEN API Service
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=simple
User=rangen
Group=rangen
WorkingDirectory=/opt/rangen/production
Environment=PYTHONPATH=/opt/rangen/production
Environment=ENVIRONMENT=production
ExecStart=/usr/bin/python3 -m src.main --config config/production_config.json
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit"))

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/opt/rangen/production/logs /opt/rangen/production/data

[Install]
WantedBy=multi-user.target
"""
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(service_content)
            
            logger.info(f"systemd服务配置已创建: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"创建systemd服务配置失败: {e}")
            return False
    
    def create_monitoring_config(self, output_path: str = "monitoring_config.json"):
        """创建监控配置"""
        monitoring_config = {
            "monitoring": {
                "enabled": True,
                "interval": 30,
                "endpoints": [
                    {
                        "name": "API健康检查",
                        "url": "http://localhost:8080/health",
                        "method": "GET",
                        "timeout": get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")),
                        "expected_status": 200
                    },
                    {
                        "name": "数据库连接",
                        "url": "http://localhost:8080/health/db",
                        "method": "GET",
                        "timeout": get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")),
                        "expected_status": 200
                    }
                ],
                "alerts": {
                    "email": {
                        "enabled": True,
                        "smtp_server": "smtp.gmail.com",
                        "smtp_port": 587,
                        "username": "your-email@gmail.com",
                        "password": "your-app-password",
                        "to_emails": ["admin@yourcompany.com"]
                    },
                    "slack": {
                        "enabled": True,
                        "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
                        "channel": "#alerts"
                    }
                }
            },
            "logging": {
                "level": "INFO",
                "file": "/opt/rangen/production/logs/app.log",
                "max_size": "100MB",
                "backup_count": 5
            },
            "performance": {
                "auto_tuning": True,
                "tuning_interval": 300,
                "thresholds": {
                    "response_time_warning": get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")),
                    "response_time_critical": 3.0,
                    "error_rate_warning": 0.05,
                    "error_rate_critical": 0.1
                }
            }
        }
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(monitoring_config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"监控配置已创建: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"创建监控配置失败: {e}")
            return False

async def main():
    """主函数"""
    guide = ProductionDeploymentGuide()
    
    print("🚀 生产环境部署指南")
    print("=" * 80)
    
    # 显示部署指南
    guide.show_deployment_guide()
    
    # 创建部署文件
    print("\n📁 创建部署文件...")
    
    files_created = []
    
    if guide.create_deployment_script("deploy_to_production.sh"):
        files_created.append("deploy_to_production.sh")
    
    if guide.create_docker_compose("docker-compose.production.yml"):
        files_created.append("docker-compose.production.yml")
    
    if guide.create_nginx_config("nginx.conf"):
        files_created.append("nginx.conf")
    
    if guide.create_systemd_service("rangen-api.service"):
        files_created.append("rangen-api.service")
    
    if guide.create_monitoring_config("monitoring_config.json"):
        files_created.append("monitoring_config.json")
    
    print(f"\n✅ 已创建 {len(files_created)} 个部署文件:")
    for file in files_created:
        print(f"  📄 {file}")
    
    print("\n💡 部署说明:")
    print("1. 修改配置文件中的敏感信息（密码、域名等）")
    print("2. 根据实际环境调整配置参数")
    print("3. 先在测试环境验证部署流程")
    print("4. 准备回滚方案和监控告警")
    print("5. 选择合适的时间窗口进行部署")
    
    print("\n🚀 开始部署:")
    print("  # 使用脚本部署")
    print("  ./deploy_to_production.sh")
    print("  ")
    print("  # 或使用Docker Compose")
    print("  docker-compose -f docker-compose.production.yml up -d")

if __name__ == "__main__":
    asyncio.run(main())
