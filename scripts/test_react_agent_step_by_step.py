#!/usr/bin/env python3
"""
逐步测试ReAct Agent初始化过程
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_step_by_step():
    """逐步测试ReAct Agent初始化"""
    print("🔍 逐步测试ReAct Agent初始化")
    print("=" * 60)

    step = 1

    try:
        print(f"{step}️⃣ 导入ReasoningExpert...")
        from src.agents.reasoning_expert import ReasoningExpert
        print("   ✅ 导入成功")
        step += 1

        print(f"\n{step}️⃣ 实例化ReasoningExpert...")
        react_agent = ReasoningExpert()
        print("   ✅ 实例化成功")
        print(f"   📊 类型: {type(react_agent).__name__}")
        step += 1

        print(f"\n{step}️⃣ 测试register_tool方法...")
        result = react_agent.register_tool("test_tool", {"category": "test"})
        print(f"   ✅ register_tool返回: {result}")
        step += 1

        print(f"\n{step}️⃣ 导入工具类...")
        from src.agents.tools.tool_registry import get_tool_registry
        from src.agents.tools.search_tool import SearchTool
        from src.agents.tools.calculator_tool import CalculatorTool
        from src.agents.tools.knowledge_retrieval_tool import KnowledgeRetrievalTool
        from src.agents.tools.answer_generation_tool import AnswerGenerationTool
        from src.agents.tools.citation_tool import CitationTool
        print("   ✅ 所有工具类导入成功")
        step += 1

        print(f"\n{step}️⃣ 获取工具注册表...")
        tool_registry = get_tool_registry()
        print("   ✅ 工具注册表获取成功")
        step += 1

        print(f"\n{step}️⃣ 测试工具实例化...")
        tools_to_test = [
            ("KnowledgeRetrievalTool", KnowledgeRetrievalTool),
            ("AnswerGenerationTool", AnswerGenerationTool),
            ("CitationTool", CitationTool),
            ("SearchTool", SearchTool),
            ("CalculatorTool", CalculatorTool),
        ]

        for tool_name, tool_class in tools_to_test:
            try:
                tool_instance = tool_class()
                print(f"   ✅ {tool_name} 实例化成功")
            except Exception as e:
                print(f"   ❌ {tool_name} 实例化失败: {e}")
                raise
        step += 1

        print(f"\n{step}️⃣ 测试工具注册...")
        # 测试注册一个工具
        test_tool = KnowledgeRetrievalTool()
        result = react_agent.register_tool(test_tool, {"category": "core"})
        print(f"   ✅ 工具注册测试成功，返回: {result}")
        step += 1

        print("\n" + "=" * 60)
        print("🎉 所有步骤测试通过！")
        print("💡 这意味着ReAct Agent初始化过程本身是正确的")
        print("💡 问题可能在于UnifiedResearchSystem的其他部分")

        return True

    except Exception as e:
        print(f"❌ 步骤{step}失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_step_by_step()
    if not success:
        print("\n🔧 需要修复上述步骤中的问题")
    else:
        print("\n🎯 初始化过程本身正确，问题在别处")
