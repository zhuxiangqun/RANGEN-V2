#!/usr/bin/env python3
"""
立即运行迁移测试
"""

import asyncio
import sys
import os
import time

def main():
    print('🚀 立即开始KnowledgeRetrievalAgent迁移测试')
    print('=' * 70)

    # 设置项目路径
    project_root = "/Users/syu/workdata/person/zy/RANGEN-main(syu-python)"
    sys.path.insert(0, project_root)
    os.chdir(project_root)

    # 运行异步测试
    asyncio.run(run_migration_test())

async def run_migration_test():
    try:
        # 步骤计数器
        step = 1

        # 1. 环境检查
        print(f'\\n📋 步骤{step}: 环境检查')
        print('-' * 40)
        step += 1

        if not os.path.exists('src'):
            print('❌ src目录不存在')
            return
        print('✅ 项目结构正确')

        if not os.path.exists('.env'):
            print('❌ .env文件不存在')
            return
        print('✅ 配置文件存在')

        # 2. 加载环境变量
        print(f'\\n🔧 步骤{step}: 加载环境变量')
        print('-' * 40)
        step += 1

        try:
            with open('.env', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip().strip('"').strip("'")
            print('✅ 环境变量加载成功')
        except Exception as e:
            print(f'❌ 环境变量加载失败: {e}')
            return

        # 3. API配置验证
        print(f'\\n🔑 步骤{step}: API配置验证')
        print('-' * 40)
        step += 1

        api_key = os.getenv('DEEPSEEK_API_KEY', '')
        if not api_key:
            print('❌ DEEPSEEK_API_KEY未设置')
            return

        base_url = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
        model = os.getenv('DEEPSEEK_MODEL', 'deepseek-reasoner')

        print(f'✅ API密钥: 已配置 (长度: {len(api_key)})')
        print(f'✅ API地址: {base_url}')
        print(f'✅ 模型: {model}')

        # 4. 组件导入
        print(f'\\n📦 步骤{step}: 组件导入')
        print('-' * 40)
        step += 1

        try:
            from src.agents.expert_agents import KnowledgeRetrievalAgent
            print('✅ KnowledgeRetrievalAgent导入成功')

            from src.agents.rag_agent import RAGExpert
            print('✅ RAGExpert导入成功')

            from src.adapters.knowledge_retrieval_agent_adapter import KnowledgeRetrievalAgentAdapter
            print('✅ KnowledgeRetrievalAgentAdapter导入成功')

            from src.strategies.gradual_replacement import GradualReplacementStrategy
            print('✅ GradualReplacementStrategy导入成功')

        except Exception as e:
            print(f'❌ 组件导入失败: {e}')
            import traceback
            traceback.print_exc()
            return

        # 5. 实例创建
        print(f'\\n🏗️ 步骤{step}: 实例创建')
        print('-' * 40)
        step += 1

        try:
            old_agent = KnowledgeRetrievalAgent()
            print('✅ 旧Agent创建成功')

            new_agent = RAGExpert()
            print('✅ 新Agent创建成功')

            adapter = KnowledgeRetrievalAgentAdapter()
            print('✅ 适配器创建成功')

            strategy = GradualReplacementStrategy(old_agent, new_agent, adapter)
            print('✅ 迁移策略创建成功')

        except Exception as e:
            print(f'❌ 实例创建失败: {e}')
            import traceback
            traceback.print_exc()
            return

        # 6. 迁移测试执行
        print(f'\\n🧪 步骤{step}: 迁移测试执行')
        print('-' * 40)

        test_results = []

        test_scenarios = [
            (0.0, "全部使用旧Agent (KnowledgeRetrievalAgent)"),
            (0.5, "50%概率使用新Agent (RAGExpert)，50%使用旧Agent"),
            (1.0, "全部使用新Agent (RAGExpert)")
        ]

        for i, (rate, description) in enumerate(test_scenarios, 1):
            print(f'\\n🧪 测试 {i}/3: {description}')
            print(f'🔄 设置替换比例: {rate:.0%}')

            strategy.replacement_rate = rate

            context = {
                "query": f"测试知识检索迁移功能 - 场景{i}",
                "max_iterations": 1,
                "use_tools": False,
                "enable_knowledge_retrieval": True  # 改为True，让RAGExpert执行知识检索
            }

            try:
                print('⚡ 开始执行...')
                start_time = time.time()

                result = await strategy.execute_with_gradual_replacement(context)

                execution_time = time.time() - start_time

                executed_by = result.get("_executed_by", "unknown")
                success = result.get("success", False)
                
                # 调试信息：显示完整的结果结构
                if executed_by == "new_agent":
                    print(f'   调试: result keys = {list(result.keys())[:10]}')
                    if "error" in result:
                        print(f'   错误: {result.get("error")}')
                    if "data" in result:
                        data = result.get("data")
                        if data:
                            print(f'   数据: {type(data)}, keys = {list(data.keys())[:5] if isinstance(data, dict) else "N/A"}')
                        else:
                            print(f'   数据: None或空')

                # 确定Agent信息
                if executed_by == "old_agent":
                    agent_icon = "🤖"
                    agent_name = "KnowledgeRetrievalAgent"
                elif executed_by == "new_agent":
                    agent_icon = "🆕"
                    agent_name = "RAGExpert"
                else:
                    agent_icon = "❓"
                    agent_name = "未知Agent"

                status_icon = "✅" if success else "❌"
                status_text = "执行成功" if success else "执行失败"

                print(f'{status_icon} {agent_icon} {status_text}: {agent_name} ({execution_time:.3f}s)')
                
                # 如果失败，显示更多调试信息
                if not success:
                    print(f'   调试信息: success={success}, executed_by={executed_by}')
                    if "data" in result:
                        data_info = result.get("data", {})
                        if isinstance(data_info, dict):
                            print(f'   数据键: {list(data_info.keys())[:5]}')
                        else:
                            print(f'   数据类型: {type(data_info)}')
                    if "error" in result:
                        print(f'   错误信息: {result.get("error")}')

                test_results.append({
                    "scenario": i,
                    "rate": rate,
                    "executed_by": executed_by,
                    "agent_name": agent_name,
                    "success": success,
                    "time": execution_time,
                    "description": description
                })

            except Exception as e:
                error_msg = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
                print(f'❌ 执行失败: {error_msg}')

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

        # 7. 测试总结
        print(f'\\n📊 步骤{step}: 测试总结')
        print('=' * 40)
        step += 1

        successful_tests = [r for r in test_results if r["success"]]
        failed_tests = [r for r in test_results if not r["success"]]

        print(f'✅ 成功测试: {len(successful_tests)}/3')
        print(f'❌ 失败测试: {len(failed_tests)}/3')

        if len(successful_tests) == 3:
            print('\\n🎉 恭喜！迁移测试完全成功！')
            print('✅ KnowledgeRetrievalAgent成功迁移到RAGExpert')
            print('🚀 新Agent工作正常，可以进行生产部署')

        elif len(successful_tests) >= 1:
            print('\\n⚠️ 部分测试成功，迁移基本可行')
            print('🔧 建议进一步检查失败的测试场景')

        else:
            print('\\n❌ 所有测试失败，需要检查配置')
            print('🔧 请检查API密钥、网络连接等')

        # 显示详细结果
        print('\\n📋 测试详细结果:')
        for result in test_results:
            status_icon = "✅" if result["success"] else "❌"
            agent_icon = "🤖" if result["executed_by"] == "old_agent" else "🆕" if result["executed_by"] == "new_agent" else "❓"
            time_display = f"{result['time']:.3f}s" if result["success"] else "失败"
            print(f'   {status_icon} 场景{result["scenario"]}: {agent_icon} {result["agent_name"]} ({time_display})')

        # 显示失败详情
        if failed_tests:
            print('\\n❌ 失败详情:')
            for failed in failed_tests:
                error_info = failed.get("error", "未知错误")
                print(f'   • 场景{failed["scenario"]}: {error_info[:150]}...')

        # 最终结论
        print('\\n🏁 最终结论:')
        print('=' * 40)

        if len(successful_tests) == 3:
            print('✅ KnowledgeRetrievalAgent → RAGExpert 迁移成功！')
            print('🎯 新Agent已准备好投入使用')
        elif len(successful_tests) > 0:
            print('⚠️ 迁移部分成功，可以有限使用')
        else:
            print('❌ 迁移失败，需要进一步调试')

        print('=' * 70)

    except Exception as e:
        print(f'\\n💥 测试过程中发生严重错误: {e}')
        import traceback
        traceback.print_exc()
        print('=' * 70)

if __name__ == "__main__":
    main()
