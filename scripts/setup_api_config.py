#!/usr/bin/env python3
"""
API配置设置脚本
帮助用户正确配置DeepSeek API
"""

import os
import sys
from pathlib import Path

def setup_api_config():
    print('🔧 API配置设置助手')
    print('=' * 60)

    # 检查当前配置
    print('📋 当前环境变量状态:')
    deepseek_vars = {
        'DEEPSEEK_API_KEY': os.getenv('DEEPSEEK_API_KEY', ''),
        'DEEPSEEK_BASE_URL': os.getenv('DEEPSEEK_BASE_URL', ''),
        'DEEPSEEK_MODEL': os.getenv('DEEPSEEK_MODEL', '')
    }

    for key, value in deepseek_vars.items():
        if value:
            masked_value = value[:10] + '...' + value[-4:] if len(value) > 14 else value
            status = '✅ 已设置'
        else:
            masked_value = '未设置'
            status = '❌ 未设置'
        print(f'   {status} {key}: {masked_value}')

    # 检查是否有.env文件
    env_file = Path('.env')
    if env_file.exists():
        print('\\n📄 .env文件状态: ✅ 存在')
        try:
            with open(env_file, 'r') as f:
                content = f.read()
            lines = [line for line in content.split('\\n') if line.strip() and not line.strip().startswith('#')]
            print(f'   包含 {len(lines)} 个配置项')
        except Exception as e:
            print(f'   ❌ 读取失败: {e}')
    else:
        print('\\n📄 .env文件状态: ❌ 不存在')

    print('\\n🚀 配置步骤:')
    print('   1. 获取DeepSeek API密钥')
    print('      • 访问 https://platform.deepseek.com/')
    print('      • 注册账户并创建API密钥')
    print('      • 复制API密钥（格式类似: sk-xxxxxxxxxxxxxxxxxx）')
    print('')
    print('   2. 设置环境变量')
    print('      方法1 - 临时设置（当前会话有效）:')
    print('      export DEEPSEEK_API_KEY="你的API密钥"')
    print('      export DEEPSEEK_BASE_URL="https://api.deepseek.com/v1"')
    print('      export DEEPSEEK_MODEL="deepseek-reasoner"')
    print('')
    print('      方法2 - 永久设置（添加到shell配置文件）:')
    print('      echo \'export DEEPSEEK_API_KEY="你的API密钥"\' >> ~/.bashrc')
    print('      echo \'export DEEPSEEK_BASE_URL="https://api.deepseek.com/v1"\' >> ~/.bashrc')
    print('      echo \'export DEEPSEEK_MODEL="deepseek-reasoner"\' >> ~/.bashrc')
    print('      source ~/.bashrc')
    print('')
    print('      方法3 - 创建.env文件（推荐）:')
    print('      创建 .env 文件并添加以下内容:')
    print('      ```')
    print('      DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxx')
    print('      DEEPSEEK_BASE_URL=https://api.deepseek.com/v1')
    print('      DEEPSEEK_MODEL=deepseek-reasoner')
    print('      ```')
    print('')
    print('   3. 验证配置')
    print('      运行: python3 setup_api_config.py')
    print('      或运行: python3 -c "import os; print(os.getenv(\'DEEPSEEK_API_KEY\', \'未设置\'))"')

    # 测试API连接
    if deepseek_vars['DEEPSEEK_API_KEY']:
        print('\\n🧪 测试API连接:')

        try:
            from src.core.llm_integration import LLMIntegration

            config = {
                'llm_provider': 'deepseek',
                'api_key': deepseek_vars['DEEPSEEK_API_KEY'],
                'base_url': deepseek_vars['DEEPSEEK_BASE_URL'] or 'https://api.deepseek.com/v1',
                'model': deepseek_vars['DEEPSEEK_MODEL'] or 'deepseek-reasoner'
            }

            llm_client = LLMIntegration(config)
            print('   ✅ LLM客户端初始化成功')

            # 简单测试（注意：这会消耗API额度）
            test_prompt = 'Hello'
            print('   📤 发送测试请求...')
            response = llm_client.call_deepseek_api(test_prompt, max_tokens=10)

            if response and 'error' not in str(response).lower():
                print('   ✅ API连接测试成功')
                print(f'      响应: {str(response)[:50]}...')
            else:
                print('   ❌ API连接测试失败')
                print(f'      错误: {response}')

        except Exception as e:
            print(f'   ❌ API测试异常: {e}')
    else:
        print('\\n🧪 API连接测试: ⚠️  请先设置DEEPSEEK_API_KEY环境变量')

    print('\\n💡 常见问题:')
    print('   • API密钥格式错误: 确保以"sk-"开头')
    print('   • 网络连接问题: 检查防火墙和代理设置')
    print('   • API额度不足: 检查DeepSeek账户余额')
    print('   • 模型不存在: 确认模型名称正确(deepseek-reasoner或deepseek-chat)')
    print('=' * 60)

def validate_api_key_format(api_key: str) -> bool:
    """验证API密钥格式"""
    if not api_key:
        return False

    # DeepSeek API密钥通常以sk-开头
    if api_key.startswith('sk-') and len(api_key) > 20:
        return True

    return False

if __name__ == '__main__':
    setup_api_config()
