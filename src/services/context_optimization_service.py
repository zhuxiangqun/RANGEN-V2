#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上下文优化服务 - Token优化和上下文压缩策略

基于上下文工程最佳实践：
1. Token优化：减少不必要的token使用，优化提示词结构
2. 上下文压缩：智能压缩长上下文，保留关键信息
3. 智能截断：基于重要性截断，避免信息丢失
4. 重复检测：检测并移除重复内容
5. 语义缓存：缓存相似查询结果，减少重复计算

核心功能：
- Token使用分析和优化建议
- 上下文长度管理和压缩
- 提示词工程优化
- 语义相似性检测和去重
- 性能与质量平衡优化
"""

import re
import hashlib
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


class OptimizationStrategy(str, Enum):
    """优化策略枚举"""
    TOKEN_REDUCTION = "token_reduction"      # Token减少
    CONTEXT_COMPRESSION = "context_compression"  # 上下文压缩
    SUMMARIZATION = "summarization"          # 摘要生成
    TRUNCATION = "truncation"                # 截断处理
    DEDUPLICATION = "deduplication"          # 去重处理
    PROMPT_OPTIMIZATION = "prompt_optimization"  # 提示词优化


class CompressionMethod(str, Enum):
    """压缩方法枚举"""
    EXTRACTIVE = "extractive"      # 抽取式（保留关键句子）
    ABSTRACTIVE = "abstractive"    # 抽象式（生成摘要）
    HYBRID = "hybrid"              # 混合式
    SEMANTIC = "semantic"          # 语义压缩（基于嵌入）


@dataclass
class ContextOptimizationConfig:
    """上下文优化配置"""
    max_context_tokens: int = 8000                 # 最大上下文token数
    target_compression_ratio: float = 0.5          # 目标压缩比例
    enable_semantic_cache: bool = True             # 启用语义缓存
    cache_ttl_seconds: int = 3600                  # 缓存过期时间
    min_similarity_threshold: float = 0.8          # 最小相似度阈值
    enable_token_analysis: bool = True             # 启用token分析
    optimization_strategies: List[OptimizationStrategy] = field(default_factory=list)
    compression_method: CompressionMethod = CompressionMethod.HYBRID
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.optimization_strategies:
            self.optimization_strategies = [
                OptimizationStrategy.TOKEN_REDUCTION,
                OptimizationStrategy.CONTEXT_COMPRESSION,
                OptimizationStrategy.DEDUPLICATION
            ]


@dataclass
class TokenAnalysisResult:
    """Token分析结果"""
    total_tokens: int                              # 总token数
    prompt_tokens: int                             # 提示词token数
    context_tokens: int                            # 上下文token数
    estimated_cost: float                          # 预估成本
    optimization_suggestions: List[str]            # 优化建议
    potential_savings_percent: float               # 潜在节省百分比
    compression_applicable: bool                   # 是否可压缩


@dataclass
class OptimizationResult:
    """优化结果"""
    original_content: str                          # 原始内容
    optimized_content: str                         # 优化后内容
    tokens_before: int                             # 优化前token数
    tokens_after: int                              # 优化后token数
    tokens_saved: int                              # 节省的token数
    compression_ratio: float                       # 压缩比例
    applied_strategies: List[OptimizationStrategy] # 应用的策略
    quality_score: float                           # 质量评分（0-1）
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticCacheEntry:
    """语义缓存条目"""
    content_hash: str                              # 内容哈希
    original_content: str                          # 原始内容
    compressed_content: str                        # 压缩后内容
    tokens_saved: int                              # 节省的token数
    created_at: float                              # 创建时间
    accessed_count: int = 0                        # 访问次数
    last_accessed: float = 0                       # 最后访问时间


class ContextOptimizationService:
    """上下文优化服务"""
    
    def __init__(self, config: Optional[ContextOptimizationConfig] = None):
        self.config = config or ContextOptimizationConfig()
        self.logger = logging.getLogger(__name__)
        
        # 语义缓存（基于内容哈希）
        self.semantic_cache: Dict[str, SemanticCacheEntry] = {}
        self.cache_lock = threading.RLock()
        
        # 统计信息
        self.stats = {
            "total_optimizations": 0,
            "total_tokens_saved": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "compression_applications": 0
        }
        self.stats_lock = threading.RLock()
        
        # 初始化优化策略
        self._init_optimization_strategies()
        
        self.logger.info("上下文优化服务初始化完成")
    
    def _init_optimization_strategies(self) -> None:
        """初始化优化策略处理器"""
        self.strategy_handlers = {
            OptimizationStrategy.TOKEN_REDUCTION: self._apply_token_reduction,
            OptimizationStrategy.CONTEXT_COMPRESSION: self._apply_context_compression,
            OptimizationStrategy.SUMMARIZATION: self._apply_summarization,
            OptimizationStrategy.TRUNCATION: self._apply_truncation,
            OptimizationStrategy.DEDUPLICATION: self._apply_deduplication,
            OptimizationStrategy.PROMPT_OPTIMIZATION: self._apply_prompt_optimization
        }
    
    def optimize_context(
        self, 
        content: str, 
        context_type: str = "general",
        strategies: Optional[List[OptimizationStrategy]] = None,
        max_tokens: Optional[int] = None
    ) -> OptimizationResult:
        """
        优化上下文内容
        
        Args:
            content: 要优化的内容
            context_type: 上下文类型（general, code, document等）
            strategies: 优化策略列表（默认使用配置策略）
            max_tokens: 最大token限制
            
        Returns:
            OptimizationResult: 优化结果
        """
        start_time = time.time()
        
        # 检查语义缓存
        if self.config.enable_semantic_cache:
            cached_result = self._check_semantic_cache(content)
            if cached_result:
                self._update_stats(cache_hit=True)
                self.logger.info(f"语义缓存命中，节省 {cached_result.tokens_saved} tokens")
                return cached_result
        
        self._update_stats(cache_hit=False)
        
        # 确定使用的策略
        strategies_to_apply = strategies or self.config.optimization_strategies
        
        # 分析token使用
        token_analysis = self.analyze_token_usage(content)
        
        # 初始状态
        current_content = content
        current_tokens = token_analysis.total_tokens
        applied_strategies = []
        
        # 确定最大token限制
        token_limit = max_tokens or self.config.max_context_tokens
        
        # 如果已经在限制内，检查是否还需要优化
        if current_tokens <= token_limit:
            # 只应用轻量级优化
            strategies_to_apply = [
                s for s in strategies_to_apply 
                if s in [OptimizationStrategy.TOKEN_REDUCTION, OptimizationStrategy.DEDUPLICATION]
            ]
        
        # 按顺序应用优化策略
        for strategy in strategies_to_apply:
            if current_tokens <= token_limit and strategy not in [
                OptimizationStrategy.TOKEN_REDUCTION,
                OptimizationStrategy.DEDUPLICATION
            ]:
                # 如果已经满足token限制，跳过重型优化
                continue
            
            handler = self.strategy_handlers.get(strategy)
            if handler:
                try:
                    result = handler(current_content, context_type, token_limit)
                    if result and result["optimized"]:
                        current_content = result["content"]
                        current_tokens = result["tokens"]
                        applied_strategies.append(strategy)
                        self.logger.debug(f"应用策略 {strategy.value}: {result.get('details', '')}")
                        
                        # 检查是否已达到目标
                        if current_tokens <= token_limit:
                            break
                except Exception as e:
                    self.logger.error(f"策略 {strategy.value} 应用失败: {e}")
        
        # 计算优化结果
        tokens_saved = token_analysis.total_tokens - current_tokens
        compression_ratio = current_tokens / max(token_analysis.total_tokens, 1)
        
        # 估算质量评分（简化版本）
        quality_score = self._estimate_quality_score(
            content, current_content, tokens_saved, applied_strategies
        )
        
        result = OptimizationResult(
            original_content=content,
            optimized_content=current_content,
            tokens_before=token_analysis.total_tokens,
            tokens_after=current_tokens,
            tokens_saved=tokens_saved,
            compression_ratio=compression_ratio,
            applied_strategies=applied_strategies,
            quality_score=quality_score,
            metadata={
                "context_type": context_type,
                "optimization_time_ms": (time.time() - start_time) * 1000,
                "token_analysis": token_analysis.optimization_suggestions
            }
        )
        
        # 更新统计
        with self.stats_lock:
            self.stats["total_optimizations"] += 1
            self.stats["total_tokens_saved"] += tokens_saved
            if OptimizationStrategy.CONTEXT_COMPRESSION in applied_strategies:
                self.stats["compression_applications"] += 1
        
        # 添加到语义缓存
        if self.config.enable_semantic_cache and tokens_saved > 0:
            self._add_to_semantic_cache(content, result)
        
        self.logger.info(f"上下文优化完成: 节省 {tokens_saved} tokens ({compression_ratio:.1%})")
        
        return result
    
    def analyze_token_usage(self, content: str) -> TokenAnalysisResult:
        """
        分析Token使用情况
        
        注意：这是一个简化版本，实际系统中应使用实际的tokenizer
        这里使用启发式方法：大约4个字符=1个token
        
        Args:
            content: 要分析的内容
            
        Returns:
            TokenAnalysisResult: Token分析结果
        """
        # 简化token估算：4个字符≈1个token
        estimated_tokens = len(content) // 4
        
        # 分析内容结构（简化版本）
        lines = content.split('\n')
        code_blocks = len(re.findall(r'```.*?```', content, re.DOTALL))
        urls = len(re.findall(r'https?://\S+', content))
        
        # 生成优化建议
        suggestions = []
        
        # 检查长段落
        long_paragraphs = [p for p in content.split('\n\n') if len(p) > 1000]
        if long_paragraphs:
            suggestions.append(f"检测到 {len(long_paragraphs)} 个过长段落，考虑分割或压缩")
        
        # 检查重复内容（简化检测）
        if len(set(lines)) < len(lines) * 0.8:
            suggestions.append("检测到可能的重复内容，考虑去重")
        
        # 检查代码块
        if code_blocks > 3:
            suggestions.append(f"检测到 {code_blocks} 个代码块，考虑简化或提取关键部分")
        
        # 检查URL
        if urls > 5:
            suggestions.append(f"检测到 {urls} 个URL，考虑移除或缩短")
        
        # 估算潜在节省
        potential_savings = 0.0
        if suggestions:
            # 根据建议数量估算节省比例
            potential_savings = min(0.3, len(suggestions) * 0.05)
        
        # 检查是否可压缩
        compression_applicable = estimated_tokens > 1000  # 超过1000token可压缩
        
        return TokenAnalysisResult(
            total_tokens=estimated_tokens,
            prompt_tokens=estimated_tokens * 0.3,  # 估算值
            context_tokens=estimated_tokens * 0.7,  # 估算值
            estimated_cost=estimated_tokens * 0.000002,  # 假设$2/1M tokens
            optimization_suggestions=suggestions,
            potential_savings_percent=potential_savings,
            compression_applicable=compression_applicable
        )
    
    def _apply_token_reduction(self, content: str, context_type: str, max_tokens: int) -> Dict[str, Any]:
        """应用Token减少策略"""
        optimized = content
        
        # 移除多余的空格和换行
        optimized = re.sub(r'\n{3,}', '\n\n', optimized)
        optimized = re.sub(r' {2,}', ' ', optimized)
        
        # 移除多余的标点
        optimized = re.sub(r'[.,;:!?]{2,}', lambda m: m.group()[0], optimized)
        
        # 根据上下文类型进行特定优化
        if context_type == "code":
            # 代码优化：移除多余注释和空白
            optimized = self._optimize_code_content(optimized)
        elif context_type == "document":
            # 文档优化：简化格式
            optimized = self._optimize_document_content(optimized)
        
        # 估算token减少
        original_tokens = len(content) // 4
        optimized_tokens = len(optimized) // 4
        
        if optimized_tokens < original_tokens:
            return {
                "optimized": True,
                "content": optimized,
                "tokens": optimized_tokens,
                "details": f"Token减少: {original_tokens - optimized_tokens} tokens"
            }
        
        return {"optimized": False, "content": content, "tokens": original_tokens}
    
    def _apply_context_compression(self, content: str, context_type: str, max_tokens: int) -> Dict[str, Any]:
        """应用上下文压缩策略"""
        # 简化版本：提取关键句子
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 5:
            # 句子太少，不适合压缩
            original_tokens = len(content) // 4
            return {"optimized": False, "content": content, "tokens": original_tokens}
        
        # 提取关键句子（前30% + 后20%）
        keep_count = max(3, int(len(sentences) * 0.3))
        key_sentences = sentences[:keep_count] + sentences[-keep_count//2:]
        
        # 确保不重复
        unique_sentences = []
        seen = set()
        for s in key_sentences:
            if s not in seen and len(s) > 10:  # 至少10个字符
                unique_sentences.append(s)
                seen.add(s)
        
        compressed_content = '. '.join(unique_sentences) + '.'
        
        # 估算token
        original_tokens = len(content) // 4
        compressed_tokens = len(compressed_content) // 4
        
        if compressed_tokens < original_tokens * self.config.target_compression_ratio:
            return {
                "optimized": True,
                "content": compressed_content,
                "tokens": compressed_tokens,
                "details": f"上下文压缩: {original_tokens}→{compressed_tokens} tokens"
            }
        
        return {"optimized": False, "content": content, "tokens": original_tokens}
    
    def _apply_summarization(self, content: str, context_type: str, max_tokens: int) -> Dict[str, Any]:
        """应用摘要生成策略（简化版本）"""
        # 在实际系统中，这里应该调用LLM生成摘要
        # 这里使用简单的启发式方法
        
        if len(content) < 500:
            original_tokens = len(content) // 4
            return {"optimized": False, "content": content, "tokens": original_tokens}
        
        # 提取第一段和最后一段
        paragraphs = content.split('\n\n')
        if len(paragraphs) >= 3:
            summary = paragraphs[0] + '\n\n' + paragraphs[-1]
        else:
            summary = content[:500] + '...'  # 简单截断
        
        original_tokens = len(content) // 4
        summary_tokens = len(summary) // 4
        
        if summary_tokens < original_tokens * 0.5:  # 至少压缩50%
            return {
                "optimized": True,
                "content": summary,
                "tokens": summary_tokens,
                "details": f"摘要生成: {original_tokens}→{summary_tokens} tokens"
            }
        
        return {"optimized": False, "content": content, "tokens": original_tokens}
    
    def _apply_truncation(self, content: str, context_type: str, max_tokens: int) -> Dict[str, Any]:
        """应用截断策略"""
        target_chars = max_tokens * 4  # 估算字符数
        
        if len(content) <= target_chars:
            original_tokens = len(content) // 4
            return {"optimized": False, "content": content, "tokens": original_tokens}
        
        # 智能截断：尝试在段落边界截断
        truncated = content[:target_chars]
        
        # 查找最后一个段落分隔符
        last_paragraph = truncated.rfind('\n\n')
        if last_paragraph > target_chars * 0.8:  # 如果在后20%内找到
            truncated = truncated[:last_paragraph]
        
        # 查找最后一个句子结束符
        last_sentence = max(
            truncated.rfind('. '),
            truncated.rfind('! '),
            truncated.rfind('? ')
        )
        if last_sentence > target_chars * 0.9:  # 如果在后10%内找到
            truncated = truncated[:last_sentence + 1]
        
        truncated_tokens = len(truncated) // 4
        
        return {
            "optimized": True,
            "content": truncated + '...',
            "tokens": truncated_tokens,
            "details": f"智能截断: {len(content)//4}→{truncated_tokens} tokens"
        }
    
    def _apply_deduplication(self, content: str, context_type: str, max_tokens: int) -> Dict[str, Any]:
        """应用去重策略"""
        lines = content.split('\n')
        unique_lines = []
        seen_lines = set()
        
        for line in lines:
            # 简化去重：忽略空格和大小写差异
            normalized = line.strip().lower()
            if normalized and normalized not in seen_lines:
                unique_lines.append(line)
                seen_lines.add(normalized)
        
        deduplicated = '\n'.join(unique_lines)
        
        original_tokens = len(content) // 4
        deduplicated_tokens = len(deduplicated) // 4
        
        if deduplicated_tokens < original_tokens:
            return {
                "optimized": True,
                "content": deduplicated,
                "tokens": deduplicated_tokens,
                "details": f"内容去重: {original_tokens - deduplicated_tokens} tokens"
            }
        
        return {"optimized": False, "content": content, "tokens": original_tokens}
    
    def _apply_prompt_optimization(self, content: str, context_type: str, max_tokens: int) -> Dict[str, Any]:
        """应用提示词优化策略"""
        optimized = content
        
        # 移除多余的提示词短语
        redundant_phrases = [
            r'please\s+',
            r'kindly\s+',
            r'could\s+you\s+',
            r'would\s+you\s+',
            r'i\s+would\s+like\s+to\s+',
            r'can\s+you\s+'
        ]
        
        for phrase in redundant_phrases:
            optimized = re.sub(phrase, '', optimized, flags=re.IGNORECASE)
        
        # 简化问候语
        optimized = re.sub(r'^(hi|hello|hey|dear)\s+[^,\n]*,?\s*', '', optimized, flags=re.IGNORECASE)
        
        original_tokens = len(content) // 4
        optimized_tokens = len(optimized) // 4
        
        if optimized_tokens < original_tokens:
            return {
                "optimized": True,
                "content": optimized,
                "tokens": optimized_tokens,
                "details": f"提示词优化: {original_tokens - optimized_tokens} tokens"
            }
        
        return {"optimized": False, "content": content, "tokens": original_tokens}
    
    def _optimize_code_content(self, code: str) -> str:
        """优化代码内容"""
        optimized = code
        
        # 移除多余的空行（保留最多2个连续空行）
        optimized = re.sub(r'\n{3,}', '\n\n', optimized)
        
        # 移除行尾空格
        optimized = '\n'.join(line.rstrip() for line in optimized.split('\n'))
        
        return optimized
    
    def _optimize_document_content(self, document: str) -> str:
        """优化文档内容"""
        optimized = document
        
        # 简化标题格式
        optimized = re.sub(r'^(#{1,6})\s+', r'# ', optimized, flags=re.MULTILINE)
        
        # 移除多余的空格
        optimized = re.sub(r' {2,}', ' ', optimized)
        
        return optimized
    
    def _estimate_quality_score(
        self, 
        original: str, 
        optimized: str, 
        tokens_saved: int,
        strategies: List[OptimizationStrategy]
    ) -> float:
        """估算质量评分（简化版本）"""
        base_score = 1.0
        
        # 基于节省的token数调整
        if tokens_saved > 0:
            # 节省越多，潜在质量损失越大
            compression_ratio = len(optimized) / max(len(original), 1)
            if compression_ratio < 0.3:
                base_score *= 0.7  # 压缩过多
            elif compression_ratio < 0.6:
                base_score *= 0.9  # 适度压缩
            else:
                base_score *= 0.95  # 轻微压缩
        
        # 基于策略调整
        heavy_strategies = [
            OptimizationStrategy.CONTEXT_COMPRESSION,
            OptimizationStrategy.SUMMARIZATION,
            OptimizationStrategy.TRUNCATION
        ]
        
        heavy_count = sum(1 for s in strategies if s in heavy_strategies)
        if heavy_count > 1:
            base_score *= 0.8  # 多个重型策略
        
        return max(0.1, min(1.0, base_score))
    
    def _check_semantic_cache(self, content: str) -> Optional[OptimizationResult]:
        """检查语义缓存"""
        content_hash = self._generate_content_hash(content)
        
        with self.cache_lock:
            entry = self.semantic_cache.get(content_hash)
            if entry:
                # 检查是否过期
                current_time = time.time()
                if current_time - entry.created_at <= self.config.cache_ttl_seconds:
                    # 更新访问统计
                    entry.accessed_count += 1
                    entry.last_accessed = current_time
                    
                    # 创建优化结果
                    return OptimizationResult(
                        original_content=content,
                        optimized_content=entry.compressed_content,
                        tokens_before=len(content) // 4,
                        tokens_after=len(entry.compressed_content) // 4,
                        tokens_saved=entry.tokens_saved,
                        compression_ratio=len(entry.compressed_content) / max(len(content), 1),
                        applied_strategies=[OptimizationStrategy.CONTEXT_COMPRESSION],
                        quality_score=0.9,  # 缓存结果假设质量较高
                        metadata={
                            "from_cache": True,
                            "cache_hit": True,
                            "original_hash": entry.content_hash
                        }
                    )
                else:
                    # 缓存过期，移除
                    del self.semantic_cache[content_hash]
        
        return None
    
    def _add_to_semantic_cache(self, content: str, result: OptimizationResult) -> None:
        """添加到语义缓存"""
        content_hash = self._generate_content_hash(content)
        
        with self.cache_lock:
            # 检查缓存大小，如果需要则清理
            max_cache_size = 1000
            if len(self.semantic_cache) >= max_cache_size:
                # 移除最旧或最少使用的条目（简化：移除第一个）
                if self.semantic_cache:
                    oldest_key = next(iter(self.semantic_cache))
                    del self.semantic_cache[oldest_key]
            
            entry = SemanticCacheEntry(
                content_hash=content_hash,
                original_content=content,
                compressed_content=result.optimized_content,
                tokens_saved=result.tokens_saved,
                created_at=time.time()
            )
            
            self.semantic_cache[content_hash] = entry
    
    def _generate_content_hash(self, content: str) -> str:
        """生成内容哈希"""
        # 简化版本：使用MD5哈希
        normalized = content.strip().lower()
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    def _update_stats(self, cache_hit: bool) -> None:
        """更新统计信息"""
        with self.stats_lock:
            if cache_hit:
                self.stats["cache_hits"] += 1
            else:
                self.stats["cache_misses"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.stats_lock:
            stats = self.stats.copy()
            
            # 计算缓存命中率
            total_cache_access = stats["cache_hits"] + stats["cache_misses"]
            if total_cache_access > 0:
                stats["cache_hit_rate"] = stats["cache_hits"] / total_cache_access
            else:
                stats["cache_hit_rate"] = 0.0
            
            # 计算平均节省
            if stats["total_optimizations"] > 0:
                stats["avg_tokens_saved"] = stats["total_tokens_saved"] / stats["total_optimizations"]
            else:
                stats["avg_tokens_saved"] = 0
            
            return stats
    
    def clear_cache(self) -> None:
        """清空缓存"""
        with self.cache_lock:
            cache_size = len(self.semantic_cache)
            self.semantic_cache.clear()
            self.logger.info(f"已清空语义缓存，释放 {cache_size} 个条目")


# 全局实例（单例模式）
_context_optimization_service = None
_context_optimization_lock = threading.RLock()


def get_context_optimization_service(
    config: Optional[ContextOptimizationConfig] = None
) -> ContextOptimizationService:
    """
    获取上下文优化服务实例（单例模式）
    
    Args:
        config: 配置对象
        
    Returns:
        ContextOptimizationService: 服务实例
    """
    global _context_optimization_service
    
    with _context_optimization_lock:
        if _context_optimization_service is None:
            _context_optimization_service = ContextOptimizationService(config)
        
        return _context_optimization_service


__all__ = [
    "OptimizationStrategy",
    "CompressionMethod",
    "ContextOptimizationConfig",
    "TokenAnalysisResult",
    "OptimizationResult",
    "SemanticCacheEntry",
    "ContextOptimizationService",
    "get_context_optimization_service",
]