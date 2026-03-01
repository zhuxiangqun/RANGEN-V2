#!/usr/bin/env python3
"""
从FRAMES数据集导入Wikipedia链接作为知识条目
- 每个Wikipedia链接作为一个知识条目
- 条目名称使用数据集的prompt（query）内容
- 支持断点续传和查重
"""

import json
import sys
import os
import re
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Set
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from knowledge_management_system.api.service_interface import get_knowledge_service
from knowledge_management_system.utils.wikipedia_fetcher import get_wikipedia_fetcher
from knowledge_management_system.utils.logger import get_logger

logger = get_logger()

# 进度文件路径
PROGRESS_FILE = "data/knowledge_management/import_progress.json"


def load_progress(progress_file_path: str = None) -> Dict[str, Any]:
    """加载导入进度"""
    progress_file = Path(progress_file_path or PROGRESS_FILE)
    if progress_file.exists():
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"加载进度文件失败: {e}")
    
    return {
        'processed_item_indices': [],
        'failed_item_indices': [],  # 🚀 修复：添加失败条目跟踪
        'total_items': 0,
        'start_time': None,
        'last_update': None
    }


def save_progress(progress: Dict[str, Any], progress_file_path: str = None) -> None:
    """保存导入进度"""
    progress_file = Path(progress_file_path or PROGRESS_FILE)
    progress_file.parent.mkdir(parents=True, exist_ok=True)
    
    progress['last_update'] = datetime.now().isoformat()
    
    try:
        # 🚀 修复：使用临时文件写入，然后原子性重命名，避免写入过程中崩溃导致文件损坏
        temp_file = progress_file.with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
        # 原子性重命名
        temp_file.replace(progress_file)
        logger.debug(f"进度文件已保存: {progress_file}")
    except Exception as e:
        logger.error(f"保存进度文件失败: {e}")
        # 即使保存失败，也不中断程序运行


def clean_wikipedia_content(content: str) -> str:
    """
    清理Wikipedia内容（移除引用标记、格式化等）
    
    Args:
        content: 原始内容
        
    Returns:
        清理后的内容
    """
    if not content:
        return ""
    
    # 1. 清理引用标记（如 [ 82 ], [ 83 ]）
    content = re.sub(r'\[\s*\d+\s*\]', '', content)
    
    # 2. 清理JSON属性残留（如 "}},"i":0}}]}' id="mwBXM"）
    # 匹配各种JSON属性格式
    content = re.sub(r'["\']?\}\},"[^"]*":\d+\}\}\}\]?["\']?\s*id=["\'][^"\']*["\']', '', content)
    content = re.sub(r'["\']?\}\},"[^"]*":\d+\}\}\}\]?["\']?', '', content)
    # 清理单独的id属性（如 id="mwBXM"）
    content = re.sub(r'\s*id=["\'][^"\']*["\']', '', content)
    # 清理JSON片段（如 "}},"i":0}}]}'）
    content = re.sub(r'["\']?\}\}[^"\']*["\']?', '', content)
    
    # 3. 清理HTML实体
    try:
        import html
        content = html.unescape(content)
    except Exception:
        pass
    
    # 4. 清理多余的空白字符
    content = re.sub(r'[ \t]+', ' ', content)
    content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
    
    # 5. 清理行首行尾空白
    lines = [line.strip() for line in content.split('\n')]
    lines = [line for line in lines if line]  # 移除空行
    content = '\n'.join(lines)
    
    return content.strip()


