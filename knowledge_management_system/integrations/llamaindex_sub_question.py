#!/usr/bin/env python3
"""
LlamaIndex 子问题分解器
将复杂查询分解为子问题
"""

from typing import List, Dict, Any, Optional
from ..utils.logger import get_logger

logger = get_logger()

# 尝试导入 LlamaIndex（可选依赖）
try:
    from llama_index.core.query_engine import SubQuestionQueryEngine
    from llama_index.core.tools import QueryEngineTool
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False
    logger.warning("LlamaIndex 未安装，子问题分解功能将不可用。如需使用，请运行: pip install llamaindex")


class SubQuestionDecomposer:
    """将复杂查询分解为子问题"""
    
    def __init__(self, query_engines: Optional[List[Any]] = None):
        """
        初始化子问题分解器
        
        Args:
            query_engines: 查询引擎列表（用于子问题查询）
        """
        self.enabled = LLAMAINDEX_AVAILABLE
        self.logger = logger
        self.query_engines = query_engines or []
        
        if self.enabled:
            self._init_decomposer()
        else:
            self.sub_question_engine = None
    
    def _init_decomposer(self):
        """初始化子问题分解器"""
        try:
            if not self.query_engines:
                self.logger.warning("未提供查询引擎，子问题分解器将使用降级模式")
                self.sub_question_engine = None
                return
            
            # 创建查询引擎工具列表
            tools = []
            for idx, engine in enumerate(self.query_engines):
                tool = QueryEngineTool.from_defaults(
                    query_engine=engine,
                    name=f"query_engine_{idx}",
                    description=f"查询引擎 {idx}"
                )
                tools.append(tool)
            
            # 创建子问题查询引擎
            self.sub_question_engine = SubQuestionQueryEngine.from_defaults(
                query_engine_tools=tools
            )
            
            self.logger.info(f"✅ 子问题分解器初始化成功，包含 {len(tools)} 个查询引擎")
            
        except Exception as e:
            self.logger.error(f"子问题分解器初始化失败: {e}")
            self.enabled = False
            self.sub_question_engine = None
    
    def decompose(self, query: str) -> Dict[str, Any]:
        """
        分解查询为子问题
        
        Args:
            query: 原始查询
        
        Returns:
            包含子问题和结果的字典
        """
        if not self.enabled or self.sub_question_engine is None:
            self.logger.warning("子问题分解器未启用，返回原始查询")
            return {
                'sub_questions': [query],
                'results': [],
                'error': '子问题分解器未启用'
            }
        
        try:
            # 执行子问题查询
            response = self.sub_question_engine.query(query)
            
            # 提取子问题和结果
            sub_questions = []
            results = []
            
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    if hasattr(node, 'node'):
                        results.append({
                            'text': str(node.node.text) if hasattr(node.node, 'text') else '',
                            'score': getattr(node, 'score', 0.0),
                            'metadata': getattr(node.node, 'metadata', {})
                        })
            
            # 尝试从响应中提取子问题
            # 注意：LlamaIndex 的子问题查询引擎会自动处理子问题分解
            # 这里我们返回最终结果和中间步骤（如果有）
            
            return {
                'response': str(response),
                'sub_questions': sub_questions,  # 如果LlamaIndex提供子问题列表，可以在这里提取
                'results': results,
                'metadata': getattr(response, 'metadata', {})
            }
            
        except Exception as e:
            self.logger.error(f"子问题分解失败: {e}")
            return {
                'sub_questions': [query],
                'results': [],
                'error': str(e)
            }

