#!/usr/bin/env python3
"""
知识检索工具
封装知识检索服务，作为Agent的工具使用
"""

import time
import logging
from typing import Dict, Any, Optional

from .base_tool import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class KnowledgeRetrievalTool(BaseTool):
    """知识检索工具 - 封装知识检索服务"""
    
    def __init__(self):
        """初始化知识检索工具"""
        super().__init__(
            tool_name="knowledge_retrieval",
            description="知识检索工具：从知识库中检索相关信息"
        )
        
        # 延迟导入，避免循环依赖
        self._service = None
    
    def _get_service(self):
        """获取知识检索服务（延迟初始化）"""
        if self._service is None:
            try:
                from src.services.knowledge_retrieval_service import KnowledgeRetrievalService
                self._service = KnowledgeRetrievalService()
                self.logger.info("✅ 知识检索服务初始化成功")
            except Exception as e:
                self.logger.error(f"❌ 知识检索服务初始化失败: {e}")
                raise
        return self._service
    
    async def call(self, query: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> ToolResult:
        """
        调用知识检索工具
        
        Args:
            query: 查询文本
            context: 上下文信息（可选）
            **kwargs: 其他参数
            
        Returns:
            ToolResult: 工具执行结果
        """
        start_time = time.time()
        
        try:
            self.module_logger.info(f"🔍 知识检索工具调用: {query[:100]}...")
            
            # 获取服务实例
            service = self._get_service()
            
            # 构建执行上下文
            execution_context = {
                "query": query,
                "type": "knowledge_retrieval"
            }
            if context:
                execution_context.update(context)
            
            # 执行知识检索
            result = await service.execute(execution_context, context)
            
            if not result.success:
                self.module_logger.warning(f"⚠️ 知识检索失败: {result.error}")
                self._record_call(False)
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"知识检索失败: {result.error}",
                    execution_time=time.time() - start_time
                )
            
            # 提取检索结果
            sources = []
            if isinstance(result.data, dict):
                sources = result.data.get('sources', [])
            elif isinstance(result.data, list):
                sources = result.data
            
            # 构建返回结果
            result_data = {
                "sources": sources,
                "query": query,
                "count": len(sources)
            }
            
            execution_time = time.time() - start_time
            self.module_logger.info(f"✅ 知识检索工具执行成功，获取 {len(sources)} 条结果，耗时: {execution_time:.2f}秒")
            self._record_call(True)
            
            return ToolResult(
                success=True,
                data=result_data,
                metadata={
                    "source_count": len(sources),
                    "execution_time": execution_time,
                    "processing_time": getattr(result, 'processing_time', 0.0)
                },
                execution_time=execution_time
            )
            
        except Exception as e:
            self.module_logger.error(f"❌ 知识检索工具执行失败: {e}", exc_info=True)
            self._record_call(False)
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """获取工具参数模式"""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "查询文本，需要从知识库检索的问题或关键词"
                },
                "context": {
                    "type": "object",
                    "description": "上下文信息（可选），可以包含额外的查询参数"
                }
            },
            "required": ["query"]
        }
