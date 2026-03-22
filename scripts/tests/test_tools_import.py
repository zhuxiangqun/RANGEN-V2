#!/usr/bin/env python3
"""
测试工具导入和实例化
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_tool_imports():
    """测试工具导入"""
    print("🔍 测试工具导入和实例化")
    print("=" * 50)

    tools_to_test = [
        ("SearchTool", "src.agents.tools.search_tool", "SearchTool"),
        ("CalculatorTool", "src.agents.tools.calculator_tool", "CalculatorTool"),
        ("KnowledgeRetrievalTool", "src.agents.tools.knowledge_retrieval_tool", "KnowledgeRetrievalTool"),
        ("AnswerGenerationTool", "src.agents.tools.answer_generation_tool", "AnswerGenerationTool"),
        ("CitationTool", "src.agents.tools.citation_tool", "CitationTool"),
    ]

    failed_tools = []

    for tool_name, module_path, class_name in tools_to_test:
        try:
            print(f"\n🔧 测试 {tool_name}...")
            module = __import__(module_path, fromlist=[class_name])
            tool_class = getattr(module, class_name)

            # 尝试实例化
            tool_instance = tool_class()
            print(f"   ✅ {tool_name} 导入和实例化成功")

        except ImportError as e:
            print(f"   ❌ {tool_name} 导入失败: {e}")
            failed_tools.append((tool_name, f"Import error: {e}"))
        except Exception as e:
            print(f"   ❌ {tool_name} 实例化失败: {e}")
            failed_tools.append((tool_name, f"Instantiation error: {e}"))

    print("\n" + "=" * 50)
    if failed_tools:
        print("❌ 发现问题工具:")
        for tool_name, error in failed_tools:
            print(f"   • {tool_name}: {error}")
        print("\n💡 这可能是导致ReAct Agent初始化失败的原因")
        return False
    else:
        print("✅ 所有工具导入和实例化成功")
        return True

if __name__ == "__main__":
    success = test_tool_imports()
    if not success:
        print("\n🔧 建议修复失败的工具类")
    else:
        print("\n🎉 工具测试通过，问题可能在其他地方")
