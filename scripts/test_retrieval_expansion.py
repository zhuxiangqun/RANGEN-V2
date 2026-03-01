#!/usr/bin/env python3
"""
Test script for Small-to-Big Retrieval (Context Expansion)
"""

import sys
import os
import logging
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge_management_system.api.service_interface import KnowledgeManagementService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_retrieval_expansion():
    logger.info("🚀 Starting Retrieval Expansion Test...")
    
    service = KnowledgeManagementService()
    
    # 1. Import Data
    logger.info("Importing document...")
    large_content = "This is a sentence in a large document. " * 500
    large_content = "## Section 1\n" + large_content + "\n\n## Section 2\n" + large_content
    
    metadata = {"source": "test_script_retrieval", "title": "Large Retrieval Doc"}
    
    knowledge_ids = service.import_knowledge(
        data=[{"content": large_content, "metadata": metadata}],
        source_type="list",
        modality="text"
    )
    logger.info(f"Imported {len(knowledge_ids)} chunks.")
    
    # Wait for indexing? (import_knowledge vectorizes immediately)
    
    # 2. Query
    query = "sentence in a large document"
    logger.info(f"Querying: '{query}' with expand_context=True")
    
    results = service.query_knowledge(
        query=query,
        top_k=5,
        similarity_threshold=0.5, # Standard threshold
        expand_context=True,
        use_rerank=False
    )
    
    if not results:
        logger.error("❌ No results found!")
        return
    
    logger.info(f"Found {len(results)} results.")
    
    found_target = False
    for i, result in enumerate(results):
        content = result.get('content', '')
        full_content = result.get('full_content', '')
        parent_id = result.get('metadata', {}).get('parent_id')
        title = result.get('metadata', {}).get('title')
        
        logger.info(f"Result {i+1}: ID={result['knowledge_id']}, Title={title}")
        
        if title == "Large Retrieval Doc":
            found_target = True
            logger.info(f"  ✅ Found target document!")
            logger.info(f"  Chunk Length: {len(content)}")
            logger.info(f"  Full Content Length: {len(full_content)}")
            logger.info(f"  Parent ID: {parent_id}")
            
            if len(full_content) > len(content):
                logger.info("  ✅ Full content is larger than chunk content")
            else:
                logger.error("  ❌ Full content is NOT larger than chunk content")
                
            if full_content == large_content:
                 logger.info("  ✅ Full content matches original exactly")
            else:
                 logger.warning("  ⚠️ Full content matches original but might differ slightly (e.g. whitespace)")

    if not found_target:
        logger.error("❌ Target document not found in top results!")

    logger.info("🎉 Test Complete!")

if __name__ == "__main__":
    test_retrieval_expansion()
