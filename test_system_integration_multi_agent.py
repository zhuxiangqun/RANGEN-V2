#!/usr/bin/env python3
"""
系统集成测试 - 多Agent协作功能验证

测试所有已迁移Agent之间的协作功能，确保：
1. ReActAgent (ReasoningExpert) 正常工作
2. ChiefAgent (AgentCoordinator) 正常工作
3. KnowledgeRetrievalAgent (RAGExpert) 正常工作
4. CitationAgent (QualityController) 正常工作
5. 各Agent之间的协作接口兼容
"""

import asyncio
import sys
import os
import time
from pathlib import Path
from typing import Dict, Any, List

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class MultiAgentIntegrationTest:
    """多Agent集成测试"""

    def __init__(self):
        self.test_results = []
        self.agents = {}

    async def setup_agents(self):
        """设置所有测试Agent"""
        print("🔧 设置测试Agent...")

        try:
            # 1. 设置ReActAgent (ReasoningExpert)
            from src.agents.reasoning_expert import ReasoningExpert
            self.agents['react'] = ReasoningExpert()
            print("✅ ReasoningExpert设置成功")

            # 2. 设置ChiefAgent (AgentCoordinator)
            from src.agents.agent_coordinator import AgentCoordinator
            self.agents['chief'] = AgentCoordinator()
            print("✅ AgentCoordinator设置成功")

            # 3. 设置KnowledgeRetrievalAgent (RAGExpert)
            from src.agents.rag_expert import RAGExpert
            self.agents['knowledge'] = RAGExpert()
            print("✅ RAGExpert设置成功")

            # 4. 设置CitationAgent (QualityController)
            from src.agents.quality_controller import QualityController
            self.agents['citation'] = QualityController()
            print("✅ QualityController设置成功")

            return True

        except Exception as e:
            print(f"❌ Agent设置失败: {e}")
            return False

    async def test_individual_agent_functionality(self):
        """测试单个Agent的功能"""
        print("\n🔍 测试单个Agent功能...")

        test_cases = [
            {
                'agent': 'react',
                'name': 'ReasoningExpert',
                'context': {
                    'query': '分析人工智能发展趋势',
                    'task_type': 'analysis'
                }
            },
            {
                'agent': 'chief',
                'name': 'AgentCoordinator',
                'context': {
                    'action': 'submit_task',
                    'task': {
                        'type': 'coordination',
                        'description': '组织团队分析项目'
                    }
                }
            },
            {
                'agent': 'knowledge',
                'name': 'RAGExpert',
                'context': {
                    'query': '什么是机器学习？',
                    'enable_knowledge_retrieval': True
                }
            },
            {
                'agent': 'citation',
                'name': 'QualityController',
                'context': {
                    'answer': '机器学习是人工智能的一个分支',
                    'evidence': [{'content': 'ML定义', 'source': 'test'}]
                }
            }
        ]

        for test_case in test_cases:
            agent_name = test_case['agent']
            display_name = test_case['name']

            try:
                start_time = time.time()
                result = await self.agents[agent_name].execute(test_case['context'])
                execution_time = time.time() - start_time

                success = getattr(result, 'success', True) if hasattr(result, 'success') else True

                self.test_results.append({
                    'test_type': 'individual',
                    'agent': agent_name,
                    'name': display_name,
                    'success': success,
                    'execution_time': execution_time,
                    'error': None
                })

                print(".2f"
            except Exception as e:
                print(f"❌ {display_name}测试失败: {e}")
                self.test_results.append({
                    'test_type': 'individual',
                    'agent': agent_name,
                    'name': display_name,
                    'success': False,
                    'execution_time': 0,
                    'error': str(e)
                })

    async def test_agent_collaboration_scenarios(self):
        """测试Agent协作场景"""
        print("\n🔗 测试Agent协作场景...")

        collaboration_scenarios = [
            {
                'name': '知识检索+推理协作',
                'description': 'RAGExpert检索知识，ReasoningExpert进行推理',
                'steps': [
                    {
                        'agent': 'knowledge',
                        'context': {'query': '人工智能发展历史', 'enable_knowledge_retrieval': True},
                        'output_key': 'knowledge_result'
                    },
                    {
                        'agent': 'react',
                        'context': {'query': '基于检索结果分析AI发展趋势', 'knowledge_context': '${knowledge_result}'},
                        'input_key': 'knowledge_result'
                    }
                ]
            },
            {
                'name': '推理+引用质量控制',
                'description': 'ReasoningExpert推理，QualityController验证引用质量',
                'steps': [
                    {
                        'agent': 'react',
                        'context': {'query': '解释深度学习原理', 'task_type': 'explanation'},
                        'output_key': 'reasoning_result'
                    },
                    {
                        'agent': 'citation',
                        'context': {'answer': '${reasoning_result}', 'evidence': []},
                        'input_key': 'reasoning_result'
                    }
                ]
            },
            {
                'name': '协调器+多Agent协作',
                'description': 'AgentCoordinator协调多个Agent完成复杂任务',
                'steps': [
                    {
                        'agent': 'chief',
                        'context': {
                            'action': 'coordinate_analysis',
                            'task': '分析当前AI技术栈的优势和劣势',
                            'agents_needed': ['knowledge', 'react', 'citation']
                        }
                    }
                ]
            }
        ]

        for scenario in collaboration_scenarios:
            print(f"   测试场景: {scenario['name']}")
            print(f"   描述: {scenario['description']}")

            scenario_success = True
            step_results = []

            # 执行协作步骤
            context_data = {}

            for step in scenario['steps']:
                try:
                    agent_name = step['agent']
                    context = step['context'].copy()

                    # 替换上下文中的变量
                    for key, value in context.items():
                        if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                            var_name = value[2:-1]
                            if var_name in context_data:
                                context[key] = context_data[var_name]

                    start_time = time.time()
                    result = await self.agents[agent_name].execute(context)
                    execution_time = time.time() - start_time

                    success = getattr(result, 'success', True) if hasattr(result, 'success') else True

                    if success and 'output_key' in step:
                        context_data[step['output_key']] = result

                    step_results.append({
                        'agent': agent_name,
                        'success': success,
                        'execution_time': execution_time
                    })

                    if not success:
                        scenario_success = False

                except Exception as e:
                    print(f"     ❌ 步骤失败 ({agent_name}): {e}")
                    scenario_success = False
                    step_results.append({
                        'agent': agent_name,
                        'success': False,
                        'execution_time': 0,
                        'error': str(e)
                    })

            self.test_results.append({
                'test_type': 'collaboration',
                'scenario_name': scenario['name'],
                'success': scenario_success,
                'steps': step_results
            })

            status = "✅ 通过" if scenario_success else "❌ 失败"
            print(f"   结果: {status}")

    async def test_system_integration(self):
        """测试系统整体集成"""
        print("\n🏗️ 测试系统整体集成...")

        try:
            from src.unified_research_system import UnifiedResearchSystem

            # 初始化系统
            system = UnifiedResearchSystem()
            await system.initialize()

            # 测试系统执行
            test_query = "分析当前AI技术的应用场景和发展趋势"

            start_time = time.time()
            result = await system.execute_research(test_query)
            execution_time = time.time() - start_time

            success = getattr(result, 'success', True) if hasattr(result, 'success') else True

            self.test_results.append({
                'test_type': 'integration',
                'component': 'UnifiedResearchSystem',
                'success': success,
                'execution_time': execution_time
            })

            status = "✅ 通过" if success else "❌ 失败"
            print(f"   UnifiedResearchSystem集成测试: {status} ({execution_time:.2f}s)")

        except Exception as e:
            print(f"❌ 系统集成测试失败: {e}")
            self.test_results.append({
                'test_type': 'integration',
                'component': 'UnifiedResearchSystem',
                'success': False,
                'execution_time': 0,
                'error': str(e)
            })

    def generate_report(self):
        """生成测试报告"""
        print("\n📊 生成测试报告...")

        # 统计结果
        individual_tests = [r for r in self.test_results if r['test_type'] == 'individual']
        collaboration_tests = [r for r in self.test_results if r['test_type'] == 'collaboration']
        integration_tests = [r for r in self.test_results if r['test_type'] == 'integration']

        individual_passed = sum(1 for r in individual_tests if r['success'])
        collaboration_passed = sum(1 for r in collaboration_tests if r['success'])
        integration_passed = sum(1 for r in integration_tests if r['success'])

        print("=" * 80)
        print("🎯 多Agent集成测试报告")
        print("=" * 80)
        print(f"📈 单个Agent测试: {individual_passed}/{len(individual_tests)} 通过")
        print(f"🔗 协作场景测试: {collaboration_passed}/{len(collaboration_tests)} 通过")
        print(f"🏗️ 系统集成测试: {integration_passed}/{len(integration_tests)} 通过")

        total_passed = individual_passed + collaboration_passed + integration_passed
        total_tests = len(self.test_results)

        print(f"📊 总体通过率: {total_passed}/{total_tests} ({total_passed/total_tests*100:.1f}%)")

        # 详细结果
        print("\n📋 详细测试结果:")
        print("-" * 40)

        for result in self.test_results:
            if result['test_type'] == 'individual':
                status = "✅" if result['success'] else "❌"
                print(".2f"            elif result['test_type'] == 'collaboration':
                status = "✅" if result['success'] else "❌"
                print(f"{status} 协作场景: {result['scenario_name']}")
            elif result['test_type'] == 'integration':
                status = "✅" if result['success'] else "❌"
                print(f"{status} 系统集成: {result['component']} ({result['execution_time']:.2f}s)")

        # 生成建议
        print("\n💡 测试建议:")
        if total_passed == total_tests:
            print("🎉 所有测试通过！系统集成状态良好，可以投入生产使用。")
        else:
            failed_tests = [r for r in self.test_results if not r['success']]
            print(f"⚠️ 发现 {len(failed_tests)} 个失败的测试，需要进一步检查。")

        return total_passed == total_tests

async def main():
    """主函数"""
    print("🚀 开始多Agent集成测试")
    print("=" * 80)

    tester = MultiAgentIntegrationTest()

    # 1. 设置Agent
    if not await tester.setup_agents():
        print("❌ Agent设置失败，测试终止")
        return False

    # 2. 测试单个Agent功能
    await tester.test_individual_agent_functionality()

    # 3. 测试Agent协作场景
    await tester.test_agent_collaboration_scenarios()

    # 4. 测试系统整体集成
    await tester.test_system_integration()

    # 5. 生成报告
    success = tester.generate_report()

    print("\n" + "=" * 80)
    if success:
        print("🎉 多Agent集成测试全部通过！")
        print("✅ 系统协作功能正常")
        print("✅ Agent间接口兼容")
        print("✅ 整体集成稳定")
    else:
        print("⚠️ 多Agent集成测试发现问题")
        print("需要检查失败的测试项")

    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
