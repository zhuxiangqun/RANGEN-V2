#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Context Engineering Agent Wrapper

⚠️ DEPRECATED: 此模块已不再维护。
请使用 src.services.context_optimization_service 代替。
"""

import warnings
warnings.warn(
    "ContextEngineeringAgentWrapper is deprecated. Use src.services.context_optimization_service instead.",
    DeprecationWarning,
    stacklevel=2
)

import time
# -*- coding: utf-8 -*-

import time
import logging
from typing import Dict, Any, Optional

from src.adapters.context_engineering_agent_adapter import ContextEngineeringAgentAdapter
from src.agents.base_agent import AgentResult

logger = logging.getLogger(__name__)


class ContextEngineeringAgentWrapper:
    def __init__(self, enable_gradual_replacement: bool = True):
        self.adapter = ContextEngineeringAgentAdapter()
        self.enable_gradual_replacement = enable_gradual_replacement
        logger.info(f"ContextEngineeringAgentWrapper initialized (gradual_replacement={enable_gradual_replacement})")

    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        start_time = time.time()
        try:
            result_dict = await self.adapter.execute_adapted(context)
            processing_time = result_dict.get("processing_time")
            if processing_time is None:
                processing_time = time.time() - start_time

            return AgentResult(
                success=result_dict.get("success", False),
                data=result_dict.get("data"),
                confidence=result_dict.get("confidence", 0.0),
                processing_time=processing_time,
                metadata=result_dict.get("metadata"),
                error=result_dict.get("error"),
            )
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return AgentResult(
                success=False,
                data=None,
                confidence=0.0,
                processing_time=time.time() - start_time,
                error=str(e),
            )

