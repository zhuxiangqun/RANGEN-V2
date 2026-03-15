#!/usr/bin/env python3
"""验证Skill系统核心组件"""

import sys
import os

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 60)
print("验证Skill系统核心组件")
print("=" * 60)

# 测试1: 导入LLMSkillExecutor
print("\n[1] 导入 LLMSkillExecutor...")
try:
    from src.agents.skills.llm_driven_executor import LLMSkillExecutor
    print("    ✅ LLMSkillExecutor 导入成功")
except Exception as e:
    print(f"    ❌ 导入失败: {e}")

# 测试2: 导入AI Skill Trigger
print("\n[2] 导入 AI Skill Trigger...")
try:
    from src.agents.skills.ai_skill_trigger import AISkillTrigger, ai_auto_trigger_skills
    print("    ✅ AI Skill Trigger 导入成功")
except Exception as e:
    print(f"    ❌ 导入失败: {e}")

# 测试3: 导入HybridToolExecutor
print("\n[3] 导入 HybridToolExecutor...")
try:
    from src.agents.skills.hybrid_tool_executor import HybridToolExecutor
    print("    ✅ HybridToolExecutor 导入成功")
except Exception as e:
    print(f"    ❌ 导入失败: {e}")

# 测试4: 导入InProcessMCPExecutor
print("\n[4] 导入 InProcessMCPExecutor...")
try:
    from src.agents.tools.in_process_mcp import InProcessMCPExecutor
    print("    ✅ InProcessMCPExecutor 导入成功")
except Exception as e:
    print(f"    ❌ 导入失败: {e}")

# 测试5: 测试skill加载
print("\n[5] 测试 Skill 加载...")
try:
    from src.agents.skills.ai_skill_trigger import AISkillTrigger
    trigger = AISkillTrigger()
    skills = trigger._load_skills_from_files()
    print(f"    ✅ 加载了 {len(skills)} 个skills")
    for s in skills[:3]:
        print(f"       - {s.name}")
except Exception as e:
    print(f"    ❌ 加载失败: {e}")

print("\n" + "=" * 60)
print("验证完成!")
print("=" * 60)
