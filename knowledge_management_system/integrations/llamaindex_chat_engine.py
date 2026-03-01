#!/usr/bin/env python3
"""
LlamaIndex 聊天引擎
支持多轮对话和上下文记忆
"""

from typing import List, Dict, Any, Optional
from ..utils.logger import get_logger

logger = get_logger()

# 尝试导入 LlamaIndex（可选依赖）
try:
    from llama_index.core.chat_engine import SimpleChatEngine, ContextChatEngine
    from llama_index.core.memory import ChatMemoryBuffer
    from llama_index.core.query_engine import RetrieverQueryEngine
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False
    logger.warning("LlamaIndex 未安装，聊天引擎功能将不可用。如需使用，请运行: pip install llamaindex")


class LlamaIndexChatEngine:
    """多轮对话引擎"""
    
    def __init__(self, query_engine: Optional[Any] = None):
        """
        初始化聊天引擎
        
        Args:
            query_engine: 查询引擎（如果提供，将使用上下文聊天引擎；否则使用简单聊天引擎）
        """
        self.enabled = LLAMAINDEX_AVAILABLE
        self.logger = logger
        self.query_engine = query_engine
        
        if self.enabled:
            self._init_chat_engine()
        else:
            self.chat_engine = None
    
    def _init_chat_engine(self):
        """初始化聊天引擎"""
        try:
            if self.query_engine:
                # 使用上下文聊天引擎（基于检索的上下文）
                memory = ChatMemoryBuffer.from_defaults(token_limit=3000)
                self.chat_engine = ContextChatEngine.from_defaults(
                    retriever=self.query_engine.retriever if hasattr(self.query_engine, 'retriever') else None,
                    memory=memory
                )
                self.logger.info("✅ 上下文聊天引擎初始化成功")
            else:
                # 使用简单聊天引擎（无检索上下文）
                self.chat_engine = SimpleChatEngine.from_defaults()
                self.logger.info("✅ 简单聊天引擎初始化成功")
        except Exception as e:
            self.logger.error(f"聊天引擎初始化失败: {e}")
            self.enabled = False
            self.chat_engine = None
    
    def chat(
        self, 
        query: str, 
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        支持上下文的对话查询
        
        Args:
            query: 当前查询
            conversation_history: 对话历史（格式：[{"role": "user", "content": "..."}, ...]）
        
        Returns:
            包含回答和元数据的字典
        """
        if not self.enabled or self.chat_engine is None:
            self.logger.warning("聊天引擎未启用，无法进行对话")
            return {
                'response': '',
                'error': '聊天引擎未启用'
            }
        
        try:
            # 如果有对话历史，可以手动设置到内存中
            # 注意：LlamaIndex 的聊天引擎会自动管理对话历史
            
            # 执行查询
            response = self.chat_engine.chat(query)
            
            return {
                'response': str(response),
                'source_nodes': getattr(response, 'source_nodes', []),
                'metadata': getattr(response, 'metadata', {})
            }
            
        except Exception as e:
            self.logger.error(f"对话查询失败: {e}")
            return {
                'response': '',
                'error': str(e)
            }
    
    def reset(self):
        """重置对话历史"""
        if self.chat_engine and hasattr(self.chat_engine, 'reset'):
            self.chat_engine.reset()
            self.logger.info("✅ 对话历史已重置")

