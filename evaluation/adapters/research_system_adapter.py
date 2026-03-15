#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
研究系统适配器

将生产系统的研究功能适配为评测系统可用的接口。
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from ..interfaces import ResearchSystemInterface, EvaluationRequest, EvaluationResult

class ResearchSystemAdapter(ResearchSystemInterface):
    """研究系统适配器"""
    
    def __init__(self, research_system=None):
        self.research_system = research_system
        self.logger = logging.getLogger(__name__)
        self._initialize_research_system()
    
    def _initialize_research_system(self):
        """初始化研究系统 - 完全独立，不依赖核心系统"""
        try:
            # 智能质量分析系统应该完全独立，不需要研究系统适配器
            self.logger.info("智能质量分析系统独立运行，无需外部依赖")
            self.research_system = None
            
        except Exception as e:
            self.logger.error(f"研究系统适配器初始化失败: {e}")
            self.research_system = None
    
    async def research(self, request: EvaluationRequest) -> EvaluationResult:
        """执行研究请求"""
        try:
            if self.research_system is None:
                return EvaluationResult(
                    query=request.query,
                    answer="",
                    confidence=0.0,
                    execution_time=0.0,
                    success=False,
                    error="研究系统未初始化"
                )
            
            # 创建研究请求对象
            research_request = self._create_research_request(request)
            
            # 执行研究（同步方法在异步环境中运行）
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    self.research_system.execute_research,
                    research_request
                ),
                timeout=request.timeout
            )
            
            # 转换为评测结果
            return self._convert_to_evaluation_result(request, result)
            
        except asyncio.TimeoutError:
            return EvaluationResult(
                query=request.query,
                answer="",
                confidence=0.0,
                execution_time=request.timeout,
                success=False,
                error="请求超时"
            )
        except Exception as e:
            self.logger.error(f"研究请求执行失败: {e}")
            return EvaluationResult(
                query=request.query,
                answer="",
                confidence=0.0,
                execution_time=0.0,
                success=False,
                error=str(e)
            )
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            if self.research_system is None:
                return {"status": "unavailable", "error": "研究系统未初始化"}
            
            return {
                "status": "available",
                "system_type": type(self.research_system).__name__,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _create_research_request(self, request: EvaluationRequest):
        """创建研究请求对象"""
        try:
            # 尝试使用UnifiedResearchSystem的ResearchRequest
            from src.unified_research_system import ResearchRequest
            return ResearchRequest(
                query=request.query,
                context=request.context or {}
            )
        except ImportError:
            # 回退到UnifiedResearchSystem的ResearchRequest
            from src.unified_research_system import ResearchRequest
            return ResearchRequest(
                query=request.query,
                context=request.context or {}
            )
    
    def _convert_to_evaluation_result(self, request: EvaluationRequest, result) -> EvaluationResult:
        """将研究结果转换为评测结果"""
        try:
            # 处理不同的结果格式
            if hasattr(result, 'result'):
                answer = result.result
                confidence = getattr(result, 'confidence', 0.0)
            elif hasattr(result, 'answer'):
                answer = result.answer
                confidence = getattr(result, 'confidence', 0.0)
            elif isinstance(result, dict):
                answer = result.get('answer', result.get('result', ''))
                confidence = result.get('confidence', 0.0)
            else:
                answer = str(result)
                confidence = 0.0
            
            return EvaluationResult(
                query=request.query,
                answer=answer,
                confidence=confidence,
                execution_time=0.0,  # 将在外部计算
                success=True,
                metadata=request.metadata or {}
            )
            
        except Exception as e:
            self.logger.error(f"结果转换失败: {e}")
            return EvaluationResult(
                query=request.query,
                answer="",
                confidence=0.0,
                execution_time=0.0,
                success=False,
                error=f"结果转换失败: {e}"
            )
