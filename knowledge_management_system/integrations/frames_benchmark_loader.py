#!/usr/bin/env python3
"""
FRAMES-Benchmark 数据集集成模块
从 Hugging Face 加载 FRAMES-Benchmark 数据并集成到 KMS 向量知识库
"""

import json
import csv
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datasets import load_dataset
import pandas as pd

from ..utils.logger import get_logger
from ..core.knowledge_importer import KnowledgeImporter
from ..api.service_interface import KnowledgeManagementService

logger = get_logger()


class FramesBenchmarkLoader:
    """FRAMES-Benchmark 数据集加载器"""
    
    def __init__(self):
        self.logger = logger
        self.importer = KnowledgeImporter()
        self.service = KnowledgeManagementService()
        
        # FRAMES 数据集配置
        self.dataset_name = "google/frames-benchmark"
        self.cache_dir = Path("data/frames_benchmark")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def load_frames_dataset(self, split: str = "test") -> pd.DataFrame:
        """
        从 Hugging Face 加载 FRAMES-Benchmark 数据集
        
        Args:
            split: 数据集分割 ('test', 'validation', 'train')
            
        Returns:
            包含数据的 pandas DataFrame
        """
        try:
            self.logger.info(f"正在从 Hugging Face 加载 FRAMES-Benchmark 数据集 ({split} 分割)...")
            
            # 加载数据集
            dataset = load_dataset(self.dataset_name, split=split)
            
            # 转换为 DataFrame
            df = pd.DataFrame(dataset)
            
            self.logger.info(f"成功加载 {len(df)} 条记录")
            return df
            
        except Exception as e:
            self.logger.error(f"从 Hugging Face 加载数据集失败: {e}")
            # 尝试从缓存加载
            cache_file = self.cache_dir / f"frames_{split}.csv"
            if cache_file.exists():
                self.logger.info(f"尝试从缓存加载数据集: {cache_file}")
                return pd.read_csv(cache_file)
            else:
                self.logger.error("缓存文件不存在，无法加载数据集")
                return pd.DataFrame()
    
    def cache_dataset(self, df: pd.DataFrame, split: str = "test") -> bool:
        """
        将数据集缓存到本地
        
        Args:
            df: 数据 DataFrame
            split: 数据集分割名称
            
        Returns:
            是否成功缓存
        """
        try:
            cache_file = self.cache_dir / f"frames_{split}.csv"
            df.to_csv(cache_file, index=False, encoding='utf-8')
            self.logger.info(f"数据集已缓存到: {cache_file}")
            return True
        except Exception as e:
            self.logger.error(f"缓存数据集失败: {e}")
            return False
    
    def process_frames_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        处理 FRAMES 数据，转换为 KMS 知识条目格式
        
        Args:
            df: FRAMES 数据 DataFrame
            
        Returns:
            知识条目列表
        """
        knowledge_entries = []
        
        for idx, row in df.iterrows():
            try:
                # 构建知识条目内容
                content_parts = []
                
                # 问题和答案
                prompt_val = row.get('Prompt')
                if prompt_val is not None and not pd.isna(prompt_val):
                    content_parts.append(f"问题: {prompt_val}")
                
                answer_val = row.get('Answer')
                if answer_val is not None and not pd.isna(answer_val):
                    content_parts.append(f"答案: {answer_val}")
                
                # 收集所有Wikipedia链接
                wiki_links = []
                for i in range(1, 12):  # wikipedia_link_1 到 wikipedia_link_11+
                    wiki_col = f'wikipedia_link_{i}' if i <= 10 else 'wikipedia_link_11+'
                    wiki_val = row.get(wiki_col)
                    if wiki_val is not None and not pd.isna(wiki_val):
                        wiki_links.append(str(wiki_val))
                
                if wiki_links:
                    content_parts.append(f"相关Wikipedia页面: {', '.join(wiki_links)}")
                
                # 推理类型
                reasoning_types_val = row.get('reasoning_types')
                if reasoning_types_val is not None and not pd.isna(reasoning_types_val):
                    content_parts.append(f"推理类型: {reasoning_types_val}")
                
                # 所有wiki链接（如果是完整列表）
                all_wiki_links_val = row.get('wiki_links')
                if all_wiki_links_val is not None and not pd.isna(all_wiki_links_val):
                    content_parts.append(f"完整Wiki链接列表: {all_wiki_links_val}")
                
                # 合并内容
                content = "\n\n".join(content_parts)
                
                # 构建元数据
                prompt_val = row.get('Prompt')
                answer_val = row.get('Answer')
                wiki_links_val = row.get('wiki_links')
                
                metadata = {
                    "source": "frames-benchmark",
                    "dataset": "frames-benchmark",
                    "split": "test",
                    "index": idx,
                    "question": str(prompt_val) if prompt_val is not None and not pd.isna(prompt_val) else '',
                    "answer": str(answer_val) if answer_val is not None and not pd.isna(answer_val) else '',
                    "wiki_links": str(wiki_links_val) if wiki_links_val is not None and not pd.isna(wiki_links_val) else '',
                }
                
                # 添加额外的元数据
                reasoning_types_val = row.get('reasoning_types')
                if reasoning_types_val is not None and not pd.isna(reasoning_types_val):
                    metadata['reasoning_types'] = str(reasoning_types_val)
                
                # 创建知识条目
                knowledge_entry = {
                    'content': content,
                    'metadata': metadata
                }
                
                knowledge_entries.append(knowledge_entry)
                
            except Exception as e:
                self.logger.warning(f"处理第 {idx} 行数据时出错: {e}")
                continue
        
        self.logger.info(f"成功处理 {len(knowledge_entries)} 条知识条目")
        return knowledge_entries
    
    def import_to_kms(self, knowledge_entries: List[Dict[str, Any]], modality: str = "text") -> bool:
        """
        将知识条目导入到 KMS 系统
        
        Args:
            knowledge_entries: 知识条目列表
            modality: 数据模态
            
        Returns:
            是否成功导入
        """
        try:
            if not knowledge_entries:
                self.logger.warning("没有知识条目需要导入")
                return False
            
            self.logger.info(f"准备导入 {len(knowledge_entries)} 条知识条目到 KMS")
            
            # 使用 knowledge_importer 导入数据
            valid_entries = self.importer.import_from_list(knowledge_entries, modality=modality)
            
            if not valid_entries:
                self.logger.error("没有有效的知识条目可以导入")
                return False
            
            self.logger.info(f"验证通过 {len(valid_entries)} 条有效知识条目")
            
            # 通过 service_interface 导入到向量知识库
            success_count = 0
            for i, entry in enumerate(valid_entries):
                try:
                    success = self.service.import_knowledge(entry, modality=modality)
                    if success:
                        success_count += 1
                    else:
                        self.logger.warning(f"导入知识条目失败: index {entry.get('metadata', {}).get('index', i)}")
                except Exception as e:
                    self.logger.error(f"导入单个知识条目时出错: {e}")
            
            self.logger.info(f"成功导入 {success_count}/{len(valid_entries)} 条知识条目到 KMS")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"导入知识条目到 KMS 失败: {e}")
            return False
    
    def load_and_import(self, split: str = "test", use_cache: bool = True) -> bool:
        """
        完整流程：加载数据集、处理、导入到 KMS
        
        Args:
            split: 数据集分割
            use_cache: 是否使用缓存
            
        Returns:
            是否成功完成整个流程
        """
        try:
            # 1. 加载数据集
            df = self.load_frames_dataset(split)
            if df.empty:
                self.logger.error("无法加载数据集")
                return False
            
            # 2. 缓存数据集（如果需要）
            if use_cache:
                self.cache_dataset(df, split)
            
            # 3. 处理数据
            knowledge_entries = self.process_frames_data(df)
            if not knowledge_entries:
                self.logger.error("数据处理失败")
                return False
            
            # 4. 导入到 KMS
            success = self.import_to_kms(knowledge_entries)
            
            if success:
                self.logger.info("✅ FRAMES-Benchmark 数据集成功集成到 KMS")
            else:
                self.logger.error("❌ FRAMES-Benchmark 数据集集成失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"完整流程执行失败: {e}")
            return False
    
    def verify_jane_ballou_integration(self) -> bool:
        """
        验证 "Jane Ballou" 相关数据是否正确集成
        
        Returns:
            是否能够正确检索到 "Jane Ballou" 相关信息
        """
        try:
            self.logger.info("验证 'Jane Ballou' 相关数据集成...")
            
            # 查询 "Jane Ballou"
            results = self.service.query_knowledge(
                query="Jane Ballou",
                top_k=5,
                modality="text"
            )
            
            if not results:
                self.logger.warning("未找到任何关于 'Jane Ballou' 的结果")
                return False
            
            # 检查结果中是否包含 "Jane Ballou"
            found_jane_ballou = False
            for result in results:
                content = result.get('content', '')
                if 'jane ballou' in content.lower():
                    found_jane_ballou = True
                    self.logger.info("✅ 成功找到 'Jane Ballou' 相关信息")
                    self.logger.info(f"匹配内容片段: {content[:200]}...")
                    break
            
            if not found_jane_ballou:
                self.logger.warning("❌ 未在搜索结果中找到 'Jane Ballou' 相关信息")
                self.logger.info(f"搜索结果数量: {len(results)}")
                for i, result in enumerate(results):
                    self.logger.info(f"结果 {i+1}: {result.get('content', '')[:100]}...")
            
            return found_jane_ballou
            
        except Exception as e:
            self.logger.error(f"验证 'Jane Ballou' 数据集成时出错: {e}")
            return False


def main():
    """主函数 - 用于测试"""
    loader = FramesBenchmarkLoader()
    
    # 加载并导入 FRAMES-Benchmark 数据集
    success = loader.load_and_import(split="test", use_cache=True)
    
    if success:
        print("✅ FRAMES-Benchmark 数据集集成成功")
        
        # 验证 "Jane Ballou" 数据
        jane_found = loader.verify_jane_ballou_integration()
        if jane_found:
            print("✅ 'Jane Ballou' 数据验证成功")
        else:
            print("❌ 'Jane Ballou' 数据验证失败")
    else:
        print("❌ FRAMES-Benchmark 数据集集成失败")


if __name__ == "__main__":
    main()