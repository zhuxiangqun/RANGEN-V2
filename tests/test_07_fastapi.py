#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 FastAPI 接口"""

import sys
sys.path.insert(0, '.')

print('=== 测试 FastAPI 接口 ===')

try:
    # 测试导入 FastAPI 核心模块
    print('1. 测试导入 FastAPI 核心模块...')
    from fastapi import FastAPI, APIRouter, HTTPException
    from fastapi.testclient import TestClient
    print('   ✓ FastAPI 核心模块导入成功')
    
    # 测试导入 Gateway
    print('2. 测试导入 Gateway...')
    from src.gateway.gateway import Gateway
    print('   ✓ Gateway 导入成功')
    
    # 测试创建 FastAPI 实例
    print('3. 测试创建 FastAPI 实例...')
    test_app = FastAPI(title="RANGEN Test API")
    print(f'   ✓ FastAPI 实例创建成功: {test_app.title}')
    
    # 测试 APIRouter
    print('4. 测试 APIRouter...')
    router = APIRouter()
    print(f'   ✓ APIRouter 创建成功')
    
    print()
    print('=== FastAPI 接口 测试通过 ✓ ===')
    sys.exit(0)
    
except Exception as e:
    print(f'✗ 测试失败: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
