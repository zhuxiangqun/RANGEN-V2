#!/usr/bin/env python3
"""
测试脚本：使用少量数据测试向量知识库构建
验证构建过程是否正常，包括：
1. 数据导入是否正常
2. 元数据文件是否正确生成
3. 进度文件是否正确更新
4. 向量索引是否正确构建
5. 是否有任何错误

使用方式：
  python scripts/test_vector_build_small.py --sample-size 10
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from knowledge_management_system.scripts.build_vector_knowledge_base import (
    build_vector_knowledge_base_from_list
)
from knowledge_management_system.api.service_interface import get_knowledge_service


def extract_test_samples(dataset_path: Path, sample_size: int = 10) -> list:
    """从完整数据集中提取测试样本"""
    if not dataset_path.exists():
        print(f"❌ 数据集文件不存在: {dataset_path}")
        sys.exit(1)
    
    print(f"📖 正在从数据集加载样本...")
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    if not isinstance(dataset, list):
        print(f"❌ 数据集格式错误：必须是JSON数组")
        sys.exit(1)
    
    # 提取前N条数据
    test_samples = dataset[:sample_size]
    print(f"✅ 已提取 {len(test_samples)} 条测试样本")
    
    return test_samples


def convert_frames_to_import_format(samples: list) -> list:
    """将FRAMES格式转换为导入脚本期望的格式"""
    print(f"🔄 正在转换数据格式...")
    
    converted_data = []
    for idx, item in enumerate(samples):
        # 提取Prompt作为content
        content = item.get('Prompt', item.get('question', item.get('query', '')))
        if not content:
            print(f"⚠️ 跳过第 {idx} 条数据（无内容）")
            continue
        
        # 构建metadata
        metadata = {
            'answer': item.get('Answer', ''),
            'dataset_source': 'frames_dataset.json',
            'item_index': item.get('Unnamed: 0', idx)
        }
        
        # 提取Wikipedia链接
        wikipedia_links = []
        for i in range(1, 12):  # wikipedia_link_1 到 wikipedia_link_11+
            link = item.get(f'wikipedia_link_{i}', '')
            if link and link.strip():
                wikipedia_links.append(link.strip())
        
        if wikipedia_links:
            metadata['wikipedia_links'] = wikipedia_links
        
        # 添加其他字段到metadata
        for key, value in item.items():
            if key not in ['Prompt', 'Answer', 'Unnamed: 0'] and not key.startswith('wikipedia_link_'):
                if isinstance(value, (str, int, float, bool)):
                    metadata[key] = value
        
        converted_data.append({
            'content': content,
            'metadata': metadata
        })
    
    print(f"✅ 已转换 {len(converted_data)} 条数据")
    return converted_data


def check_initial_state():
    """检查初始状态"""
    print("\n" + "=" * 70)
    print("📊 检查初始状态")
    print("=" * 70)
    
    metadata_path = Path("data/knowledge_management/metadata.json")
    progress_path = Path("data/knowledge_management/vector_import_progress.json")
    
    initial_state = {
        'metadata_exists': metadata_path.exists(),
        'metadata_entry_count': 0,
        'progress_exists': progress_path.exists(),
        'progress_processed': 0,
        'progress_failed': 0
    }
    
    # 检查元数据文件
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            initial_state['metadata_entry_count'] = len(metadata.get('entries', {}))
            print(f"✅ 元数据文件: 存在 ({initial_state['metadata_entry_count']} 条条目)")
        except json.JSONDecodeError as e:
            print(f"⚠️ 元数据文件损坏: {e}")
            initial_state['metadata_exists'] = False
    else:
        print("ℹ️ 元数据文件: 不存在（将创建新文件）")
    
    # 检查进度文件
    if progress_path.exists():
        try:
            with open(progress_path, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            initial_state['progress_processed'] = len(progress.get('processed_item_indices', []))
            initial_state['progress_failed'] = len(progress.get('failed_item_indices', []))
            print(f"✅ 进度文件: 存在 (已处理: {initial_state['progress_processed']}, 失败: {initial_state['progress_failed']})")
        except json.JSONDecodeError as e:
            print(f"⚠️ 进度文件损坏: {e}")
            initial_state['progress_exists'] = False
    else:
        print("ℹ️ 进度文件: 不存在（将创建新文件）")
    
    return initial_state


def verify_build_result(initial_state: dict, sample_size: int):
    """验证构建结果"""
    print("\n" + "=" * 70)
    print("🔍 验证构建结果")
    print("=" * 70)
    
    metadata_path = Path("data/knowledge_management/metadata.json")
    progress_path = Path("data/knowledge_management/vector_import_progress.json")
    
    results = {
        'metadata_valid': False,
        'metadata_new_entries': 0,
        'progress_valid': False,
        'progress_new_processed': 0,
        'temp_files_clean': True,
        'vector_index_exists': False
    }
    
    # 验证元数据文件
    if not metadata_path.exists():
        print("❌ 元数据文件不存在")
        return results
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        final_entry_count = len(metadata.get('entries', {}))
        results['metadata_new_entries'] = final_entry_count - initial_state['metadata_entry_count']
        results['metadata_valid'] = True
        
        print(f"✅ 元数据文件: 格式正确")
        print(f"   初始条目数: {initial_state['metadata_entry_count']}")
        print(f"   最终条目数: {final_entry_count}")
        print(f"   新增条目数: {results['metadata_new_entries']}")
        
    except json.JSONDecodeError as e:
        print(f"❌ 元数据文件损坏: {e}")
        return results
    except Exception as e:
        print(f"❌ 读取元数据文件失败: {e}")
        return results
    
    # 验证进度文件
    if not progress_path.exists():
        print("⚠️ 进度文件不存在（可能未保存）")
    else:
        try:
            with open(progress_path, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            
            final_processed = len(progress.get('processed_item_indices', []))
            final_failed = len(progress.get('failed_item_indices', []))
            results['progress_new_processed'] = final_processed - initial_state['progress_processed']
            results['progress_valid'] = True
            
            print(f"✅ 进度文件: 格式正确")
            print(f"   初始已处理: {initial_state['progress_processed']}")
            print(f"   最终已处理: {final_processed}")
            print(f"   新增已处理: {results['progress_new_processed']}")
            print(f"   失败条目数: {final_failed}")
            
        except json.JSONDecodeError as e:
            print(f"❌ 进度文件损坏: {e}")
        except Exception as e:
            print(f"❌ 读取进度文件失败: {e}")
    
    # 检查临时文件残留
    temp_files = [
        metadata_path.with_suffix('.tmp'),
        progress_path.with_suffix('.tmp')
    ]
    temp_files_found = [f for f in temp_files if f.exists()]
    if temp_files_found:
        print(f"⚠️ 发现临时文件残留: {len(temp_files_found)} 个")
        for f in temp_files_found:
            print(f"   - {f}")
        results['temp_files_clean'] = False
    else:
        print("✅ 无临时文件残留（原子性写入正常）")
    
    # 检查向量索引（可能有多个可能的路径）
    possible_index_paths = [
        Path("data/knowledge_management/vector_index.bin"),
        Path("data/knowledge_management/vector_index.faiss"),
        Path("data/knowledge_management/faiss_index.bin"),
        Path("data/knowledge_management/faiss_index.faiss")
    ]
    
    vector_index_path = None
    for path in possible_index_paths:
        if path.exists():
            vector_index_path = path
            break
    
    if vector_index_path:
        results['vector_index_exists'] = True
        index_size = vector_index_path.stat().st_size / 1024 / 1024
        print(f"✅ 向量索引文件: 存在 ({vector_index_path.name}, {index_size:.2f} MB)")
        
        # 检查映射文件
        mapping_path = vector_index_path.with_suffix('.mapping.json')
        if mapping_path.exists():
            mapping_size = mapping_path.stat().st_size / 1024
            print(f"✅ 映射文件: 存在 ({mapping_size:.2f} KB)")
    else:
        print("⚠️ 向量索引文件: 不存在（可能需要重新构建索引）")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="使用少量数据测试向量知识库构建",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--sample-size",
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
        "--dataset-path",
        type=str,
        default="data/frames_dataset.json",
        help="数据集路径（默认: data/frames_dataset.json）"
    )
    
    parser.add_argument(
        "--clear-progress",
        action="store_true",
        help="清除之前的测试进度（从头开始）"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🧪 向量知识库构建测试（少量数据）")
    print("=" * 70)
    print()
    print(f"📦 测试样本数: {args.sample_size}")
    print(f"📏 批次大小: {args.batch_size}")
    print(f"📂 数据集路径: {args.dataset_path}")
    print(f"🔄 清除进度: {args.clear_progress}")
    print()
    
    # 清除进度（如果指定）
    if args.clear_progress:
        progress_path = Path("data/knowledge_management/vector_import_progress.json")
        if progress_path.exists():
            progress_path.unlink()
            print(f"✅ 已清除进度文件: {progress_path}")
    
    # 检查初始状态
    initial_state = check_initial_state()
    
    # 提取测试样本
    dataset_path = Path(args.dataset_path)
    test_samples = extract_test_samples(dataset_path, args.sample_size)
    
    # 转换数据格式
    converted_data = convert_frames_to_import_format(test_samples)
    
    if not converted_data:
        print("❌ 没有可转换的数据")
        sys.exit(1)
    
    # 执行构建
    print("\n" + "=" * 70)
    print("🚀 开始构建向量知识库")
    print("=" * 70)
    print()
    
    try:
        build_vector_knowledge_base_from_list(
            data=converted_data,
            batch_size=args.batch_size,
            resume=not args.clear_progress,  # 如果清除了进度，则从头开始
            retry_failed=True
        )
        print("\n✅ 构建完成")
    except Exception as e:
        print(f"\n❌ 构建失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 验证构建结果
    results = verify_build_result(initial_state, args.sample_size)
    
    # 总结
    print("\n" + "=" * 70)
    print("📊 测试总结")
    print("=" * 70)
    
    all_passed = True
    
    if results['metadata_valid']:
        print("✅ 元数据文件: 正常")
        if results['metadata_new_entries'] > 0:
            print(f"   ✅ 成功导入 {results['metadata_new_entries']} 条新条目")
        else:
            print(f"   ⚠️ 未新增条目（可能已存在）")
    else:
        print("❌ 元数据文件: 异常")
        all_passed = False
    
    if results['progress_valid']:
        print("✅ 进度文件: 正常")
        if results['progress_new_processed'] > 0:
            print(f"   ✅ 进度已更新 ({results['progress_new_processed']} 条)")
        else:
            print(f"   ⚠️ 进度未更新（可能已处理过）")
    else:
        print("⚠️ 进度文件: 异常或不存在")
    
    if results['temp_files_clean']:
        print("✅ 临时文件: 无残留（原子性写入正常）")
    else:
        print("⚠️ 临时文件: 有残留")
        all_passed = False
    
    if results['vector_index_exists']:
        print("✅ 向量索引: 存在")
    else:
        print("⚠️ 向量索引: 不存在（可能需要重新构建）")
    
    print()
    if all_passed:
        print("🎉 测试通过！构建过程正常。")
        print("💡 可以继续使用完整数据集进行构建。")
    else:
        print("⚠️ 测试发现问题，请检查上述问题。")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

