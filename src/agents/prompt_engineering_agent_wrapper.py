#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PromptEngineeringAgentWrapper - Wrapper for adapter compatibility
"""

import time
import logging
from typing import Dict, Any, Optional

from src.adapters.prompt_engineering_agent_adapter import PromptEngineeringAgentAdapter
from src.agents.base_agent import AgentResult

logger = logging.getLogger(__name__)

class PromptEngineeringAgentWrapper:
    """
    Wrapper for PromptEngineeringAgentAdapter to maintain compatibility
    with code expecting PromptEngineeringAgentWrapper.
    """
    
    def __init__(self, enable_gradual_replacement: bool = True):
        self.adapter = PromptEngineeringAgentAdapter()
        self.enable_gradual_replacement = enable_gradual_replacement
        logger.info(f"PromptEngineeringAgentWrapper initialized (gradual_replacement={enable_gradual_replacement})")
        
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """Execute the prompt engineering task via adapter"""
        start_time = time.time()
        try:
            # The adapter returns a dict with success, data, confidence, error keys
            # based on adapt_result method in PromptEngineeringAgentAdapter
            result_dict = await self.adapter.execute_adapted(context)
            
            # Ensure processing_time exists
            processing_time = result_dict.get('processing_time')
            if processing_time is None:
                processing_time = time.time() - start_time
            
            # Convert dict to AgentResult object
            return AgentResult(
                success=result_dict.get('success', False),
                data=result_dict.get('data'),
                confidence=result_dict.get('confidence', 0.0),
                processing_time=processing_time,
                metadata=result_dict.get('metadata'),
                error=result_dict.get('error')
            )
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return AgentResult(
                success=False,
                data=None,
                confidence=0.0,
                processing_time=time.time() - start_time,
                error=str(e)
            )

    async def record_prompt_performance(
        self,
        prompt_type: str,
        template_name: str,
        query: str,
        answer_quality: float,
        response_time: float,
        cost: Optional[float] = None
    ):
        """Record performance metrics (placeholder/logging)"""
        # Since adapter delegates to ToolOrchestrator which might not have direct
        # performance recording for prompts exposed this way, we'll just log it for now.
        # This prevents the AttributeError when UnifiedPromptManager calls it.
        logger.info(f"Recording prompt performance: {prompt_type}/{template_name} - Quality: {answer_quality:.2f}")
