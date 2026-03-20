#!/usr/bin/env python3
"""
快速状态检查脚本
"""

import os
import sys
from pathlib import Path

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(".env"))
    print('✅ .env 文件加载成功')
except Exception as e:
    print(f'加载 .env 文件失败: {e}')

sys.path.insert(0, os.path.dirname(__file__))

def quick_status_check():
    print('🔍 快速状态检查')
    print('=' * 50)

    # 检查环境变量
    print('📋 环境变量:')
    env_vars = ['DEEPSEEK_API_KEY', 'DEEPSEEK_BASE_URL', 'DEEPSEEK_MODEL']
    api_configured = False

    for var in env_vars:
        value = os.getenv(var, '')
        if value:
            masked = value[:10] + '...' + value[-4:] if len(value) > 14 else value
            print(f'   ✅ {var}: {masked}')
            if var == 'DEEPSEEK_API_KEY' and len(value) > 10:
                api_configured = True
        else:
            print(f'   ❌ {var}: 未设置')

    # 检查模块导入
    print('\\n🔧 模块状态:')
    try:
        from src.core.llm_integration import LLMIntegration
        print('   ✅ LLMIntegration模块导入成功')
    except Exception as e:
        print(f'   ❌ LLMIntegration模块导入失败: {e}')
        return False

    try:
        from src.agents.react_agent import ReActAgent
        print('   ✅ ReActAgent模块导入成功')
    except Exception as e:
        print(f'   ❌ ReActAgent模块导入失败: {e}')

    # 检查迁移状态
    print('\\n🚀 迁移状态:')
    try:
        from scripts.start_gradual_replacement import AGENT_MAPPING
        print('   ✅ 迁移配置加载成功')
        print(f'   📊 可迁移Agent数量: {len(AGENT_MAPPING)}')

        for agent_name, config in AGENT_MAPPING.items():
            print(f'      • {agent_name} → {config["target_agent"]}')

    except Exception as e:
        print(f'   ❌ 迁移配置加载失败: {e}')

    print('\\n📋 推荐下一步:')
    if api_configured:
        print('   ✅ API配置已设置，可以开始Agent迁移测试')
        print('   💡 运行: python3 temp_migration_test.py')
    else:
        print('   ⚠️ API配置未完成，请先配置环境变量')
        print('   💡 运行: python3 setup_api_config.py')
        print('   💡 或手动设置: export DEEPSEEK_API_KEY=\"你的API密钥\"')

    print('=' * 50)

if __name__ == '__main__':
    quick_status_check()
