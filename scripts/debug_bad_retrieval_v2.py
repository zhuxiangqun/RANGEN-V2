
import asyncio
import sys
import os
import logging
from pathlib import Path
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.services.knowledge_retrieval_service import KnowledgeRetrievalService
from src.services.query_analyzer import QueryAnalyzer
from src.memory.enhanced_faiss_memory import EnhancedFAISSMemory

async def main():
    print("Initializing services...")
    retrieval_service = KnowledgeRetrievalService()
    
    # Manually initialize helper services
    print("Initializing helper components...")
    retrieval_service._init_query_analyzer()
    retrieval_service._init_retrieval_helpers()
    retrieval_service._init_content_processor()
    retrieval_service._init_knowledge_retriever()
    
    # Check which backend is used
    if getattr(retrieval_service, 'kms_service', None):
        print("✅ Using KnowledgeManagementService (KMS)")
    elif getattr(retrieval_service, 'faiss_service', None):
        print(f"✅ Using FAISS Service: {type(retrieval_service.faiss_service)}")
        # Ensure FAISS service is initialized
        if hasattr(retrieval_service.faiss_service, 'get_instance'):
            await retrieval_service.faiss_service.get_instance()
        elif hasattr(retrieval_service.faiss_service, 'initialize'):
             if asyncio.iscoroutinefunction(retrieval_service.faiss_service.initialize):
                 await retrieval_service.faiss_service.initialize()
             else:
                 retrieval_service.faiss_service.initialize()
        elif hasattr(retrieval_service.faiss_service, 'wait_for_initialization'):
             retrieval_service.faiss_service.wait_for_initialization()
    else:
        print("⚠️ No knowledge backend available in retrieval_service")
        print("   Initializing EnhancedFAISSMemory manually...")
        memory = EnhancedFAISSMemory()
        if hasattr(memory, 'wait_for_initialization'):
             # Increase timeout to allow embedding to finish
             print("⏳ Waiting for FAISS initialization (timeout=300s)...")
             if not memory.wait_for_initialization(timeout=300.0):
                 print("❌ FAISS initialization timed out!")
             else:
                 print("✅ FAISS initialized successfully")

        
        # Create a wrapper that mimics FAISSService async search
        class AsyncMemoryWrapper:
            def __init__(self, memory):
                self.memory = memory
            
            async def search(self, query, top_k):
                # Call sync search
                return self.memory.search(query, top_k=top_k)
                
        retrieval_service.faiss_service = AsyncMemoryWrapper(memory)
        print("✅ Manually initialized EnhancedFAISSMemory (wrapped async)")

    query_analyzer = retrieval_service.query_analyzer
    
    queries = [
        "Which organization publishes the World Economic Outlook report?",
        "Where is the headquarters of Globalpolicy.org located?", 
        "What is the capital city of the country where Globalpolicy.org is located?"
    ]
    
    print("\n--- Testing Retrieval ---")
    for query in queries:
        print(f"\nQuery: {query}")
        try:
            # Analyze query (synchronous)
            analysis = query_analyzer.analyze_query(query)
            print(f"Analysis type: {analysis.get('type')}")
            
            # Retrieve knowledge
            print("Calling _retrieve_from_faiss...")
            # Note: _retrieve_from_faiss returns a LIST of dicts (sources), not an AgentResult or wrapped object
            # Wait, let's check the return type in KnowledgeRetrievalService._retrieve_from_faiss
            # It returns Optional[List[Dict[str, Any]]] based on the code I read (formatted_sources)
            # Actually, looking at the code I read earlier:
            # L1181: formatted_sources = []
            # ...
            # return formatted_sources (implied, though I didn't see the return statement in the snippet, it usually returns the list)
            
            # Re-reading the snippet from earlier:
            # L1156: async def _get_faiss_knowledge(...) -> Optional[Dict[str, Any]]:
            # Wait, type hint says Dict, but implementation usually returns list of sources?
            # Let's check the return value carefully.
            
            result = await retrieval_service._get_faiss_knowledge(query, analysis)
            
            if result:
                # Based on standard implementation, it might return a list of sources OR a dict with 'sources' key
                # Let's inspect it
                print(f"Result type: {type(result)}")
                sources = []
                if isinstance(result, list):
                    sources = result
                elif isinstance(result, dict) and 'sources' in result:
                    sources = result['sources']
                elif isinstance(result, dict):
                    # Maybe it returns a single source?
                    sources = [result]
                
                print(f"Sources count: {len(sources)}")
                for i, res in enumerate(sources):
                    content = res.get('content', '')
                    score = res.get('similarity_score', res.get('score', 0))
                    print(f"[{i}] Score: {score:.4f} | Source: {res.get('source')}")
                    print(f"    Content: {content[:200]}...")
                    if "Globalpolicy.org" in content:
                        print("    🚨 FOUND Globalpolicy.org HERE!")
            else:
                print("Result is None/Empty")

        except Exception as e:
            print(f"Error processing query: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
