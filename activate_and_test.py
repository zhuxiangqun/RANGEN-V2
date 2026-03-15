#!/usr/bin/env python3
"""
激活虚拟环境并运行迁移测试
"""

import sys
import os
import subprocess

# 项目根目录
project_root = "/Users/syu/workdata/person/zy/RANGEN-main(syu-python)"
os.chdir(project_root)

print("🔧 激活虚拟环境并运行迁移测试")
print("=" * 60)

# 检查.venv是否存在
venv_path = os.path.join(project_root, ".venv")
venv_python = os.path.join(venv_path, "bin", "python3")

if not os.path.exists(venv_path):
    print("❌ .venv目录不存在")
    print("💡 请先创建虚拟环境: python3 -m venv .venv")
    sys.exit(1)

if not os.path.exists(venv_python):
    print("❌ 虚拟环境中的Python不存在")
    print(f"   路径: {venv_python}")
    sys.exit(1)

print(f"✅ 虚拟环境存在: {venv_path}")
print(f"✅ Python路径: {venv_python}")

# 检查当前是否在虚拟环境中
in_venv = sys.prefix != sys.base_prefix

if in_venv:
    print("✅ 当前已在虚拟环境中")
    print(f"   当前Python: {sys.executable}")
else:
    print("⚠️  当前不在虚拟环境中")
    print("💡 将使用虚拟环境中的Python运行测试")

print("\n" + "=" * 60)
print("🚀 开始运行迁移测试")
print("=" * 60)

# 使用虚拟环境中的Python运行测试
test_script = """
import asyncio
import sys
import os
import time

# 设置项目环境
project_root = "/Users/syu/workdata/person/zy/RANGEN-main(syu-python)"
sys.path.insert(0, project_root)
os.chdir(project_root)

print("🚀 KnowledgeRetrievalAgent迁移测试")
print("=" * 60)

async def run_test():
    try:
        # 1. 环境检查
        print("\\n📋 步骤1: 环境检查")
        if os.path.exists("src") and os.path.exists(".env"):
            print("✅ 环境检查通过")
        else:
            print("❌ 环境检查失败")
            return

        # 2. 加载环境变量
        print("\\n🔧 步骤2: 加载环境变量")
        try:
            with open(".env", "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip().strip('"').strip("'")
            print("✅ 环境变量加载成功")
        except Exception as e:
            print(f"❌ 环境变量加载失败: {e}")
            return

        # 3. 检查API配置
        print("\\n🔑 步骤3: 检查API配置")
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if not api_key:
            print("❌ API密钥未设置")
            return
        print(f"✅ API密钥已配置 (长度: {len(api_key)})")

        # 4. 导入组件
        print("\\n📦 步骤4: 导入组件")
        try:
            from src.agents.expert_agents import KnowledgeRetrievalAgent
            from src.agents.rag_agent import RAGExpert
            from src.adapters.knowledge_retrieval_agent_adapter import KnowledgeRetrievalAgentAdapter
            from src.strategies.gradual_replacement import GradualReplacementStrategy
            print("✅ 组件导入成功")
        except Exception as e:
            print(f"❌ 组件导入失败: {e}")
            import traceback
            traceback.print_exc()
            return

        # 5. 创建实例
        print("\\n🏗️ 步骤5: 创建实例")
        try:
            old_agent = KnowledgeRetrievalAgent()
            new_agent = RAGExpert()
            adapter = KnowledgeRetrievalAgentAdapter()
            strategy = GradualReplacementStrategy(old_agent, new_agent, adapter)
            print("✅ 实例创建成功")
        except Exception as e:
            print(f"❌ 实例创建失败: {e}")
            import traceback
            traceback.print_exc()
            return

        # 6. 执行测试
        print("\\n🧪 步骤6: 执行迁移测试")
        print("-" * 40)

        results = []
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

                results.append({
                    "rate": rate,
                    "executed_by": executed_by,
                    "success": success,
                    "time": duration
                })

            except Exception as e:
                print(f"   ❌ 执行失败: {str(e)[:100]}...")
                results.append({
                    "rate": rate,
                    "executed_by": "error",
                    "success": False,
                    "time": 0
                })

            await asyncio.sleep(1.5)

        # 7. 测试总结
        print("\\n📊 步骤7: 测试总结")
        print("-" * 40)

        successful = sum(1 for r in results if r["success"])
        print(f"✅ 成功测试: {successful}/3")

        if successful == 3:
            print("\\n🎉 迁移测试完全成功！")
            print("✅ KnowledgeRetrievalAgent → RAGExpert 迁移成功")
        elif successful > 0:
            print("\\n⚠️ 部分测试成功")
        else:
            print("\\n❌ 所有测试失败")

        print("\\n🏁 测试完成！")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(run_test())
"""

# 使用虚拟环境中的Python执行测试
try:
    result = subprocess.run(
        [venv_python, "-c", test_script],
        cwd=project_root,
        capture_output=False,
        text=True
    )
    
    print("\n" + "=" * 60)
    if result.returncode == 0:
        print("✅ 测试执行完成")
    else:
        print(f"⚠️ 测试退出码: {result.returncode}")
    
except Exception as e:
    print(f"❌ 执行失败: {e}")
    import traceback
    traceback.print_exc()
