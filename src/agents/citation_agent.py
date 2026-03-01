"""
Specialist Citation Agent Implementation
"""
from typing import Dict, Any, Optional, List
import time
import os
import json
import re
from src.interfaces.agent import IAgent, AgentConfig, AgentResult, ExecutionStatus
from src.services.logging_service import get_logger
from src.core.llm_integration import LLMIntegration
from src.prompts.citation.cite import CITATION_SYSTEM_PROMPT, CITATION_USER_PROMPT

logger = get_logger(__name__)

class CitationAgent(IAgent):
    """
    Agent responsible for adding citations to generated content.
    Matches text segments with source documents.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                name="citation_agent",
                description="Adds academic/reference citations to text",
                version="1.0.0"
            )
        super().__init__(config)
        
        # Initialize LLM Integration
        llm_config = {
            "llm_provider": os.getenv("LLM_PROVIDER", "deepseek"),
            "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
            "model": os.getenv("CITATION_MODEL", "deepseek-chat"),
            "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        }
        self.llm = LLMIntegration(llm_config)
        
        logger.info(f"CitationAgent initialized: {self.config.name}")

    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """Validate input requirements"""
        if "text" not in inputs or "sources" not in inputs:
            logger.error("Input validation failed: 'text' and 'sources' are required")
            return False
        return True

    async def execute(self, inputs: Dict[str, Any], context: Optional[Dict] = None) -> AgentResult:
        """
        Execute citation logic.
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

            text = inputs["text"]
            sources = inputs["sources"]
            
            # Format sources for prompt
            sources_str = ""
            for i, src in enumerate(sources):
                # Handle dict or string sources
                content = src.get("content", str(src)) if isinstance(src, dict) else str(src)
                src_id = src.get("id", i+1) if isinstance(src, dict) else i+1
                sources_str += f"[{src_id}] {content[:300]}...\n" # Truncate for prompt context window
            
            # 2. Call LLM
            prompt = f"{CITATION_SYSTEM_PROMPT}\n\n{CITATION_USER_PROMPT.format(text=text, sources=sources_str)}"
            
            logger.info(f"Generating citations for text length {len(text)} with {len(sources)} sources")
            response = self.llm._call_llm(prompt)
            
            # 3. Parse Response
            result = {
                "cited_text": text,
                "references": []
            }
            
            if response:
                json_match = re.search(r"\{.*\}", response, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group(0))
                    except json.JSONDecodeError:
                        logger.warning("Citation response JSON decode failed")
                        # Fallback: assume response is cited text if not JSON
                        result["cited_text"] = response
                else:
                    # Fallback: assume response is cited text if not JSON
                    result["cited_text"] = response

            execution_time = time.time() - start_time
            
            return AgentResult(
                agent_name=self.config.name,
                status=ExecutionStatus.COMPLETED,
                output=result,
                execution_time=execution_time,
                metadata={"source_count": len(sources)}
            )
            
        except Exception as e:
            logger.error(f"CitationAgent execution failed: {e}")
            return AgentResult(
                agent_name=self.config.name,
                status=ExecutionStatus.FAILED,
                output=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
