
import asyncio
import os
import sys
from pathlib import Path
import traceback

# Add project root to path (parent of this script)
sys.path.append(str(Path(__file__).parent))

from src.services.knowledge_retrieval_service import KnowledgeRetrievalService
from src.services.faiss_service import FAISSService
from src.services.query_analyzer import QueryAnalyzer

async def main():
    print("Initializing services...")
    retrieval_service = KnowledgeRetrievalService()
    # Manually initialize services since initialize() method is missing and __init__ skips it
    if hasattr(retrieval_service, '_initialize_services'):
        retrieval_service._initialize_services()
    else:
        print("Warning: _initialize_services not found")
        
    query_analyzer = QueryAnalyzer()
    
    queries = [
        "Which organization publishes the World Economic Outlook report?",
        "Where is the headquarters of Globalpolicy.org located?",
        "What is the capital city of the country where Globalpolicy.org is located?"
    ]
    
    print("\n--- Testing Retrieval ---")
    for query in queries:
        print(f"\nQuery: {query}")
        try:
            analysis = query_analyzer.analyze_query(query)
            results = await retrieval_service._retrieve_knowledge(query, analysis)
            
            # Check if results is a dict (new format) or list (old format)
            if isinstance(results, dict):
                print(f"Results keys: {list(results.keys())}")
                sources = results.get('sources', [])
            else:
                sources = results
                
            print(f"Sources count: {len(sources)}")
            for i, res in enumerate(sources):
                if isinstance(res, dict):
                    content = res.get('content', '')
                    source = res.get('source', 'unknown')
                    score = res.get('score', res.get('similarity', 0))
                    print(f"[{i}] Score: {score:.4f} | Source: {source}")
                    print(f"    Content: {content[:200]}...")
                else:
                    print(f"[{i}] {type(res)}: {str(res)[:100]}...")
        except Exception as e:
            print(f"Error processing query: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
