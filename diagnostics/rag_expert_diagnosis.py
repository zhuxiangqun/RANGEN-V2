#!/usr/bin/env python3
"""
RAGExpert深度诊断 - 分析60%成功率问题的根本原因

执行方式:
cd /Users/syu/workdata/person/zy/RANGEN-main\(syu-python\)
source .venv/bin/activate
python diagnostics/rag_expert_diagnosis.py
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

async def diagnose_rag_expert():
    """深度诊断RAGExpert的60%成功率问题"""

    print("🔬 RAGExpert深度诊断")
    print("=" * 50)

    # 测试查询集合
    test_queries = [
        "What is machine learning?",
        "Explain neural networks",
        "How does AI work?",
        "What are the benefits of deep learning?",
        "Explain supervised learning",
    ]

    # 测试不同配置下的表现
    configurations = [
        {
            "name": "默认配置",
            "env_vars": {},
            "description": "使用默认配置"
        },
        {
            "name": "强制轻量级模式",
            "env_vars": {"USE_LIGHTWEIGHT_RAG": "true"},
            "description": "强制使用轻量级模式，跳过复杂初始化"
        },
        {
            "name": "禁用Jina",
            "env_vars": {"USE_LIGHTWEIGHT_RAG": "true", "JINA_API_KEY": ""},
            "description": "禁用Jina API依赖"
        }
    ]

    results = {}

    for config in configurations:
        print(f"\n📊 测试配置: {config['name']}")
        print(f"   描述: {config['description']}")

        # 设置环境变量
        original_env = {}
        for key, value in config['env_vars'].items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value

        try:
            # 测试RAGExpert
            success_count = 0
            total_tests = len(test_queries)

            # 初始化RAGExpert
            start_time = time.time()
            rag_agent = RAGExpert()
            init_time = time.time() - start_time

            print(".2f")
            for i, query in enumerate(test_queries, 1):
                try:
                    result = await rag_agent.execute({"query": query})
                    status = "✅" if result.success else "❌"
                    success_count += 1 if result.success else 0
                    print(f"   查询{i}: {status} - {query[:30]}...")

                    # 记录失败详情
                    if not result.success:
                        print(f"      错误: {result.error}")

                except Exception as e:
                    print(f"   查询{i}: 💥 异常 - {str(e)[:50]}...")

            success_rate = (success_count / total_tests) * 100
            results[config['name']] = {
                'success_rate': success_rate,
                'init_time': init_time,
                'total_queries': total_tests,
                'successful_queries': success_count
            }

            print(".1f")
        except Exception as e:
            print(f"   💥 配置测试失败: {e}")
            results[config['name']] = {
                'success_rate': 0.0,
                'init_time': 0.0,
                'error': str(e)
            }

        # 恢复环境变量
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    # 分析结果
    print("\n🎯 诊断结果分析")
    print("=" * 50)

    # 找出最佳配置
    best_config = max(results.items(), key=lambda x: x[1]['success_rate'])
    worst_config = min(results.items(), key=lambda x: x[1]['success_rate'])

    print(f"🏆 最佳配置: {best_config[0]} ({best_config[1]['success_rate']:.1f}%)")
    print(f"📉 最差配置: {worst_config[0]} ({worst_config[1]['success_rate']:.1f}%)")

    # 分析配置差异
    print("\n🔍 配置影响分析:")
    for config_name, data in results.items():
        rate = data['success_rate']
        init_time = data['init_time']
        print(".1f")
    # 给出建议
    print("\n💡 优化建议:")
    if best_config[1]['success_rate'] >= 90:
        print("✅ RAGExpert在最佳配置下表现优秀，建议采用该配置")
        print(f"   配置: {best_config[0]}")
    elif best_config[1]['success_rate'] >= 70:
        print("⚠️ RAGExpert表现一般，需要进一步优化")
        print("   建议：检查依赖配置、API密钥、网络连接")
    else:
        print("❌ RAGExpert存在严重问题")
        print("   建议：检查基础依赖、配置正确性")

    return results

async def test_initialization_performance():
    """测试RAGExpert的初始化性能"""

    print("\n⚡ RAGExpert初始化性能测试")
    print("-" * 40)

    configs = [
        ("默认配置", {}),
        ("轻量级模式", {"USE_LIGHTWEIGHT_RAG": "true"}),
        ("禁用外部API", {"USE_LIGHTWEIGHT_RAG": "true", "JINA_API_KEY": ""})
    ]

    for config_name, env_vars in configs:
        # 设置环境变量
        original_env = {}
        for key, value in env_vars.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value

        try:
            start_time = time.time()
            rag_agent = RAGExpert()
            init_time = time.time() - start_time

            print(".2f")
            # 测试一个简单查询
            result = await rag_agent.execute({"query": "test"})
            status = "✅" if result.success else "❌"
            print(f"   简单查询测试: {status}")

        except Exception as e:
            print(f"   💥 初始化失败: {e}")

        # 恢复环境变量
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

async def main():
    """主函数"""
    print("🚀 开始RAGExpert深度诊断...\n")

    # 执行深度诊断
    results = await diagnose_rag_expert()

    # 初始化性能测试
    await test_initialization_performance()

    print("\n🎉 RAGExpert诊断完成！")
    print("基于诊断结果，可以制定针对性的优化方案。")

if __name__ == "__main__":
    asyncio.run(main())
