#!/usr/bin/env python3
"""
模型部署工具

将训练好的模型部署到生产环境，包括：
- 验证模型完整性
- 更新配置
- 备份旧模型
- 部署新模型
"""
import sys
import os
import json
import shutil
import argparse
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(dotenv_path=project_root / '.env')


def deploy_model(model_name: str, model_path: str = None, backup: bool = True):
    """部署模型"""
    print("=" * 80)
    print(f"模型部署: {model_name}")
    print("=" * 80)
    
    model_dir = project_root / "data" / "ml_models"
    
    # 确定模型文件路径
    if model_path:
        source_path = Path(model_path)
    else:
        source_path = model_dir / f"{model_name}.pkl"
    
    if not source_path.exists():
        print(f"❌ 模型文件不存在: {source_path}")
        return False
    
    print(f"\n📦 源模型文件: {source_path}")
    print(f"   文件大小: {source_path.stat().st_size / 1024:.2f} KB")
    
    # 验证模型完整性
    print(f"\n🔍 验证模型完整性...")
    try:
        import pickle
        with open(source_path, 'rb') as f:
            model = pickle.load(f)
        print(f"✅ 模型文件完整")
    except Exception as e:
        print(f"❌ 模型文件损坏: {e}")
        return False
    
    # 备份旧模型
    target_path = model_dir / f"{model_name}.pkl"
    if backup and target_path.exists():
        backup_dir = model_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        from datetime import datetime
        backup_name = f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        backup_path = backup_dir / backup_name
        
        shutil.copy2(target_path, backup_path)
        print(f"✅ 旧模型已备份: {backup_path}")
    
    # 部署新模型
    print(f"\n🚀 部署新模型...")
    try:
        if source_path != target_path:
            shutil.copy2(source_path, target_path)
        print(f"✅ 模型已部署: {target_path}")
    except Exception as e:
        print(f"❌ 部署失败: {e}")
        return False
    
    # 更新配置
    print(f"\n⚙️  更新配置...")
    try:
        config_file = project_root / "config" / "ml_training_config.json"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 更新模型路径
            model_config_key = {
                "parallel_query_classifier": "parallel_classifier",
                "deep_confidence_estimator": "deep_confidence",
                "logic_structure_parser": "logic_parser",
                "fewshot_pattern_learner": "fewshot_learner",
                "transformer_planner": "transformer_planner",
                "gnn_plan_optimizer": "gnn_optimizer"
            }.get(model_name, model_name)
            
            if model_config_key in config.get("ml_training", {}):
                config["ml_training"][model_config_key]["model_path"] = str(target_path)
                
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                
                print(f"✅ 配置已更新")
            else:
                print(f"⚠️  配置键不存在: {model_config_key}")
    except Exception as e:
        print(f"⚠️  配置更新失败: {e}")
    
    print(f"\n{'='*80}")
    print("✅ 模型部署完成！")
    print(f"{'='*80}")
    
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="模型部署工具")
    parser.add_argument("model", type=str, help="模型名称")
    parser.add_argument("--model-path", type=str, help="模型文件路径（默认：data/ml_models/{model}.pkl）")
    parser.add_argument("--no-backup", action="store_true", help="不备份旧模型")
    
    args = parser.parse_args()
    
    deploy_model(args.model, args.model_path, backup=not args.no_backup)


if __name__ == "__main__":
    main()

