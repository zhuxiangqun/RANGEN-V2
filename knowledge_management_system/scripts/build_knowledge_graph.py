#!/usr/bin/env python3
"""
独立构建知识图谱脚本
从已导入的知识条目（向量数据库）中提取实体和关系，构建知识图谱
支持断点续传、错误数据重导入和详细进度显示

使用方式：
  python build_knowledge_graph.py                    # 从所有条目构建
  python build_knowledge_graph.py --batch-size 50    # 指定批次大小
  python build_knowledge_graph.py --resume           # 断点续传
  python build_knowledge_graph.py --retry-failed      # 重新处理失败条目
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Set, Optional
import time
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from knowledge_management_system.api.service_interface import get_knowledge_service
from knowledge_management_system.utils.logger import get_logger

logger = get_logger()

# 进度文件路径
GRAPH_PROGRESS_FILE = "data/knowledge_management/graph_progress.json"


def load_graph_progress() -> Dict[str, Any]:
    """加载知识图谱构建进度"""
    progress_file = Path(GRAPH_PROGRESS_FILE)
    if progress_file.exists():
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"加载知识图谱进度文件失败: {e}")
    
    return {
        'processed_entry_ids': [],
        'failed_entry_ids': [],
        'total_entries': 0,
        'start_time': None,
        'last_update': None,
        # 🚀 新增：统计信息
        'extracted_entry_ids': [],  # 提取到数据的条目ID
        'no_data_entry_ids': []  # 未提取到数据的条目ID
    }


def save_graph_progress(progress: Dict[str, Any]) -> None:
    """保存知识图谱构建进度"""
    progress_file = Path(GRAPH_PROGRESS_FILE)
    progress_file.parent.mkdir(parents=True, exist_ok=True)
    
    progress['last_update'] = datetime.now().isoformat()
    
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def build_knowledge_graph_from_existing_entries(
    batch_size: int = 200,  # 🚀 性能优化：增加默认批次大小（从100增加到200）
    extract_entities: bool = True,
    extract_relations: bool = True,
    resume: bool = True,
    retry_failed: bool = False,
    auto_retry_failed: bool = True
) -> Dict[str, Any]:
    """
    从已存在的知识条目中构建知识图谱（支持断点续传和错误重试）
    
    Args:
        batch_size: 每批处理的条目数
        extract_entities: 是否提取实体
        extract_relations: 是否提取关系
        resume: 是否断点续传
        retry_failed: 是否只重新处理之前失败的条目（不处理未处理的条目）
        auto_retry_failed: 是否自动重试失败的条目（默认True，在断点续传时自动包含失败的条目）
    
    Returns:
        构建结果统计
    """
    service = get_knowledge_service()
    
    # 加载进度
    progress = load_graph_progress() if resume else {
        'processed_entry_ids': [],
        'failed_entry_ids': [],
        'total_entries': 0,
        'start_time': datetime.now().isoformat()
    }
    
    processed_entry_ids = set(progress.get('processed_entry_ids', []))
    failed_entry_ids = set(progress.get('failed_entry_ids', []))
    
    # 获取所有知识条目
    # 🚀 修复：使用 knowledge_manager 的 list_knowledge 方法
    all_knowledge_entries = service.knowledge_manager.list_knowledge(limit=100000)  # 设置一个足够大的limit
    total_entries = len(all_knowledge_entries)
    
    if total_entries == 0:
        logger.warning("⚠️ 知识库中没有条目，无法构建知识图谱")
        return {
            'total_entries': 0,
            'entities_created': 0,
            'relations_created': 0,
            'elapsed_time': 0
        }
    
    # 🚀 优化：从条目字典中提取知识ID，并构建ID到条目的映射（避免重复查询）
    # list_knowledge() 返回的是条目字典列表，每个条目包含 'id' 和 'metadata' 字段
    all_knowledge_ids = []
    knowledge_id_to_entry = {}  # 🚀 优化：构建ID到条目的映射，避免重复查询
    
    for entry in all_knowledge_entries:
        knowledge_id = entry.get('id')
        if knowledge_id:
            all_knowledge_ids.append(knowledge_id)
            knowledge_id_to_entry[knowledge_id] = entry  # 保存条目数据，避免后续重复查询
    
    total_entries = len(all_knowledge_ids)
    
    # 更新总条目数（在开始处理前就保存，确保进度检查脚本能正确显示）
    progress['total_entries'] = total_entries
    save_graph_progress(progress)  # 🎯 修复：立即保存，确保进度检查脚本能正确显示
    
    # 过滤需要处理的条目
    if resume:
        if retry_failed:
            # 只重新处理失败的条目（不处理未处理的条目）
            entries_to_process = [kid for kid in all_knowledge_ids if kid in failed_entry_ids]
            logger.info(f"🔄 断点续传模式：只重新处理 {len(entries_to_process)} 个失败条目")
        else:
            # 🚀 优化：默认自动重试失败的条目（合并未处理和失败的条目）
            if auto_retry_failed:
                # 跳过已成功处理的条目，但包含之前失败的条目（自动重试）
                entries_to_process = [
                    kid for kid in all_knowledge_ids 
                    if kid not in processed_entry_ids  # 未处理的条目
                    or kid in failed_entry_ids  # 或之前失败的条目（自动重试）
                ]
                failed_count = len([kid for kid in entries_to_process if kid in failed_entry_ids])
                if failed_count > 0:
                    logger.info(f"🔄 断点续传模式：已处理 {len(processed_entry_ids)} 条，剩余 {len(entries_to_process)} 条（其中 {failed_count} 个失败条目将自动重试）")
                else:
                    logger.info(f"🔄 断点续传模式：已处理 {len(processed_entry_ids)} 条，剩余 {len(entries_to_process)} 条")
            else:
                # 不自动重试失败的条目（只处理未处理的条目）
                entries_to_process = [kid for kid in all_knowledge_ids if kid not in processed_entry_ids]
                logger.info(f"🔄 断点续传模式：已处理 {len(processed_entry_ids)} 条，剩余 {len(entries_to_process)} 条（不重试失败的条目）")
    else:
        entries_to_process = all_knowledge_ids
        logger.info(f"🔄 从头开始构建：共 {len(entries_to_process)} 条")
        processed_entry_ids.clear()
        failed_entry_ids.clear()
        progress['processed_entry_ids'] = []
        progress['failed_entry_ids'] = []
        progress['start_time'] = datetime.now().isoformat()
    
    if not entries_to_process:
        logger.info("✅ 所有条目已处理完成")
        return {
            'total_entries': total_entries,
            'entities_created': 0,
            'relations_created': 0,
            'elapsed_time': 0,
            'message': '所有条目已处理'
        }
    
    logger.info(f"📊 开始构建知识图谱：")
    logger.info(f"   总条目数: {total_entries}")
    logger.info(f"   待处理: {len(entries_to_process)}")
    logger.info(f"   已处理: {len(processed_entry_ids)}")
    logger.info(f"   失败: {len(failed_entry_ids)}")
    logger.info(f"   批次大小: {batch_size}")
    logger.info(f"   提取实体: {extract_entities}")
    logger.info(f"   提取关系: {extract_relations}")
    
    start_time = time.time()
    graph_data = []
    processed_count = 0
    new_failed_ids = []
    
    # 🚀 优化：累计统计信息（用于最终报告）
    total_entities_created = 0
    total_relations_created = 0
    
    # 分批处理
    total_batches = (len(entries_to_process) + batch_size - 1) // batch_size
    
    for batch_idx in range(total_batches):
        batch_start = batch_idx * batch_size
        batch_end = min(batch_start + batch_size, len(entries_to_process))
        batch_knowledge_ids = entries_to_process[batch_start:batch_end]
        
        batch_num = batch_idx + 1
        progress_pct = ((batch_end + len(processed_entry_ids)) / total_entries * 100) if total_entries > 0 else 0
        
        logger.info(f"📦 处理批次 {batch_num}/{total_batches}（条目 {batch_start + 1}-{batch_end}/{len(entries_to_process)}，总进度: {progress_pct:.1f}%）...")
        
        # 🚀 优化：批量处理文本向量化，提升性能
        # 🚀 性能优化：直接使用已获取的条目数据，避免重复查询数据库
        # 收集所有条目的内容
        batch_contents = []
        batch_metadata_list = []
        batch_knowledge_id_map = {}  # 映射：索引 -> knowledge_id
        
        for idx, knowledge_id in enumerate(batch_knowledge_ids):
            try:
                # 🚀 性能优化：优先使用已缓存的条目数据，避免重复查询
                if knowledge_id in knowledge_id_to_entry:
                    entry_info = knowledge_id_to_entry[knowledge_id]
                else:
                    # 回退：如果缓存中没有，再查询（这种情况应该很少）
                    entry_info = service.knowledge_manager.get_knowledge(knowledge_id)
                    if entry_info:
                        knowledge_id_to_entry[knowledge_id] = entry_info  # 缓存结果
                
                if not entry_info:
                    new_failed_ids.append(knowledge_id)
                    continue
                
                entry_metadata = entry_info.get('metadata', {})
                content = entry_metadata.get('content', '')
                
                if not content:
                    new_failed_ids.append(knowledge_id)
                    continue
                
                batch_contents.append(content)
                batch_metadata_list.append(entry_metadata)
                batch_knowledge_id_map[len(batch_contents) - 1] = knowledge_id
                
            except Exception as e:
                kid_str = str(knowledge_id) if knowledge_id else "unknown"
                logger.warning(f"⚠️ 获取条目 {kid_str[:50]}... 时出错: {e}")
                new_failed_ids.append(knowledge_id)
                failed_entry_ids.add(knowledge_id)
                continue
        
        # 🚀 优化：批量向量化文本（如果使用graph_builder的build_from_text方法）
        # 注意：_extract_entities_and_relations 不使用embedding，所以这里主要是优化graph_builder的调用
        # 如果后续需要，可以在这里添加批量向量化逻辑
        
        # 🚀 阶段1优化：批量向量化文本，提升性能
        # 如果使用graph_builder的build_from_text方法，可以批量向量化文本
        # 注意：_extract_entities_and_relations内部会按优先级尝试多种方法，可能不需要向量化
        # 但如果需要向量化，这里可以批量处理
        
        # 🚀 阶段2优化：使用线程池并发提取实体和关系（提高处理速度）
        # 注意：保持每个条目处理完后立即保存进度，确保断点续传功能正常
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import threading
        
        # 🚀 性能优化：增加并发数（从10增加到20），提升处理速度
        # 注意：根据API限流和系统资源调整，避免过多并发导致资源竞争
        # 可以通过环境变量 MAX_WORKERS 自定义并发数
        import os
        max_workers = int(os.getenv('MAX_WORKERS', '20'))  # 默认20个并发
        max_workers = min(max_workers, len(batch_contents))  # 不超过批次大小
        
        def extract_for_entry(idx: int, content: str, entry_metadata: Dict[str, Any], knowledge_id: Optional[str]) -> tuple:
            """提取单个条目的实体和关系"""
            try:
                extracted_data = service._extract_entities_and_relations(
                    content,
                    entry_metadata
                )
                return (idx, knowledge_id, extracted_data, None)
            except Exception as e:
                return (idx, knowledge_id, None, e)
        
        # 🚀 性能优化：如果使用LLM提取，尝试批量处理
        # 检查是否需要使用LLM（当其他方法都失败时，LLM是fallback）
        # 由于LLM是fallback方法，这里先尝试批量处理需要LLM的条目
        # 注意：_extract_entities_and_relations内部会按优先级尝试多种方法，LLM是最后的选择
        # 所以这里主要是优化LLM调用部分，而不是整个提取过程
        
        # 并发提取实体和关系
        if max_workers > 1 and len(batch_contents) > 1:
            logger.debug(f"   🔄 使用线程池并发提取（{max_workers}个并发）...")
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                future_to_entry = {
                    executor.submit(
                        extract_for_entry,
                        idx,
                        content,
                        entry_metadata,
                        batch_knowledge_id_map.get(idx)
                    ): (idx, batch_knowledge_id_map.get(idx))
                    for idx, (content, entry_metadata) in enumerate(zip(batch_contents, batch_metadata_list))
                    if batch_knowledge_id_map.get(idx) is not None
                }
                
                # 🚀 性能优化：收集所有结果后再统一处理，减少进度保存频率
                # 使用线程锁确保线程安全
                import threading
                progress_lock = threading.Lock()
                
                results = {}
                for future in as_completed(future_to_entry):
                    idx, knowledge_id = future_to_entry[future]
                    try:
                        result = future.result()
                        results[idx] = result
                    except Exception as e:
                        logger.warning(f"⚠️ 并发提取任务异常: {e}")
                        results[idx] = (idx, knowledge_id, None, e)
                
                # 🚀 性能优化：统一处理所有结果，减少进度保存频率
                # 🚀 优化：统计未提取到数据的条目数量
                no_data_count = 0
                for idx in sorted(results.keys()):
                    idx, knowledge_id, extracted_data, error = results[idx]
                    
                    # 🚀 修复：检查knowledge_id是否为None
                    if knowledge_id is None:
                        continue
                    
                    # 使用锁确保线程安全
                    with progress_lock:
                        if error:
                            kid_str = str(knowledge_id) if knowledge_id else "unknown"
                            logger.warning(f"⚠️ 处理条目 {kid_str[:50]}... 时出错: {error}")
                            new_failed_ids.append(knowledge_id)
                            failed_entry_ids.add(knowledge_id)
                            processed_entry_ids.add(knowledge_id)
                            processed_count += 1
                        else:
                            if extracted_data:
                                graph_data.extend(extracted_data)
                                logger.info(f"   ✅ 条目 {knowledge_id[:8] if knowledge_id else 'unknown'}... 提取到 {len(extracted_data)} 条数据，graph_data 现在有 {len(graph_data)} 条")
                                # 🚀 新增：记录提取到数据的条目
                                if 'extracted_entry_ids' not in progress:
                                    progress['extracted_entry_ids'] = []
                                if knowledge_id not in progress['extracted_entry_ids']:
                                    progress['extracted_entry_ids'].append(knowledge_id)
                                # 从未提取列表中移除（如果存在）
                                if 'no_data_entry_ids' in progress and knowledge_id in progress['no_data_entry_ids']:
                                    progress['no_data_entry_ids'].remove(knowledge_id)
                            else:
                                # 🚀 优化：降级为DEBUG级别，减少日志噪音
                                # 注意：未提取到数据可能是正常的（某些条目可能不包含实体/关系信息）
                                no_data_count += 1
                                logger.debug(f"   ⚠️ 条目 {knowledge_id[:8] if knowledge_id else 'unknown'}... 未提取到数据（extracted_data 为空）")
                                # 🚀 新增：记录未提取到数据的条目
                                if 'no_data_entry_ids' not in progress:
                                    progress['no_data_entry_ids'] = []
                                if knowledge_id not in progress['no_data_entry_ids']:
                                    progress['no_data_entry_ids'].append(knowledge_id)
                                # 从提取列表中移除（如果存在）
                                if 'extracted_entry_ids' in progress and knowledge_id in progress['extracted_entry_ids']:
                                    progress['extracted_entry_ids'].remove(knowledge_id)
                            
                            processed_entry_ids.add(knowledge_id)
                            if knowledge_id in failed_entry_ids:
                                failed_entry_ids.remove(knowledge_id)
                            processed_count += 1
                
                # 🚀 优化：批次处理完成后，统计并记录未提取到数据的条目数量
                if no_data_count > 0:
                    logger.debug(f"   📊 批次 {batch_num} 中有 {no_data_count} 个条目未提取到数据（这是正常的，某些条目可能不包含实体/关系信息）")
                
                # 🚀 性能优化：批次处理完成后统一保存进度（减少I/O操作）
                progress['processed_entry_ids'] = list(processed_entry_ids)
                progress['failed_entry_ids'] = list(failed_entry_ids)
                save_graph_progress(progress)
        else:
                # 串行处理（单线程或单条目）
            # 🚀 优化：统计未提取到数据的条目数量，减少日志噪音
            no_data_count = 0
            for idx, (content, entry_metadata) in enumerate(zip(batch_contents, batch_metadata_list)):
                knowledge_id = batch_knowledge_id_map.get(idx)
                if not knowledge_id:
                    continue
                    
                try:
                    # 提取实体和关系
                    extracted_data = service._extract_entities_and_relations(
                        content,
                        entry_metadata
                    )
                    
                    if extracted_data:
                        graph_data.extend(extracted_data)
                        logger.info(f"   ✅ 条目 {knowledge_id[:8] if knowledge_id else 'unknown'}... 提取到 {len(extracted_data)} 条数据，graph_data 现在有 {len(graph_data)} 条")
                        # 🚀 新增：记录提取到数据的条目
                        if 'extracted_entry_ids' not in progress:
                            progress['extracted_entry_ids'] = []
                        if knowledge_id not in progress['extracted_entry_ids']:
                            progress['extracted_entry_ids'].append(knowledge_id)
                        # 从未提取列表中移除（如果存在）
                        if 'no_data_entry_ids' in progress and knowledge_id in progress['no_data_entry_ids']:
                            progress['no_data_entry_ids'].remove(knowledge_id)
                    else:
                        # 🚀 优化：降级为DEBUG级别，减少日志噪音
                        no_data_count += 1
                        logger.debug(f"   ⚠️ 条目 {knowledge_id[:8] if knowledge_id else 'unknown'}... 未提取到数据（extracted_data 为空）")
                        # 🚀 新增：记录未提取到数据的条目
                        if 'no_data_entry_ids' not in progress:
                            progress['no_data_entry_ids'] = []
                        if knowledge_id not in progress['no_data_entry_ids']:
                            progress['no_data_entry_ids'].append(knowledge_id)
                        # 从提取列表中移除（如果存在）
                        if 'extracted_entry_ids' in progress and knowledge_id in progress['extracted_entry_ids']:
                            progress['extracted_entry_ids'].remove(knowledge_id)
                    
                    # 🎯 关键修复：无论提取结果如何，都记录为已处理（支持断点续传）
                    # 即使 extracted_data 为空（没有提取到实体和关系），也应该标记为已处理
                    # 这样断点续传时就不会重复处理该条目
                    processed_entry_ids.add(knowledge_id)
                    if knowledge_id in failed_entry_ids:
                        failed_entry_ids.remove(knowledge_id)
                    processed_count += 1
                    
                except Exception as e:
                    kid_str = str(knowledge_id) if knowledge_id else "unknown"
                    logger.warning(f"⚠️ 处理条目 {kid_str[:50]}... 时出错: {e}")
                    new_failed_ids.append(knowledge_id)
                    failed_entry_ids.add(knowledge_id)
                    # 🚀 修复：失败时也记录为已处理（保持断点续传功能）
                    processed_entry_ids.add(knowledge_id)
                    processed_count += 1
                    continue
            
            # 🚀 优化：批次处理完成后，统计并记录未提取到数据的条目数量
            if no_data_count > 0:
                logger.debug(f"   📊 批次 {batch_num} 中有 {no_data_count} 个条目未提取到数据（这是正常的，某些条目可能不包含实体/关系信息）")
                
                # 🚀 性能优化：批次处理完成后统一保存进度（减少I/O操作）
                progress['processed_entry_ids'] = list(processed_entry_ids)
                progress['failed_entry_ids'] = list(failed_entry_ids)
                save_graph_progress(progress)
        
        # 🚀 优化：每批处理完后立即构建和保存（降低内存占用，避免数据丢失）
        logger.info(f"   📊 批次 {batch_num} 处理完成，graph_data 有 {len(graph_data)} 条数据")
        if graph_data:
            logger.info(f"   🔄 构建批次 {batch_num} 的知识图谱数据（{len(graph_data)} 条）...")
            batch_graph_start_time = time.time()
            
            try:
                # 立即构建和保存当前批次的数据
                # 🚀 优化：启用属性合并
                batch_graph_result = service.graph_builder.build_from_structured_data(
                    graph_data,
                    **{"merge_properties": True}  # 使用kwargs避免类型检查问题
                )
                batch_graph_elapsed = time.time() - batch_graph_start_time
                
                # 累计统计
                batch_entities = batch_graph_result.get('entities_created', 0)
                batch_relations = batch_graph_result.get('relations_created', 0)
                total_entities_created += batch_entities
                total_relations_created += batch_relations
                
                logger.info(f"   ✅ 批次 {batch_num} 构建完成: {batch_entities}个实体, {batch_relations}条关系 (耗时: {batch_graph_elapsed:.1f}秒)")
                
                # 清空，释放内存
                graph_data = []
                
            except Exception as e:
                logger.error(f"❌ 批次 {batch_num} 构建失败: {e}")
                logger.error(f"   graph_data 长度: {len(graph_data)}")
                logger.error(f"   graph_data 示例（前3条）: {graph_data[:3] if graph_data else '[]'}")
                # 不清空 graph_data，保留数据以便后续重试
                import traceback
                logger.error(f"详细错误:\n{traceback.format_exc()}")
        
        # 🚀 性能优化：每批处理完后保存进度（作为备份，防止遗漏）
        # 注意：在并发处理模式下，进度已在批次内统一保存，这里作为双重保障
        progress['processed_entry_ids'] = list(processed_entry_ids)
        progress['failed_entry_ids'] = list(failed_entry_ids)
        save_graph_progress(progress)
        
        # 每批处理完后显示进度
        elapsed = time.time() - start_time
        avg_time_per_entry = elapsed / processed_count if processed_count > 0 else 0
        remaining = len(entries_to_process) - (batch_end)
        estimated_remaining = avg_time_per_entry * remaining if avg_time_per_entry > 0 else 0
        
        logger.info(f"   ✅ 已处理 {processed_count}/{len(entries_to_process)} 条（累计: {total_entities_created}个实体, {total_relations_created}条关系）")
        if estimated_remaining > 0:
            if estimated_remaining < 60:
                logger.info(f"   ⏱️ 预计剩余: {estimated_remaining:.0f}秒")
            elif estimated_remaining < 3600:
                logger.info(f"   ⏱️ 预计剩余: {estimated_remaining/60:.1f}分钟")
            else:
                logger.info(f"   ⏱️ 预计剩余: {estimated_remaining/3600:.1f}小时")
    
    # 🚀 优化：所有批次处理完成后，不再需要构建（因为每批都已经构建了）
    # 但如果还有残留数据（比如最后一批构建失败），尝试构建
    if graph_data:
        logger.warning(f"⚠️ 检测到残留数据（{len(graph_data)} 条），尝试构建...")
        try:
            # 🚀 优化：启用属性合并
            final_graph_result = service.graph_builder.build_from_structured_data(
                graph_data,
                **{"merge_properties": True}  # 使用kwargs避免类型检查问题
            )
            total_entities_created += final_graph_result.get('entities_created', 0)
            total_relations_created += final_graph_result.get('relations_created', 0)
            graph_data = []  # 清空
        except Exception as e:
            logger.error(f"❌ 残留数据构建失败: {e}")
    
    total_elapsed = time.time() - start_time
    
    # 更新进度：如果成功构建，清除失败记录
    if len(new_failed_ids) == 0:
        progress['failed_entry_ids'] = []
    save_graph_progress(progress)
    
    # 🚀 新增：从进度文件中获取准确的统计信息
    extracted_count = len(progress.get('extracted_entry_ids', []))
    no_data_count = len(progress.get('no_data_entry_ids', []))
    
    logger.info(f"\n✅ 知识图谱构建完成：")
    logger.info(f"   处理条目: {processed_count}/{len(entries_to_process)}")
    if processed_count > 0:
        logger.info(f"   ✅ 提取到数据: {extracted_count} 条 ({extracted_count/processed_count*100:.1f}%)")
        logger.info(f"   ⚠️  未提取到数据: {no_data_count} 条 ({no_data_count/processed_count*100:.1f}%)")
    logger.info(f"   创建实体: {total_entities_created}")
    logger.info(f"   创建关系: {total_relations_created}")
    logger.info(f"   总耗时: {total_elapsed:.1f}秒")
    if new_failed_ids:
        logger.warning(f"   ⚠️ 失败条目: {len(new_failed_ids)} 条（可通过 --retry-failed 重新处理）")
    
    return {
        'total_entries': total_entries,
        'processed_entries': processed_count,
        'extracted_entries': extracted_count,
        'no_data_entries': no_data_count,
        'entities_created': total_entities_created,
        'relations_created': total_relations_created,
        'total_elapsed_time': total_elapsed,
        'failed_count': len(new_failed_ids)
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="从已导入的知识条目（向量数据库）中构建知识图谱",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 从所有条目构建
  python build_knowledge_graph.py
  
  # 指定批次大小
  python build_knowledge_graph.py --batch-size 50
  
  # 断点续传
  python build_knowledge_graph.py --resume
  
  # 重新处理失败条目
  python build_knowledge_graph.py --retry-failed
  
  # 不提取实体
  python build_knowledge_graph.py --no-entities
        """
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="每批处理的条目数（默认: 100）"
    )
    parser.add_argument(
        "--no-entities",
        action="store_true",
        help="不提取实体"
    )
    parser.add_argument(
        "--no-relations",
        action="store_true",
        help="不提取关系"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="断点续传（从上次中断的地方继续）"
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="只重新处理之前失败的条目（不处理未处理的条目）"
    )
    parser.add_argument(
        "--no-retry-failed",
        action="store_true",
        help="不自动重试失败的条目（只处理未处理的条目）"
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="不启用断点续传（从头开始）"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("📊 知识图谱构建工具")
    print("=" * 70)
    print()
    
    # 检查进度文件
    progress = load_graph_progress()
    if progress.get('processed_entry_ids'):
        processed_count = len(progress.get('processed_entry_ids', []))
        extracted_count = len(progress.get('extracted_entry_ids', []))
        no_data_count = len(progress.get('no_data_entry_ids', []))
        failed_count = len(progress.get('failed_entry_ids', []))
        
        print(f"📋 检测到进度文件：")
        print(f"   已处理: {processed_count} 条")
        if processed_count > 0:
            print(f"   ✅ 提取到数据: {extracted_count} 条 ({extracted_count/processed_count*100:.1f}%)")
            print(f"   ⚠️  未提取到数据: {no_data_count} 条 ({no_data_count/processed_count*100:.1f}%)")
        print(f"   失败: {failed_count} 条")
        print()
    
    # 🚀 优化：默认自动重试失败的条目（除非显式禁用）
    # 如果使用 --retry-failed，只处理失败的条目
    # 如果使用 --no-retry-failed，不重试失败的条目
    # 否则（默认），自动重试失败的条目
    auto_retry_failed = not args.no_retry_failed  # 默认自动重试
    
    result = build_knowledge_graph_from_existing_entries(
        batch_size=args.batch_size,
        extract_entities=not args.no_entities,
        extract_relations=not args.no_relations,
        resume=args.resume or (not args.no_resume and len(progress.get('processed_entry_ids', [])) > 0),
        retry_failed=args.retry_failed,  # 如果指定 --retry-failed，只处理失败的条目
        auto_retry_failed=auto_retry_failed  # 默认自动重试失败的条目
    )
    
    print()
    print("=" * 70)
    if 'error' in result:
        print(f"❌ 构建失败: {result['error']}")
        sys.exit(1)
    else:
        print("✅ 构建完成！")
        print(f"\n📊 最终统计：")
        print(f"   总条目数: {result.get('total_entries', 0)}")
        print(f"   已处理: {result.get('processed_entries', 0)}")
        if result.get('processed_entries', 0) > 0:
            print(f"   ✅ 提取到数据: {result.get('extracted_entries', 0)} 条 ({result.get('extracted_entries', 0)/result.get('processed_entries', 1)*100:.1f}%)")
            print(f"   ⚠️  未提取到数据: {result.get('no_data_entries', 0)} 条 ({result.get('no_data_entries', 0)/result.get('processed_entries', 1)*100:.1f}%)")
        print(f"   实体数: {result.get('entities_created', 0)}")
        print(f"   关系数: {result.get('relations_created', 0)}")
        print(f"   总耗时: {result.get('total_elapsed_time', 0):.1f}秒")
        if result.get('failed_count', 0) > 0:
            print(f"\n⚠️ 有 {result['failed_count']} 个条目处理失败，可使用 --retry-failed 重新处理")
        print("=" * 70)
        sys.exit(0)
