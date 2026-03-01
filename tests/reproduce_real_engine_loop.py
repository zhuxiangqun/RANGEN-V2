
import asyncio
import logging
import sys
import os
import json

# 添加项目根目录到路径
sys.path.append(os.getcwd())

# Mock psutil
import unittest.mock
sys.modules['psutil'] = unittest.mock.MagicMock()
sys.modules['dotenv'] = unittest.mock.MagicMock()

from src.core.real_reasoning_engine import RealReasoningEngine
from src.core.reasoning.step_generator import StepGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ReproduceRealLoop")

async def main():
    try:
        # 初始化引擎
        engine = RealReasoningEngine()
        
        # 测试查询
        query = "Who is the mother of the 15th US President?"
        logger.info(f"🚀 Testing with query: {query}")
        
        context = {"original_query": query}
        
        # 1. 生成计划
        logger.info("\n--- Phase 1: Generating Plan (Manually Injected for Control) ---")
        # steps = await engine._generate_initial_plan(query, context)
        
        # Manually inject a multi-hop plan to test association
        steps = [
            {
                "step_id": 1,
                "type": "evidence_gathering",
                "description": "Identify the 15th US President",
                "sub_query": "Who was the 15th US President?",
                "confidence": 0.9
            },
            {
                "step_id": 2,
                "type": "evidence_gathering",
                "description": "Identify the mother of the 15th US President",
                "sub_query": "Who was the mother of [step 1 result]?",
                "confidence": 0.9,
                "depends_on": [0]
            },
            {
                "step_id": 3,
                "type": "answer_synthesis",
                "description": "Synthesize the final answer",
                "sub_query": "Synthesize the answer based on previous steps",
                "confidence": 0.9,
                "depends_on": [1]
            }
        ]
        
        # Mock EvidenceProcessor to return fake evidence
        async def mock_gather_evidence(sub_query, context, options=None):
            from src.core.reasoning.models import Evidence
            logger.info(f"Mocking evidence for: {sub_query}")
            if "15th US President" in sub_query:
                return [Evidence(
                    content="James Buchanan was the 15th President of the United States.", 
                    source="mock", 
                    relevance_score=0.9,
                    confidence=0.9,
                    evidence_type="text",
                    metadata={}
                )]
            elif "James Buchanan" in sub_query or "mother" in sub_query:
                 return [Evidence(
                    content="James Buchanan's mother was Elizabeth Speer.", 
                    source="mock", 
                    relevance_score=0.9,
                    confidence=0.9,
                    evidence_type="text",
                    metadata={}
                )]
            return []

        if engine.evidence_processor:
             engine.evidence_processor.gather_evidence = mock_gather_evidence
        
        if not steps:
            logger.error("❌ Failed to generate steps.")
            return

        logger.info(f"Generated {len(steps)} steps.")
        
        # 2. 执行深度推理循环
        logger.info("\n--- Phase 2: Executing Reasoning Loop ---")
        result = await engine._execute_deep_reasoning_loop(query, steps, context)
        
        logger.info("\n--- Execution Result ---")
        logger.info(f"Success: {result.success}")
        logger.info(f"Final Answer: {result.final_answer}")
        logger.info(f"Executed Steps Count: {len(result.reasoning_steps)}")
        
        for i, step in enumerate(result.reasoning_steps):
            logger.info(f"Step {i+1}:")
            logger.info(f"  Desc: {step.get('description')}")
            logger.info(f"  SubQuery: {step.get('sub_query')}")
            logger.info(f"  Result: {step.get('result')}")
            logger.info(f"  Evidence Count: {len(step.get('evidence', []))}")

        if not result.reasoning_steps:
             logger.error("❌ No reasoning steps executed! This matches 'No associated reasoning steps' error.")
        elif not result.final_answer or result.final_answer == "Unable to determine":
             logger.warning("⚠️ Final answer not determined.")
        else:
             logger.info("✅ Full execution successful.")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
