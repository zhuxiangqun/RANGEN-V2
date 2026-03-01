#!/usr/bin/env python3
"""
数据集导入脚本
支持从Hugging Face、本地文件等导入数据集到向量知识库
"""

import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, cast
import argparse

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from knowledge_management_system.api.service_interface import get_knowledge_service
    KMS_AVAILABLE = True
except ImportError:
    KMS_AVAILABLE = False
    print("❌ 错误: 无法导入知识库管理系统")
    sys.exit(1)


def detect_source_type(dataset_source: str) -> str:
    """
    检测数据源类型
    
    Args:
        dataset_source: 数据集地址
        
    Returns:
        数据源类型: huggingface|local_json|local_csv|url_json|unknown
    """
    dataset_source_lower = dataset_source.lower()
    
    # Hugging Face URL
    if "huggingface.co" in dataset_source_lower or "hf.co" in dataset_source_lower:
        return "huggingface"
    
    # 本地文件
    if os.path.exists(dataset_source):
        if dataset_source.endswith('.json'):
            return "local_json"
        elif dataset_source.endswith('.csv'):
            return "local_csv"
        elif dataset_source.endswith('.jsonl'):
            return "local_jsonl"
    
    # HTTP/HTTPS URL
    if dataset_source.startswith(('http://', 'https://')):
        if dataset_source.endswith('.json'):
            return "url_json"
    
    return "unknown"


