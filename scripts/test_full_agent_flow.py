#!/usr/bin/env python3
"""测试完整流程: 输入→Agent→Skill→Tool"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.agent_selector import select_agent
from src.agents.skills.ai_skill_trigger import ai_auto_trigger_skills


async def test_full_flow():
    """测试完整流程"""
    print("=" * 60)
    print("测试: 完整流程 - 输入→Agent→Skill→Tool")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        "帮我计算100加200",
        "帮我写一首关于春天的诗",
        "搜索最新的AI新闻",
    ]
    
    for test_input in test_cases:
        print(f"\n{'='*60}")
        print(f"用户输入: {test_input}")
        print("="*60)
        
        # Step 1: Agent Selection
        print("\n[步骤1] Agent选择")
        agent_result = await select_agent(test_input)
        print(f"  选择的Agent: {agent_result.get('selected_agent')}")
        print(f"  Skills: {agent_result.get('skills', [])}")
        print(f"  原因: {agent_result.get('reasoning')}")
        
        # Step 2: Skill Triggering
        print("\n[步骤2] Skill触发")
        skills = await ai_auto_trigger_skills(test_input)
        print(f"  触发的Skills: {skills}")
        
        print("\n" + "="*60)
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_full_flow())
