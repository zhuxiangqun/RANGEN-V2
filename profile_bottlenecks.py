
import asyncio
import time
import sys
import logging
from functools import wraps
from typing import Any, Callable

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("profiler")

# 计时装饰器工厂
def profile_method(name: str):
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                logger.info(f"⏱️ [PROFILE] {name} took {duration:.4f}s")

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                logger.info(f"⏱️ [PROFILE] {name} took {duration:.4f}s")

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# Monkey-patch 目标模块
def apply_patches():
    try:
        from src.services.knowledge_retrieval_service import KnowledgeRetrievalService
        KnowledgeRetrievalService.execute = profile_method("KnowledgeRetrievalService.execute")(KnowledgeRetrievalService.execute)
        KnowledgeRetrievalService._perform_knowledge_retrieval = profile_method("KnowledgeRetrievalService._perform_knowledge_retrieval")(KnowledgeRetrievalService._perform_knowledge_retrieval)
        KnowledgeRetrievalService._validate_retrieval_result = profile_method("KnowledgeRetrievalService._validate_retrieval_result")(KnowledgeRetrievalService._validate_retrieval_result)
        logger.info("✅ Patched KnowledgeRetrievalService")
    except ImportError:
        logger.warning("⚠️ Could not patch KnowledgeRetrievalService")

    try:
        from src.services.knowledge_retriever import KnowledgeRetriever
        KnowledgeRetriever.get_kms_knowledge_single_round = profile_method("KnowledgeRetriever.get_kms_knowledge_single_round")(KnowledgeRetriever.get_kms_knowledge_single_round)
        logger.info("✅ Patched KnowledgeRetriever")
    except ImportError:
        logger.warning("⚠️ Could not patch KnowledgeRetriever")

    try:
        from src.utils.semantic_understanding_pipeline import SemanticUnderstandingPipeline
        SemanticUnderstandingPipeline.validate_relevance = profile_method("SemanticUnderstandingPipeline.validate_relevance")(SemanticUnderstandingPipeline.validate_relevance)
        logger.info("✅ Patched SemanticUnderstandingPipeline")
    except ImportError:
        logger.warning("⚠️ Could not patch SemanticUnderstandingPipeline")
        
    try:
        from src.services.query_analyzer import QueryAnalyzer
        QueryAnalyzer.analyze_query = profile_method("QueryAnalyzer.analyze_query")(QueryAnalyzer.analyze_query)
        QueryAnalyzer.assess_complexity = profile_method("QueryAnalyzer.assess_complexity")(QueryAnalyzer.assess_complexity)
        logger.info("✅ Patched QueryAnalyzer")
    except ImportError:
        logger.warning("⚠️ Could not patch QueryAnalyzer")

    try:
        from src.core.reasoning.reasoning_engine import RealReasoningEngine
        RealReasoningEngine.reason = profile_method("RealReasoningEngine.reason")(RealReasoningEngine.reason)
        RealReasoningEngine._execute_deep_reasoning_loop = profile_method("RealReasoningEngine._execute_deep_reasoning_loop")(RealReasoningEngine._execute_deep_reasoning_loop)
        logger.info("✅ Patched RealReasoningEngine")
    except ImportError:
        logger.warning("⚠️ Could not patch RealReasoningEngine")
    
    try:
        from src.unified_research_system import UnifiedResearchSystem
        UnifiedResearchSystem.execute_research = profile_method("UnifiedResearchSystem.execute_research")(UnifiedResearchSystem.execute_research)
        logger.info("✅ Patched UnifiedResearchSystem")
    except ImportError:
        logger.warning("⚠️ Could not patch UnifiedResearchSystem")

    try:
        from src.agents.expert_agent import ExpertAgent
        ExpertAgent._think = profile_method("ExpertAgent._think")(ExpertAgent._think)
        ExpertAgent._plan_action = profile_method("ExpertAgent._plan_action")(ExpertAgent._plan_action)
        ExpertAgent._execute_action = profile_method("ExpertAgent._execute_action")(ExpertAgent._execute_action)
        logger.info("✅ Patched ExpertAgent")
    except ImportError:
        logger.warning("⚠️ Could not patch ExpertAgent")

    try:
        from src.core.llm_integration import LLMIntegration
        LLMIntegration._call_llm = profile_method("LLMIntegration._call_llm")(LLMIntegration._call_llm)
        logger.info("✅ Patched LLMIntegration")
    except ImportError:
        logger.warning("⚠️ Could not patch LLMIntegration")

async def run_diagnostic():
    apply_patches()
    
    from src.unified_research_system import UnifiedResearchSystem, ResearchRequest
    
    system = UnifiedResearchSystem()
    query = "Imagine there is a building called Bronte tower whose height in feet is the same number as the dewey decimal classification for the Charlotte Bronte book that was published in 1847. Where would this building rank among tallest buildings in New York City, as of August 2024?"
    
    print(f"\n🚀 Starting diagnostic run for query: {query[:50]}...\n")
    try:
        # 使用较短的超时，我们只关心耗时分布，不需要等到它跑完
        request = ResearchRequest(query=query)
        await asyncio.wait_for(system.execute_research(request), timeout=180.0)
    except asyncio.TimeoutError:
        print("\n❌ Timed out as expected (or unexpected). Check logs above for timing.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_diagnostic())
