#!/usr/bin/env python3
"""
重新向量化失败的知识条目
识别没有向量的知识条目并重新进行向量化
"""

import sys
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from knowledge_management_system.api.service_interface import get_knowledge_service
from knowledge_management_system.core.vector_index_builder import VectorIndexBuilder
from knowledge_management_system.utils.logger import get_logger

logger = get_logger()


def identify_failed_entries(metadata_file: str = "data/knowledge_management/metadata.json"):
    """识别没有向量的条目"""
    with open(metadata_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    entries = data.get('entries', {})
    failed_entries = []
    
    # 读取向量映射文件，找出哪些条目已经有向量
    mapping_file = Path("data/knowledge_management/vector_index.mapping.json")
    vectorized_ids = set()
    if mapping_file.exists():
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
                # mapping 格式可能是 {index: knowledge_id} 或 {knowledge_id: index}
                if isinstance(mapping, dict):
                    for key, value in mapping.items():
                        if isinstance(key, int) or key.isdigit():
                            # 格式是 {index: knowledge_id}
                            vectorized_ids.add(value)
                        else:
                            # 格式是 {knowledge_id: index}
                            vectorized_ids.add(key)
        except Exception as e:
            logger.warning(f"读取向量映射文件失败: {e}")
    
    for entry_id, entry in entries.items():
        # 检查是否在向量映射中
        if entry_id not in vectorized_ids:
            content = entry.get('metadata', {}).get('content', '') or entry.get('content_preview', '')
            if content:
                failed_entries.append({
                    'id': entry_id,
                    'content': content,
                    'modality': entry.get('modality', 'text')
                })
    
    return failed_entries


def revectorize_entries(entry_ids: list = None, batch_size: int = 50):
    """重新向量化失败的条目"""
    kms = get_knowledge_service()
    if not kms:
        logger.error("无法获取知识库服务")
        return
    
    # 如果未指定条目ID，则识别所有失败的条目
    if entry_ids is None:
        failed_entries = identify_failed_entries()
        entry_ids = [e['id'] for e in failed_entries]
        logger.info(f"识别到 {len(entry_ids)} 个需要重新向量化的条目")
    
    if not entry_ids:
        logger.info("没有需要重新向量化的条目")
        return
    
    # 获取向量索引构建器
    index_builder = kms.index_builder
    
    # 分批处理
    total = len(entry_ids)
    success_count = 0
    fail_count = 0
    
    for i in range(0, total, batch_size):
        batch = entry_ids[i:i + batch_size]
        logger.info(f"处理批次 {i//batch_size + 1}/{(total + batch_size - 1)//batch_size}: {len(batch)} 条")
        
        for entry_id in batch:
            try:
                # 获取条目
                entry = kms.get_knowledge(entry_id)
                if not entry:
                    logger.warning(f"条目不存在: {entry_id}")
                    fail_count += 1
                    continue
                
                # 获取内容
                metadata = entry.get('metadata', {})
                content = metadata.get('content', '') or entry.get('content_preview', '')
                if not content:
                    logger.warning(f"条目内容为空: {entry_id}")
                    fail_count += 1
                    continue
                
                # 获取模态类型
                modality = entry.get('modality', 'text')
                
                # 向量化
                from knowledge_management_system.modalities.text_processor import TextProcessor
                processor = TextProcessor()
                vector = processor.encode(content)
                
                if vector is not None:
                    # 添加到向量索引
                    if index_builder.add_vector(vector, entry_id, modality):
                        success_count += 1
                        logger.info(f"✅ 成功向量化: {entry_id}")
                    else:
                        logger.warning(f"⚠️ 添加到索引失败: {entry_id}")
                        fail_count += 1
                else:
                    logger.warning(f"⚠️ 向量化失败: {entry_id}")
                    fail_count += 1
                    
            except Exception as e:
                logger.error(f"❌ 处理条目失败 {entry_id}: {e}")
                fail_count += 1
        
        # 每批处理后保存索引
        try:
            index_builder._save_index()
            logger.info(f"✅ 已保存索引（批次 {i//batch_size + 1}）")
        except Exception as e:
            logger.warning(f"⚠️ 保存索引失败: {e}")
    
    logger.info(f"重新向量化完成: 成功 {success_count}, 失败 {fail_count}")
    return success_count, fail_count


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="重新向量化失败的知识条目")
    parser.add_argument("--entry-ids", nargs="+", help="指定要重新向量化的条目ID")
    parser.add_argument("--batch-size", type=int, default=50, help="批次大小")
    parser.add_argument("--identify-only", action="store_true", help="仅识别失败的条目，不进行向量化")
    
    args = parser.parse_args()
    
    if args.identify_only:
        failed = identify_failed_entries()
        print(f"\n识别到 {len(failed)} 个需要重新向量化的条目:")
        for i, entry in enumerate(failed[:20], 1):  # 只显示前20个
            print(f"  {i}. {entry['id'][:50]}... ({entry['modality']})")
        if len(failed) > 20:
            print(f"  ... 还有 {len(failed) - 20} 个条目")
    else:
        revectorize_entries(args.entry_ids, args.batch_size)
