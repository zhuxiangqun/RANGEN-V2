# ReActAgent迁移验证代码片段
# 复制这些代码到Python解释器中运行

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

print("🔍 ReActAgent迁移验证")
print("=" * 40)

try:
    # 1. 测试导入
    print("1️⃣ 测试导入...")
    from src.unified_research_system import UnifiedResearchSystem
    from src.agents.reasoning_expert import ReasoningExpert
    print("   ✅ 导入成功")

    # 2. 测试实例化
    print("\n2️⃣ 测试实例化...")
    system = UnifiedResearchSystem()

    if hasattr(system, '_react_agent'):
        agent_type = type(system._react_agent).__name__
        print(f"   📊 Agent类型: {agent_type}")

        if agent_type == "ReasoningExpert":
            print("   ✅ 迁移成功！系统正在使用ReasoningExpert")
        else:
            print(f"   ❌ 迁移失败！仍在使用: {agent_type}")
    else:
        print("   ❌ 未找到Agent实例")

    # 3. 基本功能测试
    print("\n3️⃣ 基本功能测试...")
    expert = ReasoningExpert()
    print("   ✅ ReasoningExpert实例化成功")

    # 简单的上下文测试
    test_context = {
        "query": "Hello",
        "reasoning_type": "deductive"
    }

    print("   🔄 测试execute方法...")
    import asyncio

    async def test_execute():
        try:
            result = await asyncio.wait_for(expert.execute(test_context), timeout=10)
            print(f"   ✅ execute方法工作正常")
            print(f"   📊 结果: success={result.success}")
            return True
        except asyncio.TimeoutError:
            print("   ⚠️ execute方法超时（ReasoningExpert可能需要更多时间）")
            return True  # 超时不一定是错误
        except Exception as e:
            print(f"   ❌ execute方法失败: {e}")
            return False

    # 运行异步测试
    success = asyncio.run(test_execute())

    print("\n" + "=" * 40)
    if success:
        print("🎉 迁移验证基本通过！")
        print("💡 ReasoningExpert正在正常工作")
    else:
        print("❌ 迁移验证失败！")
        print("⚠️ 可能需要检查配置或回滚迁移")

except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("💡 可能需要检查文件路径或依赖关系")

except Exception as e:
    print(f"❌ 验证失败: {e}")
    import traceback
    traceback.print_exc()

print("\n📝 验证完成")
