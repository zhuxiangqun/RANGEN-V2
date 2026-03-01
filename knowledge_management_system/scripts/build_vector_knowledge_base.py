#!/usr/bin/env python3
"""
独立构建向量知识库脚本
从数据源导入知识并构建向量索引，不构建知识图谱
支持断点续传、错误数据重导入和详细进度显示

使用方式：
  python build_vector_knowledge_base.py --dataset-path /path/to/frames.json
  python build_vector_knowledge_base.py --dataset-path /path/to/frames.json --retry-failed
  python build_vector_knowledge_base.py --input-file /path/to/data.json --batch-size 50
"""

import sys
import os
import argparse
import json
from pathlib import Path
from typing import Dict, List, Any, Set, Optional
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from knowledge_management_system.api.service_interface import get_knowledge_service
from knowledge_management_system.utils.logger import get_logger

logger = get_logger()

# 进度文件路径
VECTOR_PROGRESS_FILE = "data/knowledge_management/vector_import_progress.json"


def load_vector_progress() -> Dict[str, Any]:
    """加载向量知识库构建进度"""
    progress_file = Path(VECTOR_PROGRESS_FILE)
    if progress_file.exists():
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"加载向量知识库进度文件失败: {e}")
    
    return {
        'processed_item_indices': [],
        'failed_item_indices': [],
        'total_items': 0,
        'start_time': None,
        'last_update': None
    }


def save_vector_progress(progress: Dict[str, Any]) -> None:
    """保存向量知识库构建进度"""
    progress_file = Path(VECTOR_PROGRESS_FILE)
    progress_file.parent.mkdir(parents=True, exist_ok=True)
    
    progress['last_update'] = datetime.now().isoformat()
    
    try:
        # 🚀 修复：使用临时文件写入，然后原子性重命名，避免写入过程中崩溃导致文件损坏
        temp_file = progress_file.with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
        # 原子性重命名
        temp_file.replace(progress_file)
        logger.debug(f"向量知识库进度文件已保存: {progress_file}")
    except Exception as e:
        logger.error(f"保存向量知识库进度文件失败: {e}")
        # 即使保存失败，也不中断程序运行


