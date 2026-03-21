#!/usr/bin/env python3
"""
Data Cleaner Tool - 数据清洗工具

清洗文本、去重、格式化，用于数据采集工作流
"""

import re
import time
import hashlib
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from collections import Counter

from .base_tool import BaseTool, ToolResult


@dataclass
class CleanResult:
    """清洗结果"""
    original_count: int
    cleaned_count: int
    duplicates_removed: int
    issues_removed: int
    cleaned_text: str
    duplicates: List[str]
    issues: List[str]


@dataclass
class DedupeResult:
    """去重结果"""
    original_count: int
    unique_count: int
    duplicates_removed: List[Dict[str, Any]]


class DataCleaner(BaseTool):
    """
    数据清洗工具
    
    支持：文本清洗、去重、质量检查
    """
    
    def __init__(self):
        super().__init__(
            tool_name="data_cleaner",
            description="清洗文本、去重、格式化，检查数据质量"
        )
        self._seen_hashes: Set[str] = set()
        self._seen_texts: Dict[str, str] = {}
    
    async def call(
        self,
        action: str,
        texts: List[str] = None,
        text: str = None,
        remove_duplicates: bool = True,
        remove_noise: bool = True,
        normalize_whitespace: bool = True,
        remove_urls: bool = False,
        remove_emails: bool = False,
        min_length: int = 10,
        max_length: int = 10000,
        **kwargs
    ) -> ToolResult:
        """
        清洗数据
        
        Args:
            action: 操作类型 (clean/dedupe/validate)
            texts: 文本列表 (用于批量清洗)
            text: 单个文本 (用于单条清洗)
            remove_duplicates: 是否去重
            remove_noise: 是否移除噪音
            normalize_whitespace: 是否规范化空白
            remove_urls: 是否移除 URL
            remove_emails: 是否移除邮箱
            min_length: 最小长度
            max_length: 最大长度
            
        Returns:
            ToolResult: 清洗结果
        """
        start_time = time.time()
        
        try:
            if action == "clean":
                result = await self._clean_texts(
                    texts=texts,
                    text=text,
                    remove_duplicates=remove_duplicates,
                    remove_noise=remove_noise,
                    normalize_whitespace=normalize_whitespace,
                    remove_urls=remove_urls,
                    remove_emails=remove_emails,
                    min_length=min_length,
                    max_length=max_length
                )
            elif action == "dedupe":
                result = await self._dedupe(
                    texts=texts or [text] if text else [],
                    use_hash=True
                )
            elif action == "validate":
                result = await self._validate(
                    texts=texts or [text] if text else [],
                    min_length=min_length,
                    max_length=max_length
                )
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unknown action: {action}",
                    execution_time=time.time() - start_time
                )
            
            return ToolResult(
                success=True,
                data=result if isinstance(result, dict) else result.__dict__,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"数据清洗失败: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def _clean_texts(
        self,
        texts: List[str],
        text: str,
        remove_duplicates: bool,
        remove_noise: bool,
        normalize_whitespace: bool,
        remove_urls: bool,
        remove_emails: bool,
        min_length: int,
        max_length: int
    ) -> Dict[str, Any]:
        """清洗多个文本"""
        
        if texts is None and text:
            texts = [text]
        
        if not texts:
            return {
                "original_count": 0,
                "cleaned_count": 0,
                "duplicates_removed": 0,
                "issues_removed": 0,
                "cleaned_texts": [],
                "duplicates": [],
                "issues": []
            }
        
        original_count = len(texts)
        cleaned_texts = []
        duplicates = []
        issues = []
        seen_hashes: Set[str] = set()
        
        for i, t in enumerate(texts):
            # 清洗文本
            cleaned = self._clean_single(
                text=t,
                remove_noise=remove_noise,
                normalize_whitespace=normalize_whitespace,
                remove_urls=remove_urls,
                remove_emails=remove_emails
            )
            
            # 长度检查
            if len(cleaned) < min_length:
                issues.append(f"Text {i}: too short ({len(cleaned)} < {min_length})")
                continue
            
            if len(cleaned) > max_length:
                cleaned = cleaned[:max_length]
            
            # 去重检查
            if remove_duplicates:
                text_hash = hashlib.md5(cleaned.encode()).hexdigest()
                if text_hash in seen_hashes:
                    duplicates.append(cleaned[:50])
                    continue
                seen_hashes.add(text_hash)
            
            cleaned_texts.append(cleaned)
        
        return {
            "original_count": original_count,
            "cleaned_count": len(cleaned_texts),
            "duplicates_removed": len(duplicates),
            "issues_removed": len(issues),
            "cleaned_texts": cleaned_texts,
            "duplicates": duplicates[:10],  # 限制数量
            "issues": issues[:10]
        }
    
    def _clean_single(
        self,
        text: str,
        remove_noise: bool,
        normalize_whitespace: bool,
        remove_urls: bool,
        remove_emails: bool
    ) -> str:
        """清洗单个文本"""
        
        if not text:
            return ""
        
        cleaned = text
        
        # 移除 URL
        if remove_urls:
            cleaned = re.sub(r'https?://\S+', '', cleaned)
            cleaned = re.sub(r'www\.\S+', '', cleaned)
        
        # 移除邮箱
        if remove_emails:
            cleaned = re.sub(r'\S+@\S+\.\S+', '', cleaned)
        
        # 移除噪音模式
        if remove_noise:
            noise_patterns = [
                r'广告', r'推广', r' Sponsored ',
                r'点击查看', r'更多精彩',
                r'Copyright \d+', r'© \d+',
                r'登录|注册|订阅',
            ]
            for pattern in noise_patterns:
                cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # 规范化空白
        if normalize_whitespace:
            cleaned = re.sub(r'\s+', ' ', cleaned)
            cleaned = cleaned.strip()
        
        return cleaned
    
    async def _dedupe(self, texts: List[str], use_hash: bool = True) -> DedupeResult:
        """去重"""
        
        original_count = len(texts)
        seen: Set[str] = set()
        unique_texts: List[str] = []
        duplicates: List[Dict[str, Any]] = []
        
        for text in texts:
            if use_hash:
                key = hashlib.md5(text.encode()).hexdigest()
            else:
                key = text
            
            if key in seen:
                duplicates.append({
                    "text": text[:100],
                    "key": key
                })
            else:
                seen.add(key)
                unique_texts.append(text)
        
        return DedupeResult(
            original_count=original_count,
            unique_count=len(unique_texts),
            duplicates_removed=duplicates
        )
    
    async def _validate(
        self,
        texts: List[str],
        min_length: int,
        max_length: int
    ) -> Dict[str, Any]:
        """验证数据质量"""
        
        valid = []
        invalid = []
        
        for i, text in enumerate(texts):
            issues = []
            
            if not text or not text.strip():
                issues.append("empty")
            
            if len(text) < min_length:
                issues.append(f"too_short ({len(text)} < {min_length})")
            
            if len(text) > max_length:
                issues.append(f"too_long ({len(text)} > {max_length})")
            
            # 检查语言一致性（假设非 ASCII 为非英文）
            non_ascii_ratio = sum(1 for c in text if ord(c) > 127) / max(len(text), 1)
            if non_ascii_ratio > 0.5:
                issues.append("high_non_ascii_ratio")
            
            if issues:
                invalid.append({
                    "index": i,
                    "text": text[:100],
                    "issues": issues
                })
            else:
                valid.append(text)
        
        return {
            "total": len(texts),
            "valid_count": len(valid),
            "invalid_count": len(invalid),
            "valid": valid[:50],
            "invalid": invalid[:50]
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_processed": len(self._seen_texts),
            "unique_count": len(set(self._seen_texts.values())),
            "duplicate_count": len(self._seen_texts) - len(set(self._seen_texts.values()))
        }
    
    def reset(self):
        """重置内部状态"""
        self._seen_hashes.clear()
        self._seen_texts.clear()
