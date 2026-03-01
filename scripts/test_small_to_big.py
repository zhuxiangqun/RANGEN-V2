#!/usr/bin/env python3
"""
Test script for Small-to-Big Retrieval (Parent Document Indexing)
"""

import sys
import os
import time
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge_management_system.api.service_interface import KnowledgeManagementService
from knowledge_management_system.core.knowledge_manager import KnowledgeManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_small_to_big():
    logger.info("🚀 Starting Small-to-Big Indexing Test...")
    
    # Initialize service
    service = KnowledgeManagementService()
    
    # Create a large document (larger than 10k threshold)
    # 10k threshold is hardcoded in service_interface.py
    logger.info("Generating large document...")
    large_content = "This is a sentence in a large document. " * 500  # ~20k chars
    large_content = "## Section 1\n" + large_content + "\n\n## Section 2\n" + large_content
    
    logger.info(f"Document length: {len(large_content)}")
    
    # Import knowledge
    logger.info("Importing document...")
    metadata = {"source": "test_script", "title": "Large Test Doc"}
    
    # We expect this to trigger:
    # 1. Create Parent Document
    # 2. Chunking
    # 3. Create Chunk Entries
    
    # Capture IDs
    knowledge_ids = service.import_knowledge(
        data=[{"content": large_content, "metadata": metadata}],
        source_type="list",
        modality="text"
    )
    
    logger.info(f"Imported {len(knowledge_ids)} chunks.")
    
    if not knowledge_ids:
        logger.error("❌ No chunks imported!")
        return
    
    # Verify Chunks have parent_id
    logger.info("Verifying chunks...")
    manager = service.knowledge_manager
    
    first_chunk_id = knowledge_ids[0]
    first_chunk = manager.get_knowledge(first_chunk_id)
    
    if not first_chunk:
        logger.error(f"❌ Could not retrieve chunk {first_chunk_id}")
        return
    
    chunk_meta = first_chunk.get('metadata', {})
    parent_id = chunk_meta.get('parent_id')
    
    if parent_id:
        logger.info(f"✅ Chunk has parent_id: {parent_id}")
        
        # Verify Parent Document exists
        parent_doc = manager.get_knowledge(parent_id)
        if parent_doc:
            logger.info("✅ Parent Document found in KnowledgeManager")
            parent_meta = parent_doc.get('metadata', {})
            if parent_meta.get('doc_type') == 'parent_document':
                logger.info("✅ Parent Document has correct doc_type='parent_document'")
            else:
                logger.warning(f"⚠️ Parent Document has wrong doc_type: {parent_meta.get('doc_type')}")
            
            # Verify content match
            if parent_doc.get('metadata', {}).get('content') == large_content:
                 logger.info("✅ Parent Document content matches original")
            else:
                 logger.warning("⚠️ Parent Document content mismatch (might be preview vs full)")
                 
        else:
            logger.error(f"❌ Parent Document {parent_id} not found!")
    else:
        logger.error("❌ Chunk missing parent_id!")
        logger.info(f"Chunk metadata: {chunk_meta}")

    logger.info("🎉 Test Complete!")

if __name__ == "__main__":
    test_small_to_big()
