#!/usr/bin/env python3
"""
生成模型性能报告

从多个来源收集数据，生成综合的模型性能报告。
"""
import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(dotenv_path=project_root / '.env')


def generate_performance_report():
    """生成综合性能报告"""
    print("=" * 80)
    print("生成模型性能报告")
    print("=" * 80)
    
    model_dir = project_root / "data" / "ml_models"
    model_dir.mkdir(parents=True, exist_ok=True)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "models": {},
        "summary": {}
    }
    
    # 1. 收集训练报告
    training_report_path = model_dir / "training_report.json"
    if training_report_path.exists():
        try:
            with open(training_report_path, 'r', encoding='utf-8') as f:
                training_report = json.load(f)
            report["training"] = training_report
            print(f"✅ 已加载训练报告")
        except Exception as e:
            print(f"⚠️ 加载训练报告失败: {e}")
    
    # 2. 收集评估报告
    eval_report_path = model_dir / "evaluation_report.json"
    if eval_report_path.exists():
        try:
            with open(eval_report_path, 'r', encoding='utf-8') as f:
                eval_report = json.load(f)
            report["evaluation"] = eval_report
            print(f"✅ 已加载评估报告")
        except Exception as e:
            print(f"⚠️ 加载评估报告失败: {e}")
    
    # 3. 收集健康报告
    health_report_path = model_dir / "health_report.json"
    if health_report_path.exists():
        try:
            with open(health_report_path, 'r', encoding='utf-8') as f:
                health_report = json.load(f)
            report["health"] = health_report
            print(f"✅ 已加载健康报告")
        except Exception as e:
            print(f"⚠️ 加载健康报告失败: {e}")
    
    # 4. 收集性能监控数据
    performance_dir = model_dir / "performance"
    if performance_dir.exists():
        performance_files = list(performance_dir.glob("performance_*.jsonl"))
        if performance_files:
            latest_file = max(performance_files, key=lambda p: p.stat().st_mtime)
            try:
                from src.core.reasoning.ml_framework.model_performance_monitor import ModelPerformanceMonitor
                monitor = ModelPerformanceMonitor(storage_path=str(performance_dir))
                performance_report = monitor.get_performance_report()
                report["performance"] = performance_report
                print(f"✅ 已加载性能监控数据")
            except Exception as e:
                print(f"⚠️ 加载性能监控数据失败: {e}")
    
    # 5. 收集模型文件信息
    model_files = list(model_dir.glob("*.pkl"))
    model_info = {}
    for model_file in model_files:
        model_name = model_file.stem
        model_info[model_name] = {
            "file_size_kb": model_file.stat().st_size / 1024,
            "modified_time": datetime.fromtimestamp(model_file.stat().st_mtime).isoformat()
        }
    report["model_files"] = model_info
    print(f"✅ 已收集 {len(model_files)} 个模型文件信息")
    
    # 6. 生成综合摘要
    summary = {
        "total_models": len(model_files),
        "trained_models": 0,
        "evaluated_models": 0,
        "healthy_models": 0,
        "total_training_samples": 0,
        "total_evaluation_samples": 0
    }
    
    if "training" in report and "results" in report["training"]:
        summary["trained_models"] = sum(1 for r in report["training"]["results"].values() if r.get("success"))
        summary["total_training_samples"] = sum(r.get("data_count", 0) for r in report["training"]["results"].values())
    
    if "evaluation" in report and "results" in report["evaluation"]:
        summary["evaluated_models"] = sum(1 for r in report["evaluation"]["results"].values() if r.get("success"))
        summary["total_evaluation_samples"] = sum(r.get("test_data_count", 0) for r in report["evaluation"]["results"].values())
    
    if "health" in report and "summary" in report["health"]:
        summary["healthy_models"] = report["health"]["summary"].get("healthy", 0)
    
    report["summary"] = summary
    
    # 7. 保存报告
    report_path = model_dir / "performance_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*80}")
    print("性能报告摘要")
    print(f"{'='*80}")
    print(f"\n   总模型数: {summary['total_models']}")
    print(f"   已训练: {summary['trained_models']}")
    print(f"   已评估: {summary['evaluated_models']}")
    print(f"   健康: {summary['healthy_models']}")
    print(f"   总训练样本: {summary['total_training_samples']}")
    print(f"   总评估样本: {summary['total_evaluation_samples']}")
    
    print(f"\n💾 性能报告已保存: {report_path}")
    print(f"\n{'='*80}")
    print("✅ 报告生成完成！")
    print(f"{'='*80}")


if __name__ == "__main__":
    generate_performance_report()

