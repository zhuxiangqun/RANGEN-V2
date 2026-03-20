#!/usr/bin/env python3
"""
快速测试 - 复制粘贴执行
"""

# 以下是完整的测试代码，复制到Python解释器中执行：

test_code = '''
import asyncio
import sys
import os
import time

# 设置项目路径
project_root = "/Users/syu/workdata/person/zy/RANGEN-main(syu-python)"
sys.path.insert(0, project_root)
os.chdir(project_root)

async def run_test():
    print("🚀 KnowledgeRetrievalAgent迁移测试")
    print("=" * 60)

    # 加载.env文件
    try:
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")
        print("✅ 环境变量已加载")
    except Exception as e:
        print(f"❌ 环境变量加载失败: {e}")
        return

    # 检查API密钥
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key:
        print("❌ API密钥未设置")
        return
    print(f"✅ API密钥已配置 (长度: {len(api_key)})")

    try:
        # 导入组件
        from src.agents.expert_agents import KnowledgeRetrievalAgent
        from src.agents.rag_agent import RAGExpert
        from src.adapters.knowledge_retrieval_agent_adapter import KnowledgeRetrievalAgentAdapter
        from src.strategies.gradual_replacement import GradualReplacementStrategy
        print("✅ 组件导入成功")

        # 创建实例
        old_agent = KnowledgeRetrievalAgent()
        new_agent = RAGExpert()
        adapter = KnowledgeRetrievalAgentAdapter()
        strategy = GradualReplacementStrategy(old_agent, new_agent, adapter)
        print("✅ 实例创建成功")

        print("\\n🧪 开始测试...\\n")

        # 测试不同比例
        for rate in [0.0, 0.5, 1.0]:
            print(f"🔄 测试替换比例: {rate:.0%}")
            strategy.replacement_rate = rate

            context = {
                "query": f"测试查询 - 比例{rate:.0%}",
                "max_iterations": 1,
                "use_tools": False,
                "enable_knowledge_retrieval": False
            }

            start = time.time()
            result = await strategy.execute_with_gradual_replacement(context)
            duration = time.time() - start

            executed_by = result.get("_executed_by", "unknown")
            success = result.get("success", False)

            agent_icon = "🤖" if executed_by == "old_agent" else "🆕"
            status_icon = "✅" if success else "❌"

            print(f"   {status_icon} {agent_icon} {executed_by}: {duration:.3f}s")
            await asyncio.sleep(1.0)

        print("\\n🎉 测试完成！")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(run_test())
'''

print("🔧 快速测试执行器")
print("=" * 60)
print()
print("请复制下面的代码到Python解释器中执行：")
print()
print("步骤1: 在终端中运行 'python3'")
print("步骤2: 在Python提示符>>>下粘贴以下代码：")
print()
exec(test_code)
print()
print("=" * 60)
