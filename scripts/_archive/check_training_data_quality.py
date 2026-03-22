#!/usr/bin/env python3
"""
训练数据质量检查工具

检查收集的训练数据质量：
- 数据量统计
- 数据分布
- 数据完整性
- 标注质量
"""
import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, List
from collections import Counter
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(dotenv_path=project_root / '.env')


def check_data_quality():
    """检查训练数据质量"""
    print("=" * 80)
    print("训练数据质量检查")
    print("=" * 80)
    
    # 检查数据目录
    data_dir = project_root / "data" / "ml_training"
    if not data_dir.exists():
        print(f"\n❌ 数据目录不存在: {data_dir}")
        print(f"   请先运行数据收集脚本: python scripts/collect_ml_training_data.py")
        return
    
    # 初始化数据收集管道
    try:
        from src.core.reasoning.ml_framework.data_collection import DataCollectionPipeline
        data_collection = DataCollectionPipeline(storage_path=str(data_dir))
        print(f"\n✅ 数据收集管道已初始化")
    except Exception as e:
        print(f"\n❌ 数据收集管道初始化失败: {e}")
        return
    
    # 加载所有数据
    all_traces = []
    
    # 从缓冲区加载
    all_traces.extend(data_collection.collection_buffer)
    
    # 从文件加载
    jsonl_files = list(data_dir.glob("execution_traces_*.jsonl"))
    for file_path in jsonl_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        trace = json.loads(line)
                        all_traces.append(trace)
        except Exception as e:
            print(f"⚠️ 加载文件失败 {file_path}: {e}")
    
    if not all_traces:
        print(f"\n📭 没有找到训练数据")
        print(f"   请先运行数据收集脚本: python scripts/collect_ml_training_data.py")
        return
    
    print(f"\n📊 总体统计:")
    print(f"   总轨迹数: {len(all_traces)}")
    print(f"   数据文件数: {len(jsonl_files)}")
    
    # 检查数据完整性
    print(f"\n🔍 数据完整性检查:")
    
    required_fields = ["query", "generated_plan", "execution_steps", "final_result"]
    missing_fields = {field: 0 for field in required_fields}
    
    for trace in all_traces:
        for field in required_fields:
            if field not in trace or not trace[field]:
                missing_fields[field] += 1
    
    for field, count in missing_fields.items():
        if count > 0:
            print(f"   ⚠️  {field}: {count} 条记录缺失 ({count/len(all_traces)*100:.1f}%)")
        else:
            print(f"   ✅ {field}: 完整")
    
    # 检查执行结果
    print(f"\n📈 执行结果统计:")
    success_count = sum(1 for t in all_traces if t.get("final_result", {}).get("success", False))
    failed_count = len(all_traces) - success_count
    
    print(f"   成功: {success_count} ({success_count/len(all_traces)*100:.1f}%)")
    print(f"   失败: {failed_count} ({failed_count/len(all_traces)*100:.1f}%)")
    
    # 检查步骤统计
    print(f"\n📋 步骤统计:")
    step_counts = [len(t.get("generated_plan", {}).get("steps", [])) for t in all_traces]
    if step_counts:
        print(f"   平均步骤数: {sum(step_counts)/len(step_counts):.1f}")
        print(f"   最少步骤数: {min(step_counts)}")
        print(f"   最多步骤数: {max(step_counts)}")
    
    # 检查自动标注
    print(f"\n🏷️  自动标注统计:")
    annotated_count = sum(1 for t in all_traces if "auto_labels" in t)
    print(f"   已标注: {annotated_count} ({annotated_count/len(all_traces)*100:.1f}%)")
    
    if annotated_count > 0:
        confidences = [t.get("auto_labels", {}).get("confidence", 0) for t in all_traces if "auto_labels" in t]
        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
            print(f"   平均标注置信度: {avg_confidence:.3f}")
            low_confidence_count = sum(1 for c in confidences if c < 0.7)
            print(f"   低置信度样本: {low_confidence_count} ({low_confidence_count/len(confidences)*100:.1f}%)")
    
    # 检查每个模型的数据质量
    print(f"\n📦 各模型数据质量:")
    
    models = [
        "parallel_query_classifier",
        "deep_confidence_estimator",
        "logic_structure_parser",
        "fewshot_pattern_learner",
        "transformer_planner",
        "gnn_plan_optimizer"
    ]
    
    for model_name in models:
        try:
            result = data_collection.extract_training_data_for_model(model_name, max_samples=None)
            training_data = result.get("training_data", [])
            labels = result.get("labels", [])
            metadata = result.get("metadata", {})
            
            print(f"\n   {model_name}:")
            print(f"      数据量: {len(training_data)} 条")
            print(f"      标签数: {len(labels)} 条")
            
            if metadata:
                for key, value in metadata.items():
                    if isinstance(value, (int, float)):
                        print(f"      {key}: {value}")
                    elif isinstance(value, dict):
                        print(f"      {key}: {json.dumps(value, ensure_ascii=False)}")
        except Exception as e:
            print(f"   ⚠️  {model_name}: 检查失败 - {e}")
    
    # 生成质量报告
    quality_report = {
        "total_traces": len(all_traces),
        "data_files": len(jsonl_files),
        "missing_fields": missing_fields,
        "success_rate": success_count / len(all_traces) if all_traces else 0,
        "annotated_rate": annotated_count / len(all_traces) if all_traces else 0,
        "avg_steps": sum(step_counts) / len(step_counts) if step_counts else 0,
        "model_data_counts": {}
    }
    
    for model_name in models:
        try:
            result = data_collection.extract_training_data_for_model(model_name, max_samples=None)
            quality_report["model_data_counts"][model_name] = {
                "data_count": len(result.get("training_data", [])),
                "labels_count": len(result.get("labels", []))
            }
        except:
            pass
    
    # 保存质量报告
    report_path = data_dir / "quality_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(quality_report, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 质量报告已保存: {report_path}")
    print(f"\n{'='*80}")
    print("✅ 数据质量检查完成！")
    print(f"{'='*80}")


if __name__ == "__main__":
    check_data_quality()

