#!/usr/bin/env python3
"""
收集ML训练数据

此脚本运行推理引擎处理查询，自动收集执行轨迹用于ML模型训练。
"""
import sys
import os
import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 🚀 修复：确保加载.env文件中的环境变量（包括API密钥）
load_dotenv(dotenv_path=project_root / '.env')


# 测试查询列表
TEST_QUERIES = [
    # 简单查询
    "Who was the first president of the United States?",
    "What is the capital of France?",
    "When was the Declaration of Independence signed?",
    
    # 关系查询
    "Who was the mother of Abraham Lincoln?",
    "What was the maiden name of the mother of the second assassinated president?",
    
    # 序数查询
    "Who was the 15th first lady of the United States?",
    "Who was the 31st first lady of the United States?",
    
    # 复合查询
    "If my future wife has the same first name as the 15th first lady's mother and her surname is the same as the second assassinated president's mother's maiden name, what is my future wife's name?",
    
    # 多步推理
    "Who was the mother of the 31st first lady of the United States?",
    "What was the maiden name of the mother of the second assassinated president of the United States?",
]


async def collect_data_for_query(engine, query: str, query_index: int) -> Dict[str, Any]:
    """为单个查询收集数据"""
    print(f"\n{'='*80}")
    print(f"处理查询 {query_index + 1}/{len(TEST_QUERIES)}")
    print(f"{'='*80}")
    print(f"查询: {query}")
    print(f"{'='*80}\n")
    
    try:
        # 准备上下文
        context = {
            'query': query,
            'evidence': [],
            'knowledge': []
        }
        
        # 执行推理
        result = await engine.reason(query, context)
        
        # 返回结果摘要
        return {
            'query': query,
            'success': result.success if hasattr(result, 'success') else False,
            'final_answer': result.final_answer if hasattr(result, 'final_answer') else '',
            'processing_time': result.processing_time if hasattr(result, 'processing_time') else 0.0,
            'num_steps': len(result.reasoning_steps) if hasattr(result, 'reasoning_steps') else 0,
            'total_confidence': result.total_confidence if hasattr(result, 'total_confidence') else 0.0
        }
        
    except Exception as e:
        print(f"❌ 处理查询失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            'query': query,
            'success': False,
            'error': str(e)
        }


async def main():
    """主函数"""
    print("=" * 80)
    print("ML训练数据收集脚本")
    print("=" * 80)
    
    # 检查配置
    config_file = project_root / "config" / "ml_training_config.json"
    if not config_file.exists():
        print(f"\n❌ 配置文件不存在: {config_file}")
        print(f"   请先运行: python scripts/enable_ml_data_collection.py")
        return
    
    print(f"\n✅ 配置文件存在: {config_file}")
    
    # 初始化推理引擎
    print(f"\n🔧 初始化推理引擎...")
    try:
        from src.core.reasoning.engine import RealReasoningEngine
        engine = RealReasoningEngine()
        
        # 检查数据收集是否启用
        if not hasattr(engine, 'data_collection_enabled') or not engine.data_collection_enabled:
            print(f"\n⚠️ 数据收集未启用")
            print(f"   请检查配置文件: {config_file}")
            print(f"   确保 'data_collection_enabled' 设置为 true")
            return
        
        print(f"✅ 推理引擎已初始化")
        print(f"✅ 数据收集已启用: {engine.data_collection_enabled}")
        
    except Exception as e:
        print(f"\n❌ 推理引擎初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 处理查询
    print(f"\n📊 开始处理 {len(TEST_QUERIES)} 个查询...")
    print(f"   数据将自动收集到: data/ml_training/")
    
    results = []
    for i, query in enumerate(TEST_QUERIES):
        result = await collect_data_for_query(engine, query, i)
        results.append(result)
        
        # 显示结果摘要
        status = "✅" if result.get('success', False) else "❌"
        print(f"\n{status} 查询 {i+1} 完成")
        if result.get('success'):
            print(f"   答案: {result.get('final_answer', '')[:60]}...")
            print(f"   步骤数: {result.get('num_steps', 0)}")
            print(f"   处理时间: {result.get('processing_time', 0):.2f}秒")
            print(f"   置信度: {result.get('total_confidence', 0):.2f}")
        else:
            print(f"   错误: {result.get('error', 'Unknown error')}")
        
        # 短暂延迟，避免API限流
        if i < len(TEST_QUERIES) - 1:
            await asyncio.sleep(2)
    
    # 统计结果
    print(f"\n{'='*80}")
    print("收集完成统计")
    print(f"{'='*80}")
    
    success_count = sum(1 for r in results if r.get('success', False))
    total_time = sum(r.get('processing_time', 0) for r in results)
    total_steps = sum(r.get('num_steps', 0) for r in results)
    
    print(f"\n📊 总体统计:")
    print(f"   总查询数: {len(results)}")
    print(f"   成功: {success_count}")
    print(f"   失败: {len(results) - success_count}")
    print(f"   总处理时间: {total_time:.2f}秒")
    print(f"   平均处理时间: {total_time/len(results):.2f}秒")
    print(f"   总步骤数: {total_steps}")
    print(f"   平均步骤数: {total_steps/len(results):.1f}")
    
    # 检查数据文件
    data_dir = project_root / "data" / "ml_training"
    if data_dir.exists():
        jsonl_files = list(data_dir.glob("*.jsonl"))
        if jsonl_files:
            latest_file = max(jsonl_files, key=lambda p: p.stat().st_mtime)
            print(f"\n💾 数据文件:")
            print(f"   最新文件: {latest_file.name}")
            
            # 统计记录数
            with open(latest_file, 'r', encoding='utf-8') as f:
                record_count = sum(1 for _ in f)
            print(f"   记录数: {record_count}")
    
    print(f"\n{'='*80}")
    print("✅ 数据收集完成！")
    print(f"{'='*80}")
    print(f"\n下一步:")
    print(f"1. 查看收集的数据: python scripts/monitor_data_collection.py")
    print(f"2. 查看数据文件: ls -lh data/ml_training/*.jsonl")
    print(f"3. 继续收集更多数据（运行此脚本多次）")


if __name__ == "__main__":
    asyncio.run(main())

