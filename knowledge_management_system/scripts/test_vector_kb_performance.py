#!/usr/bin/env python3
"""
向量知识库构建性能测试脚本
用于小规模测试优化后的性能提升

使用方式：
  python test_vector_kb_performance.py --dataset-path /path/to/frames.json --test-size 10
  python test_vector_kb_performance.py --dataset-path google/frames-benchmark --test-size 20
"""

import sys
import os
import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from knowledge_management_system.api.service_interface import get_knowledge_service
from knowledge_management_system.utils.logger import get_logger

logger = get_logger()


def extract_test_dataset(dataset_path: str, test_size: int = 10) -> str:
    """
    从完整数据集中提取测试用的子集
    
    Args:
        dataset_path: 原始数据集路径
        test_size: 测试样本数量
        
    Returns:
        测试数据集文件路径
    """
    # 检测是否为 Hugging Face 数据集标识符
    is_huggingface_id = "/" in dataset_path and not dataset_path.startswith("/") and not Path(dataset_path).exists()
    
    if is_huggingface_id:
        # 从 Hugging Face 下载数据集
        try:
            from datasets import load_dataset
        except ImportError:
            print("❌ 错误：需要安装 datasets 库才能从 Hugging Face 下载")
            print("   运行: pip install datasets")
            sys.exit(1)
        
        print(f"📥 从 Hugging Face 下载数据集: {dataset_path}")
        dataset = load_dataset(dataset_path)
        
        # 获取数据集的分割
        if hasattr(dataset, 'keys'):
            splits_raw = dataset.keys()  # type: ignore
            splits = [str(split) for split in splits_raw]
        else:
            splits = ['default']
        
        # 优先使用 test/train 分割
        preferred_splits = ['test', 'train', 'validation', 'val']
        selected_split: Optional[str] = None
        for split in preferred_splits:
            if split in splits:
                selected_split = split
                break
        
        if not selected_split:
            selected_split = splits[0] if splits else None
        
        if not selected_split:
            print("❌ 错误: 数据集没有可用的分割")
            sys.exit(1)
        
        split_data = dataset[selected_split]  # type: ignore
        
        # 转换为列表格式
        dataset_list = []
        for item in split_data:
            if isinstance(item, dict):
                dataset_list.append(item)
            else:
                try:
                    dataset_list.append(dict(item))  # type: ignore
                except (TypeError, ValueError):
                    continue
        
        # 提取测试子集
        test_data = dataset_list[:test_size]
        print(f"✅ 从 Hugging Face 数据集提取了 {len(test_data)} 个测试样本")
    else:
        # 从本地文件加载
        dataset_file = Path(dataset_path)
        if not dataset_file.exists():
            print(f"❌ 错误：数据集文件不存在: {dataset_path}")
            sys.exit(1)
        
        print(f"📂 从本地文件加载数据集: {dataset_path}")
        with open(dataset_file, 'r', encoding='utf-8') as f:
            dataset_list = json.load(f)
        
        if not isinstance(dataset_list, list):
            print("❌ 错误：数据集格式错误，应为列表格式")
            sys.exit(1)
        
        # 提取测试子集
        test_data = dataset_list[:test_size]
        print(f"✅ 从本地数据集提取了 {len(test_data)} 个测试样本")
    
    # 保存测试数据集
    test_dataset_path = Path(__file__).parent.parent.parent / "data" / "test_vector_kb_dataset.json"
    test_dataset_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(test_dataset_path, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 测试数据集已保存到: {test_dataset_path}")
    return str(test_dataset_path)


def test_vector_kb_performance(
    dataset_path: str,
    test_size: int = 10,
    batch_size: int = 5,
    include_full_text: bool = True
) -> Dict[str, Any]:
    """
    测试向量知识库构建性能
    
    Args:
        dataset_path: 数据集路径
        test_size: 测试样本数量
        batch_size: 批次大小
        include_full_text: 是否包含完整文本
        
    Returns:
        性能统计信息
    """
    from knowledge_management_system.scripts.import_wikipedia_from_frames import (
        import_wikipedia_from_frames
    )
    
    print("=" * 70)
    print("🚀 向量知识库构建性能测试")
    print("=" * 70)
    print()
    print(f"📦 测试数据集: {dataset_path}")
    print(f"📏 测试样本数: {test_size}")
    print(f"📦 批次大小: {batch_size}")
    print(f"📝 包含完整文本: {include_full_text}")
    print()
    print("=" * 70)
    print()
    
    # 提取测试数据集
    test_dataset_path = extract_test_dataset(dataset_path, test_size)
    
    # 获取服务实例
    service = get_knowledge_service()
    
    # 保存原始的 import_knowledge 方法
    original_import = service.import_knowledge
    
    # 创建包装函数，强制 build_graph=False
    def import_without_graph(*args, **kwargs):
        kwargs['build_graph'] = False
        return original_import(*args, **kwargs)
    
    # 临时替换方法
    service.import_knowledge = import_without_graph
    
    # 性能统计
    stats = {
        'test_size': test_size,
        'batch_size': batch_size,
        'start_time': time.time(),
        'end_time': None,
        'total_time': None,
        'time_per_item': None,
        'items_per_hour': None,
        'vectorization_time': 0,
        'wikipedia_fetch_time': 0,
        'total_items_processed': 0,
        'total_chunks': 0,
        'batch_vectorization_count': 0,
        'long_text_batch_count': 0
    }
    
    try:
        # 记录开始时间
        start_time = time.time()
        print(f"⏱️  开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 运行导入
        import_wikipedia_from_frames(
            dataset_path=test_dataset_path,
            batch_size=batch_size,
            include_full_text=include_full_text,
            resume=False,  # 不启用断点续传，从头开始
            skip_duplicates=True
        )
        
        # 记录结束时间
        end_time = time.time()
        total_time = end_time - start_time
        
        stats['end_time'] = end_time
        stats['total_time'] = total_time
        stats['time_per_item'] = total_time / test_size if test_size > 0 else 0
        stats['items_per_hour'] = (test_size / total_time * 3600) if total_time > 0 else 0
        
        print()
        print("=" * 70)
        print("📊 性能测试结果")
        print("=" * 70)
        print()
        print(f"✅ 测试完成！")
        print()
        print(f"📦 测试样本数: {test_size}")
        print(f"⏱️  总耗时: {total_time:.2f}秒 ({total_time/60:.2f}分钟)")
        print(f"📈 平均耗时: {stats['time_per_item']:.2f}秒/条目")
        print(f"🚀 处理速度: {stats['items_per_hour']:.1f}条目/小时")
        print()
        
        # 计算预计全量数据时间
        if test_size > 0:
            # 假设全量数据有824条（FRAMES数据集）
            full_dataset_size = 824
            estimated_full_time = (total_time / test_size) * full_dataset_size
            estimated_full_hours = estimated_full_time / 3600
            
            print(f"📊 性能预测（基于当前测试结果）:")
            print(f"   假设全量数据: {full_dataset_size} 条")
            print(f"   预计总耗时: {estimated_full_time/60:.1f}分钟 ({estimated_full_hours:.1f}小时)")
            print()
        
        print("=" * 70)
        
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ 测试失败")
        print("=" * 70)
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        stats['error'] = str(e)
    finally:
        # 恢复原始方法
        service.import_knowledge = original_import
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="向量知识库构建性能测试（小规模测试）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 从本地数据集测试（10个样本）
  python test_vector_kb_performance.py --dataset-path /path/to/frames.json --test-size 10
  
  # 从 Hugging Face 数据集测试（20个样本）
  python test_vector_kb_performance.py --dataset-path google/frames-benchmark --test-size 20
  
  # 自定义批次大小
  python test_vector_kb_performance.py --dataset-path google/frames-benchmark --test-size 10 --batch-size 5
        """
    )
    
    parser.add_argument(
        "--dataset-path",
        type=str,
        required=True,
        help="数据集路径（本地JSON文件路径或 Hugging Face 数据集标识符，如 google/frames-benchmark）"
    )
    parser.add_argument(
        "--test-size",
        type=int,
        default=10,
        help="测试样本数量（默认: 10）"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="批次大小（默认: 5）"
    )
    parser.add_argument(
        "--no-full-text",
        action="store_true",
        help="不包含完整文本（仅摘要）"
    )
    
    args = parser.parse_args()
    
    # 运行性能测试
    stats = test_vector_kb_performance(
        dataset_path=args.dataset_path,
        test_size=args.test_size,
        batch_size=args.batch_size,
        include_full_text=not args.no_full_text
    )
    
    # 保存测试结果
    result_file = Path(__file__).parent.parent.parent / "data" / "vector_kb_performance_test_result.json"
    result_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print()
    print(f"💾 测试结果已保存到: {result_file}")
    print()
    
    return 0 if 'error' not in stats else 1


if __name__ == "__main__":
    sys.exit(main())

