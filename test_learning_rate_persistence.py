#!/usr/bin/env python3
"""
学习率持久化测试脚本
验证学习率动态调整和持久化功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_learning_rate_persistence():
    """测试学习率持久化功能"""
    print("🔍 测试学习率持久化功能...")
    
    try:
        from src.config.learning_state_manager import (
            get_learning_state_manager,
            get_current_learning_rate,
            update_learning_rate
        )
        from src.utils.unified_centers import get_learning_rate
        
        # 测试1: 获取初始学习率
        initial_rate = get_current_learning_rate()
        print(f"  ✅ 初始学习率: {initial_rate}")
        
        # 测试2: 动态调整学习率
        new_rate = initial_rate * 1.5  # 增加50%
        update_learning_rate(new_rate, "performance_improvement", {"accuracy": 0.85})
        print(f"  ✅ 调整后学习率: {new_rate}")
        
        # 测试3: 验证调整是否生效
        current_rate = get_current_learning_rate()
        assert current_rate == new_rate, f"期望 {new_rate}，实际 {current_rate}"
        print(f"  ✅ 验证调整生效: {current_rate}")
        
        # 测试4: 验证统一配置中心获取
        unified_rate = get_learning_rate()
        assert unified_rate == new_rate, f"统一配置中心期望 {new_rate}，实际 {unified_rate}"
        print(f"  ✅ 统一配置中心获取: {unified_rate}")
        
        # 测试5: 检查持久化文件
        state_manager = get_learning_state_manager()
        state_file = state_manager.state_file
        assert state_file.exists(), f"状态文件不存在: {state_file}"
        print(f"  ✅ 状态文件已创建: {state_file}")
        
        # 测试6: 检查调整历史
        history = state_manager.get_adjustment_history("learning_rate")
        assert len(history) > 0, "调整历史为空"
        print(f"  ✅ 调整历史记录: {len(history)} 条")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 学习率持久化测试失败: {e}")
        return False

def test_restart_simulation():
    """模拟重启后学习率恢复"""
    print("\n🔍 模拟重启后学习率恢复...")
    
    try:
        # 第一次运行：调整学习率
        from src.config.learning_state_manager import update_learning_rate, get_current_learning_rate
        
        # 设置一个特定的学习率
        test_rate = 0.05
        update_learning_rate(test_rate, "test_adjustment")
        print(f"  ✅ 设置测试学习率: {test_rate}")
        
        # 模拟重启：重新导入模块
        import importlib
        import src.config.learning_state_manager
        importlib.reload(src.config.learning_state_manager)
        
        # 重新获取学习率
        restored_rate = src.config.learning_state_manager.get_current_learning_rate()
        assert abs(restored_rate - test_rate) < 0.001, f"期望 {test_rate}，实际 {restored_rate}"
        print(f"  ✅ 重启后学习率恢复: {restored_rate}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 重启模拟测试失败: {e}")
        return False

def test_environment_variable_override():
    """测试环境变量覆盖功能"""
    print("\n🔍 测试环境变量覆盖功能...")
    
    try:
        # 设置环境变量
        os.environ['LEARNING_RATE'] = '0.02'
        
        # 重新导入以获取新的环境变量
        import importlib
        import src.utils.unified_centers
        importlib.reload(src.utils.unified_centers)
        
        from src.utils.unified_centers import get_learning_rate
        
        # 获取学习率（应该优先使用持久化的值）
        current_rate = get_learning_rate()
        print(f"  ✅ 当前学习率: {current_rate}")
        
        # 清理环境变量
        del os.environ['LEARNING_RATE']
        
        return True
        
    except Exception as e:
        print(f"  ❌ 环境变量覆盖测试失败: {e}")
        return False

def test_state_file_management():
    """测试状态文件管理"""
    print("\n🔍 测试状态文件管理...")
    
    try:
        from src.config.learning_state_manager import get_learning_state_manager
        
        state_manager = get_learning_state_manager()
        
        # 测试状态摘要
        summary = state_manager.get_state_summary()
        print(f"  ✅ 状态摘要: {summary}")
        
        # 测试重置功能
        state_manager.reset_to_defaults()
        reset_rate = state_manager.get_learning_rate()
        assert reset_rate == 0.001, f"重置后期望 0.001，实际 {reset_rate}"
        print(f"  ✅ 重置功能正常: {reset_rate}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 状态文件管理测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始学习率持久化测试...\n")
    
    tests = [
        test_learning_rate_persistence,
        test_restart_simulation,
        test_environment_variable_override,
        test_state_file_management
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！学习率持久化功能正常！")
        return True
    else:
        print("❌ 部分测试失败，需要修复")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
