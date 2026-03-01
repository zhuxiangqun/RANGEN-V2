#!/usr/bin/env python3
"""
监控数据收集状态

实时监控数据收集情况，显示统计信息和最新数据。
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_data_files(data_dir: Path):
    """加载所有JSONL文件"""
    jsonl_files = list(data_dir.glob("*.jsonl"))
    all_records = []
    
    for file in jsonl_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        record = json.loads(line)
                        record['_source_file'] = file.name
                        record['_line_num'] = line_num
                        all_records.append(record)
                    except json.JSONDecodeError as e:
                        print(f"⚠️ {file.name}:{line_num} JSON解析错误: {e}")
        except Exception as e:
            print(f"❌ 读取文件失败 {file.name}: {e}")
    
    return all_records


def analyze_data(records):
    """分析数据"""
    if not records:
        return {
            "total_records": 0,
            "date_range": None,
            "success_rate": 0.0,
            "avg_confidence": 0.0,
            "avg_plan_quality": 0.0,
            "avg_step_correctness": 0.0,
            "parallel_opportunities": 0,
            "queries_by_type": {},
            "recent_queries": []
        }
    
    # 基本统计
    total_records = len(records)
    
    # 日期范围
    timestamps = [r.get('timestamp', '') for r in records if r.get('timestamp')]
    date_range = None
    if timestamps:
        dates = [datetime.fromisoformat(ts) for ts in timestamps if ts]
        if dates:
            date_range = (min(dates), max(dates))
    
    # 成功率
    success_count = sum(
        1 for r in records
        if r.get('final_result', {}).get('success', False)
    )
    success_rate = success_count / total_records if total_records > 0 else 0.0
    
    # 平均置信度
    confidences = [
        r.get('auto_labels', {}).get('confidence', 0.0)
        for r in records
        if r.get('auto_labels', {}).get('confidence') is not None
    ]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    
    # 平均计划质量
    plan_qualities = [
        r.get('auto_labels', {}).get('plan_quality', 0.0)
        for r in records
        if r.get('auto_labels', {}).get('plan_quality') is not None
    ]
    avg_plan_quality = sum(plan_qualities) / len(plan_qualities) if plan_qualities else 0.0
    
    # 平均步骤正确性
    step_correctness = [
        r.get('auto_labels', {}).get('step_correctness', 0.0)
        for r in records
        if r.get('auto_labels', {}).get('step_correctness') is not None
    ]
    avg_step_correctness = sum(step_correctness) / len(step_correctness) if step_correctness else 0.0
    
    # 并行机会
    parallel_opportunities = sum(
        1 for r in records
        if r.get('auto_labels', {}).get('parallel_opportunities', 0.0) > 0.5
    )
    
    # 查询类型分布（从查询文本推断）
    queries_by_type = defaultdict(int)
    for r in records:
        query = r.get('query', '').lower()
        if 'first lady' in query or 'president' in query:
            queries_by_type['historical'] += 1
        elif 'mother' in query or 'father' in query or 'maiden name' in query:
            queries_by_type['relationship'] += 1
        elif 'and' in query or 'both' in query:
            queries_by_type['composite'] += 1
        else:
            queries_by_type['other'] += 1
    
    # 最近的查询
    recent_queries = sorted(
        records,
        key=lambda r: r.get('timestamp', ''),
        reverse=True
    )[:10]
    
    return {
        "total_records": total_records,
        "date_range": date_range,
        "success_rate": success_rate,
        "avg_confidence": avg_confidence,
        "avg_plan_quality": avg_plan_quality,
        "avg_step_correctness": avg_step_correctness,
        "parallel_opportunities": parallel_opportunities,
        "queries_by_type": dict(queries_by_type),
        "recent_queries": [
            {
                "query": r.get('query', '')[:60] + '...' if len(r.get('query', '')) > 60 else r.get('query', ''),
                "timestamp": r.get('timestamp', ''),
                "success": r.get('final_result', {}).get('success', False),
                "confidence": r.get('auto_labels', {}).get('confidence', 0.0)
            }
            for r in recent_queries
        ]
    }


def display_statistics(stats):
    """显示统计信息"""
    print("=" * 80)
    print("数据收集统计")
    print("=" * 80)
    
    print(f"\n📊 总体统计:")
    print(f"   总记录数: {stats['total_records']}")
    
    if stats['date_range']:
        start_date, end_date = stats['date_range']
        print(f"   日期范围: {start_date.strftime('%Y-%m-%d %H:%M')} ~ {end_date.strftime('%Y-%m-%d %H:%M')}")
    
    print(f"\n📈 质量指标:")
    print(f"   成功率: {stats['success_rate']:.1%}")
    print(f"   平均置信度: {stats['avg_confidence']:.2f}")
    print(f"   平均计划质量: {stats['avg_plan_quality']:.2f}")
    print(f"   平均步骤正确性: {stats['avg_step_correctness']:.2f}")
    print(f"   并行机会样本: {stats['parallel_opportunities']}")
    
    if stats['queries_by_type']:
        print(f"\n📋 查询类型分布:")
        for query_type, count in stats['queries_by_type'].items():
            print(f"   {query_type}: {count}")
    
    if stats['recent_queries']:
        print(f"\n🕐 最近10条查询:")
        for i, query_info in enumerate(stats['recent_queries'], 1):
            status = "✅" if query_info['success'] else "❌"
            print(f"   {i}. {status} [{query_info['confidence']:.2f}] {query_info['query']}")
            print(f"      时间: {query_info['timestamp']}")


def main():
    """主函数"""
    data_dir = project_root / "data" / "ml_training"
    
    if not data_dir.exists():
        print(f"❌ 数据目录不存在: {data_dir}")
        print(f"   请先运行系统收集数据，或运行: python scripts/enable_ml_data_collection.py")
        return
    
    # 加载数据
    print(f"📂 加载数据文件...")
    records = load_data_files(data_dir)
    
    if not records:
        print(f"\n⚠️ 未找到任何数据记录")
        print(f"   请运行系统处理查询以收集数据")
        return
    
    # 分析数据
    print(f"📊 分析数据...")
    stats = analyze_data(records)
    
    # 显示统计信息
    display_statistics(stats)
    
    # 目标进度
    target_records = 100
    current_records = stats['total_records']
    progress = min(100, (current_records / target_records) * 100)
    
    print(f"\n🎯 收集目标进度:")
    print(f"   当前: {current_records} / {target_records} ({progress:.1f}%)")
    if current_records < target_records:
        remaining = target_records - current_records
        print(f"   还需: {remaining} 条记录")
    
    print(f"\n{'=' * 80}")


if __name__ == "__main__":
    main()

