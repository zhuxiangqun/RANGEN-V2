#!/usr/bin/env python3
"""
ML系统集成测试

测试ML/RL系统的完整工作流：
1. 数据收集
2. 模型训练
3. 模型评估
4. 模型使用
"""
import sys
import os
import asyncio
import json
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(dotenv_path=project_root / '.env')


async def test_data_collection():
    """测试数据收集"""
    print("\n" + "=" * 80)
    print("测试1: 数据收集")
    print("=" * 80)
    
    try:
        from src.core.reasoning.engine import RealReasoningEngine
        engine = RealReasoningEngine()
        
        if not engine.data_collection_enabled:
            print("⚠️ 数据收集未启用")
            return False
        
        # 执行一个简单查询
        query = "Who was the first president of the United States?"
        context = {"query": query, "evidence": [], "knowledge": []}
        
        result = await engine.reason(query, context)
        
        print(f"✅ 数据收集测试通过")
        print(f"   查询: {query}")
        print(f"   结果: {result.success}")
        return True
    except Exception as e:
        print(f"❌ 数据收集测试失败: {e}")
        return False


def test_model_training():
    """测试模型训练"""
    print("\n" + "=" * 80)
    print("测试2: 模型训练")
    print("=" * 80)
    
    try:
        from src.core.reasoning.ml_framework.parallel_query_classifier import ParallelQueryClassifier
        
        classifier = ParallelQueryClassifier()
        
        # 准备测试数据
        training_data = [
            "Who was the first president and who was the second president?",
            "What is the capital of France?",
            "Who was the mother of Abraham Lincoln and who was his father?",
        ]
        labels = [True, False, True]
        
        # 训练
        result = classifier.train(training_data, labels)
        
        if result.get("success"):
            print(f"✅ 模型训练测试通过")
            print(f"   训练样本: {result.get('training_samples', 0)}")
            print(f"   准确率: {result.get('metrics', {}).get('accuracy', 0):.3f}")
            return True
        else:
            print(f"❌ 模型训练失败: {result.get('error', 'Unknown')}")
            return False
    except Exception as e:
        print(f"❌ 模型训练测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_prediction():
    """测试模型预测"""
    print("\n" + "=" * 80)
    print("测试3: 模型预测")
    print("=" * 80)
    
    try:
        from src.core.reasoning.ml_framework.parallel_query_classifier import ParallelQueryClassifier
        
        classifier = ParallelQueryClassifier()
        
        # 测试查询
        test_query = "Who was the first president and who was the second president?"
        result = classifier.predict(test_query)
        
        print(f"✅ 模型预测测试通过")
        print(f"   查询: {test_query}")
        print(f"   是否并行: {result.get('is_parallel', False)}")
        print(f"   置信度: {result.get('confidence', 0):.3f}")
        return True
    except Exception as e:
        print(f"❌ 模型预测测试失败: {e}")
        return False


def test_model_save_load():
    """测试模型保存和加载"""
    print("\n" + "=" * 80)
    print("测试4: 模型保存和加载")
    print("=" * 80)
    
    try:
        from src.core.reasoning.ml_framework.parallel_query_classifier import ParallelQueryClassifier
        
        # 训练模型
        classifier = ParallelQueryClassifier()
        training_data = [
            "Who was the first president and who was the second president?",
            "What is the capital of France?",
        ]
        labels = [True, False]
        classifier.train(training_data, labels)
        
        # 保存模型
        model_dir = project_root / "data" / "ml_models" / "test"
        model_dir.mkdir(parents=True, exist_ok=True)
        model_path = model_dir / "test_classifier.pkl"
        
        if classifier.save_model(str(model_path)):
            print(f"✅ 模型保存成功: {model_path}")
        else:
            print(f"❌ 模型保存失败")
            return False
        
        # 加载模型
        new_classifier = ParallelQueryClassifier()
        if new_classifier.load_model(str(model_path)):
            print(f"✅ 模型加载成功")
            
            # 测试预测
            result = new_classifier.predict("test query")
            if result:
                print(f"✅ 加载的模型可以正常预测")
                return True
            else:
                print(f"❌ 加载的模型无法预测")
                return False
        else:
            print(f"❌ 模型加载失败")
            return False
    except Exception as e:
        print(f"❌ 模型保存/加载测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """运行所有测试"""
    print("=" * 80)
    print("ML系统集成测试")
    print("=" * 80)
    
    results = {}
    
    # 测试1: 数据收集
    results["data_collection"] = await test_data_collection()
    
    # 测试2: 模型训练
    results["model_training"] = test_model_training()
    
    # 测试3: 模型预测
    results["model_prediction"] = test_model_prediction()
    
    # 测试4: 模型保存/加载
    results["model_save_load"] = test_model_save_load()
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n   总测试数: {total}")
    print(f"   通过: {passed}")
    print(f"   失败: {total - passed}")
    
    print(f"\n   详细结果:")
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"      {status} {test_name}")
    
    # 保存测试报告
    report_path = project_root / "data" / "ml_models" / "integration_test_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": str(Path(__file__).stat().st_mtime),
            "results": results,
            "summary": {
                "total": total,
                "passed": passed,
                "failed": total - passed
            }
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 测试报告已保存: {report_path}")
    print(f"\n{'='*80}")
    
    if passed == total:
        print("✅ 所有测试通过！")
    else:
        print(f"⚠️  {total - passed} 个测试失败")
    
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(run_all_tests())

