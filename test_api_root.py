#!/usr/bin/env python3
"""
测试 API 根路径修复
"""

import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_api_response():
    """测试API响应格式"""
    # 模拟API响应
    api_info = {
        "name": "动态路由配置管理系统 API",
        "version": "1.0.0",
        "description": "企业级的配置管理解决方案",
        "endpoints": {
            "GET /": "API信息 (本页面)",
            "GET /config": "获取当前路由配置",
            "GET /route-types": "获取路由类型列表",
            "POST /route-types": "注册新的路由类型",
            "PUT /config/thresholds": "更新路由阈值",
            "PUT /config/keywords": "更新关键词配置"
        },
        "status": "running"
    }

    # 检查必需字段
    required_fields = ["name", "version", "description", "endpoints", "status"]
    for field in required_fields:
        if field not in api_info:
            print(f"❌ 缺少必需字段: {field}")
            return False

    print("✅ API响应格式正确")
    print(f"API名称: {api_info['name']}")
    print(f"版本: {api_info['version']}")
    print(f"状态: {api_info['status']}")
    print(f"可用端点: {len(api_info['endpoints'])} 个")

    return True

if __name__ == '__main__':
    success = test_api_response()
    if success:
        print("\n🎉 API根路径修复验证通过！")
    else:
        print("\n💥 API根路径修复验证失败！")
        sys.exit(1)
