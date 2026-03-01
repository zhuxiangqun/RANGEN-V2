from typing import List, Dict, Any, Optional
import json
import re
import logging
import asyncio

logger = logging.getLogger(__name__)

class RetrievalQualityAssessor:
    """
    Retrieval Quality Assessor (P1 Phase)
    
    Uses LLM to evaluate the quality of retrieved evidence based on:
    1. Relevance: Does it address the query?
    2. Coverage: Is the information complete?
    3. Contradiction: Are there conflicting facts? (Crucial for DDL)
    """
    
    def __init__(self, llm_service):
        self.llm = llm_service
        
    async def assess_retrieval_quality(self, query: str, evidences: List[Dict[str, Any]], beta: float) -> Dict[str, Any]:
        """
        Assess the quality of the retrieval results.
        
        Args:
            query: The user query.
            evidences: List of retrieved documents/chunks.
            beta: DDL beta parameter (controls strictness).
            
        Returns:
            Dict containing scores and a 'needs_retry' flag.
        """
        if not evidences:
            return {
                "overall_score": 0.0,
                "relevance_score": 0.0,
                "coverage_score": 0.0,
                "contradiction_score": 0.0,
                "needs_retry": True,
                "reason": "No evidence found"
            }
            
        # Extract content for analysis
        # Limit to top 5 chunks or first 2000 words to save tokens/time
        contents = []
        total_len = 0
        for e in evidences[:5]:
            content = e.get('content', '')
            # If we have full_content (Small-to-Big), use it but truncate
            if e.get('full_content'):
                content = e.get('full_content')[:1000] + "..."
            
            contents.append(content)
            total_len += len(content)
            if total_len > 8000: # Safety limit
                break
                
        combined_content = "\n---\n".join(contents)
        
        # 1. LLM Evaluation (Single pass for efficiency)
        eval_result = await self._evaluate_with_llm(query, combined_content)
        
        relevance_score = float(eval_result.get("relevance", 0.5))
        coverage_score = float(eval_result.get("coverage", 0.5))
        contradiction_score = float(eval_result.get("contradiction", 0.0)) # 0 means no contradiction
        
        # 2. Calculate Overall Score
        # Beta affects the weight of contradiction
        # Low Beta (<0.5): Speed matters, tolerate some noise.
        # High Beta (>1.3): Accuracy matters, contradictions are fatal.
        
        if beta > 1.3:
            # High Beta: Heavy penalty for contradictions and low coverage
            # Score = 30% Relevance + 30% Coverage + 40% Consistency
            overall_score = (relevance_score * 0.3) + (coverage_score * 0.3) + ((1.0 - contradiction_score) * 0.4)
        else:
            # Low Beta: Mainly focus on relevance
            # Score = 70% Relevance + 30% Coverage
            overall_score = (relevance_score * 0.7) + (coverage_score * 0.3)
            
        # 3. Determine Retry
        # Dynamic threshold based on Beta
        # If Beta is high, we demand higher quality (0.7).
        # If Beta is low, we accept lower quality (0.5).
        threshold = 0.7 if beta > 1.0 else 0.5
        needs_retry = overall_score < threshold
        
        # Force retry if contradiction is high in high-beta mode
        if beta > 1.0 and contradiction_score > 0.7:
            needs_retry = True
            eval_result["reason"] += " (Severe Contradiction Detected)"
        
        return {
            "overall_score": round(overall_score, 2),
            "relevance_score": relevance_score,
            "coverage_score": coverage_score,
            "contradiction_score": contradiction_score,
            "needs_retry": needs_retry,
            "reason": eval_result.get("reason", "Assessment completed")
        }

    async def _evaluate_with_llm(self, query: str, content: str) -> Dict[str, Any]:
        prompt = f"""
        Analyze the following retrieved information against the user query.
        
        Query: "{query}"
        
        Retrieved Information:
        {content}
        
        Evaluate the following metrics (0.0 to 1.0):
        1. Relevance: How much of the information is actually relevant to the query?
        2. Coverage: Does the information fully answer the query?
        3. Contradiction: Are there internal conflicts or obvious errors in the information? (1.0 = Severe contradictions, 0.0 = Consistent)
        
        Output format: JSON
        {{
            "relevance": <float>,
            "coverage": <float>,
            "contradiction": <float>,
            "reason": "<short explanation>"
        }}
        """
        
        try:
            # Use generate method (assuming it returns string)
            response_text = await self.llm.generate(prompt)
            return self._extract_json(response_text)
        except Exception as e:
            logger.error(f"LLM evaluation failed: {e}")
            return {"relevance": 0.5, "coverage": 0.5, "contradiction": 0.0, "reason": f"Evaluation failed: {str(e)}"}

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON object from text using regex"""
        try:
            # Find JSON block
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
            return {"relevance": 0.5, "coverage": 0.5, "contradiction": 0.0, "reason": "No JSON found in response"}
        except Exception as e:
            logger.warning(f"Failed to parse JSON from LLM response: {e}")
            return {"relevance": 0.5, "coverage": 0.5, "contradiction": 0.0, "reason": "JSON parse error"}
