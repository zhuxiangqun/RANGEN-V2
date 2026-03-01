#!/usr/bin/env python3
"""
诊断脚本：检查核心系统的知识检索和提示词生成内容

用法：
  python scripts/diagnose_knowledge_and_prompt.py --query "What is the capital of France?"
"""

import os
import json
import argparse
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 确保能够导入 src 下的模块
PROJECT_ROOT = Path(__file__).resolve().parents[1]
import sys
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.real_reasoning_engine import RealReasoningEngine
from src.agents.enhanced_knowledge_retrieval_agent import EnhancedKnowledgeRetrievalAgent


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_knowledge_item(index: int, item: Dict[str, Any]):
    """打印知识项"""
    print(f"\n[知识项 {index + 1}]")
    # 尝试多种可能的字段名
    content = (item.get('content', '') or 
              item.get('text', '') or 
              item.get('data', '') or
              str(item.get('result', '')))
    
    if content and len(content.strip()) > 0:
        print(f"  内容: {content[:200]}...")
        print(f"  内容长度: {len(content)} 字符")
    else:
        print(f"  ⚠️  内容为空或未找到")
        print(f"  可用字段: {list(item.keys())}")
    
    # 尝试多种可能的相似度字段
    similarity = (item.get('similarity_score', 0) or 
                 item.get('similarity', 0) or 
                 item.get('score', 0) or 0.0)
    print(f"  相似度: {similarity:.3f}")
    
    source = (item.get('source', '') or 
             item.get('metadata', {}).get('source', 'unknown'))
    print(f"  来源: {source}")
    
    if 'metadata' in item and item['metadata']:
        print(f"  元数据: {json.dumps(item['metadata'], ensure_ascii=False, indent=2)[:200]}")


async def diagnose_knowledge_retrieval(query: str):
    """诊断知识检索"""
    print_section("1. 知识检索诊断")
    print(f"查询: {query}")
    
    try:
        # 使用知识检索智能体
        agent = EnhancedKnowledgeRetrievalAgent()
        result = await agent.execute({"query": query})
        
        if hasattr(result, 'success') and result.success:
            data = result.data
            if isinstance(data, dict):
                sources = data.get('sources', [])
                print(f"\n✅ 检索成功，找到 {len(sources)} 条知识")
                
                for i, source in enumerate(sources[:5]):  # 只显示前5条
                    print_knowledge_item(i, source)
                    # 详细检查内容
                    content = source.get('content', '') or source.get('text', '')
                    if not content or len(content.strip()) < 5:
                        print(f"  ⚠️  警告：内容为空或过短")
                    else:
                        print(f"  ✅ 内容长度: {len(content)} 字符")
                        print(f"  ✅ 内容预览: {content[:200]}")
                
                # 检查知识相关性
                print("\n[相关性分析]")
                relevant_count = 0
                for source in sources:
                    score = source.get('similarity_score', source.get('score', 0))
                    if score > 0.5:
                        relevant_count += 1
                
                print(f"  高相关性知识 (>0.5): {relevant_count}/{len(sources)}")
                if relevant_count == 0:
                    print("  ⚠️  警告：没有高相关性知识，可能影响答案质量")
            else:
                print(f"⚠️  返回数据格式异常: {type(data)}")
        else:
            print("❌ 知识检索失败")
            if hasattr(result, 'error'):
                print(f"  错误: {result.error}")
    
    except Exception as e:
        print(f"❌ 知识检索异常: {e}")
        import traceback
        traceback.print_exc()


