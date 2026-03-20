#!/bin/bash
# RANGEN V2 快速启动脚本（极简版）

# 激活虚拟环境
source venv/bin/activate

# 启动统一服务器
python scripts/start_unified_server.py --port 8080
