#!/usr/bin/env python3
"""
RAG工具
封装RAG Agent，作为Agent的工具使用
架构优化：RAGTool -> RAGExpert (直接调用，移除RAGAgentWrapper层)
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List

from .base_tool import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class RAGTool(BaseTool):
    """RAG工具 - 封装RAG Agent，作为Agent的工具使用
    
    架构（优化后）：
    ReAct Agent
        └─ RAGTool (工具包装器)
            └─ RAGExpert (直接调用，移除RAGAgentWrapper层)
                ├─ Knowledge Retrieval (知识检索)
                └─ Answer Generation (答案生成)
    
    优化说明：
    - ✅ 移除RAGAgentWrapper层，减少包装层次（从4层减少到2-3层）
    - ✅ 直接使用RAGExpert，架构更简洁
    - ✅ 保持向后兼容，支持配置开关
    """
    
    def __init__(self):
        """初始化RAG工具"""
        super().__init__(
            tool_name="rag",
            description="检索增强生成工具：从知识库检索相关信息，然后使用LLM生成答案"
        )
        
        # 🚀 架构优化：直接使用RAGExpert，移除RAGAgentWrapper层
        # RAGExpert是8个核心Agent之一，可以直接使用
        self._rag_agent = None
    
    def _get_rag_agent(self):
        """获取RAG Agent（延迟初始化）

        优化：直接使用RAGExpert，移除RAGAgentWrapper层
        - 如果环境变量USE_NEW_AGENTS=true，使用RAGExpert（新Agent）
        - 否则，使用RAGAgent（向后兼容，RAGAgent是RAGExpert的别名）
        - 支持轻量级模式：USE_LIGHTWEIGHT_RAG=true时跳过复杂初始化
        """
        if self._rag_agent is None:
            try:
                # 延迟导入以避免循环导入问题
                from ..rag_agent import RAGExpert, RAGAgent

                # 检查配置：优先使用RAGExpert（新Agent）
                # 可以通过环境变量USE_NEW_AGENTS控制，默认为True（使用新Agent）
                use_new_agent = os.getenv('USE_NEW_AGENTS', 'true').lower() == 'true'
                use_lightweight = os.getenv('USE_LIGHTWEIGHT_RAG', 'false').lower() == 'true'

                if use_new_agent:
                    # 🚀 让RAGExpert自己决定是否使用轻量级模式
                    self._rag_agent = RAGExpert()

                    # 检查RAGExpert是否处于轻量级模式
                    if getattr(self._rag_agent, '_lightweight_mode', False):
                        self.module_logger.info("🔧 RAGExpert处于轻量级模式（由环境变量USE_LIGHTWEIGHT_RAG控制）")
                    else:
                        self.module_logger.info("✅ RAG Agent初始化成功（使用RAGExpert，完整模式）")
                else:
                    # 向后兼容：使用RAGAgent（RAGAgent是RAGExpert的别名）
                    self._rag_agent = RAGAgent()
                    self.module_logger.info("✅ RAG Agent初始化成功（使用RAGAgent，向后兼容）")

            except Exception as e:
                self.module_logger.error(f"❌ RAG Agent初始化失败: {e}", exc_info=True)
                raise
        return self._rag_agent
    
    async def call(self, query: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> ToolResult:
        """
        调用RAG工具 - 内部调用RAGAgent
        
        Args:
            query: 查询文本
            context: 上下文信息（可选）
            **kwargs: 其他参数
            
        Returns:
            ToolResult: 工具执行结果
        """
        start_time = time.time()
        
        try:
            self.module_logger.info(f"🔍 RAG工具调用: {query[:100]}...")
            
            # 🚀 架构优化：直接调用RAGExpert，移除RAGAgentWrapper层
            # RAGExpert是8个核心Agent之一，可以直接使用
            rag_agent = self._get_rag_agent()
            
            # 准备上下文
            agent_context = {
                "query": query,
                "type": "rag"
            }
            if context:
                agent_context.update(context)
            agent_context.update(kwargs)
            
            # 直接调用RAGExpert（或RAGAgent，向后兼容）
            agent_result = await rag_agent.execute(agent_context)
            
            # 处理AgentResult对象格式（RAGExpert直接返回AgentResult）
            if isinstance(agent_result, dict):
                # 如果是字典格式（向后兼容）
                success = agent_result.get("success", False)
                error = agent_result.get("error")
                data_info = agent_result.get("data", {})
                confidence = agent_result.get("confidence", 0.0)
            else:
                # AgentResult对象格式（RAGExpert的标准返回格式）
                success = agent_result.success
                error = agent_result.error
                data_info = agent_result.data
                confidence = getattr(agent_result, 'confidence', 0.0)
            
            if not success:
                # 记录失败的详细原因，便于快速定位（不改变返回逻辑）
                if isinstance(data_info, dict):
                    data_info_preview = {k: (str(v)[:200] if not isinstance(v, (dict, list)) else f"{type(v).__name__}(len={len(v)})") for k, v in list(data_info.items())[:5]}
                else:
                    data_info_preview = str(data_info)[:200]
                self.module_logger.warning(
                    f"⚠️ RAG Agent执行失败: error={error}, "
                    f"data_preview={data_info_preview}, "
                    f"confidence={confidence}"
                )
                self._record_call(False)
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"RAG Agent执行失败: {error}",
                    execution_time=time.time() - start_time
                )
            
            # 提取结果数据
            result_data = data_info if isinstance(data_info, dict) else {}
            
            execution_time = time.time() - start_time
            self.module_logger.info(f"✅ RAG工具执行成功，耗时: {execution_time:.2f}秒")
            self._record_call(True)
            
            return ToolResult(
                success=True,
                data=result_data,
                metadata={
                    "evidence_count": result_data.get("evidence", []).__len__() if isinstance(result_data.get("evidence"), list) else 0,
                    "execution_time": execution_time,
                    "confidence": confidence
                },
                execution_time=execution_time
            )
            
        except Exception as e:
            self.module_logger.error(f"❌ RAG工具执行失败: {e}", exc_info=True)
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
                    "description": "查询文本，需要检索和生成答案的问题"
                },
                "context": {
                    "type": "object",
                    "description": "上下文信息（可选），可以包含额外的查询参数"
                }
            },
            "required": ["query"]
        }

