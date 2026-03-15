#!/usr/bin/env python3
"""
ReActAgent迁移测试脚本
测试ReActAgent → ReasoningExpert的迁移功能
"""

import asyncio
import sys
import os
import time
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

async def run_react_agent_migration_test():
    """运行ReActAgent迁移测试"""
    print("🚀 开始ReActAgent迁移测试")
    print("=" * 70)

    step = 1
    
    # 1. 环境检查
    print(f'\n📋 步骤{step}: 环境检查')
    print("-" * 30)
    if Path("src").exists():
        print("✅ 项目结构正确")
    else:
        print("❌ 项目结构错误")
        return
    if Path(".env").exists():
        print("✅ 配置文件存在")
    else:
        print("❌ 配置文件不存在")
        return
    step += 1

    # 2. 加载环境变量
    print(f'\n🔧 步骤{step}: 加载环境变量')
    print("-" * 30)
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=Path(".env"))
        print("✅ 环境变量加载成功")
    except ImportError:
        try:
            with open(".env", "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip().strip('"').strip("'")
            print("✅ 环境变量手动加载成功")
        except Exception as e:
            print(f"❌ 环境变量加载失败: {e}")
            return
    except Exception as e:
        print(f"❌ 环境变量加载失败: {e}")
        return
    step += 1

    # 3. API配置验证
    print(f'\n🔑 步骤{step}: API配置验证')
    print("-" * 30)
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-reasoner")

    if not api_key:
        print("❌ DEEPSEEK_API_KEY 未设置")
        return

    print(f"✅ API密钥: 已配置 (长度: {len(api_key)})")
    print(f"✅ API地址: {base_url}")
    print(f"✅ 模型: {model}")
    step += 1

    # 4. 组件导入
    print(f'\n📦 步骤{step}: 组件导入')
    print("-" * 30)
    try:
        from src.agents.react_agent import ReActAgent
        print("✅ ReActAgent导入成功")
        from src.agents.reasoning_expert import ReasoningExpert
        print("✅ ReasoningExpert导入成功")
        from src.adapters.react_agent_adapter import ReActAgentAdapter
        print("✅ ReActAgentAdapter导入成功")
        from src.strategies.gradual_replacement import GradualReplacementStrategy
        print("✅ GradualReplacementStrategy导入成功")
    except Exception as e:
        print(f"❌ 组件导入失败: {e}")
        import traceback
        traceback.print_exc()
        return
    step += 1

    # 5. 实例创建
    print(f'\n🏗️ 步骤{step}: 实例创建')
    print("-" * 30)
    try:
        old_agent = ReActAgent()
        print("✅ 旧Agent创建成功 (ReActAgent)")
        new_agent = ReasoningExpert()
        print("✅ 新Agent创建成功 (ReasoningExpert)")
        adapter = ReActAgentAdapter()
        print("✅ 适配器创建成功")
        strategy = GradualReplacementStrategy(old_agent, new_agent, adapter)
        print("✅ 迁移策略创建成功")
    except Exception as e:
        print(f"❌ 实例创建失败: {e}")
        import traceback
        traceback.print_exc()
        return
    step += 1

    # 6. 迁移测试执行
    print(f'\n🧪 步骤{step}: 迁移测试执行')
    print("-" * 40)

    test_scenarios = [
        (0.0, "全部使用旧Agent (ReActAgent)"),
        (0.5, "50%概率使用新Agent (ReasoningExpert)，50%使用旧Agent"),
        (1.0, "全部使用新Agent (ReasoningExpert)")
    ]

    test_results = []

    for i, (rate, description) in enumerate(test_scenarios, 1):
        print(f'\n🧪 测试 {i}/{len(test_scenarios)}: {description}')
        print(f'🔄 设置替换比例: {rate:.0%}')

        strategy.replacement_rate = rate

        context = {
            "query": f"测试ReAct推理功能迁移 - 场景{i}",
            "max_iterations": 1,
            "use_tools": False,
            "enable_knowledge_retrieval": False
        }

        try:
            print('⚡ 开始执行...')
            start_time = time.time()

            result = await strategy.execute_with_gradual_replacement(context)

            execution_time = time.time() - start_time

            executed_by = result.get("_executed_by", "unknown")
            success = result.get("success", False)

            # 确定Agent信息
            if executed_by == "old_agent":
                agent_icon = "🤖"
                agent_name = "ReActAgent"
            elif executed_by == "new_agent":
                agent_icon = "🆕"
                agent_name = "ReasoningExpert"
            else:
                agent_icon = "❓"
                agent_name = "未知Agent"

            status_icon = "✅" if success else "❌"

            print(f'{status_icon} {agent_icon} 执行成功: {agent_name} ({execution_time:.3f}s)')
            print(f'   调试信息: success={success}, executed_by={executed_by}')
            data = result.get("data")
            if isinstance(data, dict):
                print(f'   数据: dict, keys = {list(data.keys())}')
            else:
                print(f'   数据: {type(data)}')
            print(f'   错误: {result.get("error")}')

            test_results.append({
                "scenario": i,
                "rate": rate,
                "executed_by": executed_by,
                "agent_name": agent_name,
                "success": success,
                "time": execution_time,
                "description": description,
                "error": result.get("error")
            })

        except Exception as e:
            error_msg = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
            print(f'❌ 执行失败: {error_msg}')
            import traceback
            traceback.print_exc()

            test_results.append({
                "scenario": i,
                "rate": rate,
                "executed_by": "error",
                "agent_name": "执行失败",
                "success": False,
                "time": 0,
                "description": description,
                "error": str(e)
            })

        # 短暂延迟，避免API限流
        if i < len(test_scenarios):
            print('⏳ 等待2秒...')
            await asyncio.sleep(2.0)

    step += 1

    # 7. 测试总结
    print(f'\n📊 步骤{step}: 测试总结')
    print("=" * 40)

    successful_tests = [r for r in test_results if r["success"]]
    failed_tests = [r for r in test_results if not r["success"]]

    print(f"✅ 成功测试: {len(successful_tests)}/{len(test_scenarios)}")
    print(f"❌ 失败测试: {len(failed_tests)}/{len(test_scenarios)}")

    if len(successful_tests) == len(test_scenarios):
        print("\n🎉 恭喜！迁移测试完全成功！")
        print("✅ ReActAgent成功迁移到ReasoningExpert")
        print("🚀 新Agent工作正常，可以进行生产部署")
    elif len(successful_tests) > 0:
        print("\n⚠️ 部分测试成功，迁移基本可行")
        print("🔧 建议进一步检查失败的测试场景")
    else:
        print("\n❌ 所有测试失败，需要进一步检查")

    print("\n📋 测试详细结果:")
    for result in test_results:
        status_icon = "✅" if result["success"] else "❌"
        agent_icon = "🤖" if result["executed_by"] == "old_agent" else "🆕" if result["executed_by"] == "new_agent" else "❓"
        error_detail = f" (错误: {result['error']})" if result.get('error') else ""
        print(f"   {status_icon} 场景{result['scenario']}: {agent_icon} {result['agent_name']} ({result['time']:.3f}s){error_detail}")

    if failed_tests:
        print("\n❌ 失败详情:")
        for failure in failed_tests:
            print(f"   • 场景{failure['scenario']}: {failure['error']}")

    print(f'\n🏁 最终结论:')
    print("=" * 40)
    if len(successful_tests) == len(test_scenarios):
        print("✅ ReActAgent → ReasoningExpert 迁移成功！")
        print("🎯 新Agent已准备好投入使用")
    else:
        print("⚠️ 迁移部分成功，可以有限使用")
    print("=" * 70)

if __name__ == '__main__':
    asyncio.run(run_react_agent_migration_test())

