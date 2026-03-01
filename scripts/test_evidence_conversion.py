#!/usr/bin/env python3
"""
测试证据转换 - 验证修复后的证据转换逻辑
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.chdir(project_root)

# 设置环境变量
os.environ.setdefault('PYTHONPATH', project_root)

from src.core.reasoning.models import Evidence
from src.core.reasoning.evidence_processor import EvidenceProcessor
from src.utils.research_logger import log_info

async def test_evidence_conversion():
    """测试证据转换逻辑"""
    print("="*80)
    print("测试证据转换逻辑")
    print("="*80)
    
    processor = EvidenceProcessor()
    
    # 模拟检索结果（来自实际检索）
    knowledge_items = [
        {
            'content': 'Harriet Rebecca Lane Johnston (May 9, 1830 – July 3, 1903) acted as first lady of the United States during the administration of her uncle, president James Buchanan, from 1857 to 1861.',
            'source': 'faiss',
            'confidence': 0.7,
            'similarity': 0.7,
            'metadata': {}
        },
        {
            'content': 'James Buchanan was the 15th president of the United States.',
            'source': 'faiss',
            'confidence': 0.7,
            'similarity': 0.7,
            'metadata': {}
        },
        {
            'content': 'Short text',  # 测试短文本过滤
            'source': 'faiss',
            'confidence': 0.05,  # 测试低confidence过滤
            'similarity': 0.05,
            'metadata': {}
        }
    ]
    
    query = 'Who was the 15th first lady of the United States?'
    context = {'knowledge': knowledge_items}
    query_analysis = {'type': 'factual'}
    
    print(f"\n测试查询: {query}")
    print(f"知识项数量: {len(knowledge_items)}")
    print(f"\n开始证据转换...")
    
    # 调用gather_evidence
    evidence_list = await processor.gather_evidence(query, context, query_analysis)
    
    print(f"\n转换结果:")
    print(f"  证据数量: {len(evidence_list)}")
    
    for i, ev in enumerate(evidence_list, 1):
        print(f"\n证据 {i}:")
        print(f"  content长度: {len(ev.content)}")
        print(f"  confidence: {ev.confidence}")
        print(f"  relevance_score: {ev.relevance_score}")
        print(f"  source: {ev.source}")
        print(f"  content预览: {ev.content[:100]}...")
    
    # 验证结果
    if len(evidence_list) >= 2:
        print(f"\n✅ 测试通过: 成功转换了 {len(evidence_list)} 条证据")
        print(f"   预期: 至少2条证据（前两条应该通过，第三条应该被过滤）")
        return True
    else:
        print(f"\n❌ 测试失败: 只转换了 {len(evidence_list)} 条证据")
        print(f"   预期: 至少2条证据")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_evidence_conversion())
    sys.exit(0 if result else 1)

