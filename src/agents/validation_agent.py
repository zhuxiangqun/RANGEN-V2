"""
Specialist Validation Agent Implementation
"""
from typing import Dict, Any, Optional, List
import time
import os
import json
import re
from src.interfaces.agent import IAgent, AgentConfig, AgentResult, ExecutionStatus
from src.services.logging_service import get_logger
from src.core.llm_integration import LLMIntegration
from src.prompts.validation.verify import VALIDATION_SYSTEM_PROMPT, VALIDATION_USER_PROMPT

logger = get_logger(__name__)

class ValidationAgent(IAgent):
    """
    Agent responsible for validating claims and answers.
    Cross-checks information against knowledge base or logic rules.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                name="validation_agent",
                description="Validates claims and checks for hallucinations",
                version="1.0.0"
            )
        super().__init__(config)
        
        # Initialize LLM Integration
        llm_config = {
            "llm_provider": os.getenv("LLM_PROVIDER", "deepseek"),
            "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
            "model": os.getenv("VALIDATION_MODEL", "deepseek-chat"),
            "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        }
        self.llm = LLMIntegration(llm_config)
        
        logger.info(f"ValidationAgent initialized: {self.config.name}")

    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """Validate input requirements"""
        if "claim" not in inputs and "answer" not in inputs:
            logger.error("Input validation failed: 'claim' or 'answer' is required")
            return False
        return True

    async def execute(self, inputs: Dict[str, Any], context: Optional[Dict] = None) -> AgentResult:
        """
        Execute validation logic.
        """
        start_time = time.time()
        
        try:
            # 1. Validation
            if not self.validate_inputs(inputs):
                return AgentResult(
                    agent_name=self.config.name,
                    status=ExecutionStatus.FAILED,
                    output=None,
                    execution_time=0.0,
                    error="Invalid input"
                )

            target = inputs.get("claim") or inputs.get("answer")
            evidence = inputs.get("evidence", [])
            evidence_str = "\n".join([f"- {e}" for e in evidence]) if evidence else "No explicit evidence provided. Use general knowledge."
            
            # 2. Call LLM
            prompt = f"{VALIDATION_SYSTEM_PROMPT}\n\n{VALIDATION_USER_PROMPT.format(claim=target, evidence=evidence_str)}"
            
            logger.info(f"Validating: {target[:50]}...")
            response = self.llm._call_llm(prompt)
            
            # 3. Parse Response
            result = {
                "is_valid": False,
                "confidence": 0.0,
                "reasoning": "Failed to parse validation result",
                "status": "error"
            }
            
            if response:
                # Try to extract JSON
                json_match = re.search(r"\{.*\}", response, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group(0))
                    except json.JSONDecodeError:
                        logger.warning("Validation response JSON decode failed")
                        result["reasoning"] = response # Fallback
                else:
                    result["reasoning"] = response

            execution_time = time.time() - start_time
            
            return AgentResult(
                agent_name=self.config.name,
                status=ExecutionStatus.COMPLETED,
                output=result,
                execution_time=execution_time,
                metadata={"evidence_count": len(evidence)}
            )
            
        except Exception as e:
            logger.error(f"ValidationAgent execution failed: {e}")
            return AgentResult(
                agent_name=self.config.name,
                status=ExecutionStatus.FAILED,
                output=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
