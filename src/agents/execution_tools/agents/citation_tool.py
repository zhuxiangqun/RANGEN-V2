#!/usr/bin/env python3
"""
引用工具
封装引用服务，作为Agent的工具使用
"""

import time
import logging
from typing import Dict, Any, Optional, List

from .base_tool import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class CitationTool(BaseTool):
    """引用工具 - 封装引用服务"""
    
    def __init__(self):
        """初始化引用工具"""
        super().__init__(
            tool_name="citation",
            description="引用工具：为答案生成引用和参考文献"
        )
        
        # 延迟导入，避免循环依赖
        self._service = None
    
    def _get_service(self):
        """获取引用服务（延迟初始化）"""
        if self._service is None:
            try:
                from src.services.citation_service import CitationService
                self._service = CitationService()
                self.logger.info("✅ 引用服务初始化成功")
            except Exception as e:
                self.logger.error(f"❌ 引用服务初始化失败: {e}")
                raise
        return self._service
    
    async def call(self, content: str, sources: Optional[List[Dict[str, Any]]] = None, context: Optional[Dict[str, Any]] = None, **kwargs) -> ToolResult:
        """
        调用引用工具
        
        Args:
            content: 需要生成引用的内容
            sources: 来源列表（可选）
            context: 上下文信息（可选）
            **kwargs: 其他参数
            
        Returns:
            ToolResult: 工具执行结果
        """
        start_time = time.time()
        
        try:
            self.module_logger.info(f"🔍 引用工具调用: {content[:100]}...")
            
            # 获取服务实例
            service = self._get_service()
            
            # 构建执行上下文
            execution_context = {
                "content": content,
                "type": "citation"
            }
            
            # 添加来源
            if sources:
                execution_context["sources"] = sources
            
            # 合并context中的其他信息
            if context:
                execution_context.update(context)
            
            # 执行引用生成
            result = service.execute(execution_context)
            
            if not result.success:
                self.module_logger.warning(f"⚠️ 引用生成失败: {result.error}")
                self._record_call(False)
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"引用生成失败: {result.error}",
                    execution_time=time.time() - start_time
                )
            
            # 提取引用结果
            citations = []
            if isinstance(result.data, dict):
                citations = result.data.get('citations', []) or result.data.get('references', [])
            elif isinstance(result.data, list):
                citations = result.data
            elif hasattr(result, 'citations'):
                citations = result.citations
            
            # 构建返回结果
            result_data = {
                "citations": citations,
                "content": content,
                "count": len(citations)
            }
            
            execution_time = time.time() - start_time
            self.module_logger.info(f"✅ 引用工具执行成功，生成 {len(citations)} 条引用，耗时: {execution_time:.2f}秒")
            self._record_call(True)
            
            return ToolResult(
                success=True,
                data=result_data,
                metadata={
                    "citation_count": len(citations),
                    "execution_time": execution_time,
                    "processing_time": getattr(result, 'processing_time', 0.0)
                },
                execution_time=execution_time
            )
            
        except Exception as e:
            self.module_logger.error(f"❌ 引用工具执行失败: {e}", exc_info=True)
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
                "content": {
                    "type": "string",
                    "description": "需要生成引用的内容"
                },
                "sources": {
                    "type": "array",
                    "description": "来源列表（可选），知识检索或推理步骤的来源"
                },
                "context": {
                    "type": "object",
                    "description": "上下文信息（可选），可以包含额外的参数"
                }
            },
            "required": ["content"]
        }
