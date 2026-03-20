#!/usr/bin/env python3
"""
快速检查虚拟环境状态 - 直接运行
"""

import sys
import os

print('🔍 快速检查虚拟环境状态')
print('=' * 50)

# 基本检查
in_venv = sys.prefix != sys.base_prefix
venv_path = os.path.join(os.getcwd(), '.venv')

print(f'📍 当前Python路径: {sys.prefix}')
print(f'📍 基础Python路径: {sys.base_prefix}')
print(f'🔧 是否在虚拟环境中: {"✅ 是" if in_venv else "❌ 否"}')

if os.path.exists(venv_path):
    print(f'✅ .venv目录存在')
else:
    print(f'❌ .venv目录不存在')

# 检查环境变量
virtual_env = os.getenv('VIRTUAL_ENV', '')
if virtual_env:
    print(f'✅ VIRTUAL_ENV: {virtual_env}')
else:
    print(f'❌ VIRTUAL_ENV: 未设置')

print('\\n💡 结论:')
if in_venv:
    print('   ✅ 当前在虚拟环境中，可以直接运行测试')
elif os.path.exists(venv_path):
    print('   ⚠️  .venv目录存在但未激活')
    print('   💡 要激活虚拟环境，运行: source .venv/bin/activate')
else:
    print('   ❌ 没有虚拟环境，可以直接运行测试（会自动加载.env）')

print('\\n🚀 下一步:')
print('   💡 无论是否在虚拟环境中，都可以运行迁移测试')
print('   💡 测试会自动加载.env文件中的API配置')

print('=' * 50)
