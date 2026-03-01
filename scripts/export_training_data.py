#!/usr/bin/env python3
"""
导出训练数据

将收集的训练数据导出为不同格式，便于外部使用。
"""
import sys
import os
import json
import csv
import argparse
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(dotenv_path=project_root / '.env')


def export_to_json(model_name: str, output_path: str):
    """导出为JSON格式"""
    try:
        from src.core.reasoning.ml_framework.data_collection import DataCollectionPipeline
        
        data_dir = project_root / "data" / "ml_training"
        data_collection = DataCollectionPipeline(storage_path=str(data_dir))
        
        result = data_collection.extract_training_data_for_model(model_name, max_samples=None)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 已导出到: {output_file}")
        print(f"   数据量: {len(result.get('training_data', []))} 条")
        
    except Exception as e:
        print(f"❌ 导出失败: {e}")


def export_to_csv(model_name: str, output_path: str):
    """导出为CSV格式"""
    try:
        from src.core.reasoning.ml_framework.data_collection import DataCollectionPipeline
        
        data_dir = project_root / "data" / "ml_training"
        data_collection = DataCollectionPipeline(storage_path=str(data_dir))
        
        result = data_collection.extract_training_data_for_model(model_name, max_samples=None)
        
        training_data = result.get("training_data", [])
        labels = result.get("labels", [])
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # 写入表头
            if model_name == "parallel_query_classifier":
                writer.writerow(["query", "is_parallel"])
                for query, label in zip(training_data, labels):
                    writer.writerow([query, label])
            elif model_name == "deep_confidence_estimator":
                writer.writerow(["query", "answer", "evidence_count", "failed_steps", "total_steps", "success", "confidence"])
                for data, label in zip(training_data, labels):
                    context = data.get("context", {})
                    writer.writerow([
                        data.get("query", ""),
                        data.get("answer", ""),
                        context.get("evidence_count", 0),
                        context.get("failed_steps", 0),
                        context.get("total_steps", 0),
                        context.get("success", False),
                        label
                    ])
            else:
                # 通用格式
                writer.writerow(["data", "label"])
                for data, label in zip(training_data, labels):
                    data_str = json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else str(data)
                    label_str = json.dumps(label, ensure_ascii=False) if isinstance(label, (dict, list)) else str(label)
                    writer.writerow([data_str, label_str])
        
        print(f"✅ 已导出到: {output_file}")
        print(f"   数据量: {len(training_data)} 条")
        
    except Exception as e:
        print(f"❌ 导出失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="导出训练数据")
    parser.add_argument("model", type=str, help="模型名称")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="导出格式")
    parser.add_argument("--output", type=str, help="输出文件路径（默认：data/ml_training/exported/{model}.{format}）")
    
    args = parser.parse_args()
    
    if not args.output:
        output_dir = project_root / "data" / "ml_training" / "exported"
        output_dir.mkdir(parents=True, exist_ok=True)
        args.output = str(output_dir / f"{args.model}.{args.format}")
    
    if args.format == "json":
        export_to_json(args.model, args.output)
    elif args.format == "csv":
        export_to_csv(args.model, args.output)


if __name__ == "__main__":
    main()

