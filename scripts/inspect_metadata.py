#!/usr/bin/env python3
import sys
import os
import json
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from knowledge_management_system.core.knowledge_manager import KnowledgeManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inspect_metadata():
    manager = KnowledgeManager()
    
    # IDs from the previous run output
    ids = [
        "2d00a977-4f41-4f6b-9d0f-e6485deda0f7",
        "f913cca9-8421-43e5-9dd8-8f33f4618847"
    ]
    
    for knowledge_id in ids:
        entry = manager.get_knowledge(knowledge_id)
        if entry:
            logger.info(f"ID: {knowledge_id}")
            logger.info(f"Metadata: {json.dumps(entry.get('metadata', {}), indent=2, ensure_ascii=False)}")
        else:
            logger.warning(f"ID {knowledge_id} not found in KnowledgeManager")

if __name__ == "__main__":
    inspect_metadata()
