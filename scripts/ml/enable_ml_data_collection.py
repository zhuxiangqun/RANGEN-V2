#!/usr/bin/env python3
"""
启用ML数据收集功能

此脚本会：
1. 检查当前配置
2. 启用数据收集功能
3. 验证配置是否正确
"""
import sys
import os
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_and_enable_config():
    """检查并启用ML数据收集配置"""
    print("=" * 80)
    print("启用ML数据收集功能")
    print("=" * 80)
    
    # 检查统一配置中心
    try:
        from src.utils.unified_centers import get_unified_config_center
        config_center = get_unified_config_center()
        
        # 获取当前配置
        current_config = config_center.get_config('ml_training', {})
        
        print(f"\n📋 当前配置:")
        print(f"   数据收集启用: {current_config.get('data_collection_enabled', False)}")
        print(f"   存储路径: {current_config.get('data_storage_path', 'data/ml_training')}")
        print(f"   并行分类器启用: {current_config.get('parallel_classifier_enabled', False)}")
        
        # 检查是否需要启用
        if current_config.get('data_collection_enabled', False):
            print(f"\n✅ 数据收集功能已经启用！")
            return True
        
        # 启用配置
        print(f"\n🔧 启用数据收集功能...")
        
        # 更新配置
        ml_config = {
            "data_collection_enabled": True,
            "data_storage_path": "data/ml_training",
            "parallel_classifier_enabled": True,
            "parallel_classifier": {
                "threshold": 0.5,
                "model_path": None
            }
        }
        
        # 合并现有配置
        updated_config = {**current_config, **ml_config}
        
        # 设置配置（如果配置中心支持）
        if hasattr(config_center, 'set_config'):
            config_center.set_config('ml_training', updated_config)
            print(f"✅ 配置已更新到统一配置中心")
        else:
            print(f"⚠️ 统一配置中心不支持动态设置，需要手动配置")
            print(f"\n请手动在配置文件中添加以下配置：")
            print(json.dumps({"ml_training": updated_config}, indent=2, ensure_ascii=False))
            
            # 尝试创建配置文件
            config_file = project_root / "config" / "ml_training_config.json"
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({"ml_training": updated_config}, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ 已创建配置文件: {config_file}")
            print(f"   请确保系统能够读取此配置文件")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 配置检查失败: {e}")
        print(f"\n请手动创建配置文件: config/ml_training_config.json")
        print(f"内容如下：")
        
        default_config = {
            "ml_training": {
                "data_collection_enabled": True,
                "data_storage_path": "data/ml_training",
                "parallel_classifier_enabled": True,
                "parallel_classifier": {
                    "threshold": 0.5,
                    "model_path": None
                }
            }
        }
        
        print(json.dumps(default_config, indent=2, ensure_ascii=False))
        return False


def verify_data_directory():
    """验证数据目录"""
    print(f"\n📁 检查数据目录...")
    
    data_dir = project_root / "data" / "ml_training"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    if data_dir.exists():
        print(f"✅ 数据目录已创建: {data_dir}")
        
        # 检查现有数据
        jsonl_files = list(data_dir.glob("*.jsonl"))
        if jsonl_files:
            total_lines = 0
            for file in jsonl_files:
                with open(file, 'r', encoding='utf-8') as f:
                    total_lines += sum(1 for _ in f)
            print(f"   现有数据: {len(jsonl_files)} 个文件, {total_lines} 条记录")
        else:
            print(f"   现有数据: 无")
        
        return True
    else:
        print(f"❌ 数据目录创建失败")
        return False


def main():
    """主函数"""
    success = True
    
    # 检查并启用配置
    if not check_and_enable_config():
        success = False
    
    # 验证数据目录
    if not verify_data_directory():
        success = False
    
    print(f"\n{'=' * 80}")
    if success:
        print("✅ 配置完成！")
        print("\n下一步:")
        print("1. 运行系统处理查询，数据将自动收集")
        print("2. 查看收集的数据: ls -lh data/ml_training/*.jsonl")
        print("3. 运行监控脚本: python scripts/monitor_data_collection.py")
    else:
        print("⚠️ 配置未完全完成，请检查上述提示")
    print("=" * 80)


if __name__ == "__main__":
    main()

