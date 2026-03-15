#!/usr/bin/env python3
"""测试完整的 LLM → 工具调用 流程"""
import asyncio
import sys
sys.path.insert(0, '/Users/apple/workdata/person/zy/RANGEN-main(syu-python)')

from src.agents.skills.llm_driven_executor import LLMSkillExecutor, PromptStyle


async def test_llm_to_tool():
    """测试 LLM → 工具调用 完整流程"""
    
    executor = LLMSkillExecutor()
    
    print("=" * 60)
    print("测试: LLM → 工具调用 → 结果")
    print("=" * 60)
    
    # 测试用例：让LLM决定是否调用工具
    test_cases = [
        ("计算 25 * 4 + 10", "测试数学计算"),
        ("100加200等于多少", "测试中文数学"),
        ("你好，请介绍一下自己", "测试无需工具"),
    ]
    
    for user_input, desc in test_cases:
        print(f"\n{'='*60}")
        print(f"测试: {desc}")
        print(f"输入: {user_input}")
        print("-" * 60)
        
        result = await executor.execute(user_input, prompt_style=PromptStyle.SIMPLE)
        
        print(f"成功: {result.success}")
        print(f"使用工具: {result.tools_used}")
        print(f"结果: {result.content[:200]}...")
        if result.error:
            print(f"错误: {result.error}")
    
    print(f"\n{'='*60}")
    print("测试完成!")


if __name__ == "__main__":
    asyncio.run(test_llm_to_tool())