def extract_wikipedia_links_from_item(item: Dict[str, Any]) -> List[str]:
    """从单个FRAMES数据项中提取Wikipedia链接"""
    wikipedia_links = []
    
    def parse_wikipedia_links(value):
        """解析Wikipedia链接的辅助函数"""
        parsed_links = []
        
        if isinstance(value, list):
            parsed_links = [link for link in value if isinstance(link, str) and 'wikipedia.org' in link.lower() and link.strip()]
        elif isinstance(value, str):
            # 方式1: JSON解析
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    parsed_links = [link for link in parsed if isinstance(link, str) and 'wikipedia.org' in link.lower() and link.strip()]
            except:
                pass
            
            # 方式2: ast.literal_eval
            if not parsed_links:
                try:
                    import ast
                    parsed = ast.literal_eval(value)
                    if isinstance(parsed, list):
                        parsed_links = [link for link in parsed if isinstance(link, str) and 'wikipedia.org' in link.lower() and link.strip()]
                except:
                    pass
            
            # 方式3: 正则表达式
            if not parsed_links:
                import re
                url_pattern = r'https?://[^\s,\[\]]*wikipedia\.org[^\s,\[\]]*'
                found_urls = re.findall(url_pattern, value)
                parsed_links = [url.strip("'\"") for url in found_urls if url.strip()]
        
        return parsed_links
    
    # 优先从 wiki_links 字段提取
    if 'wiki_links' in item and item['wiki_links']:
        links = parse_wikipedia_links(item['wiki_links'])
        wikipedia_links.extend(links)
        
    # 尝试从 metadata.wiki_links 提取 (适配 documents.json 格式)
    if not wikipedia_links and 'metadata' in item and isinstance(item['metadata'], dict):
        metadata = item['metadata']
        if 'wiki_links' in metadata and metadata['wiki_links']:
            links = parse_wikipedia_links(metadata['wiki_links'])
            wikipedia_links.extend(links)
    
    # 如果 wiki_links 没有或为空，尝试从 evidence 字段提取
    if not wikipedia_links and 'evidence' in item and item['evidence']:
        links = parse_wikipedia_links(item['evidence'])
        wikipedia_links.extend(links)
    
    # 去重
    return list(set([link for link in wikipedia_links if link and link.strip()]))


def check_item_processed(service, prompt: str, item_index: int) -> bool:
    """检查item是否已经导入过（基于item_index或prompt查重）"""
    try:
        # 查询知识库，检查是否有相同item_index或prompt的条目
        results = service.query_knowledge(
            query=prompt[:100],  # 使用prompt的前100字符作为查询
            top_k=10,
            similarity_threshold=0.0
        )
        
        for result in results:
            metadata = result.get('metadata', {})
            # 检查item_index是否匹配
            result_index = metadata.get('item_index')
            if result_index is not None and result_index == item_index:
                return True
            # 检查prompt是否匹配
            result_prompt = metadata.get('prompt', '')
            if result_prompt and result_prompt.strip() == prompt.strip():
                return True
        
        return False
    except Exception as e:
        logger.debug(f"查重检查失败: {e}")
        return False


