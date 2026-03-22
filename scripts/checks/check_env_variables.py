#!/usr/bin/env python3
"""
检查环境变量设置
"""

import os
import sys
from pathlib import Path

print("🔍 环境变量检查")
print("=" * 30)

# 检查关键环境变量
env_vars = [
    'USE_LIGHTWEIGHT_RAG',
    'USE_NEW_AGENTS',
    'DEEPSEEK_API_KEY',
    'DEEPSEEK_BASE_URL'
]

for var in env_vars:
    value = os.environ.get(var, 'not_set')
    if var == 'DEEPSEEK_API_KEY' and value != 'not_set':
        # 隐藏API密钥，只显示长度
        value = f"已设置 (长度: {len(value)})"
    print(f"   {var} = {value}")

print("\n📋 诊断建议:")
lightweight = os.environ.get('USE_LIGHTWEIGHT_RAG')
if lightweight == 'true':
    print("❌ USE_LIGHTWEIGHT_RAG设置为true，将使用轻量级模式")
    print("   解决方法：")
    print("   1. 运行: unset USE_LIGHTWEIGHT_RAG")
    print("   2. 或在脚本开头删除此环境变量")
    print("   3. 重启Python进程")
elif lightweight is None:
    print("✅ USE_LIGHTWEIGHT_RAG未设置，将使用完整模式")
else:
    print(f"⚠️  USE_LIGHTWEIGHT_RAG设置为: {lightweight}")

print("\n🚀 测试命令:")
print("   python3 test_full_rag_functionality.py  # 测试完整RAG功能")
print("   USE_LIGHTWEIGHT_RAG=true python3 test_lightweight_rag.py  # 测试轻量级模式")