def build_vector_knowledge_base_from_frames(
    dataset_path: str,
    batch_size: int = 10,
    include_full_text: bool = True,
    resume: bool = True,
    skip_duplicates: bool = True,
    retry_failed: bool = True,
    force_download: bool = False  # 🆕 是否强制重新下载数据集
) -> None:
    """
    从FRAMES数据集构建向量知识库（不构建知识图谱）
    支持断点续传和错误数据重导入
    支持从 Hugging Face 自动下载数据集（如 google/frames-benchmark）
    
    Args:
        dataset_path: FRAMES数据集路径（本地文件路径或 Hugging Face 数据集标识符，如 google/frames-benchmark）
        batch_size: 批次大小
        include_full_text: 是否包含完整文本
        resume: 是否断点续传
        skip_duplicates: 是否跳过重复条目
        retry_failed: 是否重新导入失败的数据
    """
    from knowledge_management_system.scripts.import_wikipedia_from_frames import (
        import_wikipedia_from_frames
    )
    
    # 🆕 检测是否为 Hugging Face 数据集标识符
    actual_dataset_path = dataset_path
    is_huggingface_id = "/" in dataset_path and not dataset_path.startswith("/") and not Path(dataset_path).exists()
    
    if is_huggingface_id:
        # 尝试从 Hugging Face 下载数据集
        print("=" * 70)
        print("📥 检测到 Hugging Face 数据集标识符")
        print("=" * 70)
        print(f"📦 数据集: {dataset_path}")
        print()
        
        try:
            try:
                from datasets import load_dataset
            except (ImportError, PermissionError, OSError) as e:
                print(f"❌ 错误：无法导入 datasets 库: {e}")
                print("   这可能是由于权限限制或依赖问题导致的")
                print("   解决方案：")
                print("   1. 确保在非沙箱环境中运行")
                print("   2. 检查虚拟环境是否正确激活")
                print("   3. 如果是权限问题，可能需要管理员权限")
                sys.exit(1)
            
            # 确定本地保存路径
            if "frames" in dataset_path.lower() or "frames-benchmark" in dataset_path.lower():
                local_dataset_path = Path(__file__).parent.parent.parent / "data" / "frames_dataset.json"
            else:
                # 对于其他数据集，使用数据集名称作为文件名
                dataset_name = dataset_path.replace("/", "_")
                local_dataset_path = Path(__file__).parent.parent.parent / "data" / f"{dataset_name}.json"
            
            # 如果本地文件已存在，检查是否需要强制重新下载
            if local_dataset_path.exists() and not force_download:
                print(f"ℹ️  本地数据集文件已存在: {local_dataset_path}")
                actual_dataset_path = str(local_dataset_path)
                print(f"✅ 将使用本地数据集文件: {actual_dataset_path}")
                print(f"💡 提示：如需重新下载最新版本，请使用 --force-download 选项")
                print()
            else:
                if local_dataset_path.exists() and force_download:
                    print(f"🔄 强制重新下载模式：将删除现有本地文件并重新下载")
                    local_dataset_path.unlink()
                    print(f"   ✅ 已删除现有文件: {local_dataset_path}")
                # 从 Hugging Face 下载原始数据集
                print(f"📥 正在从 Hugging Face 下载数据集: {dataset_path}")
                dataset = load_dataset(dataset_path)
                
                # 获取数据集的分割
                if hasattr(dataset, 'keys'):
                    splits_raw = dataset.keys()  # type: ignore
                    splits = [str(split) for split in splits_raw]
                else:
                    splits = ['default']
                
                print(f"   发现数据集分割: {', '.join(splits)}")
                
                # 🚀 修复：知识库构建不需要分割，合并所有分割的数据
                # 这样可以构建完整的知识库，而不是只使用部分数据
                print(f"   💡 知识库构建：将合并所有分割的数据（共 {len(splits)} 个分割）")
                
                dataset_list = []
                total_items = 0
                
                # 合并所有分割的数据
                for split_name in splits:
                    split_data = dataset[split_name]  # type: ignore
                    split_count = 0
                    
                    print(f"   📦 正在加载分割 '{split_name}'...")
                    for item in split_data:
                        # 安全转换：如果item是dict则直接使用，否则尝试转换
                        if isinstance(item, dict):
                            dataset_list.append(item)
                            split_count += 1
                        else:
                            try:
                                dataset_list.append(dict(item))  # type: ignore
                                split_count += 1
                            except (TypeError, ValueError):
                                continue
                    
                    total_items += split_count
                    print(f"      ✅ 分割 '{split_name}': {split_count} 条数据")
                
                print(f"   ✅ 合并完成：共 {total_items} 条数据（来自 {len(splits)} 个分割）")
                
                # 转换为列表格式并保存
                print(f"💾 保存数据集到本地: {local_dataset_path}")
                local_dataset_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(local_dataset_path, 'w', encoding='utf-8') as f:
                    json.dump(dataset_list, f, ensure_ascii=False, indent=2)
                
                print(f"✅ 数据集已保存到: {local_dataset_path} (共 {len(dataset_list)} 条)")
                actual_dataset_path = str(local_dataset_path)
                print()
            
        except Exception as e:
            print(f"❌ 从 Hugging Face 下载数据集失败: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        # 检查本地文件是否存在
        dataset_file = Path(dataset_path)
        if not dataset_file.exists():
            print(f"❌ 错误：数据集文件不存在: {dataset_path}")
            print()
            print("💡 提示：")
            print("   1. 如果要从 Hugging Face 下载，可以使用数据集标识符，如：")
            print(f"      {Path(__file__).name} --dataset-path google/frames-benchmark")
            print("   2. 或者先下载数据集到本地，然后使用本地路径")
            sys.exit(1)
    
    print("=" * 70)
    print("📊 向量知识库构建工具（FRAMES数据集）")
    print("=" * 70)
    print()
    print(f"📦 数据集路径: {actual_dataset_path}")
    print(f"📏 批次大小: {batch_size}")
    print(f"📝 包含完整文本: {include_full_text}")
    print(f"🔄 断点续传: {resume}")
    print(f"⏭️ 跳过重复: {skip_duplicates}")
    print(f"🔄 重试失败数据: {retry_failed}")
    print()
    print("⚠️ 注意：此命令只构建向量知识库，不构建知识图谱")
    print("   如需构建知识图谱，请使用: python build_knowledge_graph.py")
    print()
    print("=" * 70)
    print()
    
    service = get_knowledge_service()
    
    # 保存原始的 import_knowledge 方法
    original_import = service.import_knowledge
    
    # 创建包装函数，强制 build_graph=False
    def import_without_graph(*args, **kwargs):
        kwargs['build_graph'] = False
        # 🆕 确保启用失败数据重导入
        kwargs['reload_failed'] = retry_failed
        return original_import(*args, **kwargs)
    
    # 临时替换方法
    service.import_knowledge = import_without_graph
    
    try:
        # 🆕 使用 vector_import_progress.json 作为进度文件
        import_wikipedia_from_frames(
            dataset_path=actual_dataset_path,
            batch_size=batch_size,
            include_full_text=include_full_text,
            resume=resume,
            skip_duplicates=skip_duplicates,
            progress_file_path=VECTOR_PROGRESS_FILE  # 🆕 使用统一的进度文件路径
        )
    finally:
        # 恢复原始方法
        service.import_knowledge = original_import
    
    print()
    print("=" * 70)
    print("✅ 向量知识库构建完成！")
    print("=" * 70)


def build_vector_knowledge_base_from_list(
    data: List[Dict[str, Any]],
    batch_size: int = 100,
    resume: bool = True,
    retry_failed: bool = True
) -> None:
    """
    从数据列表构建向量知识库（不构建知识图谱）
    支持断点续传和错误数据重导入
    
    Args:
        data: 知识数据列表
        batch_size: 批次大小
        resume: 是否断点续传
        retry_failed: 是否重新导入失败的数据
    """
    service = get_knowledge_service()
    
    # 加载进度
    progress = load_vector_progress() if resume else {
        'processed_item_indices': [],
        'failed_item_indices': [],
        'total_items': len(data),
        'start_time': datetime.now().isoformat()
    }
    
    processed_indices = set(progress.get('processed_item_indices', []))
    failed_indices = set(progress.get('failed_item_indices', []))
    
    # 过滤需要处理的数据
    if resume:
        if retry_failed:
            # 重新处理失败的数据
            items_to_process = [(i, item) for i, item in enumerate(data) if i in failed_indices]
            logger.info(f"🔄 断点续传模式：重新处理 {len(items_to_process)} 个失败条目")
        else:
            # 跳过已处理的数据
            items_to_process = [(i, item) for i, item in enumerate(data) if i not in processed_indices]
            logger.info(f"🔄 断点续传模式：已处理 {len(processed_indices)} 条，剩余 {len(items_to_process)} 条")
    else:
        items_to_process = [(i, item) for i, item in enumerate(data)]
        logger.info(f"🔄 从头开始构建：共 {len(items_to_process)} 条")
        processed_indices.clear()
        failed_indices.clear()
        progress['processed_item_indices'] = []
        progress['failed_item_indices'] = []
        progress['total_items'] = len(data)
        progress['start_time'] = datetime.now().isoformat()
    
    if not items_to_process:
        logger.info("✅ 所有数据项已处理完成")
        return
    
    print("=" * 70)
    print("📊 向量知识库构建工具（数据列表）")
    print("=" * 70)
    print()
    print(f"📦 总数据条目数: {len(data)}")
    print(f"📦 待处理条目数: {len(items_to_process)}")
    print(f"📏 批次大小: {batch_size}")
    print(f"🔄 断点续传: {resume}")
    print(f"🔄 重试失败数据: {retry_failed}")
    print()
    print("⚠️ 注意：此命令只构建向量知识库，不构建知识图谱")
    print("   如需构建知识图谱，请使用: python build_knowledge_graph.py")
    print()
    print("=" * 70)
    print()
    
    # 分批处理
    total_batches = (len(items_to_process) + batch_size - 1) // batch_size
    import time
    start_time = time.time()
    
    for batch_idx in range(total_batches):
        batch_start = batch_idx * batch_size
        batch_end = min(batch_start + batch_size, len(items_to_process))
        batch_items = items_to_process[batch_start:batch_end]
        
        batch_num = batch_idx + 1
        progress_pct = ((batch_end + len(processed_indices)) / len(data) * 100) if len(data) > 0 else 0
        
        logger.info(f"📦 处理批次 {batch_num}/{total_batches}（条目 {batch_start + 1}-{batch_end}/{len(items_to_process)}，总进度: {progress_pct:.1f}%）...")
        
        # 转换为导入格式
        batch_data = [item for _, item in batch_items]
        
        try:
            knowledge_ids = service.import_knowledge(
                data=batch_data,
                modality="text",
                source_type="list",
                build_graph=False,  # 🆕 不构建知识图谱
                reload_failed=retry_failed  # 🆕 重试失败数据
            )
            
            imported = len([kid for kid in knowledge_ids if kid])
            
            # 🚀 修复：更精确的进度更新逻辑
            # 由于 import_knowledge 可能对内容进行分块，一个原始条目可能产生多个知识条目
            # 我们使用保守策略：如果导入的知识条目数 >= 批次条目数，认为批次成功
            # 否则，如果导入数 > 0，认为部分成功（标记为已处理，但记录警告）
            # 如果导入数 = 0，认为批次失败
            batch_success = imported >= len(batch_data)
            batch_partial = imported > 0 and imported < len(batch_data)
            
            # 更新进度
            for item_idx, _ in batch_items:
                if item_idx < len(data):
                    if batch_success:
                        # 批次完全成功，标记所有条目为已处理
                        processed_indices.add(item_idx)
                        if item_idx in failed_indices:
                            failed_indices.remove(item_idx)
                    elif batch_partial:
                        # 批次部分成功，标记为已处理（但记录警告）
                        processed_indices.add(item_idx)
                        if item_idx in failed_indices:
                            failed_indices.remove(item_idx)
                        logger.warning(f"条目 {item_idx} 部分导入成功（导入 {imported}/{len(batch_data)} 条知识条目）")
                    else:
                        # 批次完全失败，标记为失败
                        failed_indices.add(item_idx)
                        if item_idx in processed_indices:
                            processed_indices.remove(item_idx)
            
            progress['processed_item_indices'] = list(processed_indices)
            progress['failed_item_indices'] = list(failed_indices)
            save_vector_progress(progress)
            
            # 计算进度和预计剩余时间
            elapsed = time.time() - start_time
            processed_count = len(processed_indices)
            avg_time_per_item = elapsed / processed_count if processed_count > 0 else 0
            remaining = len(items_to_process) - (batch_end)
            estimated_remaining = avg_time_per_item * remaining if avg_time_per_item > 0 else 0
            
            logger.info(f"   ✅ 批次 {batch_num} 导入 {imported}/{len(batch_data)} 条知识条目")
            logger.info(f"   📊 总进度: {processed_count}/{len(data)} ({processed_count/len(data)*100:.1f}%)")
            if estimated_remaining > 0:
                if estimated_remaining < 60:
                    logger.info(f"   ⏱️ 预计剩余: {estimated_remaining:.0f}秒")
                elif estimated_remaining < 3600:
                    logger.info(f"   ⏱️ 预计剩余: {estimated_remaining/60:.1f}分钟")
                else:
                    logger.info(f"   ⏱️ 预计剩余: {estimated_remaining/3600:.1f}小时")
            
        except Exception as e:
            logger.error(f"❌ 批次 {batch_num} 导入失败: {e}")
            import traceback
            traceback.print_exc()
            
            # 记录失败的条目
            for item_idx, _ in batch_items:
                failed_indices.add(item_idx)
            progress['failed_item_indices'] = list(failed_indices)
            save_vector_progress(progress)
            continue
    
    print()
    print("=" * 70)
    print("✅ 向量知识库构建完成！")
    if failed_indices:
        print(f"⚠️ 失败条目: {len(failed_indices)} 条（可使用 --retry-failed 重新处理）")
    print("=" * 70)


def build_vector_knowledge_base_from_file(
    file_path: str,
    batch_size: int = 10,
    resume: bool = True,
    retry_failed: bool = True,
    chunk_strategy: str = "sentence"
) -> None:
    """
    🆕 阶段3：从文件构建向量知识库（支持PDF、Markdown、网页等格式）
    
    Args:
        file_path: 文件路径
        batch_size: 批次大小
        resume: 是否断点续传
        retry_failed: 是否重试失败数据
        chunk_strategy: 文档分块策略
    """
    print("=" * 70)
    # 检测是否为URL
    is_url = file_path.startswith('http://') or file_path.startswith('https://')
    source_type = "URL" if is_url else "文件"
    print(f"📊 向量知识库构建工具（{source_type}导入 - LlamaIndex）")
    print("=" * 70)
    print()
    if is_url:
        print(f"🌐 URL地址: {file_path}")
    else:
        print(f"📄 文件路径: {file_path}")
    print(f"📏 批次大小: {batch_size}")
    print(f"🔄 断点续传: {resume}")
    print(f"🔄 重试失败数据: {retry_failed}")
    print(f"📝 分块策略: {chunk_strategy}")
    print()
    print("⚠️ 注意：此命令只构建向量知识库，不构建知识图谱")
    print("   如需构建知识图谱，请使用: python build_knowledge_graph.py")
    print()
    print("=" * 70)
    print()
    
    service = get_knowledge_service()
    
    # 保存原始的 import_knowledge 方法
    original_import = service.import_knowledge
    
    # 创建包装函数，强制 build_graph=False
    def import_without_graph(*args, **kwargs):
        kwargs['build_graph'] = False
        kwargs['reload_failed'] = retry_failed
        kwargs['use_llamaindex'] = True  # 使用LlamaIndex
        kwargs['chunk_strategy'] = chunk_strategy
        return original_import(*args, **kwargs)
    
    # 临时替换方法
    service.import_knowledge = import_without_graph
    
    try:
        # 直接导入文件或URL
        is_url = file_path.startswith('http://') or file_path.startswith('https://')
        if is_url:
            print(f"📥 正在从URL导入: {file_path}...")
        else:
            print(f"📥 正在导入文件: {file_path}...")
        knowledge_ids = service.import_knowledge(
            data=file_path,
            modality="text",
            source_type="file",
            build_graph=False,
            reload_failed=retry_failed,
            use_llamaindex=True,
            chunk_strategy=chunk_strategy
        )
        
        imported = len([kid for kid in knowledge_ids if kid])
        print(f"✅ 成功导入 {imported} 条知识条目")
        
    except Exception as e:
        logger.error(f"❌ 导入文件失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 恢复原始方法
        service.import_knowledge = original_import
    
    print("=" * 70)
    print("✅ 向量知识库构建完成！")
    print("=" * 70)


if __name__ == "__main__":
    print("DEBUG: Entered main function")
    parser = argparse.ArgumentParser(
        description="构建向量知识库（不构建知识图谱）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 从 Hugging Face 自动下载并构建（推荐）
  python build_vector_knowledge_base.py --dataset-path google/frames-benchmark --batch-size 10
  
  # 从本地FRAMES数据集构建（断点续传）
  python build_vector_knowledge_base.py --dataset-path /path/to/frames.json --batch-size 10
  
  # 重新处理失败的数据
  python build_vector_knowledge_base.py --dataset-path /path/to/frames.json --retry-failed
  
  # 从JSON文件构建（从头开始）
  python build_vector_knowledge_base.py --input-file /path/to/data.json --batch-size 50 --no-resume
  
  # 🆕 从PDF文件构建（使用LlamaIndex）
  python build_vector_knowledge_base.py --file /path/to/document.pdf --use-llamaindex
  
  # 🆕 从Markdown文件构建（使用LlamaIndex，指定分块策略）
  python build_vector_knowledge_base.py --file /path/to/document.md --use-llamaindex --chunk-strategy semantic
  
  # 🆕 从网页URL构建（使用LlamaIndex）
  python build_vector_knowledge_base.py --url https://example.com/article
  
  # 🆕 从URL构建（使用--file参数）
  python build_vector_knowledge_base.py --file https://example.com/article --use-llamaindex
        """
    )
    
    parser.add_argument(
        "--dataset-path",
        type=str,
        help="FRAMES数据集路径（本地JSON文件路径或 Hugging Face 数据集标识符，如 google/frames-benchmark）"
    )
    parser.add_argument(
        "--input-file",
        type=str,
        help="输入数据文件路径（JSON格式，包含知识条目列表）"
    )
    parser.add_argument(
        "--file",
        type=str,
        dest="file_path",
        help="🆕 文件路径或URL（支持PDF、Markdown、网页、URL等多种格式，需要--use-llamaindex）"
    )
    parser.add_argument(
        "--url",
        type=str,
        dest="url_path",
        help="🆕 网页URL（等同于 --file <URL> --use-llamaindex 的快捷方式）"
    )
    parser.add_argument(
        "--use-llamaindex",
        action="store_true",
        help="🆕 使用LlamaIndex处理文件（支持PDF、Markdown、网页等格式）"
    )
    parser.add_argument(
        "--chunk-strategy",
        type=str,
        default="sentence",
        choices=["sentence", "semantic", "simple"],
        help="🆕 文档分块策略（仅LlamaIndex模式，默认: sentence）"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="批次大小（默认: 10）"
    )
    parser.add_argument(
        "--no-full-text",
        action="store_true",
        help="不包含完整文本（仅摘要）"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="启用断点续传（从上次中断的地方继续）"
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="不启用断点续传（从头开始）"
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="重新处理之前失败的数据"
    )
    parser.add_argument(
        "--no-skip-duplicates",
        action="store_true",
        help="不跳过重复条目"
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="强制从 Hugging Face 重新下载数据集（即使本地文件已存在）"
    )
    
    args = parser.parse_args()
    
    if args.dataset_path:
        # 从FRAMES数据集构建
        # 检查是否有进度文件
        progress = load_vector_progress()
        resume_enabled = args.resume or (not args.no_resume and len(progress.get('processed_item_indices', [])) > 0)
        
        build_vector_knowledge_base_from_frames(
            dataset_path=args.dataset_path,
            batch_size=args.batch_size,
            include_full_text=not args.no_full_text,
            resume=resume_enabled,
            skip_duplicates=not args.no_skip_duplicates,
            retry_failed=args.retry_failed,
            force_download=args.force_download
        )
    elif args.input_file:
        # 从JSON文件构建
        input_path = Path(args.input_file)
        if not input_path.exists():
            print(f"❌ 文件不存在: {args.input_file}")
            sys.exit(1)
        
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print(f"❌ 输入文件必须是JSON数组格式")
            sys.exit(1)
        
        # 检查是否有进度文件
        progress = load_vector_progress()
        resume_enabled = args.resume or (not args.no_resume and len(progress.get('processed_item_indices', [])) > 0)
        
        build_vector_knowledge_base_from_list(
            data=data,
            batch_size=args.batch_size,
            resume=resume_enabled,
            retry_failed=args.retry_failed
        )
    elif args.url_path:
        # 🆕 从URL构建（快捷方式）
        build_vector_knowledge_base_from_file(
            file_path=args.url_path,
            batch_size=args.batch_size,
            resume=args.resume or (not args.no_resume),
            retry_failed=args.retry_failed,
            chunk_strategy=args.chunk_strategy
        )
    elif args.file_path:
        # 🆕 阶段3：从文件或URL构建（支持PDF、Markdown、网页、URL等格式）
        # 检查是否为URL
        is_url = args.file_path.startswith('http://') or args.file_path.startswith('https://')
        
        if not is_url:
            # 本地文件，检查是否存在
            file_path = Path(args.file_path)
            if not file_path.exists():
                print(f"❌ 文件不存在: {args.file_path}")
                sys.exit(1)
        
        if not args.use_llamaindex:
            print("⚠️  警告：未指定 --use-llamaindex，将尝试使用JSON格式导入")
            print("   如果文件不是JSON格式，请使用 --use-llamaindex 参数")
            # 降级到JSON格式
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        progress = load_vector_progress()
                        resume_enabled = args.resume or (not args.no_resume and len(progress.get('processed_item_indices', [])) > 0)
                        build_vector_knowledge_base_from_list(
                            data=data,
                            batch_size=args.batch_size,
                            resume=resume_enabled,
                            retry_failed=args.retry_failed
                        )
                    else:
                        print(f"❌ JSON文件必须是数组格式")
                        sys.exit(1)
                except json.JSONDecodeError:
                    print(f"❌ 文件不是有效的JSON格式，请使用 --use-llamaindex 参数")
                    sys.exit(1)
        else:
            # 使用LlamaIndex导入文件或URL
            build_vector_knowledge_base_from_file(
                file_path=args.file_path,  # 可以是文件路径或URL
                batch_size=args.batch_size,
                resume=args.resume or (not args.no_resume),
                retry_failed=args.retry_failed,
                chunk_strategy=args.chunk_strategy
            )
    else:
        parser.print_help()
        print()
        print("❌ 错误：必须指定 --dataset-path、--input-file、--file 或 --url")
        sys.exit(1)