async def diagnose_prompt_generation(query: str):
    """诊断提示词生成"""
    print_section("2. 提示词生成诊断")
    print(f"查询: {query}")
    
    try:
        # 创建推理引擎
        engine = RealReasoningEngine()
        
        # 模拟上下文
        context = {}
        
        # 获取查询类型
        query_type = engine._analyze_query_type_with_ml(query)
        print(f"\n查询类型: {query_type}")
        
        # 模拟证据收集
        evidence_list = []
        try:
            evidence_list = await engine._gather_evidence(query, context, {'type': query_type})
            print(f"\n证据数量: {len(evidence_list)}")
            
            if evidence_list:
                print("\n[证据内容预览]")
                for i, ev in enumerate(evidence_list[:3]):  # 只显示前3条
                    content = ev.content if hasattr(ev, 'content') else str(ev)
                    print(f"  证据 {i+1}: {content[:150]}...")
        except Exception as e:
            print(f"⚠️  证据收集失败: {e}")
        
        # 生成提示词
        evidence_text = ""
        if evidence_list:
            evidence_text = "\n".join([
                ev.content if hasattr(ev, 'content') else str(ev)
                for ev in evidence_list[:5]
            ])
        
        # 生成提示词
        template_name = "reasoning_with_evidence" if evidence_text else "reasoning_without_evidence"
        prompt = engine._generate_optimized_prompt(
            template_name=template_name,
            query=query,
            evidence=evidence_text,
            query_type=query_type,
            enhanced_context={}
        )
        
        print(f"\n✅ 提示词生成成功")
        print(f"  模板: {template_name}")
        print(f"  提示词长度: {len(prompt)} 字符")
        
        # 检查提示词内容
        print("\n[提示词内容检查]")
        checks = [
            ("包含查询", query in prompt),
            ("包含证据" if evidence_text else "无证据模式", evidence_text[:50] in prompt if evidence_text else True),
            ("包含格式要求", "ANSWER FORMAT" in prompt or "格式" in prompt),
            ("包含推理步骤", "Reasoning Process" in prompt or "推理" in prompt),
        ]
        
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"  {status} {check_name}: {check_result}")
        
        # 检查提示词中是否包含证据
        print("\n[提示词内容验证]")
        if evidence_text:
            if evidence_text[:100] in prompt:
                print(f"  ✅ 证据已正确插入提示词")
                # 找到证据在提示词中的位置
                evidence_pos = prompt.find(evidence_text[:50])
                if evidence_pos > 0:
                    print(f"  ✅ 证据位置: 第 {evidence_pos} 字符")
                    print(f"  ✅ 证据前文: {prompt[max(0, evidence_pos-100):evidence_pos]}")
                    print(f"  ✅ 证据内容: {prompt[evidence_pos:evidence_pos+200]}...")
            else:
                print(f"  ❌ 警告：证据未正确插入提示词")
                print(f"  证据内容: {evidence_text[:200]}...")
                print(f"  提示词中查找: {evidence_text[:50] in prompt}")
        
        # 检查查询是否在提示词中
        if query in prompt:
            print(f"  ✅ 查询已正确插入提示词")
        else:
            print(f"  ❌ 警告：查询未正确插入提示词")
        
        # 显示提示词预览
        print("\n[提示词预览 (前800字符)]")
        print(prompt[:800])
        print("...")
        
        # 显示提示词末尾
        if len(prompt) > 800:
            print("\n[提示词末尾 (最后300字符)]")
            print("...")
            print(prompt[-300:])
    
    except Exception as e:
        print(f"❌ 提示词生成异常: {e}")
        import traceback
        traceback.print_exc()


async def diagnose_full_flow(query: str):
    """诊断完整流程"""
    print_section("3. 完整流程诊断")
    print(f"查询: {query}")
    
    try:
        # 创建推理引擎
        engine = RealReasoningEngine()
        
        # 执行推理
        context = {}
        result = await engine.reason(query, context)
        
        print(f"\n✅ 推理完成")
        print(f"  最终答案: {result.final_answer}")
        print(f"  推理类型: {result.reasoning_type}")
        print(f"  置信度: {result.confidence}")
        
        if hasattr(result, 'reasoning_steps') and result.reasoning_steps:
            print(f"\n推理步骤数: {len(result.reasoning_steps)}")
            for i, step in enumerate(result.reasoning_steps[:3]):
                print(f"  步骤 {i+1}: {step.get('type', 'unknown')} - {step.get('description', '')[:50]}")
    
    except Exception as e:
        print(f"❌ 完整流程异常: {e}")
        import traceback
        traceback.print_exc()


async def main():
    parser = argparse.ArgumentParser(description="诊断知识检索和提示词生成")
    parser.add_argument("--query", type=str, required=True, help="测试查询")
    parser.add_argument("--full", action="store_true", help="执行完整流程诊断")
    
    args = parser.parse_args()
    
    print("🔍 开始诊断...")
    print(f"查询: {args.query}")
    
    # 1. 知识检索诊断
    await diagnose_knowledge_retrieval(args.query)
    
    # 2. 提示词生成诊断
    await diagnose_prompt_generation(args.query)
    
    # 3. 完整流程诊断（可选）
    if args.full:
        await diagnose_full_flow(args.query)
    
    print("\n" + "=" * 80)
    print("✅ 诊断完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
