
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from src.services.knowledge_retrieval_service import KnowledgeRetrievalService
from src.knowledge.vector_database import VectorKnowledgeBase

import logging
logging.basicConfig(level=logging.INFO)

async def verify_knowledge():
    print("🔍 Verifying Knowledge Retrieval Service...")
    
    # 1. Verify VectorKnowledgeBase direct access
    print("\n--- 1. Direct VectorKnowledgeBase Check ---")
    try:
        vkb = VectorKnowledgeBase()
        results = vkb.search("Who is the 15th First Lady?", top_k=3)
        print(f"Direct Search Results ({len(results)}):")
        for res in results:
            print(f" - {res['text'][:100]}... (Distance: {res.get('distance', 'N/A')})")
        
        if not results:
            print("❌ Direct search failed to find any results.")
        else:
            print("✅ Direct search successful.")
    except Exception as e:
        print(f"❌ Direct VectorKnowledgeBase check failed: {e}")
        import traceback
        traceback.print_exc()

    # 2. Verify KnowledgeRetrievalService
    print("\n--- 2. KnowledgeRetrievalService Check ---")
    try:
        service = KnowledgeRetrievalService()
        # Initialize (lazy init usually happens on execute, but we can force it or just call execute)
        
        # Mock context
        context = {
            "query": "Who is the 15th First Lady?",
            "type": "knowledge_retrieval"
        }
        
        # We need to manually trigger initialization if it's lazy and internal
        # Check if we can access the underlying vector_kb
        print("Initializing knowledge base via internal method...")
        service._initialize_knowledge_base() # Ensure it's initialized
        
        if hasattr(service, 'vector_kb') and service.vector_kb:
            print("✅ Service vector_kb initialized.")
            service_results = service.vector_kb.search("Who is the 15th First Lady?", top_k=3)
            print(f"Service VectorKB Results ({len(service_results)}):")
            for res in service_results:
                print(f" - {res['text'][:100]}... (Distance: {res.get('distance', 'N/A')})")
        else:
            print("⚠️ Service vector_kb not accessible or None.")
            # Try to debug why
            from src.knowledge.vector_database import get_vector_knowledge_base
            print(f"Debug: get_vector_knowledge_base in script context is: {get_vector_knowledge_base}")
            print(f"Debug: Service has vector_kb attribute: {hasattr(service, 'vector_kb')}")
            if hasattr(service, 'vector_kb'):
                print(f"Debug: Service vector_kb value: {service.vector_kb}")
        
    except Exception as e:
        print(f"❌ KnowledgeRetrievalService check failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_knowledge())
