#!/usr/bin/env python3
"""
PageIndex 完整流程脚本

功能:
1. 从 parasail-ai/frames-benchmark-wikipedia 加载数据
2. 保存为 Markdown 文件
3. 使用 PageIndex 索引
4. 测试检索效果

使用:
    python scripts/pageindex_frames_benchmark.py
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置日志
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """主流程"""
    
    print("=" * 60)
    print("PageIndex 索引流程 - frames-benchmark-wikipedia")
    print("=" * 60)
    
    # 1. 检查依赖
    print("\n[1/4] 检查依赖...")
    
    deps_ok = True
    
    # 检查 datasets
    try:
        from datasets import load_dataset
        print("  ✅ datasets")
    except ImportError:
        print("  ❌ datasets - 请运行: pip install datasets")
        deps_ok = False
    
    # 检查 pypdf (可选)
    try:
        import pypdf
        print("  ✅ pypdf")
    except ImportError:
        print("  ⚠️  pypdf - 可选，pip install pypdf")
    
    if not deps_ok:
        print("\n❌ 缺少必要依赖，流程终止")
        return
    
    # 2. 初始化PageIndex
    print("\n[2/4] 初始化PageIndex...")
    
    from src.kms.pageindex import PageIndex, PageIndexConfig
    
    config = PageIndexConfig(
        index_storage_path="./data/pageindex",
        model=os.getenv("LLM_MODEL", "deepseek-chat"),
        max_pages_per_node=10,
        max_tokens_per_node=20000,
        add_node_summary=True,
        add_doc_description=True
    )
    
    pageindex = PageIndex(config)
    print("  ✅ PageIndex 初始化完成")
    
    # 3. 加载并索引数据
    print("\n[3/4] 加载并索引数据...")
    print("  数据集: parasail-ai/frames-benchmark-wikipedia")
    print("  说明: 已包含完整Wikipedia文章内容，无需抓取")
    
    from src.kms.web_crawler import get_wiki_indexer
    
    indexer = get_wiki_indexer(pageindex, output_dir="./data/wiki_content")
    
    # 索引数据 (先测试10条)
    print("\n  开始索引 (全部数据)...")
    
    result = await indexer.index_from_dataset(
        "parasail-ai/frames-benchmark-wikipedia",
        link_field="link",
        content_field="text",
        title_field="title",
        max_items=None  # 索引全部数据
    )
    
    print(f"\n  索引结果:")
    print(f"    总数: {result['total']}")
    print(f"    成功: {result['success']}")
    print(f"    失败: {result['failed']}")
    print(f"    来源: {result['source']}")
    
    if result['errors']:
        print(f"    错误: {result['errors'][:3]}")
    
    # 4. 测试检索
    print("\n[4/4] 测试检索...")
    
    # 测试问题 (来自 frames-benchmark)
    test_questions = [
        "Who is the President of the United States?",
        "What company did Barack Obama work for?",
        "When was Python programming language created?"
    ]
    
    for question in test_questions:
        print(f"\n  问题: {question}")
        
        results = await pageindex.retrieve(question, top_k=2)
        
        for i, r in enumerate(results):
            print(f"\n  结果 {i+1}:")
            print(f"    标题: {r.title}")
            print(f"    页面: {r.page_range}")
            print(f"    内容: {r.content[:200]}...")
            print(f"    推理: {r.reasoning}")
    
    print("\n" + "=" * 60)
    print("✅ 流程完成!")
    print("=" * 60)
    
    # 建议下一步
    print("""
下一步:
1. 如果测试效果OK，扩大索引范围:
   max_items=None  # 索引全部2520条

2. 集成到RANGEN系统:
   from src.kms.unified_retrieval import UnifiedRetrieval

3. 通过MCP暴露工具:
   from src.kms.pageindex_mcp import get_pageindex_mcp_tools
""")


if __name__ == "__main__":
    asyncio.run(main())