def load_huggingface_dataset(dataset_path: str) -> List[Dict[str, Any]]:
    """
    从Hugging Face加载数据集
    
    Args:
        dataset_path: Hugging Face数据集路径（如 google/frames-benchmark）
        
    Returns:
        知识条目列表
    """
    try:
        try:
            from datasets import load_dataset
        except ImportError:
            print("❌ 错误: 需要安装 datasets 库")
            print("   运行: pip install datasets")
            sys.exit(1)
        
        print(f"📥 正在从 Hugging Face 加载数据集: {dataset_path}")
        dataset = load_dataset(dataset_path)
        
        # 获取数据集的分割（train/test/validation等）
        # 处理类型：dataset.keys() 可能返回 str 或 NamedSplit
        # 使用 hasattr 检查是否有 keys 方法，避免类型检查错误
        if hasattr(dataset, 'keys'):
            splits_raw = dataset.keys()  # type: ignore
            splits = [str(split) for split in splits_raw]  # 转换为字符串列表
        else:
            # 如果是 IterableDataset，尝试直接访问
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
        
        # 使用合并后的数据
        split_data = dataset_list
        
        # 🚀 保存数据集到本地（如果是FRAMES数据集，方便后续断点续传）
        if "frames" in dataset_path.lower() or "frames-benchmark" in dataset_path.lower():
            local_dataset_path = Path(__file__).parent.parent.parent / "data" / "frames_dataset.json"
            local_dataset_path.parent.mkdir(parents=True, exist_ok=True)
            
            if not local_dataset_path.exists():
                print(f"💾 保存FRAMES数据集到本地: {local_dataset_path}")
                # 转换为列表格式
                dataset_list = []
                for item in split_data:
                    # 安全转换：如果item是dict则直接使用，否则尝试转换
                    if isinstance(item, dict):
                        dataset_list.append(item)
                    else:
                        try:
                            dataset_list.append(dict(item))  # type: ignore
                        except (TypeError, ValueError):
                            # 如果无法转换，跳过该项
                            continue
                
                with open(local_dataset_path, 'w', encoding='utf-8') as f:
                    json.dump(dataset_list, f, ensure_ascii=False, indent=2)
                print(f"✅ 数据集已保存到: {local_dataset_path}")
            else:
                print(f"ℹ️  本地数据集文件已存在: {local_dataset_path}")
        
        # 转换为知识条目格式
        knowledge_entries = []
        for i, item in enumerate(split_data):
            # 提取文本内容（尝试常见字段）
            content = None
            metadata = {}
            
            # 尝试常见的内容字段
            for field in ['query', 'question', 'text', 'content', 'prompt', 'input']:
                if field in item and item[field]:
                    content = str(item[field])
                    break
            
            # 如果找不到内容字段，尝试使用所有字段组合
            if not content:
                # 组合所有文本字段
                text_parts = []
                for key, value in item.items():
                    if isinstance(value, str) and value.strip():
                        text_parts.append(f"{key}: {value}")
                if text_parts:
                    content = " | ".join(text_parts)
            
            # 如果还是找不到内容，跳过这条
            if not content or not content.strip():
                continue
            
            # 🚀 提取答案字段（如果存在）
            # 优先使用 Answer 字段（Hugging Face 官方数据集格式：google/frames-benchmark）
            # 兼容 expected_answer 和 answer（本地数据集格式）
            if 'Answer' in item:
                metadata['Answer'] = item['Answer']
                metadata['expected_answer'] = item['Answer']  # 同时存储为标准字段名
            elif 'expected_answer' in item:
                metadata['expected_answer'] = item['expected_answer']
            elif 'answer' in item:
                metadata['answer'] = item['answer']
            
            # 🚀 提取 Wikipedia 链接
            # 支持从以下字段提取：
            #   1. wiki_links（FRAMES 数据集官方字段，优先）
            #   2. evidence（备用字段，包含Wikipedia链接列表）
            #   注意：不使用 wikipedia_link_* 字段
            # 支持多种格式：
            #   1. Python 列表：['url1', 'url2']
            #   2. JSON 数组字符串：["url1", "url2"]
            #   3. Python 列表字符串：'[\"url1\", \"url2\"]' 或 "['url1', 'url2']"
            #   4. 逗号分隔字符串：url1, url2
            wikipedia_links = []
            
            def parse_wikipedia_links(value):
                """解析Wikipedia链接的辅助函数"""
                parsed_links = []
                
                if isinstance(value, list):
                    # 直接是列表格式
                    parsed_links = [link for link in value if isinstance(link, str) and 'wikipedia.org' in link.lower() and link.strip()]
                elif isinstance(value, str):
                    # 尝试多种解析方式
                    
                    # 方式1: 尝试解析 JSON 字符串（双引号格式）
                    try:
                        parsed = json.loads(value)
                        if isinstance(parsed, list):
                            parsed_links = [link for link in parsed if isinstance(link, str) and 'wikipedia.org' in link.lower() and link.strip()]
                    except (json.JSONDecodeError, ValueError):
                        pass
                    
                    # 方式2: 尝试解析 Python 字面量（单引号格式，如 "['url1', 'url2']"）
                    if not parsed_links:
                        try:
                            import ast
                            parsed = ast.literal_eval(value)
                            if isinstance(parsed, list):
                                parsed_links = [link for link in parsed if isinstance(link, str) and 'wikipedia.org' in link.lower() and link.strip()]
                        except (ValueError, SyntaxError):
                            pass
                    
                    # 方式3: 如果前两种都失败，尝试按逗号分割（并清理引号和方括号）
                    if not parsed_links:
                        # 移除方括号和引号
                        cleaned = value.strip()
                        if cleaned.startswith('['):
                            cleaned = cleaned[1:]
                        if cleaned.endswith(']'):
                            cleaned = cleaned[:-1]
                        
                        for link in cleaned.split(','):
                            link = link.strip()
                            # 移除引号（单引号或双引号）
                            link = link.strip("'\"")
                            link = link.strip()
                            # 只保留Wikipedia链接
                            if link and 'wikipedia.org' in link.lower():
                                parsed_links.append(link)
                    
                    # 方式4: 使用正则表达式提取所有Wikipedia URL
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
                item_metadata = item['metadata']
                if 'wiki_links' in item_metadata and item_metadata['wiki_links']:
                    links = parse_wikipedia_links(item_metadata['wiki_links'])
                    wikipedia_links.extend(links)
            
            # 如果 wiki_links 没有或为空，尝试从 evidence 字段提取
            if not wikipedia_links and 'evidence' in item and item['evidence']:
                links = parse_wikipedia_links(item['evidence'])
                wikipedia_links.extend(links)
            
            # 去重 Wikipedia 链接
            wikipedia_links = list(set([link for link in wikipedia_links if link and link.strip()]))
            if wikipedia_links:
                metadata['wikipedia_links'] = wikipedia_links
                metadata['_wikipedia_links_count'] = len(wikipedia_links)
            
            # 保存其他元数据
            for key, value in item.items():
                # 排除已处理的字段和 wikipedia_link_* 字段（不使用）
                # 注意：evidence字段包含在metadata中，但Wikipedia链接已提取到wikipedia_links
                if key not in ['query', 'question', 'text', 'content', 'prompt', 'input', 'answer', 'wiki_links', 'evidence']:
                    if not key.startswith('wikipedia_link_'):  # 忽略 wikipedia_link_* 字段
                        if isinstance(value, (str, int, float, bool)):
                            metadata[key] = value
            
            # 🚀 如果evidence字段中包含Wikipedia链接但已提取，可以选择保存evidence或跳过
            # 这里选择保存evidence作为原始数据参考
            if 'evidence' in item and item['evidence']:
                metadata['_original_evidence'] = item['evidence']
            
            # 添加数据集信息
            metadata['dataset_source'] = dataset_path
            metadata['dataset_split'] = selected_split
            metadata['item_index'] = i
            
            knowledge_entries.append({
                'content': content.strip(),
                'metadata': metadata
            })
        
        print(f"✅ 成功加载 {len(knowledge_entries)} 条知识条目")
        return knowledge_entries
        
    except Exception as e:
        print(f"❌ 加载 Hugging Face 数据集失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def load_local_json(file_path: str) -> List[Dict[str, Any]]:
    """
    从本地JSON文件加载数据
    
    Args:
        file_path: JSON文件路径
        
    Returns:
        知识条目列表
    """
    try:
        print(f"📥 正在加载本地JSON文件: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        knowledge_entries = []
        
        # 处理不同的JSON格式
        if isinstance(data, list):
            entries = data
        elif isinstance(data, dict):
            # 尝试常见键名
            entries = (
                data.get('entries', []) or 
                data.get('knowledge', []) or 
                data.get('data', []) or
                data.get('items', [])
            )
            if not entries:
                # 如果是单个条目
                if 'content' in data or 'text' in data:
                    entries = [data]
        else:
            print(f"❌ 不支持的JSON格式")
            sys.exit(1)
        
        for i, entry in enumerate(entries):
            # 提取内容
            content = (
                entry.get('content') or 
                entry.get('text') or 
                entry.get('query') or 
                entry.get('question') or
                str(entry)
            )
            
            if not content or not isinstance(content, str):
                continue
            
            # 提取元数据
            metadata = {}
            for key, value in entry.items():
                if key not in ['content', 'text', 'query', 'question']:
                    if isinstance(value, (str, int, float, bool, list, dict)):
                        metadata[key] = value
            
            metadata['dataset_source'] = file_path
            metadata['item_index'] = i
            
            knowledge_entries.append({
                'content': content.strip(),
                'metadata': metadata
            })
        
        print(f"✅ 成功加载 {len(knowledge_entries)} 条知识条目")
        return knowledge_entries
        
    except Exception as e:
        print(f"❌ 加载本地JSON文件失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def load_local_csv(file_path: str) -> List[Dict[str, Any]]:
    """
    从本地CSV文件加载数据
    
    Args:
        file_path: CSV文件路径
        
    Returns:
        知识条目列表
    """
    try:
        import csv
        
        print(f"📥 正在加载本地CSV文件: {file_path}")
        
        knowledge_entries = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for i, row in enumerate(reader):
                # 尝试找到内容列
                content = None
                for col in ['content', 'text', 'query', 'question', 'prompt']:
                    if col in row and row[col]:
                        content = row[col]
                        break
                
                if not content:
                    # 使用第一列作为内容
                    first_key = next(iter(row.keys()))
                    content = row[first_key]
                
                if not content or not content.strip():
                    continue
                
                # 提取元数据
                metadata = {}
                for key, value in row.items():
                    if key not in ['content', 'text', 'query', 'question']:
                        metadata[key] = value
                
                metadata['dataset_source'] = file_path
                metadata['item_index'] = i
                
                knowledge_entries.append({
                    'content': content.strip(),
                    'metadata': metadata
                })
        
        print(f"✅ 成功加载 {len(knowledge_entries)} 条知识条目")
        return knowledge_entries
        
    except Exception as e:
        print(f"❌ 加载本地CSV文件失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """
    从JSONL文件加载数据
    
    Args:
        file_path: JSONL文件路径
        
    Returns:
        知识条目列表
    """
    try:
        print(f"📥 正在加载JSONL文件: {file_path}")
        
        knowledge_entries = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    entry = json.loads(line)
                    
                    # 提取内容
                    content = (
                        entry.get('content') or 
                        entry.get('text') or 
                        entry.get('query') or 
                        entry.get('question') or
                        str(entry)
                    )
                    
                    if not content or not isinstance(content, str):
                        continue
                    
                    # 提取元数据
                    metadata = {}
                    for key, value in entry.items():
                        if key not in ['content', 'text', 'query', 'question']:
                            if isinstance(value, (str, int, float, bool, list, dict)):
                                metadata[key] = value
                    
                    metadata['dataset_source'] = file_path
                    metadata['item_index'] = i
                    
                    knowledge_entries.append({
                        'content': content.strip(),
                        'metadata': metadata
                    })
                except json.JSONDecodeError:
                    continue
        
        print(f"✅ 成功加载 {len(knowledge_entries)} 条知识条目")
        return knowledge_entries
        
    except Exception as e:
        print(f"❌ 加载JSONL文件失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def extract_wikipedia_links_from_entries(knowledge_entries: List[Dict[str, Any]]) -> List[str]:
    """
    从知识条目中提取所有 Wikipedia 链接
    
    🚀 注意：从 wikipedia_links 元数据字段提取（可能来自 wiki_links 或 evidence 字段）
    
    Args:
        knowledge_entries: 知识条目列表
    
    Returns:
        Wikipedia URL 列表（去重）
    """
    wikipedia_links = []
    for entry in knowledge_entries:
        metadata = entry.get('metadata', {})
        
        # 🚀 提取 wikipedia_links 字段（来自数据集的 wiki_links 或 evidence 字段）
        if 'wikipedia_links' in metadata:
            links = metadata['wikipedia_links']
            if isinstance(links, list):
                wikipedia_links.extend([link for link in links if isinstance(link, str) and link.strip()])
            elif isinstance(links, str):
                # 尝试多种解析方式
                parsed_links = []
                
                # 方式1: 尝试解析 JSON 字符串（双引号格式）
                try:
                    parsed = json.loads(links)
                    if isinstance(parsed, list):
                        parsed_links = [link for link in parsed if isinstance(link, str) and link.strip()]
                except (json.JSONDecodeError, ValueError):
                    pass
                
                # 方式2: 尝试解析 Python 字面量（单引号格式）
                if not parsed_links:
                    try:
                        import ast
                        parsed = ast.literal_eval(links)
                        if isinstance(parsed, list):
                            parsed_links = [link for link in parsed if isinstance(link, str) and link.strip()]
                    except (ValueError, SyntaxError):
                        pass
                
                # 方式3: 如果前两种都失败，尝试按逗号分割（并清理引号和方括号）
                if not parsed_links:
                    # 移除方括号和引号
                    cleaned = links.strip()
                    if cleaned.startswith('['):
                        cleaned = cleaned[1:]
                    if cleaned.endswith(']'):
                        cleaned = cleaned[:-1]
                    
                    for link in cleaned.split(','):
                        link = link.strip()
                        # 移除引号（单引号或双引号）
                        link = link.strip("'\"")
                        link = link.strip()
                        if link:
                            parsed_links.append(link)
                
                wikipedia_links.extend(parsed_links)
    
    # 去重
    unique_links = list(set([link for link in wikipedia_links if link]))
    return unique_links


def fetch_wikipedia_content(wikipedia_urls: List[str], include_full_text: bool = True) -> List[Dict[str, Any]]:
    """
    抓取 Wikipedia 页面内容
    
    Args:
        wikipedia_urls: Wikipedia URL 列表
        include_full_text: 是否抓取完整文本（否则只抓取摘要）
        
    Returns:
        Wikipedia 页面内容列表
    """
    try:
        from knowledge_management_system.utils.wikipedia_fetcher import get_wikipedia_fetcher  # type: ignore
        
        fetcher = get_wikipedia_fetcher()
        print(f"📥 开始抓取 {len(wikipedia_urls)} 个 Wikipedia 页面...")
        
        results = fetcher.fetch_multiple_pages(
            wikipedia_urls,
            include_full_text=include_full_text,
            deduplicate=True
        )
        
        print(f"✅ 成功抓取 {len(results)}/{len(wikipedia_urls)} 个 Wikipedia 页面")
        return results
        
    except ImportError as e:
        print(f"⚠️  无法导入 Wikipedia 抓取器: {e}")
        return []
    except Exception as e:
        print(f"❌ 抓取 Wikipedia 内容失败: {e}")
        import traceback
        traceback.print_exc()
        return []


def convert_wikipedia_to_knowledge_entries(wikipedia_pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    将 Wikipedia 页面内容转换为知识条目格式
    
    Args:
        wikipedia_pages: Wikipedia 页面内容列表
        
    Returns:
        知识条目列表
    """
    knowledge_entries = []
    
    for page in wikipedia_pages:
        title = page.get('title', '')
        content = page.get('content', '') or page.get('summary', '')
        url = page.get('url', '')
        
        if not content or not content.strip():
            continue
        
        # 构建知识条目
        knowledge_entry = {
            'content': content.strip(),
            'metadata': {
                'title': title,
                'source': 'wikipedia',
                'source_url': url,
                'content_type': 'wikipedia_page',
                'wikipedia_title': title
            }
        }
        
        knowledge_entries.append(knowledge_entry)
    
    return knowledge_entries


def import_to_knowledge_base(
    knowledge_entries: List[Dict[str, Any]], 
    batch_size: int = 100,
    fetch_wikipedia: bool = True,
    wikipedia_full_text: bool = True  # ✅ 修改：默认抓取完整内容而非摘要
) -> None:
    """
    将知识条目导入到向量知识库（支持自动抓取 Wikipedia 内容）
    
    Args:
        knowledge_entries: 知识条目列表
        batch_size: 批处理大小
        fetch_wikipedia: 是否自动抓取 Wikipedia 链接的内容
        wikipedia_full_text: 是否抓取 Wikipedia 完整文本（否则只抓取摘要）
    """
    if not knowledge_entries:
        print("⚠️ 没有可导入的知识条目")
        return
    
    print(f"\n📚 开始导入到向量知识库...")
    print(f"   总条目数: {len(knowledge_entries)}")
    print(f"   批处理大小: {batch_size}")
    
    service = get_knowledge_service()
    
    # 🆕 如果启用，提取并抓取 Wikipedia 内容
    wikipedia_knowledge_entries = []
    if fetch_wikipedia:
        print("\n🔍 检查 Wikipedia 链接...")
        wikipedia_urls = extract_wikipedia_links_from_entries(knowledge_entries)
        
        if wikipedia_urls:
            print(f"   发现 {len(wikipedia_urls)} 个唯一的 Wikipedia 链接")
            
            # 询问用户是否抓取（如果是交互式）
            # 🚀 改进：检查环境变量或参数
            auto_fetch_wikipedia = os.getenv('AUTO_FETCH_WIKIPEDIA', '').lower() in ('true', '1', 'yes', 'y')
            if sys.stdin.isatty() and not auto_fetch_wikipedia:  # 检查是否为交互式终端且未设置自动模式
                try:
                    response = input(f"   是否抓取这些 Wikipedia 页面内容？[Y/n]: ").strip().lower()
                    if response and response != 'y' and response != 'yes':
                        print("   ⏭️  跳过 Wikipedia 内容抓取")
                        fetch_wikipedia = False
                except (EOFError, KeyboardInterrupt):
                    print("   ⏭️  跳过 Wikipedia 内容抓取")
                    fetch_wikipedia = False
            elif not sys.stdin.isatty() or auto_fetch_wikipedia:
                # 非交互式模式或自动模式：默认抓取
                print(f"   ✅ 自动模式：将抓取 Wikipedia 内容")
            
            if fetch_wikipedia:
                # 抓取 Wikipedia 内容
                wikipedia_pages = fetch_wikipedia_content(wikipedia_urls, include_full_text=wikipedia_full_text)
                
                if wikipedia_pages:
                    # 转换为知识条目
                    wikipedia_knowledge_entries = convert_wikipedia_to_knowledge_entries(wikipedia_pages)
                    print(f"   ✅ 成功抓取 {len(wikipedia_knowledge_entries)} 个 Wikipedia 页面")
                else:
                    print("   ⚠️  未能抓取到 Wikipedia 内容")
        else:
            print("   ℹ️  未发现 Wikipedia 链接")
    
    total_imported = 0
    
    # 先导入原始知识条目
    if knowledge_entries:
        print(f"\n📦 导入原始知识条目 ({len(knowledge_entries)} 条)...")
        for i in range(0, len(knowledge_entries), batch_size):
            batch = knowledge_entries[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(knowledge_entries) + batch_size - 1) // batch_size
            
            print(f"   正在导入第 {batch_num}/{total_batches} 批 ({len(batch)} 条)...")
            import time
            batch_start_time = time.time()
            
            try:
                knowledge_ids = service.import_knowledge(
                    data=batch,
                    modality="text",
                    source_type="list"
                )
                
                batch_elapsed = time.time() - batch_start_time
                batch_imported = len([kid for kid in knowledge_ids if kid])
                total_imported += batch_imported
                
                print(f"   ✅ 本批导入 {batch_imported}/{len(batch)} 条 (耗时: {batch_elapsed:.1f}秒)")
                
                # 🚀 如果单批耗时超过60秒，警告
                if batch_elapsed > 60:
                    print(f"   ⚠️  本批处理较慢（{batch_elapsed:.1f}秒），可能是网络或API问题")
                
            except Exception as e:
                print(f"   ❌ 本批导入失败: {e}")
                continue
    
    # 再导入 Wikipedia 内容（如果有）
    if wikipedia_knowledge_entries:
        print(f"\n📦 导入 Wikipedia 内容 ({len(wikipedia_knowledge_entries)} 条)...")
        wiki_imported = 0
        for i in range(0, len(wikipedia_knowledge_entries), batch_size):
            batch = wikipedia_knowledge_entries[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(wikipedia_knowledge_entries) + batch_size - 1) // batch_size
            
            print(f"   正在导入 Wikipedia 批次 {batch_num}/{total_batches} ({len(batch)} 条)...")
            
            try:
                knowledge_ids = service.import_knowledge(
                    data=batch,
                    modality="text",
                    source_type="list"
                )
                
                batch_imported = len([kid for kid in knowledge_ids if kid])
                wiki_imported += batch_imported
                
                print(f"   ✅ Wikipedia 批次 {batch_num} 导入 {batch_imported}/{len(batch)} 条")
                
            except Exception as e:
                print(f"   ❌ Wikipedia 批次 {batch_num} 导入失败: {e}")
                continue
        
        print(f"\n✅ Wikipedia 内容导入完成: {wiki_imported}/{len(wikipedia_knowledge_entries)} 条")
        total_imported += wiki_imported
    
    print(f"\n✅ 导入完成: 共导入 {total_imported} 条知识")
    
    # 显示统计信息
    try:
        stats = service.get_statistics()
        print(f"\n📊 知识库统计:")
        print(f"   总条目数: {stats.get('total_knowledge', 0)}")
        print(f"   向量索引大小: {stats.get('vector_index_size', 0)}")
    except Exception as e:
        print(f"   无法获取统计信息: {e}")


def check_jina_api_key() -> bool:
    """
    检查JINA_API_KEY是否设置
    
    优先级：.env文件 > 环境变量 > 配置文件
    
    Returns:
        True如果已设置，False如果未设置
    """
    # 🚀 首先尝试加载 .env 文件
    try:
        from dotenv import load_dotenv
        # 查找项目根目录的 .env 文件
        project_root = Path(__file__).parent.parent.parent
        env_path = project_root / '.env'
        if env_path.exists():
            load_dotenv(env_path, override=False)
            print(f"✅ 已从 .env 文件加载环境变量: {env_path}")
        else:
            # 尝试当前目录
            env_path = Path.cwd() / '.env'
            if env_path.exists():
                load_dotenv(env_path, override=False)
                print(f"✅ 已从当前目录 .env 文件加载环境变量: {env_path}")
    except ImportError:
        pass  # python-dotenv 未安装，跳过
    except Exception:
        pass  # 忽略加载错误
    
    # 从环境变量读取
    api_key = os.getenv("JINA_API_KEY")
    
    # 如果没有从环境变量获取，尝试从配置文件读取
    if not api_key:
        try:
            import json
            config_path = Path(__file__).parent.parent / "config" / "system_config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if "api_keys" in config and "jina" in config["api_keys"]:
                        api_key = config["api_keys"]["jina"]
        except Exception:
            pass
    
    return api_key is not None and len(api_key.strip()) > 0


def main():
    # 🚀 在脚本开始时加载 .env 文件（优先级最高）
    env_loaded = False
    try:
        from dotenv import load_dotenv
        project_root = Path(__file__).parent.parent.parent
        env_path = project_root / '.env'
        if env_path.exists():
            load_dotenv(env_path, override=False)
            env_loaded = True
        else:
            env_path = Path.cwd() / '.env'
            if env_path.exists():
                load_dotenv(env_path, override=False)
                env_loaded = True
    except ImportError:
        pass  # python-dotenv 未安装，静默处理
    except Exception:
        pass  # 加载失败，静默处理
    
    # 如果加载成功，验证JINA_API_KEY
    if env_loaded:
        api_key = os.getenv('JINA_API_KEY')
        if api_key and len(api_key.strip()) > 10:
            print(f"✅ 已从 .env 文件加载 JINA_API_KEY")
        # 不打印，避免干扰输出

    # 原有代码继续...
    parser = argparse.ArgumentParser(
        description='导入数据集到向量知识库',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s https://huggingface.co/datasets/google/frames-benchmark
  %(prog)s /path/to/dataset.json
  %(prog)s /path/to/dataset.csv
  %(prog)s google/frames-benchmark

注意:
  - 需要设置环境变量 JINA_API_KEY 才能进行文本向量化
  - 获取API密钥: https://jina.ai/
  - 支持自动抓取 Wikipedia 链接内容（默认启用）
        """
    )
    parser.add_argument(
        'dataset_source',
        help='数据集地址（Hugging Face URL/路径 或 本地文件路径）'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='批处理大小（默认: 100）'
    )
    parser.add_argument(
        '--fetch-wikipedia',
        action='store_true',
        default=True,
        help='是否自动抓取 Wikipedia 链接的内容（默认: True）'
    )
    parser.add_argument(
        '--no-fetch-wikipedia',
        dest='fetch_wikipedia',
        action='store_false',
        help='不抓取 Wikipedia 内容'
    )
    parser.add_argument(
        '--wikipedia-full-text',
        action='store_true',
        default=False,
        help='是否抓取 Wikipedia 完整文本（默认: 仅摘要，更快）'
    )
    
    args = parser.parse_args()
    
    # 🚀 改进：在开始导入前检查API密钥
    if not check_jina_api_key():
        print("=" * 60)
        print("⚠️  警告: JINA_API_KEY 未设置")
        print("=" * 60)
        print()
        print("文本向量化需要 JINA_API_KEY 才能正常工作。")
        print("如果没有设置API密钥，导入的数据将无法生成向量，无法进行向量搜索。")
        print()
        print("💡 设置方法:")
        print("   1. 设置环境变量:")
        print("      export JINA_API_KEY='your-api-key-here'")
        print()
        print("   2. 或在配置文件中配置:")
        print("      knowledge_management_system/config/system_config.json")
        print("      添加: { \"api_keys\": { \"jina\": \"your-api-key-here\" } }")
        print()
        print("   3. 获取API密钥: https://jina.ai/")
        print()
        # 🚀 改进：非交互式模式自动继续，交互式模式询问用户
        if sys.stdin.isatty():
            try:
                response = input("是否继续导入（数据将无法向量化）? [y/N]: ").strip().lower()
                if response != 'y':
                    print("❌ 已取消导入")
                    sys.exit(1)
            except (EOFError, KeyboardInterrupt):
                print("❌ 已取消导入")
                sys.exit(1)
        else:
            # 非交互式模式：自动继续（但会警告）
            print("⚠️  非交互式模式：将继续导入（数据将无法向量化）")
        print()
    
    dataset_source = args.dataset_source
    
    # 检测数据源类型
    source_type = detect_source_type(dataset_source)
    
    print("=" * 60)
    print("数据集导入工具")
    print("=" * 60)
    print(f"数据源: {dataset_source}")
    print(f"类型: {source_type}")
    if check_jina_api_key():
        print(f"✅ JINA_API_KEY: 已设置")
    else:
        print(f"⚠️  JINA_API_KEY: 未设置（数据将无法向量化）")
    print("=" * 60)
    print()
    
    # 根据类型加载数据
    knowledge_entries = []
    
    if source_type == "huggingface":
        # 提取数据集路径（去除URL部分）
        if "/datasets/" in dataset_source:
            dataset_path = dataset_source.split("/datasets/")[-1]
        else:
            dataset_path = dataset_source
        
        knowledge_entries = load_huggingface_dataset(dataset_path)
        
    elif source_type == "local_json":
        knowledge_entries = load_local_json(dataset_source)
        
    elif source_type == "local_csv":
        knowledge_entries = load_local_csv(dataset_source)
        
    elif source_type == "local_jsonl":
        knowledge_entries = load_jsonl(dataset_source)
        
    elif source_type == "url_json":
        print(f"❌ 暂不支持从URL下载JSON文件，请先下载到本地")
        sys.exit(1)
        
    else:
        print(f"❌ 无法识别的数据源类型: {dataset_source}")
        print(f"   支持的类型:")
        print(f"   - Hugging Face数据集 (huggingface.co/...)")
        print(f"   - 本地JSON文件 (.json)")
        print(f"   - 本地CSV文件 (.csv)")
        print(f"   - 本地JSONL文件 (.jsonl)")
        sys.exit(1)
    
    # 导入到知识库
    if knowledge_entries:
        import_to_knowledge_base(
            knowledge_entries, 
            batch_size=args.batch_size,
            fetch_wikipedia=getattr(args, 'fetch_wikipedia', True),
            wikipedia_full_text=getattr(args, 'wikipedia_full_text', False)
        )
    else:
        print("⚠️ 没有找到可导入的知识条目")
        sys.exit(1)


if __name__ == "__main__":
    main()

