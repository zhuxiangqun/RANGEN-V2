#!/usr/bin/env python3
"""
批量训练ML模型

此脚本从收集的执行轨迹中提取训练数据，并批量训练所有ML组件。
"""
import sys
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(dotenv_path=project_root / '.env')


async def train_all_models():
    """训练所有ML模型"""
    print("=" * 80)
    print("ML模型批量训练脚本")
    print("=" * 80)
    
    # 检查数据收集目录
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
    
    # 初始化推理引擎（用于获取ML组件）
    try:
        from src.core.reasoning.engine import RealReasoningEngine
        engine = RealReasoningEngine()
        print(f"✅ 推理引擎已初始化")
    except Exception as e:
        print(f"\n❌ 推理引擎初始化失败: {e}")
        return
    
    # 定义要训练的模型列表
    models_to_train = [
        {
            "name": "parallel_query_classifier",
            "component": engine.step_generator.parallel_classifier if hasattr(engine, 'step_generator') and engine.step_generator and hasattr(engine.step_generator, 'parallel_classifier') else None,
            "min_samples": 50,
            "description": "并行查询分类器"
        },
        {
            "name": "deep_confidence_estimator",
            "component": engine.deep_confidence_estimator if hasattr(engine, 'deep_confidence_estimator') else None,
            "min_samples": 50,
            "description": "深度置信度评估器"
        },
        {
            "name": "logic_structure_parser",
            "component": engine.step_generator.logic_parser if hasattr(engine, 'step_generator') and engine.step_generator and hasattr(engine.step_generator, 'logic_parser') else None,
            "min_samples": 50,
            "description": "逻辑结构解析器"
        },
        {
            "name": "fewshot_pattern_learner",
            "component": engine.step_generator.fewshot_learner if hasattr(engine, 'step_generator') and engine.step_generator and hasattr(engine.step_generator, 'fewshot_learner') else None,
            "min_samples": 50,
            "description": "少样本模式学习器"
        },
        {
            "name": "transformer_planner",
            "component": engine.step_generator.transformer_planner if hasattr(engine, 'step_generator') and engine.step_generator and hasattr(engine.step_generator, 'transformer_planner') else None,
            "min_samples": 30,
            "description": "Transformer计划生成器"
        },
        {
            "name": "gnn_plan_optimizer",
            "component": engine.step_generator.gnn_optimizer if hasattr(engine, 'step_generator') and engine.step_generator and hasattr(engine.step_generator, 'gnn_optimizer') else None,
            "min_samples": 30,
            "description": "GNN计划优化器"
        }
    ]
    
    print(f"\n📋 准备训练 {len(models_to_train)} 个模型...")
    
    # 训练每个模型
    results = {}
    for model_info in models_to_train:
        model_name = model_info["name"]
        component = model_info["component"]
        min_samples = model_info["min_samples"]
        description = model_info["description"]
        
        print(f"\n{'='*80}")
        print(f"训练模型: {description} ({model_name})")
        print(f"{'='*80}")
        
        if component is None:
            print(f"⚠️ 组件未启用，跳过")
            results[model_name] = {"success": False, "error": "Component not enabled"}
            continue
        
        try:
            # 提取训练数据
            print(f"📊 提取训练数据...")
            training_data_result = data_collection.extract_training_data_for_model(
                model_name,
                max_samples=min_samples * 3  # 提取更多数据
            )
            
            training_data = training_data_result.get("training_data", [])
            labels = training_data_result.get("labels", [])
            metadata = training_data_result.get("metadata", {})
            
            print(f"   提取到 {len(training_data)} 条训练数据")
            print(f"   元数据: {json.dumps(metadata, ensure_ascii=False, indent=2)}")
            
            # 🚀 改进：对于并行查询分类器，使用数据增强
            if model_name == "parallel_query_classifier" and len(training_data) > 0:
                try:
                    from src.core.reasoning.ml_framework.data_augmentation import DataAugmentation
                    augmenter = DataAugmentation()
                    training_data, labels = augmenter.augment_parallel_queries(
                        training_data,
                        labels,
                        target_ratio=0.1  # 目标正样本比例10%
                    )
                    print(f"   ✅ 数据增强后: {len(training_data)} 条训练数据")
                except Exception as e:
                    print(f"   ⚠️ 数据增强失败: {e}，使用原始数据")
            
            if len(training_data) < min_samples:
                print(f"⚠️ 训练数据不足（需要至少 {min_samples} 条，实际 {len(training_data)} 条），跳过")
                results[model_name] = {
                    "success": False,
                    "error": f"Insufficient data: {len(training_data)} < {min_samples}",
                    "data_count": len(training_data)
                }
                continue
            
            # 训练模型
            print(f"🚀 开始训练...")
            training_result = component.train(training_data, labels if labels else None)
            
            if training_result.get("success", False):
                print(f"✅ 训练成功！")
                print(f"   训练结果: {json.dumps(training_result, ensure_ascii=False, indent=2)}")
                
                # 保存模型
                model_dir = project_root / "data" / "ml_models"
                model_dir.mkdir(parents=True, exist_ok=True)
                model_path = model_dir / f"{model_name}.pkl"
                
                if component.save_model(str(model_path)):
                    print(f"✅ 模型已保存: {model_path}")
                    results[model_name] = {
                        "success": True,
                        "training_result": training_result,
                        "model_path": str(model_path),
                        "data_count": len(training_data)
                    }
                else:
                    print(f"⚠️ 模型保存失败")
                    results[model_name] = {
                        "success": True,
                        "training_result": training_result,
                        "model_path": None,
                        "data_count": len(training_data),
                        "warning": "Model save failed"
                    }
            else:
                print(f"❌ 训练失败: {training_result.get('error', 'Unknown error')}")
                results[model_name] = {
                    "success": False,
                    "error": training_result.get("error", "Unknown error"),
                    "data_count": len(training_data)
                }
                
        except Exception as e:
            print(f"❌ 训练过程出错: {e}")
            import traceback
            traceback.print_exc()
            results[model_name] = {
                "success": False,
                "error": str(e)
            }
    
    # 打印总结
    print(f"\n{'='*80}")
    print("训练完成总结")
    print(f"{'='*80}")
    
    success_count = sum(1 for r in results.values() if r.get("success", False))
    total_count = len(results)
    
    print(f"\n📊 总体统计:")
    print(f"   总模型数: {total_count}")
    print(f"   成功: {success_count}")
    print(f"   失败: {total_count - success_count}")
    
    print(f"\n📋 详细结果:")
    for model_name, result in results.items():
        status = "✅" if result.get("success", False) else "❌"
        print(f"   {status} {model_name}: ", end="")
        if result.get("success"):
            print(f"成功 (数据: {result.get('data_count', 0)} 条)")
            if result.get("model_path"):
                print(f"      模型路径: {result['model_path']}")
        else:
            print(f"失败 - {result.get('error', 'Unknown error')}")
    
    # 保存训练报告
    report_path = project_root / "data" / "ml_models" / "training_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": str(Path(__file__).stat().st_mtime),
            "results": results,
            "summary": {
                "total": total_count,
                "success": success_count,
                "failed": total_count - success_count
            }
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 训练报告已保存: {report_path}")
    print(f"\n{'='*80}")
    print("✅ 批量训练完成！")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(train_all_models())

