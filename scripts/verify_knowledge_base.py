
import sys
import os
from pathlib import Path
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.neural.factory import NeuralServiceFactory
from knowledge_management_system.api.service_interface import get_knowledge_service

def verify_knowledge_base():
    """
    Verify the content of the vector knowledge base.
    1. Check total count
    2. Perform a sample search to verify retrieval
    3. Check metadata quality
    """
    print("=" * 50)
    print("🔍 Knowledge Base Verification")
    print("=" * 50)
    
    service = get_knowledge_service()
    
    # 1. Check Stats (if available via API, otherwise infer from search)
    # Since we don't have a direct 'count' API exposed easily, we'll try a broad search
    
    print("\n1. Testing Retrieval...")
    test_queries = [
        "O.J. Simpson trial",
        "Birdman film",
        "Rubik's Cube",
        "Glastonbury Festival"
    ]
    
    for query in test_queries:
        print(f"\n   Query: '{query}'")
        try:
            results = service.query_knowledge(
                query=query,
                top_k=3,
                similarity_threshold=0.5
            )
            
            if not results:
                print("   ❌ No results found (might not be indexed yet)")
            else:
                print(f"   ✅ Found {len(results)} results")
                for i, res in enumerate(results):
                    meta = res.get('metadata', {})
                    content = res.get('content', '')[:100].replace('\n', ' ')
                    title = meta.get('title', 'No Title')
                    print(f"      {i+1}. [{title}] {content}...")
                    
                    # Verify metadata
                    print(f"         Metadata Keys: {list(meta.keys())}")
                    if 'source_urls' in meta and meta['source_urls']:
                        print(f"         Source: {meta['source_urls'][0]}")
                    else:
                        print("         ⚠️ Missing source URL")
                    if 'wikipedia_titles' in meta:
                        print(f"         Wiki Titles: {meta['wikipedia_titles']}")
                    if 'prompt' in meta:
                        print(f"         Original Prompt: {meta['prompt'][:50]}...")
                        
        except Exception as e:
            print(f"   ❌ Search failed: {e}")

if __name__ == "__main__":
    verify_knowledge_base()
