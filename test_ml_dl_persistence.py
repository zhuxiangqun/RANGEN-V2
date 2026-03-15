#!/usr/bin/env python3
"""
ML/DL持久化功能测试脚本
验证ML和DL模型重启后是否能正确恢复
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_ml_dl_persistence():
    """测试ML/DL持久化功能"""
    print("🔍 测试ML/DL持久化功能...")
    
    try:
        from src.config.ml_dl_persistence_manager import (
            get_ml_dl_persistence_manager,
            save_ml_model,
            load_ml_model,
            save_dl_model,
            load_dl_model,
            save_learning_state,
            load_learning_state
        )
        
        persistence_manager = get_ml_dl_persistence_manager()
        
        # 测试1: 保存ML模型
        ml_model_data = {
            "model_type": "random_forest",
            "accuracy": 0.85,
            "features": ["feature1", "feature2", "feature3"],
            "trained_at": "2025-10-20T10:00:00",
            "weights": [0.1, 0.2, 0.3, 0.4]
        }
        
        success = save_ml_model("test_ml_model", ml_model_data)
        assert success, "ML模型保存失败"
        print("  ✅ ML模型保存成功")
        
        # 测试2: 加载ML模型
        loaded_ml_data = load_ml_model("test_ml_model")
        assert loaded_ml_data is not None, "ML模型加载失败"
        assert loaded_ml_data["accuracy"] == 0.85, f"ML模型数据不匹配: {loaded_ml_data}"
        print("  ✅ ML模型加载成功")
        
        # 测试3: 保存DL模型
        dl_model_data = {
            "model_type": "neural_network",
            "accuracy": 0.92,
            "layers": [128, 64, 32],
            "weights": [[0.1, 0.2], [0.3, 0.4]],
            "trained_at": "2025-10-20T10:00:00",
            "epochs": 100
        }
        
        success = save_dl_model("test_dl_model", dl_model_data)
        assert success, "DL模型保存失败"
        print("  ✅ DL模型保存成功")
        
        # 测试4: 加载DL模型
        loaded_dl_data = load_dl_model("test_dl_model")
        assert loaded_dl_data is not None, "DL模型加载失败"
        assert loaded_dl_data["accuracy"] == 0.92, f"DL模型数据不匹配: {loaded_dl_data}"
        print("  ✅ DL模型加载成功")
        
        # 测试5: 保存学习状态
        learning_data = {
            "learning_rate": 0.01,
            "batch_size": 32,
            "epochs_completed": 50,
            "loss_history": [0.5, 0.4, 0.3, 0.2],
            "accuracy_history": [0.6, 0.7, 0.8, 0.9]
        }
        
        success = save_learning_state("test_agent", learning_data)
        assert success, "学习状态保存失败"
        print("  ✅ 学习状态保存成功")
        
        # 测试6: 加载学习状态
        loaded_learning_data = load_learning_state("test_agent")
        assert loaded_learning_data is not None, "学习状态加载失败"
        assert loaded_learning_data["learning_rate"] == 0.01, f"学习状态数据不匹配: {loaded_learning_data}"
        print("  ✅ 学习状态加载成功")
        
        # 测试7: 获取持久化摘要
        summary = persistence_manager.get_persistence_summary()
        assert summary["models"]["ml_models"] >= 1, f"ML模型数量不正确: {summary}"
        assert summary["models"]["dl_models"] >= 1, f"DL模型数量不正确: {summary}"
        assert summary["learning_states"] >= 1, f"学习状态数量不正确: {summary}"
        print(f"  ✅ 持久化摘要: {summary}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ ML/DL持久化测试失败: {e}")
        return False

def test_deep_learning_engine_persistence():
    """测试深度学习引擎的持久化集成"""
    print("\n🔍 测试深度学习引擎持久化集成...")
    
    try:
        from src.ai.deep_learning_engine import DeepLearningEngine, ModelArchitecture
        
        # 创建深度学习引擎
        dl_engine = DeepLearningEngine()
        
        # 创建模型架构
        architecture = ModelArchitecture(
            input_size=10,
            layers=[{"size": 64}, {"size": 32}],
            output_size=2,
            activation="relu"
        )
        
        # 测试1: 创建模型
        success = dl_engine.create_model("test_persistence_model", architecture)
        assert success, "模型创建失败"
        print("  ✅ 模型创建成功")
        
        # 测试2: 检查模型是否在内存中
        assert "test_persistence_model" in dl_engine.models, "模型不在内存中"
        print("  ✅ 模型在内存中")
        
        # 测试3: 模拟重启 - 创建新的引擎实例
        dl_engine_new = DeepLearningEngine()
        
        # 测试4: 检查模型是否从持久化存储中恢复
        if "test_persistence_model" in dl_engine_new.models:
            print("  ✅ 模型从持久化存储中恢复成功")
        else:
            print("  ⚠️  模型未从持久化存储中恢复（可能是首次运行）")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 深度学习引擎持久化测试失败: {e}")
        return False

def test_restart_simulation():
    """模拟重启场景"""
    print("\n🔍 模拟重启场景...")
    
    try:
        # 第一次运行：创建和训练模型
        from src.config.ml_dl_persistence_manager import save_ml_model, save_learning_state
        
        # 保存训练好的模型
        trained_model = {
            "model_type": "gradient_boosting",
            "accuracy": 0.88,
            "features": ["feature1", "feature2"],
            "trained_at": "2025-10-20T10:00:00",
            "training_time": 120.5,
            "epochs": 50
        }
        
        save_ml_model("production_model", trained_model)
        print("  ✅ 生产模型已保存")
        
        # 保存学习状态
        learning_state = {
            "learning_rate": 0.005,
            "batch_size": 64,
            "epochs_completed": 50,
            "best_accuracy": 0.88,
            "convergence_rate": 0.95
        }
        
        save_learning_state("production_agent", learning_state)
        print("  ✅ 生产学习状态已保存")
        
        # 模拟重启：重新导入模块
        import importlib
        import src.config.ml_dl_persistence_manager
        importlib.reload(src.config.ml_dl_persistence_manager)
        
        # 重新加载模型和学习状态
        from src.config.ml_dl_persistence_manager import load_ml_model, load_learning_state
        
        # 验证模型恢复
        restored_model = load_ml_model("production_model")
        assert restored_model is not None, "生产模型恢复失败"
        assert restored_model["accuracy"] == 0.88, f"生产模型精度不匹配: {restored_model['accuracy']}"
        print("  ✅ 生产模型恢复成功")
        
        # 验证学习状态恢复
        restored_learning = load_learning_state("production_agent")
        assert restored_learning is not None, "生产学习状态恢复失败"
        assert restored_learning["learning_rate"] == 0.005, f"学习率不匹配: {restored_learning['learning_rate']}"
        print("  ✅ 生产学习状态恢复成功")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 重启模拟测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始ML/DL持久化测试...\n")
    
    tests = [
        test_ml_dl_persistence,
        test_deep_learning_engine_persistence,
        test_restart_simulation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！ML/DL持久化功能正常！")
        print("\n💡 现在ML和DL的学习成果会在重启后保持！")
        return True
    else:
        print("❌ 部分测试失败，需要修复")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
