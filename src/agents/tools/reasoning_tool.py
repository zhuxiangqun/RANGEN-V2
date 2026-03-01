#!/usr/bin/env python3
"""
推理工具
封装推理服务，作为Agent的工具使用
"""

import time
import logging
from typing import Dict, Any, Optional

from .base_tool import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class ReasoningTool(BaseTool):
    """推理工具 - 封装推理服务"""
    
    def __init__(self):
        """初始化推理工具"""
        super().__init__(
            tool_name="reasoning",
            description="推理工具：对查询进行多步骤推理，生成推理链和答案"
        )
        
        # 延迟导入，避免循环依赖
        self._service = None
    
    def _get_service(self):
        """获取推理服务（延迟初始化）"""
        if self._service is None:
            try:
                from src.services.reasoning_service import ReasoningService
                self._service = ReasoningService()
                self.logger.info("✅ 推理服务初始化成功")
            except Exception as e:
                self.logger.error(f"❌ 推理服务初始化失败: {e}")
                raise
        return self._service
    
    async def call(self, query: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> ToolResult:
        """
        调用推理工具
        
        Args:
            query: 查询文本
            context: 上下文信息（可选），应包含knowledge_data或evidence
            **kwargs: 其他参数
            
        Returns:
            ToolResult: 工具执行结果
        """
        start_time = time.time()
        
        try:
            self.module_logger.info(f"🔍 推理工具调用: {query[:100]}...")
            
            # 获取服务实例
            service = self._get_service()
            
            # 构建执行上下文
            execution_context = {
                "query": query,
                "type": "reasoning"
            }
            if context:
                execution_context.update(context)
            
            # 执行推理 (service.execute is synchronous)
            # Use asyncio.to_thread to avoid blocking the event loop
            import asyncio
            if asyncio.iscoroutinefunction(service.execute):
                result = await service.execute(execution_context)
            else:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: service.execute(execution_context))
            
            if not result.success:
                self.module_logger.warning(f"⚠️ 推理失败: {result.error}")
                self._record_call(False)
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"推理失败: {result.error}",
                    execution_time=time.time() - start_time
                )
            
            # 提取推理结果
            final_answer = None
            reasoning_steps = []
            confidence = 0.0
            
            if isinstance(result.data, dict):
                final_answer = result.data.get('final_answer') or result.data.get('answer')
                reasoning_steps = result.data.get('reasoning_steps', [])
                confidence = result.data.get('confidence', 0.0) or result.data.get('total_confidence', 0.0)
            elif hasattr(result, 'final_answer'):
                final_answer = result.final_answer
                reasoning_steps = getattr(result, 'reasoning_steps', [])
                confidence = getattr(result, 'total_confidence', 0.0)
            
            # 构建返回结果
            result_data = {
                "final_answer": final_answer,
                "reasoning_steps": reasoning_steps,
                "confidence": confidence,
                "query": query
            }
            
            execution_time = time.time() - start_time
            self.module_logger.info(f"✅ 推理工具执行成功，答案: {final_answer[:100] if final_answer else 'None'}，耗时: {execution_time:.2f}秒")
            self._record_call(True)
            
            return ToolResult(
                success=True,
                data=result_data,
                metadata={
                    "reasoning_steps_count": len(reasoning_steps),
                    "confidence": confidence,
                    "execution_time": execution_time,
                    "processing_time": getattr(result, 'processing_time', 0.0)
                },
                execution_time=execution_time
            )
            
        except Exception as e:
            self.module_logger.error(f"❌ 推理工具执行失败: {e}", exc_info=True)
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
                    "description": "查询文本，需要进行推理的问题"
                },
                "context": {
                    "type": "object",
                    "description": "上下文信息（可选），应包含knowledge_data或evidence用于推理"
                }
            },
            "required": ["query"]
        }
