#!/usr/bin/env python3
"""
训练数据批量处理工具

此脚本从收集的执行轨迹中批量提取和处理训练数据，用于ML模型训练。
"""
import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(dotenv_path=project_root / '.env')


def process_training_data():
    """处理训练数据"""
    print("=" * 80)
    print("训练数据批量处理工具")
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
    
    # 定义要处理的模型列表
    models_to_process = [
        "parallel_query_classifier",
        "deep_confidence_estimator",
        "logic_structure_parser",
        "fewshot_pattern_learner",
        "transformer_planner",
        "gnn_plan_optimizer"
    ]
    
    print(f"\n📋 准备处理 {len(models_to_process)} 个模型的训练数据...")
    
    # 处理每个模型的数据
    results = {}
    output_dir = project_root / "data" / "ml_training" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for model_name in models_to_process:
        print(f"\n{'='*80}")
        print(f"处理模型: {model_name}")
        print(f"{'='*80}")
        
        try:
            # 提取训练数据
            print(f"📊 提取训练数据...")
            training_data_result = data_collection.extract_training_data_for_model(
                model_name,
                max_samples=None  # 使用所有数据
            )
            
            training_data = training_data_result.get("training_data", [])
            labels = training_data_result.get("labels", [])
            metadata = training_data_result.get("metadata", {})
            
            print(f"   提取到 {len(training_data)} 条训练数据")
            print(f"   标签数: {len(labels)}")
            print(f"   元数据: {json.dumps(metadata, ensure_ascii=False, indent=2)}")
            
            if len(training_data) == 0:
                print(f"⚠️ 无训练数据，跳过")
                results[model_name] = {
                    "success": False,
                    "error": "No training data",
                    "data_count": 0
                }
                continue
            
            # 保存处理后的数据
            output_file = output_dir / f"{model_name}_training_data.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "model_name": model_name,
                    "training_data": training_data,
                    "labels": labels,
                    "metadata": metadata,
                    "data_count": len(training_data)
                }, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 数据已保存: {output_file}")
            
            results[model_name] = {
                "success": True,
                "data_count": len(training_data),
                "labels_count": len(labels),
                "output_file": str(output_file),
                "metadata": metadata
            }
                
        except Exception as e:
            print(f"❌ 处理过程出错: {e}")
            import traceback
            traceback.print_exc()
            results[model_name] = {
                "success": False,
                "error": str(e)
            }
    
    # 打印总结
    print(f"\n{'='*80}")
    print("处理完成总结")
    print(f"{'='*80}")
    
    success_count = sum(1 for r in results.values() if r.get("success", False))
    total_count = len(results)
    total_data = sum(r.get("data_count", 0) for r in results.values())
    
    print(f"\n📊 总体统计:")
    print(f"   总模型数: {total_count}")
    print(f"   成功处理: {success_count}")
    print(f"   失败: {total_count - success_count}")
    print(f"   总数据量: {total_data} 条")
    
    print(f"\n📋 详细结果:")
    for model_name, result in results.items():
        status = "✅" if result.get("success", False) else "❌"
        print(f"   {status} {model_name}: ", end="")
        if result.get("success"):
            print(f"成功 (数据: {result.get('data_count', 0)} 条)")
            print(f"      输出文件: {result.get('output_file', 'N/A')}")
        else:
            print(f"失败 - {result.get('error', 'Unknown error')}")
    
    # 保存处理报告
    report_path = output_dir / "processing_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": str(Path(__file__).stat().st_mtime),
            "results": results,
            "summary": {
                "total": total_count,
                "success": success_count,
                "failed": total_count - success_count,
                "total_data": total_data
            }
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 处理报告已保存: {report_path}")
    print(f"\n{'='*80}")
    print("✅ 训练数据处理完成！")
    print(f"{'='*80}")
    print(f"\n下一步:")
    print(f"1. 查看处理后的数据: ls -lh {output_dir}/*.json")
    print(f"2. 训练模型: python scripts/train_ml_models.py")
    print(f"3. 评估模型: python scripts/evaluate_ml_models.py")


if __name__ == "__main__":
    process_training_data()

