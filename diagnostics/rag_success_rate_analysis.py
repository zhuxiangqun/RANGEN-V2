#!/usr/bin/env python3
"""
RAGExpert成功率精确分析
区分真正的LLM调用成功 vs 轻量级模式伪成功
"""

import asyncio
import time
import sys
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.rag_agent import RAGExpert

class RAGSuccessRateAnalyzer:
    """RAGExpert成功率精确分析器"""

    def __init__(self):
        self.test_queries = [
            "What is machine learning?",
            "Explain neural networks",
            "How does AI work?",
            "What are the benefits of deep learning?",
            "Explain supervised learning",
        ]

    def analyze_success_rates(self):
        """分析不同配置下的成功率"""

        print("🔬 RAGExpert成功率精确分析")
        print("=" * 60)

        # 测试场景：强制完整模式 vs 默认轻量级模式
        scenarios = [
            {
                "name": "强制完整模式 (USE_LIGHTWEIGHT_RAG=false)",
                "env_vars": {"USE_LIGHTWEIGHT_RAG": "false"},
                "expected_behavior": "尝试调用LLM，API密钥无效时应失败"
            },
            {
                "name": "默认轻量级模式 (USE_LIGHTWEIGHT_RAG=true)",
                "env_vars": {"USE_LIGHTWEIGHT_RAG": "true"},
                "expected_behavior": "返回模拟结果，始终成功"
            },
            {
                "name": "环境变量覆盖 (DEEPSEEK_API_KEY设置)",
                "env_vars": {
                    "USE_LIGHTWEIGHT_RAG": "false",
                    "DEEPSEEK_API_KEY": "sk-test-key-for-validation"
                },
                "expected_behavior": "即使API密钥无效也会尝试LLM调用"
            }
        ]

        results = {}

        for scenario in scenarios:
            print(f"\n📊 测试场景: {scenario['name']}")
            print(f"   预期行为: {scenario['expected_behavior']}")

            # 设置环境变量
            original_env = {}
            for key, value in scenario['env_vars'].items():
                original_env[key] = os.environ.get(key)
                os.environ[key] = value

            try:
                # 执行详细测试
                scenario_result = self._test_scenario_detailed(scenario)
                results[scenario['name']] = scenario_result

                success_rate = scenario_result['success_rate']
                real_success_rate = scenario_result['real_success_rate']
                lightweight_rate = scenario_result['lightweight_rate']

                print(".1f")
                print(".1f")
                print(".1f")
                # 分析结果
                if real_success_rate > 0:
                    print("   ✅ 包含真实LLM调用")
                else:
                    print("   ⚠️  仅轻量级模式，没有真实LLM调用")
                if success_rate == 100.0 and real_success_rate == 0.0:
                    print("   🎭 纯模拟成功：所有查询都返回了模拟结果")
                elif success_rate < 100.0:
                    print("   ❌ 存在真实失败：部分查询未能完成")

            except Exception as e:
                print(f"   💥 场景测试异常: {e}")
                results[scenario['name']] = {
                    'success_rate': 0.0,
                    'real_success_rate': 0.0,
                    'lightweight_rate': 0.0,
                    'total_count': len(self.test_queries),
                    'error': str(e)
                }

            # 恢复环境变量
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

        # 生成对比分析
        self._generate_comparison_analysis(results)

        return results

    def _test_scenario_detailed(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """详细测试单个场景"""

        # 初始化RAGExpert
        rag_agent = RAGExpert()

        success_count = 0
        real_success_count = 0  # 真实LLM调用成功的数量
        lightweight_count = 0   # 轻量级模式的数量
        total_count = len(self.test_queries)
        details = []

        for query in self.test_queries:
            try:
                # 执行查询
                start_time = time.time()
                result = asyncio.run(rag_agent.execute({"query": query}))
                execution_time = time.time() - start_time

                success = result.success
                if success:
                    success_count += 1

                # 判断是否为轻量级模式结果
                is_lightweight = False
                is_real_success = False

                if result.data:
                    # 检查是否包含轻量级模式标记
                    if result.data.get('lightweight_mode'):
                        is_lightweight = True
                        lightweight_count += 1
                    # 检查是否包含实际的evidence和answer（非模拟）
                    elif (result.data.get('evidence') and len(result.data.get('evidence', [])) > 0 and
                          result.data.get('answer') and
                          not result.data['answer'].startswith('这是对查询')):
                        is_real_success = True
                        real_success_count += 1
                        lightweight_count += 1  # 轻量级也算成功，但要区分

                details.append({
                    'query': query,
                    'success': success,
                    'is_lightweight': is_lightweight,
                    'is_real_success': is_real_success,
                    'execution_time': execution_time,
                    'error': result.error if not success else None
                })

            except Exception as e:
                details.append({
                    'query': query,
                    'success': False,
                    'is_lightweight': False,
                    'is_real_success': False,
                    'execution_time': 0.0,
                    'error': str(e)
                })

        return {
            'success_rate': (success_count / total_count) * 100,
            'real_success_rate': (real_success_count / total_count) * 100,
            'lightweight_rate': (lightweight_count / total_count) * 100,
            'success_count': success_count,
            'real_success_count': real_success_count,
            'lightweight_count': lightweight_count,
            'total_count': total_count,
            'details': details,
            'scenario': scenario
        }

    def _generate_comparison_analysis(self, results: Dict[str, Any]):
        """生成对比分析"""

        print("\n🎯 成功率分析结论")
        print("=" * 60)

        # 找出关键指标
        forced_full = results.get("强制完整模式 (USE_LIGHTWEIGHT_RAG=false)", {})
        default_lightweight = results.get("默认轻量级模式 (USE_LIGHTWEIGHT_RAG=true)", {})
        env_override = results.get("环境变量覆盖 (DEEPSEEK_API_KEY设置)", {})

        print(f"📊 关键发现:")
        print(f"   强制完整模式成功率: {forced_full.get('success_rate', 0):.1f}%")
        print(f"   默认轻量级模式成功率: {default_lightweight.get('success_rate', 0):.1f}%")
        print(f"   环境变量覆盖成功率: {env_override.get('success_rate', 0):.1f}%")

        # 判断API密钥是否真正生效
        api_working = env_override.get('real_success_rate', 0) > forced_full.get('real_success_rate', 0)

        if api_working:
            print("   ✅ API密钥生效：环境变量设置能提升真实LLM调用成功率")
        else:
            print("   ❌ API密钥未生效：即使设置环境变量也没有真实LLM调用")

        # 判断轻量级模式的贡献
        lightweight_impact = default_lightweight.get('success_rate', 0) - forced_full.get('success_rate', 0)

        if lightweight_impact > 0:
            print(".1f")
            print("      原因：轻量级模式提供了降级保障")
        else:
            print("   ⚠️  轻量级模式没有额外收益")

        # 给出最终结论
        print("\n🎯 最终结论:")
        if default_lightweight.get('success_rate', 0) > 80:
            if api_working:
                print("   ✅ RAGExpert优化成功：高成功率 + API密钥生效")
            else:
                print("   🎭 RAGExpert表面成功：高成功率仅来自轻量级模式降级")
        else:
            print("   ❌ RAGExpert需要进一步优化：成功率仍不理想")

        print("\n💡 建议行动:")
        if not api_working:
            print("   1. 验证DEEPSEEK_API_KEY是否正确设置到环境变量")
            print("   2. 测试真实LLM API连接性")
            print("   3. 检查网络连接和API额度")

        if lightweight_impact > 20:
            print("   4. 评估轻量级模式的业务价值")
            print("   5. 考虑在API不可用时启用降级模式")

        print("   6. 运行生产环境测试验证最终表现")

def main():
    """主函数"""
    analyzer = RAGSuccessRateAnalyzer()
    results = analyzer.analyze_success_rates()

    print("\n🎉 RAGExpert成功率分析完成！")
    print("基于精确分析结果，可以做出正确的优化决策。")

if __name__ == "__main__":
    main()
