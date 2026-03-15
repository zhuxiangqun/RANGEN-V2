#!/usr/bin/env python3
"""
检查环境变量和配置文件
"""

import os
import sys
import glob
sys.path.insert(0, os.path.dirname(__file__))

def check_env_config():
    print('🔍 检查环境变量和配置文件')
    print('=' * 60)

    # 检查环境变量
    print('📋 检查环境变量:')
    env_vars = [
        'DEEPSEEK_API_KEY',
        'DEEPSEEK_BASE_URL',
        'DEEPSEEK_MODEL',
        'OPENAI_API_KEY',
        'OPENAI_BASE_URL',
        'OPENAI_MODEL'
    ]

    env_found = []
    for key in env_vars:
        value = os.getenv(key, '')
        if value:
            masked_value = value[:10] + '...' + value[-4:] if len(value) > 14 else value
            print(f'   ✅ {key}: {masked_value} (长度: {len(value)})')
            env_found.append(key)
        else:
            print(f'   ❌ {key}: 未设置')

    print(f'\\n📊 环境变量统计: {len(env_found)}/{len(env_vars)} 已设置')

    # 查找配置文件
    print('\\n🔧 查找配置文件:')
    config_patterns = ['.env', '.env.*', 'env', 'env.*', '*.env', '*.cfg', '*.conf']
    config_files = []

    for pattern in config_patterns:
        files = glob.glob(f'**/{pattern}', recursive=True)
        for file_path in files:
            if os.path.isfile(file_path):
                config_files.append(file_path)

    if config_files:
        print(f'   发现 {len(config_files)} 个配置文件:')
        for file_path in config_files:
            print(f'      📄 {file_path}')
    else:
        print('   ❌ 未发现配置文件')

    # 检查常见的配置文件位置
    common_paths = [
        '.env',
        '.env.local',
        '.env.development',
        '.env.production',
        'config/.env',
        'src/config/.env',
        'settings.env'
    ]

    print('\\n🔍 检查常见配置文件位置:')
    for path in common_paths:
        if os.path.exists(path):
            print(f'   ✅ {path} 存在')
            try:
                with open(path, 'r') as f:
                    content = f.read()
                lines = [line.strip() for line in content.split('\\n') if line.strip() and not line.strip().startswith('#')]
                print(f'      包含 {len(lines)} 个配置项')
            except Exception as e:
                print(f'      ❌ 读取失败: {e}')
        else:
            print(f'   ❌ {path} 不存在')

    # 检查Python代码中的配置
    print('\\n🐍 检查Python代码中的配置:')
    try:
        from src.core.llm_integration import LLMIntegration
        print('   ✅ LLMIntegration模块导入成功')

        # 创建一个测试配置来检查默认行为
        test_config = {
            'llm_provider': 'deepseek',
            'api_key': os.getenv('DEEPSEEK_API_KEY', ''),
            'model': os.getenv('DEEPSEEK_MODEL', 'deepseek-reasoner'),
            'base_url': os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
        }

        llm_client = LLMIntegration(test_config)
        print('   ✅ LLMIntegration实例创建成功')
        print(f'      API密钥: {"设置" if llm_client.api_key else "未设置"}')
        print(f'      模型: {llm_client.model}')
        print(f'      Base URL: {llm_client.base_url}')

    except Exception as e:
        print(f'   ❌ LLMIntegration测试失败: {e}')
        import traceback
        traceback.print_exc()

    print('\\n💡 建议解决方案:')
    print('   1. 创建.env文件并设置正确的API密钥:')
    print('      DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxx')
    print('      DEEPSEEK_BASE_URL=https://api.deepseek.com/v1')
    print('      DEEPSEEK_MODEL=deepseek-reasoner')
    print('')
    print('   2. 确保API密钥有效且未过期')
    print('   3. 检查网络连接是否正常')
    print('   4. 验证DeepSeek API服务是否可用')
    print('=' * 60)

if __name__ == '__main__':
    check_env_config()
