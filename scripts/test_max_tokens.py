#!/usr/bin/env python3
"""测试max_tokens配置是否生效"""

import os
import sys
from pathlib import Path

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from src.core.llm_integration import LLMIntegration

def test_max_tokens():
    """测试max_tokens配置"""
    print("测试max_tokens配置...")
    
    # 创建LLMIntegration实例
    config = {
        'model': 'deepseek-reasoner',
        'llm_provider': 'deepseek'
    }
    llm = LLMIntegration(config)
    
    # 测试_get_max_tokens方法
    print(f"1. 推理模型 (deepseek-reasoner) 基础tokens: {llm._get_max_tokens('deepseek-reasoner', None)}")
    print(f"2. 推理模型 (deepseek-reasoner) 复杂问题: {llm._get_max_tokens('deepseek-reasoner', 'complex')}")
    print(f"3. 推理模型 (deepseek-reasoner) 简单问题: {llm._get_max_tokens('deepseek-reasoner', 'simple')}")
    
    print(f"\n4. 聊天模型 (deepseek-chat) 基础tokens: {llm._get_max_tokens('deepseek-chat', None)}")
    print(f"5. 聊天模型 (deepseek-chat) 复杂问题: {llm._get_max_tokens('deepseek-chat', 'complex')}")
    print(f"6. 聊天模型 (deepseek-chat) 简单问题: {llm._get_max_tokens('deepseek-chat', 'simple')}")
    
    # 检查去重窗口配置
    print(f"\n7. 去重窗口配置: {llm._dedup_window} 秒")
    print(f"8. 去重是否启用: {llm._dedup_enabled}")
    
    # 检查环境变量
    print(f"\n9. 环境变量 DEDUPLICATION_WINDOW: {os.getenv('DEDUPLICATION_WINDOW', '未设置')}")
    print(f"10. 环境变量 MAX_TOKENS: {os.getenv('MAX_TOKENS', '未设置')}")
    
    print("\n✅ 配置测试完成")

if __name__ == '__main__':
    test_max_tokens()