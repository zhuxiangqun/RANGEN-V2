#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试配置服务 ConfigService"""

import sys
sys.path.insert(0, '.')

print('=== 测试配置服务 (ConfigService) ===')

try:
    from src.services.config_service import ConfigService
    
    # 获取单例实例
    config = ConfigService()
    
    # 测试读取配置
    print('1. 测试获取配置值...')
    llm_provider = config.get('LLM_PROVIDER', 'mock')
    print(f'   LLM_PROVIDER: {llm_provider}')
    
    # 测试默认值
    print('2. 测试默认值...')
    test_val = config.get('NON_EXISTENT_KEY', 'default_value')
    print(f'   NON_EXISTENT_KEY (default): {test_val}')
    
    # 测试获取多个配置
    print('3. 测试获取多个配置...')
    llm_api_key = config.get('LLM_API_KEY', 'not_set')
    model_name = config.get('MODEL_NAME', 'default')
    max_tokens = config.get('MAX_TOKENS', 0)
    print(f'   LLM_API_KEY: {"已设置" if llm_api_key != "not_set" and llm_api_key else "未设置"}')
    print(f'   MODEL_NAME: {model_name}')
    print(f'   MAX_TOKENS: {max_tokens}')
    
    print()
    print('=== ConfigService 测试通过 ✓ ===')
    sys.exit(0)
    
except Exception as e:
    print(f'✗ 测试失败: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
