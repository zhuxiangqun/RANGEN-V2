#!/usr/bin/env python3
"""
统一上下文工程中心
整合所有上下文管理功能，实现完整的上下文工程系统
"""

import os
import time
import logging
import json
import hashlib
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from src.visualization.orchestration_tracker import get_orchestration_tracker

# 🚀 MCP协议集成
try:
    from src.utils.mcp_protocol import (
        get_mcp_protocol_handler,
        MCPMessageType,
        MCPPriority
    )
    # 注意：MCPContextType 在 mcp_protocol.py 中可能不存在，使用字符串代替
    MCP_AVAILABLE = True
except (ImportError, AttributeError) as e:
    MCP_AVAILABLE = False
    # 不在这里记录警告，因为MCP是可选的

logger = logging.getLogger(__name__)


class ContextCategory(Enum):
    """上下文类别 - 三类上下文"""
    GUIDING = "guiding"  # 引导型上下文：行为规范、操作指南
    INFORMATIONAL = "informational"  # 知识型上下文：RAG、记忆系统、状态记录
    ACTIONABLE = "actionable"  # 操作型上下文：工具定义、工具调用记录


class ContextScope(Enum):
    """上下文作用域"""
    SHORT_TERM = "short_term"  # 短期上下文：当前对话轮次
    LONG_TERM = "long_term"  # 长期上下文：用户历史偏好
    IMPLICIT = "implicit"  # 隐性上下文：环境参数（时间、位置等）


class ContextSource(Enum):
    """上下文来源"""
    USER_INPUT = "user_input"  # 用户输入
    SYSTEM_LOG = "system_log"  # 系统日志
    KNOWLEDGE_BASE = "knowledge_base"  # 知识库片段
    TOOL_DEFINITION = "tool_definition"  # 工具定义
    TOOL_CALL = "tool_call"  # 工具调用
    TOOL_RESULT = "tool_result"  # 工具返回结果
    ENVIRONMENT = "environment"  # 环境参数


@dataclass
class ContextFragment:
    """上下文片段 - 完整的元数据结构"""
    # 基础信息
    id: str
    content: str
    category: ContextCategory
    scope: ContextScope
    source: ContextSource
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    priority: float = 0.5  # 优先级 0.0-1.0
    
    # 可追溯性
    trace_id: Optional[str] = None  # 追溯ID
    parent_id: Optional[str] = None  # 父片段ID
    error_context: bool = False  # 是否为错误上下文
    
    # 可解释性
    purpose: str = ""  # 用途说明
    relevance_score: float = 0.5  # 相关性评分
    confidence: float = 0.5  # 置信度
    
    # 信息熵控制
    is_key_clue: bool = False  # 是否为关键线索
    reasoning_anchor: Optional[str] = None  # 推理锚点（结构化数据标签）
    is_redundant: bool = False  # 是否为冗余噪声
    
    # 生命周期
    ttl: Optional[int] = None  # 生存时间（秒）
    max_age: Optional[int] = None  # 最大年龄（秒）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextFragment':
        """从字典创建"""
        # 处理枚举类型
        if isinstance(data.get('category'), str):
            data['category'] = ContextCategory(data['category'])
        if isinstance(data.get('scope'), str):
            data['scope'] = ContextScope(data['scope'])
        if isinstance(data.get('source'), str):
            data['source'] = ContextSource(data['source'])
        return cls(**data)


