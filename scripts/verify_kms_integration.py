"""
Verification script for KMS Integration
"""
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from src.agents.tools.retrieval_tool import RetrievalTool
from src.services.logging_service import get_logger

logger = get_logger("verify_kms")

async def verify_kms():
    logger.info("Starting KMS Integration Verification...")
    
    try:
        tool = RetrievalTool()
        logger.info("RetrievalTool instantiated.")
        
        # Test 1: Check KMS availability
        if tool.kms:
            logger.info("✅ KMS Connection Successful.")
        else:
            logger.error("❌ KMS Connection Failed.")
            return

        # Test 2: Real Retrieval
        query = "quantum computing"
        logger.info(f"Testing retrieval for: '{query}'")
        
        result = await tool.execute(query=query, top_k=3)
        
        if result.success:
            logger.info("✅ Retrieval Successful.")
            logger.info(f"Found {len(result.output)} documents.")
            for doc in result.output:
                logger.info(f" - {doc.get('content')[:100]}...")
        else:
            logger.error(f"❌ Retrieval Failed: {result.error}")
            
    except Exception as e:
        logger.error(f"Verification crashed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_kms())
