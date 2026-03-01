#!/usr/bin/env python3
"""
测试数据收集功能

运行此脚本来验证数据收集管道是否正常工作。
"""
import sys
import os
import asyncio
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.reasoning.ml_framework.data_collection import DataCollectionPipeline


def create_mock_trace() -> dict:
    """创建模拟的执行轨迹用于测试"""
    return {
        "query": "Who was the 15th first lady of the United States?",
        "plan": {
            "steps": [
                {
                    "type": "evidence_gathering",
                    "description": "Find the 15th first lady",
                    "sub_query": "Who was the 15th first lady of the United States?",
                    "depends_on": [],
                    "parallel_group": None
                },
                {
                    "type": "evidence_gathering",
                    "description": "Find the mother's name",
                    "sub_query": "What was the first name of the mother of [result from step 1]?",
                    "depends_on": [1],
                    "parallel_group": None
                }
            ]
        },
        "execution": [
            {
                "step_index": 0,
                "sub_query": "Who was the 15th first lady of the United States?",
                "answer": "Harriet Rebecca Lane Johnston",
                "evidence_count": 3,
                "step_failed": False,
                "answer_recovered": False
            },
            {
                "step_index": 1,
                "sub_query": "What was the first name of the mother of Harriet Rebecca Lane Johnston?",
                "answer": "Jane",
                "evidence_count": 2,
                "step_failed": False,
                "answer_recovered": False
            }
        ],
        "result": {
            "final_answer": "Jane",
            "total_confidence": 0.85,
            "success": True
        },
        "metrics": {
            "processing_time": 12.5,
            "step_times": {"step_0": 5.2, "step_1": 4.8},
            "total_steps": 2,
            "failed_steps": 0,
            "evidence_count": 5
        }
    }


def test_data_collection():
    """测试数据收集功能"""
    print("=" * 80)
    print("测试数据收集功能")
    print("=" * 80)
    
    # 初始化数据收集管道
    storage_path = "data/ml_training/test"
    pipeline = DataCollectionPipeline(storage_path=storage_path)
    
    print(f"\n✅ 数据收集管道已初始化")
    print(f"   存储路径: {storage_path}")
    
    # 创建并收集多个模拟轨迹
    print(f"\n📊 开始收集模拟数据...")
    num_traces = 5
    
    for i in range(num_traces):
        trace = create_mock_trace()
        # 修改查询以创建不同的样本
        trace["query"] = f"Test query {i+1}: {trace['query']}"
        pipeline.collect_execution_trace(trace)
        print(f"   ✅ 已收集轨迹 {i+1}/{num_traces}")
    
    # 检查缓冲区
    print(f"\n📦 缓冲区状态:")
    print(f"   缓冲区大小: {len(pipeline.collection_buffer)}")
    print(f"   标注队列大小: {len(pipeline.annotation_queue)}")
    
    # 手动保存缓冲区
    print(f"\n💾 保存数据...")
    pipeline._save_buffer()
    
    # 检查保存的文件
    storage_dir = Path(storage_path)
    if storage_dir.exists():
        jsonl_files = list(storage_dir.glob("*.jsonl"))
        print(f"\n✅ 数据已保存")
        print(f"   找到 {len(jsonl_files)} 个JSONL文件")
        
        if jsonl_files:
            latest_file = max(jsonl_files, key=lambda p: p.stat().st_mtime)
            print(f"   最新文件: {latest_file.name}")
            
            # 读取并显示第一条记录
            with open(latest_file, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                if first_line:
                    record = json.loads(first_line)
                    print(f"\n📄 第一条记录预览:")
                    print(f"   查询: {record.get('query', '')[:60]}...")
                    print(f"   时间戳: {record.get('timestamp', '')}")
                    print(f"   计划步骤数: {len(record.get('generated_plan', {}).get('steps', []))}")
                    print(f"   执行步骤数: {len(record.get('execution_steps', []))}")
                    print(f"   最终结果: {record.get('final_result', {}).get('success', False)}")
                    
                    # 显示自动标注结果
                    auto_labels = record.get('auto_labels', {})
                    if auto_labels:
                        print(f"\n🏷️  自动标注结果:")
                        print(f"   计划质量: {auto_labels.get('plan_quality', 0):.2f}")
                        print(f"   步骤正确性: {auto_labels.get('step_correctness', 0):.2f}")
                        print(f"   并行机会: {auto_labels.get('parallel_opportunities', 0):.2f}")
                        print(f"   重试有效性: {auto_labels.get('retry_effectiveness', 0):.2f}")
                        print(f"   整体置信度: {auto_labels.get('confidence', 0):.2f}")
    
    # 测试标注队列
    annotation_queue = pipeline.get_annotation_queue()
    if annotation_queue:
        print(f"\n📋 人工标注队列:")
        print(f"   队列大小: {len(annotation_queue)}")
        print(f"   这些样本的自动标注置信度较低，需要人工审核")
    
    print(f"\n{'=' * 80}")
    print("✅ 测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    test_data_collection()

