#!/usr/bin/env python3
"""
RAGExpert失败原因深度分析

分析RAGExpert独立运行时的40%失败率根本原因
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

class RAGFailureAnalyzer:
    """RAGExpert失败分析器"""

    def __init__(self):
        self.failure_cases = []
        self.success_cases = []
        self.test_queries = [
            "What is machine learning?",
            "Explain neural networks",
            "How does AI work?",
            "What are the benefits of deep learning?",
            "Explain supervised learning",
        ]

    async def analyze_failures(self):
        """执行完整失败分析"""

        print("🔬 RAGExpert失败原因深度分析")
        print("=" * 50)

        # 测试不同配置下的表现
        configs = [
            {
                "name": "完整模式",
                "env_vars": {},
                "description": "使用完整RAG功能"
            },
            {
                "name": "轻量级模式",
                "env_vars": {"USE_LIGHTWEIGHT_RAG": "true"},
                "description": "跳过复杂初始化"
            },
            {
                "name": "禁用并行",
                "env_vars": {"USE_LIGHTWEIGHT_RAG": "false"},
                "description": "禁用并行检索",
                "context_override": {"use_parallel": False}
            }
        ]

        results = {}

        for config in configs:
            print(f"\n📊 测试配置: {config['name']}")
            print(f"   描述: {config['description']}")

            # 设置环境变量
            original_env = {}
            for key, value in config['env_vars'].items():
                original_env[key] = os.environ.get(key)
                os.environ[key] = value

            try:
                # 执行详细测试
                config_result = await self._test_config_detailed(config)
                results[config['name']] = config_result

                success_rate = config_result['success_rate']
                print(".1f")
                # 分析失败原因
                if config_result['failures']:
                    print(f"   失败详情:")
                    for failure in config_result['failures']:
                        print(f"     ❌ {failure['query'][:30]}...: {failure['error'][:50]}")

            except Exception as e:
                print(f"   💥 配置测试异常: {e}")
                results[config['name']] = {
                    'success_rate': 0.0,
                    'success_count': 0,
                    'total_count': len(self.test_queries),
                    'failures': [],
                    'error': str(e)
                }

            # 恢复环境变量
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

        # 生成分析报告
        await self._generate_analysis_report(results)

        return results

    async def _test_config_detailed(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """详细测试单个配置"""

        # 初始化RAGExpert
        rag_agent = RAGExpert()

        success_count = 0
        total_count = len(self.test_queries)
        failures = []
        successes = []

        for query in self.test_queries:
            try:
                # 准备上下文
                context = {"query": query}
                if config.get('context_override'):
                    context.update(config['context_override'])

                # 执行查询
                start_time = time.time()
                result = await rag_agent.execute(context)
                execution_time = time.time() - start_time

                if result.success:
                    success_count += 1
                    successes.append({
                        'query': query,
                        'execution_time': execution_time,
                        'confidence': result.confidence,
                        'evidence_count': len(result.data.get('evidence', [])) if result.data else 0
                    })
                else:
                    failures.append({
                        'query': query,
                        'error': result.error or "Unknown error",
                        'execution_time': execution_time,
                        'config': config['name']
                    })

            except Exception as e:
                failures.append({
                    'query': query,
                    'error': str(e),
                    'execution_time': 0.0,
                    'config': config['name']
                })

        return {
            'success_rate': (success_count / total_count) * 100,
            'success_count': success_count,
            'total_count': total_count,
            'failures': failures,
            'successes': successes,
            'config': config
        }

    async def _generate_analysis_report(self, results: Dict[str, Any]):
        """生成分析报告"""

        print("\n🎯 失败原因分析报告")
        print("=" * 50)

        # 找出最佳和最差配置
        best_config = max(results.items(), key=lambda x: x[1]['success_rate'])
        worst_config = min(results.items(), key=lambda x: x[1]['success_rate'])

        print(f"🏆 最佳配置: {best_config[0]} ({best_config[1]['success_rate']:.1f}%)")
        print(f"📉 最差配置: {worst_config[0]} ({worst_config[1]['success_rate']:.1f}%)")

        # 分析失败模式
        all_failures = []
        for config_name, data in results.items():
            all_failures.extend(data.get('failures', []))

        if all_failures:
            print(f"\n❌ 失败模式分析 (共{len(all_failures)}个失败):")

            # 按错误类型分组
            error_types = {}
            for failure in all_failures:
                error_type = self._categorize_error(failure['error'])
                if error_type not in error_types:
                    error_types[error_type] = []
                error_types[error_type].append(failure)

            for error_type, failures in error_types.items():
                percentage = (len(failures) / len(all_failures)) * 100
                print(".1f")
                print(f"      示例: {failures[0]['query'][:30]}...: {failures[0]['error'][:50]}")

        # 给出优化建议
        print("\n💡 优化建议:")
        if best_config[1]['success_rate'] >= 90:
            print("✅ 轻量级模式表现优秀，建议默认启用")
            print("   原因：避免了复杂的初始化和依赖问题")
        elif best_config[1]['success_rate'] >= 70:
            print("⚠️ 需要修复完整模式的关键问题")
            if 'timeout' in str(all_failures[0]['error'] if all_failures else ''):
                print("   建议：增加超时时间，优化API调用")
            elif 'network' in str(all_failures[0]['error'] if all_failures else '').lower():
                print("   建议：实现网络错误的降级策略")
            else:
                print("   建议：检查配置参数和依赖关系")
        else:
            print("❌ 存在系统性问题")
            print("   建议：简化架构，优先保证基本功能")

    def _categorize_error(self, error_msg: str) -> str:
        """对错误进行分类"""
        error_lower = error_msg.lower()

        if 'timeout' in error_lower:
            return '超时错误'
        elif 'network' in error_lower or 'connection' in error_lower:
            return '网络错误'
        elif 'api' in error_lower:
            return 'API错误'
        elif 'config' in error_lower or 'init' in error_lower:
            return '配置错误'
        elif 'memory' in error_lower:
            return '内存错误'
        else:
            return '其他错误'

async def main():
    """主函数"""
    analyzer = RAGFailureAnalyzer()
    results = await analyzer.analyze_failures()

    print("\n🎉 RAGExpert失败分析完成！")
    print("基于分析结果，可以制定针对性的修复方案。")

if __name__ == "__main__":
    asyncio.run(main())
