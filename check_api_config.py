#!/usr/bin/env python3
"""
检查API配置状态
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

def check_api_config():
    print('🔍 检查API配置状态')
    print('=' * 60)

    # 检查环境变量
    print('📋 检查环境变量:')
    api_keys = ['DEEPSEEK_API_KEY', 'DEEPSEEK_BASE_URL', 'DEEPSEEK_MODEL']
    for key in api_keys:
        value = os.getenv(key, '')
        if value:
            masked_value = value[:10] + '...' + value[-4:] if len(value) > 14 else value
            print(f'   ✅ {key}: {masked_value} (长度: {len(value)})')
        else:
            print(f'   ❌ {key}: 未设置')

    print('\n🔧 检查配置文件:')
    config_file = '.env'
    if os.path.exists(config_file):
        print('   ✅ .env文件存在')

        # 读取并检查关键配置
        try:
            with open(config_file, 'r') as f:
                content = f.read()

            deepseek_lines = [line for line in content.split('\n') if 'DEEPSEEK' in line.upper() and not line.strip().startswith('#')]
            print(f'   📄 发现 {len(deepseek_lines)} 个DeepSeek相关配置')

            for line in deepseek_lines:
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if value:
                        masked_value = value[:10] + '...' + value[-4:] if len(value) > 14 else value
                        print(f'      • {key}: {masked_value}')
                    else:
                        print(f'      • {key}: 空值')
        except Exception as e:
            print(f'   ❌ 读取.env文件失败: {e}')
    else:
        print('   ❌ .env文件不存在')

    print('\n🧪 测试API连接:')
    try:
        from src.core.llm_integration import LLMIntegration

        print('   🔄 初始化LLM客户端...')
        llm_client = LLMIntegration()

        print('   📤 测试简单API调用...')
        # 测试一个简单的API调用
        test_prompt = 'Say hello'

        response = llm_client.call_deepseek_api(test_prompt, max_tokens=10)

        if response and 'error' not in response:
            print('   ✅ API连接成功')
            print(f'      响应: {response[:50]}...')
        else:
            error_msg = response.get('error', '未知错误') if isinstance(response, dict) else str(response)
            print(f'   ❌ API连接失败: {error_msg[:100]}...')

    except Exception as e:
        print(f'   ❌ API测试异常: {e}')

    print('\n💡 配置建议:')
    print('   1. 确保DEEPSEEK_API_KEY正确设置')
    print('   2. 检查网络连接是否正常')
    print('   3. 验证API密钥是否有效且未过期')
    print('   4. 确认DEEPSEEK_BASE_URL正确')
    print('=' * 60)

if __name__ == '__main__':
    check_api_config()
