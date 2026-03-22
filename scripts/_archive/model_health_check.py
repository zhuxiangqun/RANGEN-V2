#!/usr/bin/env python3
"""
模型健康检查工具

检查所有ML模型的健康状态：
- 模型文件是否存在
- 模型是否可以加载
- 模型是否可以预测
- 模型性能指标
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


def check_model_health(model_name: str, component) -> Dict[str, Any]:
    """检查单个模型的健康状态"""
    health_status = {
        "model_name": model_name,
        "file_exists": False,
        "can_load": False,
        "can_predict": False,
        "is_trained": False,
        "errors": []
    }
    
    model_dir = project_root / "data" / "ml_models"
    model_path = model_dir / f"{model_name}.pkl"
    
    # 检查文件是否存在
    if model_path.exists():
        health_status["file_exists"] = True
        health_status["file_size"] = model_path.stat().st_size / 1024  # KB
    else:
        health_status["errors"].append("模型文件不存在")
        return health_status
    
    # 检查是否可以加载
    try:
        if component and hasattr(component, 'load_model'):
            if component.load_model(str(model_path)):
                health_status["can_load"] = True
                health_status["is_trained"] = getattr(component, 'is_trained', False)
            else:
                health_status["errors"].append("模型加载失败")
        else:
            health_status["errors"].append("组件不支持加载")
    except Exception as e:
        health_status["errors"].append(f"加载异常: {str(e)}")
    
    # 检查是否可以预测
    if health_status["can_load"]:
        try:
            # 使用测试数据
            if model_name == "parallel_query_classifier":
                test_query = "Who was the first president and who was the second president?"
                result = component.predict(test_query)
                if result and "is_parallel" in result:
                    health_status["can_predict"] = True
            elif model_name == "deep_confidence_estimator":
                test_data = {
                    "query": "test",
                    "answer": "test answer",
                    "evidence": [],
                    "context": {}
                }
                result = component.predict(test_data)
                if result and "prediction" in result:
                    health_status["can_predict"] = True
            else:
                # 通用测试
                test_input = "test query"
                result = component.predict(test_input)
                if result:
                    health_status["can_predict"] = True
        except Exception as e:
            health_status["errors"].append(f"预测异常: {str(e)}")
    
    return health_status


def check_all_models():
    """检查所有模型"""
    print("=" * 80)
    print("模型健康检查")
    print("=" * 80)
    
    # 初始化推理引擎
    try:
        from src.core.reasoning.engine import RealReasoningEngine
        engine = RealReasoningEngine()
        print(f"\n✅ 推理引擎已初始化")
    except Exception as e:
        print(f"\n❌ 推理引擎初始化失败: {e}")
        return
    
    # 定义要检查的模型
    models_to_check = [
        {
            "name": "parallel_query_classifier",
            "component": engine.step_generator.parallel_classifier if hasattr(engine, 'step_generator') and engine.step_generator and hasattr(engine.step_generator, 'parallel_classifier') else None
        },
        {
            "name": "deep_confidence_estimator",
            "component": engine.deep_confidence_estimator if hasattr(engine, 'deep_confidence_estimator') else None
        },
        {
            "name": "logic_structure_parser",
            "component": engine.step_generator.logic_parser if hasattr(engine, 'step_generator') and engine.step_generator and hasattr(engine.step_generator, 'logic_parser') else None
        },
        {
            "name": "fewshot_pattern_learner",
            "component": engine.step_generator.fewshot_learner if hasattr(engine, 'step_generator') and engine.step_generator and hasattr(engine.step_generator, 'fewshot_learner') else None
        },
        {
            "name": "transformer_planner",
            "component": engine.step_generator.transformer_planner if hasattr(engine, 'step_generator') and engine.step_generator and hasattr(engine.step_generator, 'transformer_planner') else None
        },
        {
            "name": "gnn_plan_optimizer",
            "component": engine.step_generator.gnn_optimizer if hasattr(engine, 'step_generator') and engine.step_generator and hasattr(engine.step_generator, 'gnn_optimizer') else None
        }
    ]
    
    print(f"\n📋 检查 {len(models_to_check)} 个模型...\n")
    
    results = []
    for model_info in models_to_check:
        model_name = model_info["name"]
        component = model_info["component"]
        
        print(f"🔍 检查: {model_name}")
        health = check_model_health(model_name, component)
        results.append(health)
        
        # 显示结果
        status_icon = "✅" if all([health["file_exists"], health["can_load"], health["can_predict"]]) else "❌"
        print(f"   {status_icon} 文件存在: {health['file_exists']}")
        if health["file_exists"]:
            print(f"      文件大小: {health.get('file_size', 0):.2f} KB")
        print(f"   {'✅' if health['can_load'] else '❌'} 可以加载: {health['can_load']}")
        print(f"   {'✅' if health['is_trained'] else '❌'} 已训练: {health['is_trained']}")
        print(f"   {'✅' if health['can_predict'] else '❌'} 可以预测: {health['can_predict']}")
        
        if health["errors"]:
            print(f"   ⚠️  错误:")
            for error in health["errors"]:
                print(f"      - {error}")
        print()
    
    # 生成报告
    healthy_count = sum(1 for r in results if all([r["file_exists"], r["can_load"], r["can_predict"]]))
    total_count = len(results)
    
    print(f"{'='*80}")
    print("健康检查总结")
    print(f"{'='*80}")
    print(f"\n   总模型数: {total_count}")
    print(f"   健康: {healthy_count}")
    print(f"   不健康: {total_count - healthy_count}")
    
    # 保存报告
    report_path = project_root / "data" / "ml_models" / "health_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": str(Path(__file__).stat().st_mtime),
            "results": results,
            "summary": {
                "total": total_count,
                "healthy": healthy_count,
                "unhealthy": total_count - healthy_count
            }
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 健康报告已保存: {report_path}")
    print(f"\n{'='*80}")
    print("✅ 健康检查完成！")
    print(f"{'='*80}")


if __name__ == "__main__":
    check_all_models()

