#!/usr/bin/env python3
"""
配置一致性验证脚本
验证重构后的配置系统是否正常工作
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_unified_config_center():
    """测试统一配置中心"""
    print("🔍 测试统一配置中心...")
    
    try:
        from src.utils.unified_centers import (
            get_unified_config_center,
            get_max_evaluation_items,
            get_batch_size,
            get_learning_rate,
            get_max_concurrent_queries,
            get_request_timeout,
            get_max_cache_size
        )
        
        config_center = get_unified_config_center()
        
        # 测试便捷函数
        print(f"  ✅ MAX_EVALUATION_ITEMS: {get_max_evaluation_items()}")
        print(f"  ✅ BATCH_SIZE: {get_batch_size()}")
        print(f"  ✅ LEARNING_RATE: {get_learning_rate()}")
        print(f"  ✅ MAX_CONCURRENT_QUERIES: {get_max_concurrent_queries()}")
        print(f"  ✅ REQUEST_TIMEOUT: {get_request_timeout()}")
        print(f"  ✅ MAX_CACHE_SIZE: {get_max_cache_size()}")
        
        # 测试直接访问
        print(f"  ✅ 直接访问 MAX_EVALUATION_ITEMS: {config_center.get_env_config('system', 'MAX_EVALUATION_ITEMS')}")
        print(f"  ✅ 直接访问 BATCH_SIZE: {config_center.get_env_config('ai_ml', 'BATCH_SIZE')}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 统一配置中心测试失败: {e}")
        return False

def test_environment_variables():
    """测试环境变量覆盖"""
    print("\n🔍 测试环境变量覆盖...")
    
    try:
        # 设置测试环境变量
        os.environ['MAX_EVALUATION_ITEMS'] = '50'
        os.environ['BATCH_SIZE'] = '16'
        os.environ['LEARNING_RATE'] = '0.01'
        
        # 重新导入以获取新的环境变量
        import importlib
        import src.utils.unified_centers
        importlib.reload(src.utils.unified_centers)
        
        from src.utils.unified_centers import (
            get_max_evaluation_items,
            get_batch_size,
            get_learning_rate
        )
        
        # 验证环境变量是否生效
        assert get_max_evaluation_items() == 50, f"期望 50，实际 {get_max_evaluation_items()}"
        assert get_batch_size() == 16, f"期望 16，实际 {get_batch_size()}"
        assert get_learning_rate() == 0.01, f"期望 0.01，实际 {get_learning_rate()}"
        
        print(f"  ✅ 环境变量覆盖测试通过")
        print(f"    MAX_EVALUATION_ITEMS: {get_max_evaluation_items()}")
        print(f"    BATCH_SIZE: {get_batch_size()}")
        print(f"    LEARNING_RATE: {get_learning_rate()}")
        
        # 清理环境变量
        del os.environ['MAX_EVALUATION_ITEMS']
        del os.environ['BATCH_SIZE']
        del os.environ['LEARNING_RATE']
        
        return True
        
    except Exception as e:
        print(f"  ❌ 环境变量覆盖测试失败: {e}")
        return False

def test_config_factory():
    """测试配置工厂"""
    print("\n🔍 测试配置工厂...")
    
    try:
        from src.config.config_factory import ConfigManager
        
        config_manager = ConfigManager()
        
        # 测试动态配置
        max_items = config_manager.get_dynamic_config('ai_ml', 'max_evaluation_items')
        batch_size = config_manager.get_dynamic_config('ai_ml', 'batch_size')
        learning_rate = config_manager.get_dynamic_config('ai_ml', 'learning_rate')
        
        print(f"  ✅ ConfigFactory MAX_EVALUATION_ITEMS: {max_items}")
        print(f"  ✅ ConfigFactory BATCH_SIZE: {batch_size}")
        print(f"  ✅ ConfigFactory LEARNING_RATE: {learning_rate}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 配置工厂测试失败: {e}")
        return False

def test_system_constants():
    """测试系统常量"""
    print("\n🔍 测试系统常量...")
    
    try:
        from src.config.system_constants import SystemConstants
        
        constants = SystemConstants()
        
        # 测试常量访问
        vector_dim = constants.get_constant('VECTOR_DIMENSION')
        api_key_length = constants.get_constant('API_KEY_LENGTH')
        
        print(f"  ✅ VECTOR_DIMENSION: {vector_dim}")
        print(f"  ✅ API_KEY_LENGTH: {api_key_length}")
        
        # 验证环境变量配置已移除
        all_constants = constants.get_all_constants()
        env_vars = ['MAX_EVALUATION_ITEMS', 'BATCH_SIZE', 'LEARNING_RATE', 'REQUEST_TIMEOUT']
        
        for env_var in env_vars:
            if env_var in all_constants:
                print(f"  ⚠️  警告: {env_var} 仍在 SystemConstants 中")
            else:
                print(f"  ✅ {env_var} 已从 SystemConstants 中移除")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 系统常量测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始配置一致性验证...\n")
    
    tests = [
        test_unified_config_center,
        test_environment_variables,
        test_config_factory,
        test_system_constants
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！配置重构成功！")
        return True
    else:
        print("❌ 部分测试失败，需要修复")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
