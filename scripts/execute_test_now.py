#!/usr/bin/env python3
"""
立即执行迁移测试
"""

# 直接执行测试，避免所有shell问题
exec('''
import asyncio
import sys
import os
import time

print("🚀 启动KnowledgeRetrievalAgent迁移测试...")
print("=" * 60)

# 设置项目环境
project_root = "/Users/syu/workdata/person/zy/RANGEN-main(syu-python)"
sys.path.insert(0, project_root)
os.chdir(project_root)

async def test():
    try:
        # 步骤1: 加载环境变量
        print("📋 步骤1: 加载环境变量")
        env_loaded = False
        try:
            with open(".env", "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip().strip(\'"\').strip("\'")
            env_loaded = True
            print("✅ 环境变量加载成功")
        except Exception as e:
            print(f"❌ 环境变量加载失败: {e}")
            return

        # 步骤2: 检查API配置
        print("\\n🔑 步骤2: 检查API配置")
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if not api_key:
            print("❌ DEEPSEEK_API_KEY未设置，请检查.env文件")
            return
        print(f"✅ API密钥已配置 (长度: {len(api_key)})")

        # 步骤3: 导入组件
        print("\\n📦 步骤3: 导入组件")
        try:
            from src.agents.expert_agents import KnowledgeRetrievalAgent
            from src.agents.rag_agent import RAGExpert
            from src.adapters.knowledge_retrieval_agent_adapter import KnowledgeRetrievalAgentAdapter
            from src.strategies.gradual_replacement import GradualReplacementStrategy
            print("✅ 所有组件导入成功")
        except Exception as e:
            print(f"❌ 组件导入失败: {e}")
            return

        # 步骤4: 创建实例
        print("\\n🏗️ 步骤4: 创建实例")
        try:
            old_agent = KnowledgeRetrievalAgent()
            new_agent = RAGExpert()
            adapter = KnowledgeRetrievalAgentAdapter()
            strategy = GradualReplacementStrategy(old_agent, new_agent, adapter)
            print("✅ 实例创建成功")
        except Exception as e:
            print(f"❌ 实例创建失败: {e}")
            return

        # 步骤5: 执行测试
        print("\\n🧪 步骤5: 执行迁移测试")
        print("-" * 40)

        test_results = []

        for rate in [0.0, 0.5, 1.0]:
            print(f"\\n🔄 测试替换比例: {rate:.0%}")
            strategy.replacement_rate = rate

            context = {
                "query": f"简单测试查询 - 替换比例{rate:.0%}",
                "max_iterations": 1,
                "use_tools": False,
                "enable_knowledge_retrieval": False
            }

            try:
                start_time = time.time()
                result = await strategy.execute_with_gradual_replacement(context)
                duration = time.time() - start_time

                executed_by = result.get("_executed_by", "unknown")
                success = result.get("success", False)

                agent_icon = "🤖" if executed_by == "old_agent" else "🆕"
                status_icon = "✅" if success else "❌"

                print(f"   {status_icon} {agent_icon} {executed_by}: {duration:.3f}s")

                test_results.append({
                    "rate": rate,
                    "executed_by": executed_by,
                    "success": success,
                    "duration": duration
                })

            except Exception as e:
                print(f"   ❌ 执行失败: {str(e)[:50]}...")
                test_results.append({
                    "rate": rate,
                    "executed_by": "error",
                    "success": False,
                    "duration": 0,
                    "error": str(e)
                })

            await asyncio.sleep(1.0)

        # 步骤6: 测试总结
        print("\\n📊 步骤6: 测试总结")
        print("-" * 40)

        success_count = sum(1 for r in test_results if r["success"])
        total_count = len(test_results)

        print(f"✅ 成功测试: {success_count}/{total_count}")

        for result in test_results:
            rate = result["rate"]
            executed_by = result["executed_by"]
            success = result["success"]
            duration = result["duration"]

            agent_name = "KnowledgeRetrievalAgent" if executed_by == "old_agent" else "RAGExpert" if executed_by == "new_agent" else "错误"
            status = "成功" if success else "失败"

            print(f"   {rate:.0%} → {agent_name}: {status} ({duration:.3f}s)")

        if success_count == total_count:
            print("\\n🎉 所有测试通过！KnowledgeRetrievalAgent成功迁移到RAGExpert")
        else:
            print(f"\\n⚠️ {total_count - success_count}个测试失败，需要检查配置")

    except Exception as e:
        print(f"\\n❌ 测试过程中发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()

# 运行测试
asyncio.run(test())
''')

print("\\n" + "="*60)
print("测试执行完毕")
