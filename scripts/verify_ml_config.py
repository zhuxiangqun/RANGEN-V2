#!/usr/bin/env python3
"""
验证ML配置是否正确加载

此脚本验证系统能否正确读取和加载ML训练配置。
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 🚀 修复：在导入其他模块之前先加载.env文件
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=project_root / '.env')
    print(f"✅ 已加载.env文件: {project_root / '.env'}")
except ImportError:
    print("⚠️ dotenv未安装，跳过.env文件加载")
except Exception as e:
    print(f"⚠️ 加载.env文件失败: {e}")


def verify_config_loading():
    """验证配置加载"""
    print("=" * 80)
    print("验证ML配置加载")
    print("=" * 80)
    
    # 1. 检查配置文件是否存在
    config_file = project_root / "config" / "ml_training_config.json"
    print(f"\n1. 检查配置文件:")
    if config_file.exists():
        print(f"   ✅ 配置文件存在: {config_file}")
        
        # 读取配置内容
        import json
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            ml_config = config.get('ml_training', {})
            print(f"   📋 配置内容:")
            print(f"      - 数据收集启用: {ml_config.get('data_collection_enabled', False)}")
            print(f"      - 存储路径: {ml_config.get('data_storage_path', 'N/A')}")
            print(f"      - 并行分类器启用: {ml_config.get('parallel_classifier_enabled', False)}")
    else:
        print(f"   ❌ 配置文件不存在: {config_file}")
        print(f"   请运行: python scripts/enable_ml_data_collection.py")
        return False
    
    # 2. 测试Utils.initialize_config()
    print(f"\n2. 测试配置加载:")
    try:
        from src.core.reasoning.utils import Utils
        config = Utils.initialize_config()
        
        ml_config = config.get('ml_training', {})
        if ml_config:
            print(f"   ✅ Utils.initialize_config() 成功加载ML配置")
            print(f"      - 数据收集启用: {ml_config.get('data_collection_enabled', False)}")
            print(f"      - 存储路径: {ml_config.get('data_storage_path', 'N/A')}")
        else:
            print(f"   ⚠️ Utils.initialize_config() 未加载ML配置")
            print(f"      配置可能未正确合并")
    except Exception as e:
        print(f"   ❌ 配置加载失败: {e}")
        return False
    
    # 3. 测试统一配置中心
    print(f"\n3. 测试统一配置中心:")
    try:
        from src.utils.unified_centers import get_unified_config_center
        config_center = get_unified_config_center()
        
        # 尝试获取配置
        if hasattr(config_center, 'get_config_section'):
            ml_config = config_center.get_config_section('ml_training')
            if ml_config:
                print(f"   ✅ 统一配置中心可以获取ML配置")
            else:
                print(f"   ⚠️ 统一配置中心未找到ML配置（可能需要手动注册）")
        else:
            print(f"   ⚠️ 统一配置中心不支持get_config_section方法")
    except Exception as e:
        print(f"   ⚠️ 统一配置中心测试失败: {e}")
    
    # 4. 测试RealReasoningEngine初始化
    print(f"\n4. 测试RealReasoningEngine配置加载:")
    try:
        from src.core.reasoning.engine import RealReasoningEngine
        engine = RealReasoningEngine()
        
        if hasattr(engine, 'data_collection_enabled'):
            print(f"   ✅ RealReasoningEngine 已初始化")
            print(f"      - 数据收集启用: {engine.data_collection_enabled}")
            if engine.data_collection:
                print(f"      - 数据收集管道: ✅ 已初始化")
            else:
                print(f"      - 数据收集管道: ❌ 未初始化")
        else:
            print(f"   ⚠️ RealReasoningEngine 未找到data_collection_enabled属性")
    except Exception as e:
        print(f"   ⚠️ RealReasoningEngine 初始化失败: {e}")
        import traceback
        print(f"   错误详情: {traceback.format_exc()[:200]}")
    
    print(f"\n{'=' * 80}")
    print("✅ 验证完成")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    verify_config_loading()

