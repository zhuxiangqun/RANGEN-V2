
import asyncio
import logging
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.getcwd())

from src.core.real_reasoning_engine import RealReasoningEngine
from src.core.reasoning.step_generator import StepGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("VerifyRealGeneration")

async def main():
    try:
        # 初始化引擎
        engine = RealReasoningEngine()
        
        # 测试查询
        query = "Who is the mother of the 15th US President?"
        logger.info(f"🚀 Testing with query: {query}")
        
        # 1. 测试 StepGenerator (Phase 2)
        logger.info("\n--- Testing Step Generation (Real LLM) ---")
        context = {"original_query": query}
        
        # 强制使用真实生成，不使用Mock
        steps = await engine._generate_initial_plan(query, context)
        
        logger.info(f"Generated {len(steps)} steps:")
        for i, step in enumerate(steps):
            logger.info(f"Step {i+1}: {step.get('description')} (Sub-query: {step.get('sub_query')})")
            
        # 验证步骤相关性
        is_relevant = any("James Buchanan" in str(step) or "mother" in str(step) for step in steps)
        if is_relevant:
            logger.info("\n✅ Generated steps are RELEVANT to the query.")
        else:
            logger.warning("\n⚠️ Generated steps might be IRRELEVANT.")
            
        # 验证依赖占位符
        has_placeholder = any("[step" in str(step) for step in steps)
        if has_placeholder:
            logger.info("✅ Steps contain dependency placeholders (e.g., [step 1 result]).")
        else:
            logger.warning("⚠️ Steps DO NOT contain dependency placeholders. Multi-hop reasoning might fail.")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
