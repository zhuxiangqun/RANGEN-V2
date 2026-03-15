#!/usr/bin/env python3
"""
立即执行迁移测试 - 不依赖shell
"""

# 直接执行测试代码
exec('''
import asyncio
import sys
import os
import time

print("🚀 立即开始KnowledgeRetrievalAgent迁移测试")
print("=" * 70)

# 设置项目环境
project_root = "/Users/syu/workdata/person/zy/RANGEN-main(syu-python)"
sys.path.insert(0, project_root)
os.chdir(project_root)

async def run_test():
    try:
        print("\\n📋 环境检查...")
        if os.path.exists("src") and os.path.exists(".env"):
            print("✅ 环境检查通过")
        else:
            print("❌ 环境检查失败")
            return

        print("\\n🔧 加载环境变量...")
        try:
            with open(".env", "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip().strip(\'"\').strip("\'")
            print("✅ 环境变量加载成功")
        except Exception as e:
            print(f"❌ 环境变量加载失败: {e}")
            return

        print("\\n🔑 检查API配置...")
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if not api_key:
            print("❌ API密钥未设置")
            return
        print(f"✅ API密钥已配置 (长度: {len(api_key)})")

        print("\\n📦 导入组件...")
        from src.agents.expert_agents import KnowledgeRetrievalAgent
        from src.agents.rag_agent import RAGExpert
        from src.adapters.knowledge_retrieval_agent_adapter import KnowledgeRetrievalAgentAdapter
        from src.strategies.gradual_replacement import GradualReplacementStrategy
        print("✅ 组件导入成功")

        print("\\n🏗️ 创建实例...")
        old_agent = KnowledgeRetrievalAgent()
        new_agent = RAGExpert()
        adapter = KnowledgeRetrievalAgentAdapter()
        strategy = GradualReplacementStrategy(old_agent, new_agent, adapter)
        print("✅ 实例创建成功")

        print("\\n🧪 开始迁移测试...")
        print("-" * 40)

        for rate in [0.0, 0.5, 1.0]:
            print(f"\\n🔄 测试替换比例: {rate:.0%}")
            strategy.replacement_rate = rate

            context = {
                "query": f"测试知识检索迁移 - 比例{rate:.0%}",
                "max_iterations": 1,
                "use_tools": False,
                "enable_knowledge_retrieval": False
            }

            try:
                print("   执行中..."                start = time.time()
                result = await strategy.execute_with_gradual_replacement(context)
                duration = time.time() - start

                executed_by = result.get("_executed_by", "unknown")
                success = result.get("success", False)

                agent_icon = "🤖" if executed_by == "old_agent" else "🆕"
                status_icon = "✅" if success else "❌"

                print(f"   {status_icon} {agent_icon} {executed_by}: {duration:.3f}s")

            except Exception as e:
                print(f"   ❌ 执行失败: {str(e)[:100]}...")

            await asyncio.sleep(1.5)

        print("\\n🎉 测试完成！")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(run_test())
print("\\n" + "=" * 70)
''')

print("\\n执行完成！")
