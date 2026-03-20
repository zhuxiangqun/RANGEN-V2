#!/usr/bin/env python3
"""
测试API连接
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

def test_api_connection():
    print('🧪 测试API连接')
    print('=' * 60)

    # 检查环境变量
    api_key = os.getenv('DEEPSEEK_API_KEY', '')
    base_url = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
    model = os.getenv('DEEPSEEK_MODEL', 'deepseek-reasoner')

    print('📋 配置信息:')
    print(f'   API Key: {"设置" if api_key else "未设置"} ({len(api_key)} 字符)')
    print(f'   Base URL: {base_url}')
    print(f'   Model: {model}')

    if not api_key:
        print('\\n❌ DEEPSEEK_API_KEY 未设置，无法测试API连接')
        print('   请运行: python3 setup_api_config.py 获取设置指导')
        return False

    # 测试API连接
    try:
        from src.core.llm_integration import LLMIntegration

        config = {
            'llm_provider': 'deepseek',
            'api_key': api_key,
            'base_url': base_url,
            'model': model
        }

        print('\\n🔄 初始化LLM客户端...')
        llm_client = LLMIntegration(config)

        print('📤 发送测试请求...')
        test_prompt = 'Say "Hello, API test successful!" in exactly those words.'

        # 使用_call_llm方法进行测试（这是LLMIntegration的公共接口）
        # 注意：虽然方法名以下划线开头，但这是LLMIntegration提供的接口
        response = llm_client._call_llm(test_prompt, max_tokens_override=20)  # type: ignore

        if response and isinstance(response, str) and len(response.strip()) > 0:
            print('✅ API连接成功!')
            print(f'   响应: {response.strip()[:100]}...')
            return True
        else:
            print('❌ API连接失败 - 响应为空或无效')
            print(f'   响应: {response}')
            return False

    except Exception as e:
        print(f'❌ API连接异常: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_api_connection()
    print('\\n' + '=' * 60)
    if success:
        print('🎉 API配置正确，新Agent可以正常工作了!')
    else:
        print('💥 API配置有问题，请检查配置或联系技术支持')
    sys.exit(0 if success else 1)
