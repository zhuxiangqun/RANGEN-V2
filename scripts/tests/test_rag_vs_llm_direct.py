#!/usr/bin/env python3
"""
测试RAG流程vs LLM直接回答模式的决策逻辑
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
    print('✅ 已加载.env文件')
except ImportError:
    print('⚠️ python-dotenv未安装')

def simulate_evidence_quality_evaluation():
    """模拟证据质量评估逻辑"""

    def evaluate_evidence_quality(evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        评估证据质量，决定是否应该使用LLM直接回答
        （复制自RAG Agent的逻辑）
        """
        if len(evidence) == 0:
            # 🚀 对于复杂查询，即使没有证据也尝试RAG流程
            return {
                'is_insufficient': False,  # 改为False，让RAG流程继续
                'reason': '无证据但允许RAG流程继续',
                'avg_similarity': 0.0,
                'allow_rag_continue': True
            }

        # 计算平均相似度
        similarities = [e.get('similarity', 0.0) for e in evidence]
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0

        # 高质量证据数量（相似度>0.7）
        high_quality_count = sum(1 for s in similarities if s > 0.7)

        # 检查内容相关性（简单启发式）
        content_relevance_score = _check_content_relevance(evidence)

        # 🚀 放宽证据质量要求，让RAG流程有更多机会

        # 如果有任何证据，至少相似度>0.3，就继续RAG流程
        if avg_similarity > 0.3 and len(evidence) >= 1:
            return {
                'is_insufficient': False,
                'reason': f'有基础证据，继续RAG流程 (相似度:{avg_similarity:.2f})',
                'avg_similarity': avg_similarity,
                'allow_rag_continue': True
            }

        # 对于相似度极低的情况，才切换到LLM直接回答
        if avg_similarity < 0.2 and content_relevance_score < 0.3:
            return {
                'is_insufficient': True,
                'reason': f'证据质量极低，切换LLM直接回答 (相似度:{avg_similarity:.2f}, 相关性:{content_relevance_score:.2f})',
                'avg_similarity': avg_similarity
            }

        # 默认继续RAG流程，给推理引擎机会
        return {
            'is_insufficient': False,
            'reason': f'允许RAG流程继续 (相似度:{avg_similarity:.2f}, 证据数:{len(evidence)})',
            'avg_similarity': avg_similarity,
            'allow_rag_continue': True
        }

    def _check_content_relevance(evidence: List[Dict[str, Any]]) -> float:
        """检查证据内容的整体相关性"""
        if not evidence:
            return 0.0

        contents = []
        for e in evidence:
            content = e.get('content', '').lower()
            if content:
                contents.append(content)

        if len(contents) < 2:
            return 0.5  # 单个证据，无法评估一致性

        # 计算内容相似性（简化版）
        common_keywords = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']

        relevance_scores = []
        for content in contents:
            words = content.split()
            if not words:
                continue

            non_common_words = [w for w in words if w not in common_keywords]
            relevance_scores.append(len(non_common_words) / len(words))

        if relevance_scores:
            avg_relevance = sum(relevance_scores) / len(relevance_scores)
            return min(avg_relevance, 1.0)

        return 0.5

    # 测试不同的证据场景
    test_scenarios = [
        {
            'name': 'Groundhog Day查询 - 无证据',
            'evidence': [],
            'description': '复杂的历史推理查询，无检索结果'
        },
        {
            'name': 'Groundhog Day查询 - 低质量证据',
            'evidence': [
                {'similarity': 0.4, 'content': 'Punxsutawney Phil is a groundhog in Pennsylvania'},
                {'similarity': 0.35, 'content': 'Washington D.C. is the capital of the United States'}
            ],
            'description': '检索到相关但相似度一般的证据'
        },
        {
            'name': 'Groundhog Day查询 - 高质量证据',
            'evidence': [
                {'similarity': 0.85, 'content': 'Punxsutawney Phil predicts weather in Pennsylvania'},
                {'similarity': 0.82, 'content': 'Washington D.C. is located in the District of Columbia'},
                {'similarity': 0.78, 'content': 'Groundhog Day tradition dates back to 1887'}
            ],
            'description': '检索到高质量的相关证据'
        },
        {
            'name': '简单查询 - 不相关证据',
            'evidence': [
                {'similarity': 0.15, 'content': 'Some random content about China'},
                {'similarity': 0.12, 'content': 'Unrelated legal information'}
            ],
            'description': '简单查询检索到完全不相关的证据'
        }
    ]

    print("🧪 RAG vs LLM直接回答模式决策测试")
    print("=" * 80)

    for scenario in test_scenarios:
        print(f"\n📋 测试场景: {scenario['name']}")
        print(f"   描述: {scenario['description']}")
        print(f"   证据数量: {len(scenario['evidence'])}")

        if scenario['evidence']:
            similarities = [e['similarity'] for e in scenario['evidence']]
            avg_similarity = sum(similarities) / len(similarities)
            print(".2f")

        # 评估质量
        quality_result = evaluate_evidence_quality(scenario['evidence'])

        decision = "🔄 使用RAG流程" if not quality_result['is_insufficient'] else "🤖 使用LLM直接回答"
        print(f"   决策: {decision}")
        print(f"   原因: {quality_result['reason']}")

        if quality_result.get('allow_rag_continue'):
            print("   ✅ 允许RAG流程继续，给推理引擎机会")

    print("\n" + "=" * 80)
    print("🎯 关键改进:")
    print("   - 放宽了证据质量阈值，避免复杂查询被误判")
    print("   - 即使证据质量不高，也给RAG流程机会")
    print("   - 只有在极端情况下才切换到LLM直接回答")
    print("   - Groundhog Day这样的复杂推理查询会继续走RAG流程")

async def test_with_rag_agent():
    """使用实际的RAG Agent进行测试"""
    try:
        from src.agents.rag_agent import RAGExpert

        print("\n🔧 测试实际RAG Agent决策逻辑...")
        rag_agent = RAGExpert()

        # 模拟Groundhog Day查询的上下文
        query = "How many years earlier would Punxsutawney Phil have to be canonically alive to have made a Groundhog Day prediction in the same state as the US capitol?"

        # 模拟不同的证据质量场景
        test_contexts = [
            {
                'name': '无证据场景',
                'context': {'query': query, 'evidence': []}
            },
            {
                'name': '低质量证据场景',
                'context': {
                    'query': query,
                    'evidence': [
                        {'similarity': 0.4, 'content': 'Punxsutawney Phil is in Pennsylvania'},
                        {'similarity': 0.35, 'content': 'US Capitol is in Washington D.C.'}
                    ]
                }
            }
        ]

        for test_case in test_contexts:
            print(f"\n🧪 测试: {test_case['name']}")

            # 调用RAG Agent的证据质量评估
            quality_result = rag_agent._evaluate_evidence_quality(test_case['context'].get('evidence', []))

            decision = "🔄 RAG流程" if not quality_result['is_insufficient'] else "🤖 LLM直接回答"
            print(f"   决策: {decision}")
            print(f"   原因: {quality_result['reason']}")

    except Exception as e:
        print(f"❌ RAG Agent测试失败: {e}")

if __name__ == "__main__":
    simulate_evidence_quality_evaluation()
    asyncio.run(test_with_rag_agent())