def import_wikipedia_from_frames(
    dataset_path: str,
    batch_size: int = 20,  # 🚀 性能优化：从10增加到20，提高处理效率
    include_full_text: bool = True,  # ✅ 修改：默认抓取完整内容而非摘要
    resume: bool = True,
    skip_duplicates: bool = True,
    retry_failed: bool = False,  # 🚀 修复：添加重试失败条目的选项
    progress_file_path: str = None,  # 🆕 自定义进度文件路径
    max_concurrent: int = 6  # 🆕 控制并发抓取数，降低速率限制风险
) -> None:
    """
    从FRAMES数据集导入Wikipedia链接作为知识条目
    每个FRAMES数据项的所有Wikipedia链接内容合并为一个条目
    
    Args:
        dataset_path: FRAMES数据集JSON文件路径
        batch_size: 批处理大小（每次处理的FRAMES数据项数量）
        include_full_text: 是否抓取完整文本（✅ 默认True，抓取完整内容包含排名列表等精确数据）
        resume: 是否断点续传
        skip_duplicates: 是否跳过重复item
    """
    # 加载数据集
    print(f"📥 加载数据集: {dataset_path}")
    with open(dataset_path, 'r', encoding='utf-8') as f:
        frames_data = json.load(f)
    
    print(f"✅ 数据集加载完成: {len(frames_data)} 条数据")
    
    # 🆕 使用自定义进度文件路径（如果提供）
    actual_progress_file = progress_file_path or PROGRESS_FILE
    
    # 加载进度
    progress = load_progress(actual_progress_file) if resume else {
        'processed_item_indices': [],
        'failed_item_indices': [],  # 🚀 修复：添加失败条目跟踪
        'total_items': len(frames_data),
        'start_time': datetime.now().isoformat()
    }
    processed_indices = set(progress.get('processed_item_indices', []))
    failed_indices = set(progress.get('failed_item_indices', []))  # 🚀 修复：加载失败条目
    
    # 🚀 修复：程序启动时立即保存进度文件，确保进度文件存在
    # 这样即使程序在处理第一个批次前崩溃，进度文件也会被创建
    if not resume or not Path(actual_progress_file).exists():
        progress['total_items'] = len(frames_data)
        if not progress.get('start_time'):
            progress['start_time'] = datetime.now().isoformat()
        save_progress(progress, actual_progress_file)
    
    # 过滤已处理的item
    items_to_process = []
    print(f"DEBUG: Total frames: {len(frames_data)}")
    print(f"DEBUG: Processed indices count: {len(processed_indices)}")
    print(f"DEBUG: Failed indices count: {len(failed_indices)}")
    print(f"DEBUG: Resume={resume}, RetryFailed={retry_failed}")
    
    for i, item in enumerate(frames_data):
        if resume:
            if retry_failed:
                # 🚀 修复：如果启用重试失败，只处理失败的条目
                if i in failed_indices:
                    items_to_process.append((i, item))
            else:
                # 跳过已处理的条目（包括成功和失败的）
                if i in processed_indices or i in failed_indices:
                    continue
                items_to_process.append((i, item))
        else:
            items_to_process.append((i, item))
    
    if not items_to_process:
        print("✅ 所有数据项已处理完成")
        return
    
    print(f"📊 需要处理: {len(items_to_process)}/{len(frames_data)} 条数据项")
    if resume and processed_indices:
        print(f"   已处理: {len(processed_indices)} 条")
    
    # 初始化服务
    service = get_knowledge_service()
    fetcher = get_wikipedia_fetcher()
    
    # 批量处理
    total = len(items_to_process)
    success_count = 0
    skip_count = 0
    error_count = 0
    
    print(f"\n📚 开始导入Wikipedia内容...")
    print(f"   总数据项数: {total}")
    print(f"   批处理大小: {batch_size} (每个批次处理{batch_size}个FRAMES数据项)")
    print(f"   是否抓取完整文本: {include_full_text}")
    
    for batch_start in range(0, total, batch_size):
        batch_items = items_to_process[batch_start:batch_start + batch_size]
        batch_num = batch_start // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size
        
        print(f"\n📦 处理批次 {batch_num}/{total_batches} ({len(batch_items)} 个数据项)...")
        
        knowledge_entries = []
        batch_item_indices = []  # 🚀 修复：记录每个knowledge_entry对应的item_index
        
        for item_index, item in batch_items:
            # 提取prompt
            # 🚀 修复：支持大小写不敏感的字段名匹配（FRAMES数据集使用大写字段名）
            prompt = (
                item.get('query') or item.get('Query') or
                item.get('question') or item.get('Question') or
                item.get('prompt') or item.get('Prompt') or
                f"Item {item_index}"
            )
            
            # 查重检查
            if skip_duplicates and check_item_processed(service, prompt, item_index):
                print(f"   ⏭️  跳过已处理的数据项 [{item_index}]: {prompt[:50]}...")
                skip_count += 1
                processed_indices.add(item_index)
                progress['processed_item_indices'] = list(processed_indices)
                progress['failed_item_indices'] = list(failed_indices)
                progress['total_items'] = len(frames_data)
                save_progress(progress, actual_progress_file)
                continue
            
            # 提取该item的所有Wikipedia链接
            urls = extract_wikipedia_links_from_item(item)
            
            if not urls:
                print(f"   ⚠️  数据项 [{item_index}] 没有Wikipedia链接，跳过")
                error_count += 1
                processed_indices.add(item_index)
                progress['processed_item_indices'] = list(processed_indices)
                progress['failed_item_indices'] = list(failed_indices)
                progress['total_items'] = len(frames_data)
                save_progress(progress, actual_progress_file)
                continue
            
            print(f"   📋 数据项 [{item_index}]: {len(urls)} 个Wikipedia链接")
            print(f"      Prompt: {prompt[:80]}...")
            
            # 抓取所有URL的内容
            print(f"      📥 抓取 {len(urls)} 个Wikipedia页面...")
            fetch_start = time.time()
            
            # 🚀 优先尝试从本地 wiki_cache 加载
            wikipedia_pages = []
            urls_to_fetch = []
            
            for url in urls:
                # 提取标题作为文件名
                if '/wiki/' in url:
                    title = url.split('/wiki/')[-1]
                    # 处理 URL 编码等
                    from urllib.parse import unquote
                    title = unquote(title)
                    # 处理特殊字符
                    safe_title = title.replace('/', '_').replace(':', '_')
                    cache_path = Path(f"data/wiki_cache/{safe_title}.json")
                    
                    if cache_path.exists():
                        try:
                            with open(cache_path, 'r') as f:
                                cached_data = json.load(f)
                            
                            # 适配 cached data 结构到 wikipedia_page 结构
                            page_data = {
                                'title': cached_data.get('title', title),
                                'content': cached_data.get('content') or cached_data.get('text', ''),
                                'url': url,
                                'summary': cached_data.get('summary', '')
                            }
                            if page_data['content']:
                                wikipedia_pages.append(page_data)
                                # print(f"      ✅ 从缓存加载: {title}")
                                continue
                        except Exception as e:
                            print(f"      ⚠️  读取缓存失败 {cache_path}: {e}")
                
                urls_to_fetch.append(url)
            
            if urls_to_fetch:
                print(f"      📥 需要从网络抓取 {len(urls_to_fetch)} 个页面 (缓存命中: {len(wikipedia_pages)})")
                try:
                    # 🚀 优化：使用异步并发抓取（如果可用）
                    try:
                        # 尝试使用异步版本
                        try:
                            loop = asyncio.get_running_loop()
                        except RuntimeError:
                            # 如果没有运行中的事件循环，创建新的
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                        
                        fetched_pages = []
                        if loop.is_running():
                            # 如果事件循环已在运行，使用同步版本
                            fetched_pages = fetcher.fetch_multiple_pages(
                                urls_to_fetch,
                                include_full_text=include_full_text,
                                deduplicate=True
                            )
                        else:
                            # 使用异步版本
                            if hasattr(fetcher, 'fetch_multiple_pages_async'):
                                fetched_pages = loop.run_until_complete(
                                    fetcher.fetch_multiple_pages_async(
                                        urls_to_fetch,
                                        include_full_text=include_full_text,
                                        deduplicate=True,
                                        max_concurrent=max_concurrent
                                    )
                                )
                            else:
                                # 如果异步方法不存在，使用同步版本
                                fetched_pages = fetcher.fetch_multiple_pages(
                                    urls_to_fetch,
                                    include_full_text=include_full_text,
                                    deduplicate=True
                                )
                        
                        # 合并抓取的结果到 wikipedia_pages
                        wikipedia_pages.extend(fetched_pages)

                    except (AttributeError, RuntimeError, Exception) as e:
                        # 如果异步版本不可用，回退到同步版本
                        print(f"      ℹ️  使用同步抓取模式: {type(e).__name__}")
                        fetched_pages = fetcher.fetch_multiple_pages(
                            urls_to_fetch,
                            include_full_text=include_full_text,
                            deduplicate=True
                        )
                        wikipedia_pages.extend(fetched_pages)
                    fetch_elapsed = time.time() - fetch_start
                    print(f"      ⏱️  抓取耗时: {fetch_elapsed:.1f}秒")
                except Exception as e:
                    print(f"      ❌ 抓取失败: {type(e).__name__}: {str(e)[:100]}")
                    error_count += 1
                    # 🚀 修复：抓取失败时添加到失败列表，而不是已处理列表，以便重试
                    failed_indices.add(item_index)
                    if item_index in processed_indices:
                        processed_indices.remove(item_index)  # 从已处理列表中移除
                    # 保存进度
                    progress['processed_item_indices'] = list(processed_indices)
                    progress['failed_item_indices'] = list(failed_indices)
                    save_progress(progress, actual_progress_file)
                    continue
            else:
                # 全部命中缓存
                fetch_elapsed = time.time() - fetch_start
                print(f"      ⏱️  全部命中缓存，耗时: {fetch_elapsed:.1f}秒")
            
            if not wikipedia_pages:
                print(f"      ⚠️  未能抓取到任何内容，跳过")
                error_count += 1
                # 🚀 修复：抓取失败时添加到失败列表，以便重试
                failed_indices.add(item_index)
                if item_index in processed_indices:
                    processed_indices.remove(item_index)  # 从已处理列表中移除
                # 保存进度
                progress['processed_item_indices'] = list(processed_indices)
                progress['failed_item_indices'] = list(failed_indices)
                save_progress(progress, actual_progress_file)
                continue
            
            print(f"      ✅ 成功抓取 {len(wikipedia_pages)}/{len(urls)} 个页面")
            
            # 🚀 根本性修复：不再合并页面，而是将每个Wikipedia页面作为独立的知识条目
            # 这避免了超长文档被截断的问题，并提高了检索的精确度
            
            has_valid_content = False
            
            for page in wikipedia_pages:
                title = page.get('title', '')
                content = page.get('content', '') or page.get('summary', '')
                url = page.get('url', '')
                
                if content and content.strip():
                    # 清理内容
                    content = clean_wikipedia_content(content)
                    
                    if content:
                        has_valid_content = True
                        
                        # 为每个页面创建独立的知识条目
                        knowledge_entry = {
                            'content': content,
                            'metadata': {
                                'title': title or prompt[:50],
                                'prompt': prompt,
                                'source': 'wikipedia',
                                'source_url': url,
                                'wikipedia_title': title,
                                'content_type': 'wikipedia_page', # 单数
                                'item_index': item_index,
                                'query_id': item.get('query_id', f'item_{item_index}'),
                                'expected_answer': item.get('expected_answer') or item.get('answer', ''),
                                'dataset_source': dataset_path
                            }
                        }
                        knowledge_entries.append(knowledge_entry)

            if not has_valid_content:
                print(f"      ⚠️  所有页面内容为空，跳过")
                error_count += 1
                failed_indices.add(item_index)
                if item_index in processed_indices:
                    processed_indices.remove(item_index)
                continue
            batch_item_indices.append(item_index)  # 🚀 修复：记录对应的item_index，但不立即添加到processed_indices
            processed_indices.add(item_index)
            progress['processed_item_indices'] = list(processed_indices)
            progress['failed_item_indices'] = list(failed_indices)
            progress['total_items'] = len(frames_data)
            save_progress(progress, actual_progress_file)
        
        # 批量导入到知识库
        if knowledge_entries:
            print(f"   💾 正在导入 {len(knowledge_entries)} 条知识条目到知识库...")
            import_start = time.time()
            
            try:
                # 🚀 优化：导入后立即进行垃圾回收，释放内存
                import gc
                knowledge_ids = service.import_knowledge(
                    data=knowledge_entries,
                    modality="text",
                    source_type="list",
                    build_graph=False  # 🆕 默认不构建知识图谱，可通过独立命令构建
                )
                
                import_elapsed = time.time() - import_start
                imported = len([kid for kid in knowledge_ids if kid])
                
                # 🚀 修复：检查每个item_index对应的所有知识条目是否都已向量化
                # 一个FRAMES数据项可能产生多个知识条目（如果内容被分块）
                # 需要检查每个item_index对应的所有knowledge_ids是否都在向量索引中
                
                # 🚀 性能优化：构建item_index到knowledge_ids的映射
                # 注意：service.import_knowledge可能对内容进行分块，一个knowledge_entry可能产生多个knowledge_ids
                # 优化：直接使用knowledge_entries中的metadata，避免重复查询知识库
                item_index_to_knowledge_ids: Dict[int, List[str]] = {}
                
                # 🚀 性能优化：直接从knowledge_entries获取item_index，避免查询知识库
                # 假设knowledge_ids和knowledge_entries的顺序一致（service.import_knowledge应该保持顺序）
                for entry_idx, knowledge_id in enumerate(knowledge_ids):
                    if knowledge_id and entry_idx < len(knowledge_entries):
                        # 直接从knowledge_entries获取item_index
                        entry_metadata = knowledge_entries[entry_idx].get('metadata', {})
                        item_idx = entry_metadata.get('item_index')
                        
                        if item_idx is not None:
                            if item_idx not in item_index_to_knowledge_ids:
                                item_index_to_knowledge_ids[item_idx] = []
                            item_index_to_knowledge_ids[item_idx].append(knowledge_id)
                
                # 🚀 性能优化：如果直接从entries获取失败，再尝试查询知识库（但只查询一次，批量获取）
                if not item_index_to_knowledge_ids:
                    # 回退方案：批量查询知识库（但仍然比逐个查询快）
                    for knowledge_id in knowledge_ids:
                        if knowledge_id:
                            try:
                                entry_info = service.knowledge_manager.get_knowledge(knowledge_id)
                                if entry_info:
                                    metadata = entry_info.get('metadata', {})
                                    # 检查是否有item_index（可能在chunk_info的parent_metadata中）
                                    item_idx = metadata.get('item_index')
                                    if item_idx is None and 'chunk_info' in metadata:
                                        # 如果是分块，item_index可能在parent_metadata中
                                        parent_metadata = metadata.get('parent_metadata', {})
                                        item_idx = parent_metadata.get('item_index')
                                    
                                    if item_idx is not None:
                                        if item_idx not in item_index_to_knowledge_ids:
                                            item_index_to_knowledge_ids[item_idx] = []
                                        item_index_to_knowledge_ids[item_idx].append(knowledge_id)
                            except Exception as e:
                                logger.debug(f"获取知识条目信息失败: {e}")
                
                # 如果还是找不到，使用entry_index映射（假设顺序一致）
                if not item_index_to_knowledge_ids and len(knowledge_ids) == len(knowledge_entries):
                    for entry_idx, knowledge_id in enumerate(knowledge_ids):
                        if knowledge_id and entry_idx < len(batch_item_indices):
                            item_idx = batch_item_indices[entry_idx]
                            if item_idx not in item_index_to_knowledge_ids:
                                item_index_to_knowledge_ids[item_idx] = []
                            item_index_to_knowledge_ids[item_idx].append(knowledge_id)
                
                # 🚀 性能优化：批量检查向量化状态（一次性检查所有knowledge_ids）
                fully_processed_indices = set()
                partially_processed_indices = set()
                
                # 根据导入结果，判断每个item_index是否已创建知识条目
                for item_index in batch_item_indices:
                    item_knowledge_ids = item_index_to_knowledge_ids.get(item_index, [])
                    
                    if not item_knowledge_ids:
                        # 没有找到对应的knowledge_ids，可能是导入失败，也可能是被过滤
                        # 🚀 修改：既然没有抛出异常，说明是正常的过滤行为（或静默失败）
                        # 我们将其视为"已处理"，避免无限重试
                        # 如果是真正的系统错误，通常会抛出异常
                        print(f"   ⚠️  Item {item_index} 未生成知识条目 (可能被过滤)，标记为已处理")
                        fully_processed_indices.add(item_index)
                        continue
                    
                    fully_processed_indices.add(item_index)
                
                # 统计
                vectorized_count = sum(len(ids) for ids in item_index_to_knowledge_ids.values())
                total_knowledge_ids = len([kid for kid in knowledge_ids if kid])
                success_count += len(fully_processed_indices)
                error_count += len(partially_processed_indices)
                
                print(f"   ✅ 批次导入 {imported}/{len(knowledge_entries)} 条知识条目 (耗时: {import_elapsed:.1f}秒)")
                if partially_processed_indices:
                    print(f"   ⚠️  警告: {len(partially_processed_indices)} 个FRAMES数据项导入失败，将记录为失败")
                
                # 标记已处理与失败
                for item_index in fully_processed_indices:
                    processed_indices.add(item_index)
                    # 从失败列表中移除（如果存在）
                    if item_index in failed_indices:
                        failed_indices.remove(item_index)
                    progress['processed_item_indices'] = list(processed_indices)
                    progress['failed_item_indices'] = list(failed_indices)
                    progress['total_items'] = len(frames_data)
                    save_progress(progress, actual_progress_file)
                
                for item_index in partially_processed_indices:
                    failed_indices.add(item_index)
                    if item_index in processed_indices:
                        processed_indices.remove(item_index)  # 从已处理列表中移除
                    progress['processed_item_indices'] = list(processed_indices)
                    progress['failed_item_indices'] = list(failed_indices)
                    progress['total_items'] = len(frames_data)
                    save_progress(progress, actual_progress_file)
                
                # 🚀 修复：导入成功后立即保存进度，确保进度文件及时更新
                progress['processed_item_indices'] = list(processed_indices)
                progress['failed_item_indices'] = list(failed_indices)
                progress['total_items'] = len(frames_data)
                save_progress(progress, actual_progress_file)
                
                # 🚀 优化：导入后强制垃圾回收，释放内存
                del knowledge_entries  # 显式删除
                gc.collect()  # 强制垃圾回收
                
                # 如果导入耗时超过60秒，警告
                if import_elapsed > 60:
                    print(f"   ⚠️  导入较慢（{import_elapsed:.1f}秒），可能是向量化API响应慢")
                
            except Exception as e:
                logger.error(f"导入批次失败: {e}")
                import traceback
                traceback.print_exc()
                error_count += len(knowledge_entries)
                # 🚀 修复：导入失败时添加到失败列表，以便重试
                for item_index in batch_item_indices:
                    failed_indices.add(item_index)
                    if item_index in processed_indices:
                        processed_indices.remove(item_index)  # 从已处理列表中移除
                # 保存进度
                progress['processed_item_indices'] = list(processed_indices)
                progress['failed_item_indices'] = list(failed_indices)
                save_progress(progress, actual_progress_file)
        
        # 保存进度
        progress['processed_item_indices'] = list(processed_indices)
        progress['failed_item_indices'] = list(failed_indices)
        progress['total_items'] = len(frames_data)
        save_progress(progress, actual_progress_file)
        
        # 🚀 修复：使用logger输出，确保日志和进度文件一致
        # 同时使用print和logger，确保既能在控制台看到，也能在日志中记录
        progress_msg = f"📊 总体进度: {len(processed_indices)}/{len(frames_data)} ({len(processed_indices)/len(frames_data)*100:.1f}%)"
        print(f"   {progress_msg}")
        logger.info(progress_msg)  # 确保日志中也有记录，与进度文件保持一致
    
    # 最终统计
    print(f"\n✅ 导入完成!")
    print(f"   成功: {success_count} 条")
    print(f"   跳过: {skip_count} 条")
    print(f"   失败: {error_count} 条")
    print(f"   总计处理: {len(processed_indices)}/{len(frames_data)} 个数据项")
    
    # 清理进度文件（如果全部完成）
    if len(processed_indices) >= len(frames_data):
        print(f"\n🧹 清理进度文件...")
        progress_file = Path(actual_progress_file)
        if progress_file.exists():
            progress_file.unlink()
            print(f"   ✅ 进度文件已清理")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="从FRAMES数据集导入Wikipedia链接作为知识条目")
    parser.add_argument(
        'dataset_path',
        type=str,
        help='FRAMES数据集JSON文件路径'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=5,  # 🚀 优化：减小默认批处理大小，避免内存不足（从10改为5）
        help='批处理大小（每个批次处理的FRAMES数据项数量，默认: 5，建议3-10）'
    )
    parser.add_argument(
        '--wikipedia-full-text',
        action='store_true',
        help='抓取Wikipedia完整文本（✅ 默认启用，抓取完整内容包含排名列表等精确数据）'
    )
    parser.add_argument(
        '--wikipedia-summary-only',
        action='store_true',
        help='仅抓取Wikipedia摘要（覆盖默认的完整文本抓取）'
    )
    parser.add_argument(
        '--no-resume',
        action='store_true',
        help='不进行断点续传（从头开始）'
    )
    parser.add_argument(
        '--no-skip-duplicates',
        action='store_true',
        help='不跳过重复URL（默认: 跳过重复）'
    )
    parser.add_argument(
        '--retry-failed',
        action='store_true',
        help='重试之前失败的条目'
    )
    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=6,
        help='并发抓取的最大数（默认: 6，建议: 4-8）'
    )
    
    args = parser.parse_args()
    
    # ✅ 修改：默认抓取完整内容，除非明确指定 --wikipedia-summary-only
    # 如果设置了 --wikipedia-summary-only，则只抓取摘要
    # 否则，默认抓取完整内容（函数默认参数已经是True）
    include_full_text = not args.wikipedia_summary_only  # 默认True，除非指定summary-only
    
    import_wikipedia_from_frames(
        dataset_path=args.dataset_path,
        batch_size=args.batch_size,
        include_full_text=include_full_text,
        resume=not args.no_resume,
        skip_duplicates=not args.no_skip_duplicates,
        retry_failed=args.retry_failed,
        max_concurrent=args.max_concurrent
    )
