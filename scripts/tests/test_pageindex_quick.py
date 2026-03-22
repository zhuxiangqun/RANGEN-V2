#!/usr/bin/env python3
"""
快速测试 PageIndex 检索效果

不需要下载完整数据集，直接测试现有功能
"""

import asyncio
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 创建测试用的Markdown文件
TEST_DIR = Path("./data/test_wiki")
TEST_DIR.mkdir(parents=True, exist_ok=True)

# 创建测试文档
TEST_DOCS = [
    {
        "filename": "president.md",
        "title": "President of the United States",
        "content": """# President of the United States

The President of the United States (POTUS) is the head of state and head of government of the United States.

## Current President

Joe Biden is the current President of the United States, inaugurated on January 20, 2021.

## Qualifications

According to the U.S. Constitution, the president must:
- Be at least 35 years old
- Be a natural-born citizen
- Have resided in the United States for at least 14 years

## Term

The president serves a four-year term and can be elected for at most two terms.
"""
    },
    {
        "filename": "obama.md", 
        "title": "Barack Obama",
        "content": """# Barack Obama

Barack Obama is an American politician and attorney who served as the 44th President of the United States.

## Early Career

Before becoming president, Obama worked as:
- A community organizer in Chicago
- A civil rights attorney
- A state senator in Illinois
- A United States Senator

## Presidency

Obama was elected President in 2008 and re-elected in 2012. During his presidency, he worked on:
- Healthcare reform (Obamacare)
- Economic recovery from the 2008 financial crisis
- Climate change initiatives

## Post-Presidency

After leaving office, Obama has remained active in public life and continues to engage in political discussions.
"""
    },
    {
        "filename": "python.md",
        "title": "Python Programming Language",
        "content": """# Python Programming Language

Python is a high-level, general-purpose programming language.

## History

Python was created by Guido van Rossum and first released in 1991. The name Python comes from Monty Python, not the snake.

## Features

Python is known for:
- Easy-to-read syntax
- Dynamic typing
- Automatic memory management
- Extensive standard library

## Versions

- Python 2.0 was released in 2000
- Python 3.0 was released in 2008
- The latest version is Python 3.12 (2023)

## Use Cases

Python is widely used in:
- Web development
- Data science and machine learning
- Automation and scripting
- Scientific computing
"""
    }
]

async def main():
    print("=" * 60)
    print("PageIndex 快速测试")
    print("=" * 60)
    
    # 1. 创建测试文件
    print("\n[1/3] 创建测试文档...")
    for doc in TEST_DOCS:
        path = TEST_DIR / doc["filename"]
        path.write_text(doc["content"], encoding="utf-8")
        print(f"  ✅ {doc['filename']}")
    
    # 2. 初始化PageIndex并索引
    print("\n[2/3] 初始化PageIndex...")
    
    from src.kms.pageindex import PageIndex, PageIndexConfig
    
    config = PageIndexConfig(
        index_storage_path="./data/test_pageindex"
    )
    pageindex = PageIndex(config)
    
    # 索引所有测试文档
    for doc in TEST_DOCS:
        path = TEST_DIR / doc["filename"]
        await pageindex.index_document(
            str(path),
            doc["title"]
        )
        print(f"  ✅ 已索引: {doc['title']}")
    
    # 3. 测试检索
    print("\n[3/3] 测试检索...")
    
    test_questions = [
        ("谁是现任美国总统?", "president"),
        ("Barack Obama 之前做什么工作?", "obama"),
        ("Python 是哪一年创建的?", "python"),
    ]
    
    for question, expected_keyword in test_questions:
        print(f"\n  问题: {question}")
        
        results = await pageindex.retrieve(question, top_k=2)
        
        if results:
            r = results[0]
            print(f"  ✅ 最佳结果:")
            print(f"     标题: {r.title}")
            print(f"     页面: {r.page_range}")
            print(f"     内容: {r.content[:150]}...")
            
            # 检查是否包含关键词
            if expected_keyword.lower() in r.content.lower():
                print(f"     ✅ 包含关键词: {expected_keyword}")
            else:
                print(f"     ⚠️ 未找到关键词: {expected_keyword}")
        else:
            print(f"  ❌ 未找到结果")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print("=" * 60)
    
    print("""
下一步 - 索引真实Wikipedia数据:
    
1. 安装依赖:
   pip install datasets

2. 运行完整脚本:
   python scripts/pageindex_frames_benchmark.py
   
3. 或直接使用:
   from src.kms.web_crawler import get_wiki_indexer
   from src.kms.pageindex import PageIndex

   indexer = get_wiki_indexer(PageIndex())
   await indexer.index_from_dataset(
       "parasail-ai/frames-benchmark-wikipedia",
       max_items=100  # 先测试100条
   )
""")

if __name__ == "__main__":
    asyncio.run(main())
