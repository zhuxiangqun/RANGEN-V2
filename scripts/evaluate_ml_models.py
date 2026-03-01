#!/usr/bin/env python3
"""
评估ML模型性能

此脚本评估已训练的ML模型在测试数据上的性能。
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


def evaluate_all_models():
    """评估所有ML模型"""
    print("=" * 80)
    print("ML模型性能评估脚本")
    print("=" * 80)
    
    # 检查模型目录
    model_dir = project_root / "data" / "ml_models"
    if not model_dir.exists():
        print(f"\n❌ 模型目录不存在: {model_dir}")
        print(f"   请先运行训练脚本: python scripts/train_ml_models.py")
        return
    
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
    
    # 初始化推理引擎
    try:
        from src.core.reasoning.engine import RealReasoningEngine
        engine = RealReasoningEngine()
        print(f"✅ 推理引擎已初始化")
    except Exception as e:
        print(f"\n❌ 推理引擎初始化失败: {e}")
        return
    
    # 定义要评估的模型列表
    models_to_evaluate = [
        {
            "name": "parallel_query_classifier",
            "component": engine.step_generator.parallel_classifier if hasattr(engine, 'step_generator') and engine.step_generator and hasattr(engine.step_generator, 'parallel_classifier') else None,
            "model_path": model_dir / "parallel_query_classifier.pkl",
            "description": "并行查询分类器"
        },
        {
            "name": "deep_confidence_estimator",
            "component": engine.deep_confidence_estimator if hasattr(engine, 'deep_confidence_estimator') else None,
            "model_path": model_dir / "deep_confidence_estimator.pkl",
            "description": "深度置信度评估器"
        },
        {
            "name": "logic_structure_parser",
            "component": engine.step_generator.logic_parser if hasattr(engine, 'step_generator') and engine.step_generator and hasattr(engine.step_generator, 'logic_parser') else None,
            "model_path": model_dir / "logic_structure_parser.pkl",
            "description": "逻辑结构解析器"
        },
        {
            "name": "fewshot_pattern_learner",
            "component": engine.step_generator.fewshot_learner if hasattr(engine, 'step_generator') and engine.step_generator and hasattr(engine.step_generator, 'fewshot_learner') else None,
            "model_path": model_dir / "fewshot_pattern_learner.pkl",
            "description": "少样本模式学习器"
        },
        {
            "name": "transformer_planner",
            "component": engine.step_generator.transformer_planner if hasattr(engine, 'step_generator') and engine.step_generator and hasattr(engine.step_generator, 'transformer_planner') else None,
            "model_path": model_dir / "transformer_planner.pkl",
            "description": "Transformer计划生成器"
        },
        {
            "name": "gnn_plan_optimizer",
            "component": engine.step_generator.gnn_optimizer if hasattr(engine, 'step_generator') and engine.step_generator and hasattr(engine.step_generator, 'gnn_optimizer') else None,
            "model_path": model_dir / "gnn_plan_optimizer.pkl",
            "description": "GNN计划优化器"
        }
    ]
    
    print(f"\n📋 准备评估 {len(models_to_evaluate)} 个模型...")
    
    # 评估每个模型
    results = {}
    for model_info in models_to_evaluate:
        model_name = model_info["name"]
        component = model_info["component"]
        model_path = model_info["model_path"]
        description = model_info["description"]
        
        print(f"\n{'='*80}")
        print(f"评估模型: {description} ({model_name})")
        print(f"{'='*80}")
        
        if component is None:
            print(f"⚠️ 组件未启用，跳过")
            results[model_name] = {"success": False, "error": "Component not enabled"}
            continue
        
        if not model_path.exists():
            print(f"⚠️ 模型文件不存在: {model_path}")
            print(f"   请先训练模型: python scripts/train_ml_models.py")
            results[model_name] = {"success": False, "error": "Model file not found"}
            continue
        
        try:
            # 加载模型
            print(f"📥 加载模型...")
            if not component.load_model(str(model_path)):
                print(f"❌ 模型加载失败")
                results[model_name] = {"success": False, "error": "Model load failed"}
                continue
            
            print(f"✅ 模型已加载")
            
            # 提取测试数据（使用20%作为测试集）
            print(f"📊 提取测试数据...")
            training_data_result = data_collection.extract_training_data_for_model(
                model_name,
                max_samples=None  # 使用所有数据
            )
            
            all_data = training_data_result.get("training_data", [])
            all_labels = training_data_result.get("labels", [])
            
            if len(all_data) < 10:
                print(f"⚠️ 测试数据不足（需要至少 10 条，实际 {len(all_data)} 条），跳过")
                results[model_name] = {
                    "success": False,
                    "error": f"Insufficient test data: {len(all_data)} < 10",
                    "data_count": len(all_data)
                }
                continue
            
            # 分割训练集和测试集（80/20）
            split_idx = int(len(all_data) * 0.8)
            test_data = all_data[split_idx:]
            test_labels = all_labels[split_idx:] if all_labels else None
            
            print(f"   测试集大小: {len(test_data)} 条")
            
            # 评估模型
            print(f"🔍 开始评估...")
            if test_labels:
                evaluation_result = component.evaluate(test_data, test_labels)
            else:
                # 如果没有标签，进行预测测试
                print(f"   无标签数据，进行预测测试...")
                predictions = []
                for data in test_data[:10]:  # 只测试前10条
                    try:
                        if model_name == "parallel_query_classifier":
                            pred = component.predict(data)
                        elif model_name == "deep_confidence_estimator":
                            pred = component.predict(data)
                        else:
                            pred = component.predict(data)
                        predictions.append(pred)
                    except Exception as e:
                        print(f"   预测失败: {e}")
                
                evaluation_result = {
                    "test_samples": len(predictions),
                    "predictions": len(predictions),
                    "note": "No labels available, prediction test only"
                }
            
            print(f"✅ 评估完成！")
            print(f"   评估结果: {json.dumps(evaluation_result, ensure_ascii=False, indent=2)}")
            
            results[model_name] = {
                "success": True,
                "evaluation_result": evaluation_result,
                "test_data_count": len(test_data),
                "model_path": str(model_path)
            }
                
        except Exception as e:
            print(f"❌ 评估过程出错: {e}")
            import traceback
            traceback.print_exc()
            results[model_name] = {
                "success": False,
                "error": str(e)
            }
    
    # 打印总结
    print(f"\n{'='*80}")
    print("评估完成总结")
    print(f"{'='*80}")
    
    success_count = sum(1 for r in results.values() if r.get("success", False))
    total_count = len(results)
    
    print(f"\n📊 总体统计:")
    print(f"   总模型数: {total_count}")
    print(f"   成功评估: {success_count}")
    print(f"   失败: {total_count - success_count}")
    
    print(f"\n📋 详细结果:")
    for model_name, result in results.items():
        status = "✅" if result.get("success", False) else "❌"
        print(f"   {status} {model_name}: ", end="")
        if result.get("success"):
            eval_result = result.get("evaluation_result", {})
            print(f"成功 (测试数据: {result.get('test_data_count', 0)} 条)")
            # 打印关键指标
            if "accuracy" in eval_result:
                print(f"      准确率: {eval_result['accuracy']:.3f}")
            if "mse" in eval_result:
                print(f"      MSE: {eval_result['mse']:.4f}")
            if "f1" in eval_result or "f1_score" in eval_result:
                f1 = eval_result.get("f1") or eval_result.get("f1_score", 0)
                print(f"      F1: {f1:.3f}")
        else:
            print(f"失败 - {result.get('error', 'Unknown error')}")
    
    # 保存评估报告
    report_path = project_dir / "data" / "ml_models" / "evaluation_report.json"
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
    
    print(f"\n💾 评估报告已保存: {report_path}")
    print(f"\n{'='*80}")
    print("✅ 模型评估完成！")
    print(f"{'='*80}")


if __name__ == "__main__":
    evaluate_all_models()