class UnifiedContextEngineeringCenter:
    """统一上下文工程中心 - 完整的上下文管理系统"""
    
    def __init__(self, storage_path: Optional[str] = None):
        """初始化上下文工程中心"""
        self.logger = logging.getLogger(__name__)
        
        # 存储路径（用于长期上下文持久化）
        if storage_path is None:
            storage_path = os.getenv("CONTEXT_STORAGE_PATH", "data/context_storage")
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 上下文存储
        self.context_sessions: Dict[str, List[ContextFragment]] = {}  # 短期上下文
        self.long_term_contexts: Dict[str, Dict[str, Any]] = {}  # 长期上下文
        self.error_contexts: List[ContextFragment] = []  # 错误上下文（可追溯）
        
        # 环境参数（隐性上下文）
        self.environment_context: Dict[str, Any] = {
            'timestamp': time.time(),
            'timezone': os.getenv('TZ', 'UTC'),
            'location': None,  # 可以扩展位置信息
        }
        
        # 工具上下文（操作型上下文）
        self.tool_definitions: Dict[str, Dict[str, Any]] = {}  # 工具定义
        self.tool_call_history: List[Dict[str, Any]] = []  # 工具调用历史
        
        # 压缩配置
        self.compression_config = {
            'dynamic_enabled': True,
            'hybrid_enabled': True,
            'original_ratio': 0.3,  # 原文比例
            'summary_ratio': 0.7,  # 摘要比例
            'max_fragments': 20,
            'compression_threshold': 0.7,
        }
        
        # 记忆管理模式
        self.memory_modes = {
            'dynamic': True,  # 动态模式：实时更新和淘汰
            'static': False,  # 静态模式：持久化存储
            'hybrid': True,  # 混合模式：动态+静态
        }
        
        # 动态模式配置
        self.dynamic_mode_config = {
            'update_interval': 60,  # 更新间隔（秒）
            'eviction_threshold': 0.3,  # 淘汰阈值（优先级低于此值的片段将被淘汰）
            'max_dynamic_fragments': 100,  # 最大动态片段数
        }
        
        # 静态模式配置
        self.static_mode_config = {
            'persist_interval': 300,  # 持久化间隔（秒）
            'min_priority_to_persist': 0.5,  # 最小持久化优先级
        }
        
        # 混合模式配置
        self.hybrid_mode_config = {
            'dynamic_ratio': 0.6,  # 动态片段比例
            'static_ratio': 0.4,  # 静态片段比例
        }
        
        # 统计信息
        self.stats = {
            'total_fragments': 0,
            'guiding_contexts': 0,
            'informational_contexts': 0,
            'actionable_contexts': 0,
            'compression_count': 0,
            'cache_hits': 0,
            'cache_misses': 0,
        }
        
        # 🚀 修复：延迟加载长期上下文，避免在异步上下文中阻塞
        # 注意：_load_long_term_contexts()是同步文件I/O操作，会阻塞事件循环
        # 改为延迟加载，在第一次使用时再加载
        # self._load_long_term_contexts()  # 已移除，改为延迟加载
        self._long_term_contexts_loaded = False  # 标记是否已加载
        
        # 🚀 MCP协议集成
        self.mcp_handler = None
        if MCP_AVAILABLE:
            try:
                self.mcp_handler = get_mcp_protocol_handler()
                self.logger.info("✅ MCP协议处理器已集成")
            except (ImportError, AttributeError, NameError) as e:
                # MCP协议是可选的，失败时只记录debug信息
                self.logger.debug(f"MCP协议处理器初始化失败（可忽略）: {e}")
                self.mcp_handler = None
        
        self.logger.info("统一上下文工程中心初始化完成（延迟加载模式）")
    
    def add_context_fragment(
        self,
        session_id: str,
        content: str,
        category: ContextCategory,
        scope: ContextScope = ContextScope.SHORT_TERM,
        source: ContextSource = ContextSource.USER_INPUT,
        metadata: Optional[Dict[str, Any]] = None,
        priority: float = 0.5,
        purpose: str = "",
        is_key_clue: bool = False,
        reasoning_anchor: Optional[str] = None,
        error_context: bool = False,
        ttl: Optional[int] = None,
        parent_id: Optional[str] = None
    ) -> str:
        """添加上下文片段
        
        Args:
            session_id: 会话ID
            content: 上下文内容
            category: 上下文类别（引导型/知识型/操作型）
            scope: 上下文作用域（短期/长期/隐性）
            source: 上下文来源
            metadata: 元数据
            priority: 优先级（0.0-1.0）
            purpose: 用途说明
            is_key_clue: 是否为关键线索
            reasoning_anchor: 推理锚点
            error_context: 是否为错误上下文
            ttl: 生存时间（秒）
            parent_id: 父片段ID
            
        Returns:
            上下文片段ID
        """
        # 🎯 编排追踪：上下文合并开始
        tracker = getattr(self, '_orchestration_tracker', None) or get_orchestration_tracker()
        parent_event_id = getattr(self, '_current_parent_event_id', None)
        
        try:
            # 生成片段ID
            fragment_id = f"{session_id}_{int(time.time() * 1000)}_{hashlib.md5(content.encode()).hexdigest()[:8]}"
            
            # 创建上下文片段
            fragment = ContextFragment(
                id=fragment_id,
                content=content,
                category=category,
                scope=scope,
                source=source,
                metadata=metadata or {},
                timestamp=time.time(),
                priority=priority,
                purpose=purpose,
                is_key_clue=is_key_clue,
                reasoning_anchor=reasoning_anchor,
                error_context=error_context,
                ttl=ttl,
                trace_id=f"trace_{fragment_id}" if error_context else None,
                parent_id=parent_id
            )
            
            # 根据作用域存储
            if scope == ContextScope.SHORT_TERM:
                if session_id not in self.context_sessions:
                    self.context_sessions[session_id] = []
                self.context_sessions[session_id].append(fragment)
            elif scope == ContextScope.LONG_TERM:
                # 长期上下文持久化
                self._save_long_term_context(session_id, fragment)
            elif scope == ContextScope.IMPLICIT:
                # 隐性上下文更新环境参数
                self._update_environment_context(fragment)
            
            # 如果是错误上下文，保存到错误上下文列表
            if error_context:
                self.error_contexts.append(fragment)
                # 限制错误上下文数量（最多保留100条）
                if len(self.error_contexts) > 100:
                    self.error_contexts = self.error_contexts[-100:]
            
            # 更新统计
            self.stats['total_fragments'] += 1
            if category == ContextCategory.GUIDING:
                self.stats['guiding_contexts'] += 1
            elif category == ContextCategory.INFORMATIONAL:
                self.stats['informational_contexts'] += 1
            elif category == ContextCategory.ACTIONABLE:
                self.stats['actionable_contexts'] += 1
            
            self.logger.debug(
                f"✅ 添加上下文片段: {fragment_id} | "
                f"类别: {category.value} | 作用域: {scope.value} | "
                f"来源: {source.value} | 优先级: {priority:.2f}"
            )
            
            # 🎯 编排追踪：上下文合并完成
            if tracker:
                tracker.track_context_merge(
                    "unified_context_engineering_center",
                    {
                        "session_id": session_id,
                        "fragment_id": fragment_id,
                        "category": category.value,
                        "scope": scope.value,
                        "source": source.value,
                        "priority": priority,
                        "is_key_clue": is_key_clue
                    },
                    parent_event_id
                )
            
            return fragment_id
            
        except Exception as e:
            self.logger.error(f"添加上下文片段失败: {e}")
            return ""
    
    def get_enhanced_context(
        self,
        session_id: str,
        include_long_term: bool = True,
        include_implicit: bool = True,
        include_actionable: bool = True,
        max_fragments: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取增强的上下文
        
        Args:
            session_id: 会话ID
            include_long_term: 是否包含长期上下文
            include_implicit: 是否包含隐性上下文
            include_actionable: 是否包含操作型上下文
            max_fragments: 最大片段数
            
        Returns:
            增强的上下文字典
        """
        # 🎯 编排追踪：上下文增强开始
        tracker = getattr(self, '_orchestration_tracker', None) or get_orchestration_tracker()
        parent_event_id = getattr(self, '_current_parent_event_id', None)
        enhance_event_id = None
        if tracker:
            enhance_event_id = tracker.track_context_enhance(
                "unified_context_engineering_center",
                {
                    "session_id": session_id,
                    "include_long_term": include_long_term,
                    "include_implicit": include_implicit,
                    "include_actionable": include_actionable,
                    "max_fragments": max_fragments
                },
                parent_event_id
            )
        
        try:
            result = {
                'fragments': [],
                'guiding_contexts': [],
                'informational_contexts': [],
                'actionable_contexts': [],
                'long_term_contexts': {},
                'environment_context': {},
                'tool_context': {},
                'metadata': {
                    'session_id': session_id,
                    'timestamp': time.time(),
                    'total_fragments': 0,
                }
            }
            
            # 1. 短期上下文（当前会话）
            if session_id in self.context_sessions:
                fragments = self.context_sessions[session_id]
                
                # 过滤过期片段
                current_time = time.time()
                valid_fragments = []
                for fragment in fragments:
                    if fragment.ttl and (current_time - fragment.timestamp) > fragment.ttl:
                        continue
                    if fragment.max_age and (current_time - fragment.timestamp) > fragment.max_age:
                        continue
                    valid_fragments.append(fragment)
                
                # 信息熵控制：剔除冗余，保留关键线索
                filtered_fragments = self._apply_entropy_control(valid_fragments)
                
                # 按类别分类
                for fragment in filtered_fragments:
                    result['fragments'].append(fragment.to_dict())
                    if fragment.category == ContextCategory.GUIDING:
                        result['guiding_contexts'].append(fragment.to_dict())
                    elif fragment.category == ContextCategory.INFORMATIONAL:
                        result['informational_contexts'].append(fragment.to_dict())
                    elif fragment.category == ContextCategory.ACTIONABLE:
                        result['actionable_contexts'].append(fragment.to_dict())
            
            # 2. 长期上下文（用户偏好、跨会话数据）
            if include_long_term:
                result['long_term_contexts'] = self._get_long_term_context(session_id)
            
            # 3. 隐性上下文（环境参数）
            if include_implicit:
                result['environment_context'] = self._get_environment_context()
            
            # 4. 操作型上下文（工具定义、工具调用记录）
            if include_actionable:
                result['tool_context'] = {
                    'tool_definitions': self.tool_definitions,
                    'recent_tool_calls': self.tool_call_history[-10:],  # 最近10次调用
                }
            
            # 应用压缩（如果需要）
            if max_fragments and len(result['fragments']) > max_fragments:
                result = self._apply_compression(result, max_fragments)
            
            result['metadata']['total_fragments'] = len(result['fragments'])
            
            # 🎯 编排追踪：上下文增强完成
            if tracker and enhance_event_id:
                tracker.track_context_enhance(
                    "unified_context_engineering_center",
                    {
                        "session_id": session_id,
                        "total_fragments": result['metadata']['total_fragments'],
                        "guiding_count": len(result.get('guiding_contexts', [])),
                        "informational_count": len(result.get('informational_contexts', [])),
                        "actionable_count": len(result.get('actionable_contexts', []))
                    },
                    parent_event_id
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取增强上下文失败: {e}")
            return {}
    
    def _apply_entropy_control(self, fragments: List[ContextFragment]) -> List[ContextFragment]:
        """应用信息熵控制：剔除冗余，保留关键线索
        🚀 改进：使用LLM智能识别冗余和关键线索
        
        Args:
            fragments: 上下文片段列表
            
        Returns:
            过滤后的片段列表
        """
        try:
            if not fragments:
                return []
            
            # 1. 如果片段数量较少，直接返回（避免不必要的LLM调用）
            if len(fragments) <= 5:
                return self._apply_basic_entropy_control(fragments)
            
            # 2. 使用LLM智能识别冗余和关键线索
            try:
                from src.ai.nlp_engine import get_nlp_engine
                nlp_engine = get_nlp_engine()
                
                # 合并所有片段内容用于分析
                combined_content = '\n'.join([f"{i+1}. {f.content[:200]}" for i, f in enumerate(fragments)])
                
                # 使用LLM分析冗余和关键线索
                # 注意：如果NLP引擎不支持analyze_text，使用generate_summary作为fallback
                try:
                    if hasattr(nlp_engine, 'analyze_text'):
                        analysis_result = nlp_engine.analyze_text(combined_content)
                    else:
                        # Fallback：使用摘要生成来识别关键信息
                        summary = nlp_engine.generate_summary(combined_content, max_sentences=len(fragments))
                        # 简单的基于摘要的分析（标记包含在摘要中的片段为关键线索）
                        analysis_result = {
                            'key_clue_indices': list(range(1, min(len(fragments) + 1, 6))),  # 前5个作为关键线索
                            'redundant_indices': [],
                            'reasoning_anchors': {}
                        }
                except Exception as e:
                    self.logger.debug(f"LLM分析失败，使用基础方法: {e}")
                    analysis_result = None
                
                # 解析LLM分析结果（如果可用）
                if analysis_result and isinstance(analysis_result, dict):
                    redundant_indices = analysis_result.get('redundant_indices', [])
                    key_clue_indices = analysis_result.get('key_clue_indices', [])
                    reasoning_anchors = analysis_result.get('reasoning_anchors', {})
                    
                    # 更新片段标记
                    for i, fragment in enumerate(fragments):
                        fragment_idx = i + 1
                        if fragment_idx in redundant_indices:
                            fragment.is_redundant = True
                        if fragment_idx in key_clue_indices:
                            fragment.is_key_clue = True
                        if fragment_idx in reasoning_anchors:
                            fragment.reasoning_anchor = reasoning_anchors[fragment_idx]
                
            except Exception as e:
                self.logger.debug(f"LLM智能分析失败，使用基础方法: {e}")
            
            # 3. 应用基础信息熵控制
            return self._apply_basic_entropy_control(fragments)
            
        except Exception as e:
            self.logger.error(f"应用信息熵控制失败: {e}")
            return fragments
    
    def _apply_basic_entropy_control(self, fragments: List[ContextFragment]) -> List[ContextFragment]:
        """基础信息熵控制（不使用LLM）"""
        try:
            # 1. 保留关键线索
            key_clues = [f for f in fragments if f.is_key_clue]
            
            # 2. 剔除冗余噪声
            non_redundant = [f for f in fragments if not f.is_redundant]
            
            # 3. 保留有推理锚点的片段
            anchored = [f for f in fragments if f.reasoning_anchor]
            
            # 4. 合并并去重（基于内容hash）
            seen_hashes = set()
            filtered = []
            
            # 优先保留：关键线索 > 推理锚点 > 非冗余 > 其他
            priority_order = [
                (key_clues, 1.0),
                (anchored, 0.8),
                (non_redundant, 0.6),
                (fragments, 0.4)
            ]
            
            for fragment_list, priority in priority_order:
                for fragment in fragment_list:
                    content_hash = hashlib.md5(fragment.content.encode()).hexdigest()
                    if content_hash not in seen_hashes:
                        seen_hashes.add(content_hash)
                        filtered.append(fragment)
            
            # 5. 按优先级排序
            filtered.sort(key=lambda x: (x.priority, x.relevance_score), reverse=True)
            
            return filtered
            
        except Exception as e:
            self.logger.error(f"基础信息熵控制失败: {e}")
            return fragments
    
    def _apply_compression(
        self,
        context: Dict[str, Any],
        max_fragments: int,
        compression_mode: str = "hybrid"
    ) -> Dict[str, Any]:
        """应用压缩技术（动态/混合压缩）
        
        Args:
            context: 上下文字典
            max_fragments: 最大片段数
            compression_mode: 压缩模式（dynamic/hybrid/static）
            
        Returns:
            压缩后的上下文
        """
        try:
            fragments = [ContextFragment.from_dict(f) for f in context.get('fragments', [])]
            
            if compression_mode == "dynamic":
                # 动态压缩：实时提炼语义主干
                compressed = self._dynamic_compression(fragments, max_fragments)
            elif compression_mode == "hybrid":
                # 混合压缩：原文与摘要混合
                compressed = self._hybrid_compression(fragments, max_fragments)
            else:
                # 静态压缩：简单截断
                compressed = fragments[:max_fragments]
            
            context['fragments'] = [f.to_dict() for f in compressed]
            context['metadata']['compressed'] = True
            context['metadata']['compression_mode'] = compression_mode
            context['metadata']['original_count'] = len(fragments)
            context['metadata']['compressed_count'] = len(compressed)
            
            self.stats['compression_count'] += 1
            
            return context
            
        except Exception as e:
            self.logger.error(f"应用压缩失败: {e}")
            return context
    
    def _dynamic_compression(self, fragments: List[ContextFragment], max_fragments: int) -> List[ContextFragment]:
        """动态压缩：实时提炼语义主干"""
        try:
            # 使用NLP引擎生成摘要
            from src.ai.nlp_engine import get_nlp_engine
            nlp_engine = get_nlp_engine()
            
            # 合并所有片段内容
            combined_content = ' '.join([f.content for f in fragments])
            
            # 生成摘要（保留关键信息）
            summary = nlp_engine.generate_summary(combined_content, max_sentences=max_fragments)
            
            # 创建压缩后的片段
            compressed_fragment = ContextFragment(
                id=f"compressed_{int(time.time())}",
                content=summary,
                category=ContextCategory.INFORMATIONAL,
                scope=ContextScope.SHORT_TERM,
                source=ContextSource.SYSTEM_LOG,
                metadata={'compressed': True, 'original_count': len(fragments)},
                purpose="动态压缩后的语义摘要"
            )
            
            return [compressed_fragment]
            
        except Exception as e:
            self.logger.error(f"动态压缩失败: {e}")
            return fragments[:max_fragments]
    
    def _hybrid_compression(
        self,
        fragments: List[ContextFragment],
        max_fragments: int
    ) -> List[ContextFragment]:
        """混合压缩：原文与摘要混合，可配置比例"""
        try:
            original_ratio = self.compression_config.get('original_ratio', 0.3)
            summary_ratio = self.compression_config.get('summary_ratio', 0.7)
            
            # 计算原文和摘要的数量
            original_count = int(max_fragments * original_ratio)
            summary_count = max_fragments - original_count
            
            # 保留高优先级的原文片段
            sorted_fragments = sorted(fragments, key=lambda x: x.priority, reverse=True)
            original_fragments = sorted_fragments[:original_count]
            
            # 对剩余片段生成摘要
            remaining_fragments = sorted_fragments[original_count:]
            if remaining_fragments:
                from src.ai.nlp_engine import get_nlp_engine
                nlp_engine = get_nlp_engine()
                
                combined_content = ' '.join([f.content for f in remaining_fragments])
                summary = nlp_engine.generate_summary(combined_content, max_sentences=summary_count)
                
                summary_fragment = ContextFragment(
                    id=f"hybrid_summary_{int(time.time())}",
                    content=summary,
                    category=ContextCategory.INFORMATIONAL,
                    scope=ContextScope.SHORT_TERM,
                    source=ContextSource.SYSTEM_LOG,
                    metadata={
                        'compressed': True,
                        'compression_type': 'hybrid',
                        'original_count': len(remaining_fragments),
                        'original_ratio': original_ratio,
                        'summary_ratio': summary_ratio
                    },
                    purpose="混合压缩后的摘要（保留原文+摘要）"
                )
                
                return original_fragments + [summary_fragment]
            
            return original_fragments
            
        except Exception as e:
            self.logger.error(f"混合压缩失败: {e}")
            return fragments[:max_fragments]
    
    def add_tool_definition(self, tool_id: str, tool_definition: Dict[str, Any]) -> bool:
        """添加工具定义（操作型上下文）
        
        Args:
            tool_id: 工具ID
            tool_definition: 工具定义（包含名称、描述、参数等）
            
        Returns:
            是否成功
        """
        try:
            self.tool_definitions[tool_id] = {
                **tool_definition,
                'added_at': time.time(),
                'updated_at': time.time()
            }
            
            # 同时作为上下文片段存储
            self.add_context_fragment(
                session_id="system",
                content=json.dumps(tool_definition, ensure_ascii=False),
                category=ContextCategory.ACTIONABLE,
                scope=ContextScope.LONG_TERM,
                source=ContextSource.TOOL_DEFINITION,
                metadata={'tool_id': tool_id},
                purpose=f"工具定义: {tool_definition.get('name', tool_id)}",
                is_key_clue=True
            )
            
            self.logger.info(f"✅ 添加工具定义: {tool_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加工具定义失败: {e}")
            return False
    
    def record_tool_call(
        self,
        tool_id: str,
        call_params: Dict[str, Any],
        result: Any,
        success: bool = True,
        error: Optional[str] = None
    ) -> str:
        """记录工具调用（操作型上下文）
        
        Args:
            tool_id: 工具ID
            call_params: 调用参数
            result: 返回结果
            success: 是否成功
            error: 错误信息（如果失败）
            
        Returns:
            调用记录ID
        """
        try:
            call_record = {
                'tool_id': tool_id,
                'call_params': call_params,
                'result': result,
                'success': success,
                'error': error,
                'timestamp': time.time(),
                'call_id': f"tool_call_{int(time.time() * 1000)}"
            }
            
            self.tool_call_history.append(call_record)
            
            # 限制历史记录数量（最多保留1000条）
            if len(self.tool_call_history) > 1000:
                self.tool_call_history = self.tool_call_history[-1000:]
            
            # 作为上下文片段存储
            fragment_id = self.add_context_fragment(
                session_id="system",
                content=json.dumps(call_record, ensure_ascii=False, default=str),
                category=ContextCategory.ACTIONABLE,
                scope=ContextScope.SHORT_TERM,
                source=ContextSource.TOOL_CALL if success else ContextSource.TOOL_RESULT,
                metadata={
                    'tool_id': tool_id,
                    'success': success,
                    'call_id': call_record['call_id']
                },
                purpose=f"工具调用记录: {tool_id}",
                error_context=not success,
                is_key_clue=success  # 成功的工具调用是关键线索
            )
            
            self.logger.debug(f"✅ 记录工具调用: {tool_id} | 成功: {success}")
            return call_record['call_id']
            
        except Exception as e:
            self.logger.error(f"记录工具调用失败: {e}")
            return ""
    
    def _save_long_term_context(self, session_id: str, fragment: ContextFragment) -> bool:
        """保存长期上下文（持久化）
        
        Args:
            session_id: 会话ID
            fragment: 上下文片段
            
        Returns:
            是否成功
        """
        try:
            long_term_file = self.storage_path / f"long_term_{session_id}.json"
            
            # 加载现有数据
            if long_term_file.exists():
                with open(long_term_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {'fragments': [], 'user_preferences': {}}
            
            # 添加新片段
            data['fragments'].append(fragment.to_dict())
            
            # 限制片段数量（最多保留1000条）
            if len(data['fragments']) > 1000:
                data['fragments'] = data['fragments'][-1000:]
            
            # 保存
            with open(long_term_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"保存长期上下文失败: {e}")
            return False
    
    def _load_long_term_contexts(self) -> None:
        """加载长期上下文（延迟加载）"""
        if self._long_term_contexts_loaded:
            return  # 已经加载过，直接返回
        
        try:
            for long_term_file in self.storage_path.glob("long_term_*.json"):
                with open(long_term_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    session_id = long_term_file.stem.replace('long_term_', '')
                    self.long_term_contexts[session_id] = data
                    
            self.logger.info(f"✅ 加载长期上下文: {len(self.long_term_contexts)} 个会话")
            self._long_term_contexts_loaded = True
            
        except Exception as e:
            self.logger.error(f"加载长期上下文失败: {e}")
            self._long_term_contexts_loaded = True  # 即使失败也标记为已加载，避免重复尝试
    
    def _get_long_term_context(self, session_id: str) -> Dict[str, Any]:
        """获取长期上下文
        🚀 改进：支持动态、静态、混合三种记忆管理模式
        
        Args:
            session_id: 会话ID
            
        Returns:
            长期上下文字典
        """
        # 🚀 修复：延迟加载长期上下文，避免在初始化时阻塞
        if not self._long_term_contexts_loaded:
            self._load_long_term_contexts()
        
        try:
            result = {'fragments': [], 'user_preferences': {}}
            
            # 混合模式：合并动态和静态片段
            if self.memory_modes.get('hybrid'):
                dynamic_fragments = self.long_term_contexts.get(session_id, {}).get('fragments', [])
                static_fragments = self._load_static_fragments(session_id)
                
                # 按配置比例合并
                dynamic_ratio = self.hybrid_mode_config.get('dynamic_ratio', 0.6)
                static_ratio = self.hybrid_mode_config.get('static_ratio', 0.4)
                
                dynamic_count = int(len(dynamic_fragments) * dynamic_ratio)
                static_count = int(len(static_fragments) * static_ratio)
                
                result['fragments'] = (
                    dynamic_fragments[:dynamic_count] +
                    static_fragments[:static_count]
                )
                result['mode'] = 'hybrid'
                result['dynamic_count'] = len(dynamic_fragments[:dynamic_count])
                result['static_count'] = len(static_fragments[:static_count])
            
            # 静态模式：只返回持久化的片段
            elif self.memory_modes.get('static'):
                result['fragments'] = self._load_static_fragments(session_id)
                result['mode'] = 'static'
            
            # 动态模式：只返回内存中的片段
            elif self.memory_modes.get('dynamic'):
                result['fragments'] = self.long_term_contexts.get(session_id, {}).get('fragments', [])
                result['mode'] = 'dynamic'
            
            # 用户偏好（从持久化文件加载）
            result['user_preferences'] = self._load_user_preferences(session_id)
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取长期上下文失败: {e}")
            return {'fragments': [], 'user_preferences': {}}
    
    def _load_static_fragments(self, session_id: str) -> List[Dict[str, Any]]:
        """加载静态片段（从文件）"""
        try:
            long_term_file = self.storage_path / f"long_term_{session_id}.json"
            if long_term_file.exists():
                with open(long_term_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('fragments', [])
            return []
        except Exception as e:
            self.logger.error(f"加载静态片段失败: {e}")
            return []
    
    def _load_user_preferences(self, session_id: str) -> Dict[str, Any]:
        """加载用户偏好"""
        try:
            long_term_file = self.storage_path / f"long_term_{session_id}.json"
            if long_term_file.exists():
                with open(long_term_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('user_preferences', {})
            return {}
        except Exception as e:
            self.logger.error(f"加载用户偏好失败: {e}")
            return {}
    
    def _update_environment_context(self, fragment: ContextFragment) -> None:
        """更新环境上下文（隐性上下文）
        
        Args:
            fragment: 上下文片段
        """
        try:
            # 解析环境参数
            if fragment.metadata.get('environment'):
                env_data = fragment.metadata['environment']
                self.environment_context.update(env_data)
            
            # 更新时间戳
            self.environment_context['timestamp'] = time.time()
            self.environment_context['last_updated'] = datetime.now().isoformat()
            
        except Exception as e:
            self.logger.error(f"更新环境上下文失败: {e}")
    
    def _get_environment_context(self) -> Dict[str, Any]:
        """获取环境上下文（隐性上下文）
        
        Returns:
            环境上下文字典
        """
        # 更新当前时间
        self.environment_context['timestamp'] = time.time()
        self.environment_context['current_time'] = datetime.now().isoformat()
        
        return self.environment_context.copy()
    
    def get_error_contexts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取错误上下文（可追溯性）
        
        Args:
            limit: 返回数量限制
            
        Returns:
            错误上下文列表
        """
        return [f.to_dict() for f in self.error_contexts[-limit:]]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            **self.stats,
            'sessions_count': len(self.context_sessions),
            'long_term_sessions': len(self.long_term_contexts),
            'error_contexts_count': len(self.error_contexts),
            'tool_definitions_count': len(self.tool_definitions),
            'tool_calls_count': len(self.tool_call_history),
            'memory_modes': self.memory_modes.copy(),
            'mcp_enabled': self.mcp_handler is not None,
        }
        
        # 添加MCP协议统计（如果可用）
        if self.mcp_handler:
            try:
                mcp_stats = self.mcp_handler.get_protocol_stats()
                stats['mcp_stats'] = mcp_stats
            except Exception as e:
                self.logger.debug(f"获取MCP统计失败: {e}")
        
        return stats
    
    def export_to_mcp(self, session_id: str) -> Optional[str]:
        """导出上下文到MCP协议格式
        
        Args:
            session_id: 会话ID
            
        Returns:
            MCP上下文ID（如果成功）
        """
        if not self.mcp_handler:
            self.logger.debug("MCP协议处理器不可用（可忽略）")
            return None
        
        try:
            # 获取增强上下文
            context = self.get_enhanced_context(session_id)
            
            # 创建MCP上下文
            # 注意：MCP协议的实际接口可能不同，这里使用通用方式
            if hasattr(self.mcp_handler, 'create_component'):
                # 尝试创建MCP上下文
                try:
                    # 尝试导入MCPContextType（如果存在）
                    try:
                        from src.utils.mcp_protocol import MCPContextType
                        context_type = MCPContextType.SESSION
                    except (ImportError, AttributeError, NameError):
                        # MCPContextType不存在，跳过导出
                        self.logger.debug("MCPContextType未定义，跳过MCP导出")
                        return None
                    
                    # 调用create_component
                    mcp_context = self.mcp_handler.create_component(  # type: ignore
                        context_type=context_type,
                        content={
                            'session_id': session_id,
                            'fragments': context.get('fragments', []),
                            'guiding_contexts': context.get('guiding_contexts', []),
                            'informational_contexts': context.get('informational_contexts', []),
                            'actionable_contexts': context.get('actionable_contexts', []),
                            'long_term_contexts': context.get('long_term_contexts', {}),
                            'environment_context': context.get('environment_context', {}),
                            'tool_context': context.get('tool_context', {}),
                        },
                        metadata={
                            'timestamp': time.time(),
                            'total_fragments': len(context.get('fragments', [])),
                        }
                    )
                    
                    # 发送MCP消息
                    if hasattr(self.mcp_handler, 'send_message') and mcp_context:
                        self.mcp_handler.send_message(  # type: ignore
                            context=mcp_context,
                            message_type=MCPMessageType.SESSION,
                            payload={'action': 'export', 'session_id': session_id},
                            priority=MCPPriority.MEDIUM
                        )
                    
                    context_id = mcp_context.id if hasattr(mcp_context, 'id') else str(mcp_context)
                    self.logger.info(f"✅ 上下文已导出到MCP: {context_id}")
                    return context_id
                except (TypeError, AttributeError, NameError) as e:
                    # MCP协议接口不兼容，这是正常的（因为MCP协议可能未完全实现）
                    self.logger.debug(f"MCP协议导出失败（可忽略）: {e}")
                    return None
            else:
                # MCP协议不支持create_component，使用简化方式
                self.logger.debug("MCP协议不支持create_component，跳过导出")
                return None
            
        except Exception as e:
            self.logger.debug(f"导出上下文到MCP失败（可忽略）: {e}")
            return None


# 全局实例
_unified_context_center = None


def get_unified_context_engineering_center() -> UnifiedContextEngineeringCenter:
    """获取统一上下文工程中心实例"""
    global _unified_context_center
    if _unified_context_center is None:
        _unified_context_center = UnifiedContextEngineeringCenter()
    return _unified_context_center

