#!/usr/bin/env python3
"""
答案生成工具
封装答案生成服务，作为Agent的工具使用
"""

import time
import logging
from typing import Dict, Any, Optional

from .base_tool import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class AnswerGenerationTool(BaseTool):
    """答案生成工具 - 封装答案生成服务"""
    
    def __init__(self):
        """初始化答案生成工具"""
        super().__init__(
            tool_name="answer_generation",
            description="答案生成工具：基于知识数据和推理结果生成结构化答案"
        )
        
        # 延迟导入，避免循环依赖
        self._service = None
    
    def _get_service(self):
        """获取答案生成服务（延迟初始化）"""
        if self._service is None:
            try:
                from src.services.answer_generation_service import AnswerGenerationService
                self._service = AnswerGenerationService()
                self.logger.info("✅ 答案生成服务初始化成功")
            except Exception as e:
                self.logger.error(f"❌ 答案生成服务初始化失败: {e}")
                raise
        return self._service
    
    async def call(self, query: str, knowledge_data: Optional[list] = None, reasoning_data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None, **kwargs) -> ToolResult:
        """
        调用答案生成工具
        
        Args:
            query: 查询文本
            knowledge_data: 知识数据（可选）
            reasoning_data: 推理数据（可选）
            context: 上下文信息（可选）
            **kwargs: 其他参数
            
        Returns:
            ToolResult: 工具执行结果
        """
        start_time = time.time()
        
        try:
            self.module_logger.info(f"🔍 答案生成工具调用: {query[:100]}...")
            if knowledge_data:
                self.module_logger.info(f"🔍 [AnswerGenerationTool] 接收到 knowledge_data, 长度: {len(knowledge_data)}")
            else:
                self.module_logger.info(f"🔍 [AnswerGenerationTool] 未接收到 knowledge_data 或为空")
            
            # 获取服务实例
            service = self._get_service()
            
            # 构建执行上下文
            execution_context = {
                "query": query,
                "type": "answer_generation"
            }
            
            # 添加知识数据和推理数据
            if knowledge_data:
                execution_context["knowledge_data"] = knowledge_data
            if reasoning_data:
                execution_context["reasoning_data"] = reasoning_data
            
            # 🚀 P0修复：优先从context中提取dependencies，确保依赖传递正确
            # 合并context中的其他信息
            if context:
                # 🚀 P0修复：如果context中包含dependencies，确保它被正确传递
                if "dependencies" in context:
                    execution_context["dependencies"] = context["dependencies"]
                    self.module_logger.info(f"🔍 [AnswerGenerationTool] 从context中提取dependencies: keys={list(context['dependencies'].keys()) if context.get('dependencies') else 'empty'}")
                
                # 合并context中的其他信息（但dependencies已经单独处理，避免覆盖）
                context_copy = {k: v for k, v in context.items() if k != "dependencies"}
                execution_context.update(context_copy)
            
            # 🚀 P0修复：也检查kwargs中是否有dependencies（向后兼容）
            if "dependencies" in kwargs:
                execution_context["dependencies"] = kwargs["dependencies"]
                self.module_logger.info(f"🔍 [AnswerGenerationTool] 从kwargs中提取dependencies: keys={list(kwargs['dependencies'].keys()) if kwargs.get('dependencies') else 'empty'}")
            
            # 执行答案生成
            result = await service.execute(execution_context)
            
            if not result.success:
                self.module_logger.warning(f"⚠️ 答案生成失败: {result.error}")
                self._record_call(False)
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"答案生成失败: {result.error}",
                    execution_time=time.time() - start_time
                )
            
            # 提取答案
            answer = None
            if isinstance(result.data, dict):
                answer = result.data.get('answer') or result.data.get('final_answer')
            elif isinstance(result.data, str):
                answer = result.data
            elif hasattr(result, 'answer'):
                answer = result.answer
            
            # 构建返回结果
            result_data = {
                "answer": answer,
                "query": query
            }
            
            execution_time = time.time() - start_time
            self.module_logger.info(f"✅ 答案生成工具执行成功，答案: {answer[:100] if answer else 'None'}，耗时: {execution_time:.2f}秒")
            self._record_call(True)
            
            return ToolResult(
                success=True,
                data=result_data,
                metadata={
                    "execution_time": execution_time,
                    "processing_time": getattr(result, 'processing_time', 0.0)
                },
                execution_time=execution_time
            )
            
        except Exception as e:
            self.module_logger.error(f"❌ 答案生成工具执行失败: {e}", exc_info=True)
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
                    "description": "查询文本，需要生成答案的问题"
                },
                "knowledge_data": {
                    "type": "array",
                    "description": "知识数据（可选），从知识检索获取的数据"
                },
                "reasoning_data": {
                    "type": "object",
                    "description": "推理数据（可选），从推理工具获取的推理结果"
                },
                "context": {
                    "type": "object",
                    "description": "上下文信息（可选），可以包含额外的参数"
                }
            },
            "required": ["query"]
        }
