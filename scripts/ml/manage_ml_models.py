#!/usr/bin/env python3
"""
ML模型管理工具

提供模型管理功能：
- 列出所有模型
- 查看模型信息
- 删除模型
- 模型版本管理
- A/B测试管理
"""
import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(dotenv_path=project_root / '.env')


def list_models():
    """列出所有已训练的模型"""
    model_dir = project_root / "data" / "ml_models"
    
    if not model_dir.exists():
        print("❌ 模型目录不存在")
        return
    
    model_files = list(model_dir.glob("*.pkl"))
    
    if not model_files:
        print("📭 没有找到已训练的模型")
        return
    
    print(f"\n📦 已训练的模型 ({len(model_files)} 个):\n")
    
    for model_file in sorted(model_files):
        model_name = model_file.stem
        file_size = model_file.stat().st_size / 1024  # KB
        mtime = model_file.stat().st_mtime
        
        from datetime import datetime
        mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"  ✅ {model_name}")
        print(f"     文件: {model_file.name}")
        print(f"     大小: {file_size:.2f} KB")
        print(f"     修改时间: {mtime_str}")
        print()


def show_model_info(model_name: str):
    """显示模型详细信息"""
    model_dir = project_root / "data" / "ml_models"
    model_path = model_dir / f"{model_name}.pkl"
    
    if not model_path.exists():
        print(f"❌ 模型文件不存在: {model_path}")
        return
    
    print(f"\n📋 模型信息: {model_name}\n")
    print(f"  文件路径: {model_path}")
    print(f"  文件大小: {model_path.stat().st_size / 1024:.2f} KB")
    
    # 检查训练报告
    report_path = model_dir / "training_report.json"
    if report_path.exists():
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
                if model_name in report.get("results", {}):
                    result = report["results"][model_name]
                    print(f"\n  训练信息:")
                    if result.get("success"):
                        print(f"    状态: ✅ 训练成功")
                        print(f"    训练数据: {result.get('data_count', 0)} 条")
                        if result.get("training_result"):
                            tr = result["training_result"]
                            print(f"    模型类型: {tr.get('model_type', 'N/A')}")
                            if "accuracy" in tr.get("metrics", {}):
                                print(f"    准确率: {tr['metrics']['accuracy']:.3f}")
                            if "mse" in tr.get("metrics", {}):
                                print(f"    MSE: {tr['metrics']['mse']:.4f}")
                    else:
                        print(f"    状态: ❌ 训练失败")
                        print(f"    错误: {result.get('error', 'Unknown')}")
        except Exception as e:
            print(f"  ⚠️ 无法读取训练报告: {e}")
    
    # 检查评估报告
    eval_report_path = model_dir / "evaluation_report.json"
    if eval_report_path.exists():
        try:
            with open(eval_report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
                if model_name in report.get("results", {}):
                    result = report["results"][model_name]
                    print(f"\n  评估信息:")
                    if result.get("success"):
                        print(f"    状态: ✅ 评估成功")
                        print(f"    测试数据: {result.get('test_data_count', 0)} 条")
                        eval_result = result.get("evaluation_result", {})
                        if "accuracy" in eval_result:
                            print(f"    准确率: {eval_result['accuracy']:.3f}")
                        if "mse" in eval_result:
                            print(f"    MSE: {eval_result['mse']:.4f}")
                        if "f1" in eval_result or "f1_score" in eval_result:
                            f1 = eval_result.get("f1") or eval_result.get("f1_score", 0)
                            print(f"    F1: {f1:.3f}")
                    else:
                        print(f"    状态: ❌ 评估失败")
        except Exception as e:
            print(f"  ⚠️ 无法读取评估报告: {e}")
    
    print()


def delete_model(model_name: str, confirm: bool = False):
    """删除模型"""
    model_dir = project_root / "data" / "ml_models"
    model_path = model_dir / f"{model_name}.pkl"
    
    if not model_path.exists():
        print(f"❌ 模型文件不存在: {model_path}")
        return
    
    if not confirm:
        response = input(f"⚠️  确定要删除模型 '{model_name}' 吗? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ 取消删除")
            return
    
    try:
        model_path.unlink()
        print(f"✅ 模型已删除: {model_name}")
    except Exception as e:
        print(f"❌ 删除失败: {e}")


def show_training_stats():
    """显示训练统计信息"""
    model_dir = project_root / "data" / "ml_models"
    
    # 检查训练报告
    report_path = model_dir / "training_report.json"
    if not report_path.exists():
        print("❌ 训练报告不存在")
        return
    
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        summary = report.get("summary", {})
        results = report.get("results", {})
        
        print(f"\n📊 训练统计信息\n")
        print(f"  总模型数: {summary.get('total', 0)}")
        print(f"  成功: {summary.get('success', 0)}")
        print(f"  失败: {summary.get('failed', 0)}")
        print(f"\n  详细结果:\n")
        
        for model_name, result in results.items():
            status = "✅" if result.get("success") else "❌"
            print(f"    {status} {model_name}")
            if result.get("success"):
                print(f"        数据量: {result.get('data_count', 0)} 条")
                if result.get("model_path"):
                    print(f"        模型路径: {result['model_path']}")
            else:
                print(f"        错误: {result.get('error', 'Unknown')}")
        
        print()
    except Exception as e:
        print(f"❌ 读取训练报告失败: {e}")


def show_evaluation_stats():
    """显示评估统计信息"""
    model_dir = project_root / "data" / "ml_models"
    
    # 检查评估报告
    report_path = model_dir / "evaluation_report.json"
    if not report_path.exists():
        print("❌ 评估报告不存在")
        return
    
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        summary = report.get("summary", {})
        results = report.get("results", {})
        
        print(f"\n📊 评估统计信息\n")
        print(f"  总模型数: {summary.get('total', 0)}")
        print(f"  成功评估: {summary.get('success', 0)}")
        print(f"  失败: {summary.get('failed', 0)}")
        print(f"\n  详细结果:\n")
        
        for model_name, result in results.items():
            status = "✅" if result.get("success") else "❌"
            print(f"    {status} {model_name}")
            if result.get("success"):
                eval_result = result.get("evaluation_result", {})
                print(f"        测试数据: {result.get('test_data_count', 0)} 条")
                if "accuracy" in eval_result:
                    print(f"        准确率: {eval_result['accuracy']:.3f}")
                if "mse" in eval_result:
                    print(f"        MSE: {eval_result['mse']:.4f}")
            else:
                print(f"        错误: {result.get('error', 'Unknown')}")
        
        print()
    except Exception as e:
        print(f"❌ 读取评估报告失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="ML模型管理工具")
    parser.add_argument("action", choices=["list", "info", "delete", "training-stats", "eval-stats"],
                       help="操作类型")
    parser.add_argument("--model", type=str, help="模型名称（用于info和delete操作）")
    parser.add_argument("--yes", action="store_true", help="确认删除（不提示）")
    
    args = parser.parse_args()
    
    if args.action == "list":
        list_models()
    elif args.action == "info":
        if not args.model:
            print("❌ 请指定模型名称: --model <model_name>")
            return
        show_model_info(args.model)
    elif args.action == "delete":
        if not args.model:
            print("❌ 请指定模型名称: --model <model_name>")
            return
        delete_model(args.model, confirm=args.yes)
    elif args.action == "training-stats":
        show_training_stats()
    elif args.action == "eval-stats":
        show_evaluation_stats()


if __name__ == "__main__":
    main()

