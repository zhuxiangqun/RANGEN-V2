#!/usr/bin/env python3
"""快速性能测试 - 检查优化效果"""

import os
import time
import asyncio
import sys
from pathlib import Path

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# 设置严格模式
os.environ['STRICT_ANSWER_VALIDATION'] = 'true'

async def quick_test():
    """快速测试优化效果"""
    print("🚀 快速性能测试 - 优化后效果检查")
    print("=" * 60)
    
    # 记录开始时间
    start_time = time.time()
    
    try:
        # 导入必要的模块
        from src.core.llm_integration import LLMIntegration
        
        print("✅ 模块导入成功")
        
        # 创建LLM集成实例
        config = {
            'model': 'deepseek-reasoner',
            'llm_provider': 'deepseek'
        }
        
        llm = LLMIntegration(config)
        print(f"✅ LLM集成创建成功")
        print(f"   - 模型: {llm.model}")
        print(f"   - 去重窗口: {llm._dedup_window}秒")
        
        # 测试max_tokens计算
        max_tokens_reasoner = llm._get_max_tokens('deepseek-reasoner', 'complex')
        max_tokens_chat = llm._get_max_tokens('deepseek-chat', 'complex')
        print(f"✅ max_tokens计算测试:")
        print(f"   - 推理模型复杂问题: {max_tokens_reasoner}")
        print(f"   - 聊天模型复杂问题: {max_tokens_chat}")
        
        # 测试去重逻辑
        test_prompt = "测试优化效果"
        test_hash = llm._generate_request_hash('deepseek-reasoner', test_prompt)
        print(f"✅ 去重逻辑测试:")
        print(f"   - 请求哈希: {test_hash[:20]}...")
        
        # 模拟缓存
        llm._request_dedup_cache[test_hash] = {
            'response': '测试缓存响应',
            'timestamp': time.time() - 30  # 30秒前
        }
        
        # 检查是否在去重窗口内
        is_cached = llm._is_request_cached(test_hash)
        print(f"   - 30秒前缓存是否有效: {is_cached}")
        
        execution_time = time.time() - start_time
        print(f"\n⏱️ 测试执行时间: {execution_time:.2f}秒")
        print(f"✅ 优化配置检查完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(quick_test())
    sys.exit(0 if success else 1)