#!/usr/bin/env python3
"""
模型使用统计工具

统计模型在实际使用中的情况：
- 使用频率
- 预测次数
- 平均响应时间
- 成功率
"""
import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(dotenv_path=project_root / '.env')


def collect_usage_stats():
    """收集使用统计"""
    print("=" * 80)
    print("模型使用统计")
    print("=" * 80)
    
    performance_dir = project_root / "data" / "ml_models" / "performance"
    
    if not performance_dir.exists():
        print(f"\n⚠️ 性能数据目录不存在: {performance_dir}")
        print(f"   模型使用统计需要性能监控数据")
        return
    
    # 收集所有性能数据
    performance_files = list(performance_dir.glob("performance_*.jsonl"))
    
    if not performance_files:
        print(f"\n📭 没有找到性能数据文件")
        return
    
    print(f"\n📊 找到 {len(performance_files)} 个性能数据文件")
    
    # 统计每个模型的使用情况
    model_stats = defaultdict(lambda: {
        "total_predictions": 0,
        "total_time": 0.0,
        "correct_predictions": 0,
        "total_with_ground_truth": 0,
        "errors": 0
    })
    
    for file_path in performance_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        model_name = record.get("model_name", "unknown")
                        
                        stats = model_stats[model_name]
                        stats["total_predictions"] += 1
                        stats["total_time"] += record.get("execution_time", 0.0)
                        
                        if record.get("has_ground_truth"):
                            stats["total_with_ground_truth"] += 1
                            if record.get("is_correct"):
                                stats["correct_predictions"] += 1
                        
                        if record.get("errors"):
                            stats["errors"] += 1
        except Exception as e:
            print(f"⚠️ 读取文件失败 {file_path}: {e}")
    
    if not model_stats:
        print(f"\n📭 没有找到使用数据")
        return
    
    # 计算统计指标
    print(f"\n📈 模型使用统计:\n")
    
    for model_name, stats in sorted(model_stats.items()):
        total = stats["total_predictions"]
        avg_time = stats["total_time"] / total if total > 0 else 0.0
        
        print(f"   {model_name}:")
        print(f"      总预测次数: {total}")
        print(f"      平均响应时间: {avg_time * 1000:.2f} ms")
        
        if stats["total_with_ground_truth"] > 0:
            accuracy = stats["correct_predictions"] / stats["total_with_ground_truth"]
            print(f"      准确率: {accuracy * 100:.1f}% ({stats['correct_predictions']}/{stats['total_with_ground_truth']})")
        
        if stats["errors"] > 0:
            error_rate = stats["errors"] / total
            print(f"      错误率: {error_rate * 100:.1f}% ({stats['errors']}/{total})")
        
        print()
    
    # 保存统计报告
    stats_report = {
        "timestamp": str(Path(__file__).stat().st_mtime),
        "model_stats": dict(model_stats),
        "summary": {
            "total_models": len(model_stats),
            "total_predictions": sum(s["total_predictions"] for s in model_stats.values())
        }
    }
    
    report_path = project_root / "data" / "ml_models" / "usage_stats.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(stats_report, f, ensure_ascii=False, indent=2)
    
    print(f"💾 使用统计已保存: {report_path}")
    print(f"\n{'='*80}")
    print("✅ 统计完成！")
    print(f"{'='*80}")


if __name__ == "__main__":
    collect_usage_stats()

