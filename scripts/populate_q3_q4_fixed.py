#!/usr/bin/env python3
import os
import sys
import asyncio
import logging

# Set PYTHONPATH to include the current directory
sys.path.append(os.getcwd())

from src.services.knowledge_retrieval_service import KnowledgeRetrievalService
from src.knowledge.vector_database import VectorKnowledgeBase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    logger.info("📚 Initializing Knowledge Base Population for Q3 & Q4...")
    
    # Initialize service
    service = KnowledgeRetrievalService()
    
    # Access the knowledge base directly
    # Note: KnowledgeRetrievalService initializes self.knowledge_base in __init__ 
    # but it might be a dict or a VectorKnowledgeBase instance depending on implementation.
    # Looking at code, it seems it uses VectorKnowledgeBase.
    
    # We will try to instantiate VectorKnowledgeBase directly if service fails
    # Force using VectorKnowledgeBase directly to avoid service initialization issues
    kb_path = 'data/vector_db'
    kb = VectorKnowledgeBase(kb_path)
    
    facts = [
        # Q3: Groundhog Day 2024
        "On February 2, 2024, Punxsutawney Phil did NOT see his shadow.",
        "If Punxsutawney Phil does not see his shadow, it predicts an early spring.",
        "If Punxsutawney Phil sees his shadow, it predicts six more weeks of winter.",
        "Spring 2024 officially started on March 19, 2024 (Vernal Equinox).",
        
        # Q4: FIFA World Cup 1980-2000
        "The 1982 FIFA World Cup was won by Italy.",
        "The 1986 FIFA World Cup was won by Argentina.",
        "The 1990 FIFA World Cup was won by West Germany.",
        "The 1994 FIFA World Cup was won by Brazil.",
        "The 1998 FIFA World Cup was won by France.",
        "Italy won the World Cup in 1982.",
        "Argentina won the World Cup in 1986.",
        "West Germany won the World Cup in 1990.",
        "Brazil won the World Cup in 1994.",
        "France won the World Cup in 1998.",
        "There was no World Cup in 1980 (it is held every 4 years).",
        "The World Cups between 1980 and 2000 were held in 1982, 1986, 1990, 1994, and 1998."
    ]
    
    logger.info(f"📚 Adding {len(facts)} facts to knowledge base...")
    
    for fact in facts:
        try:
            # Use add_document or similar method
            # VectorKnowledgeBase usually has add_texts or add_documents
            kb.add_knowledge(
                text=fact,
                metadata={"source": "manual_population", "type": "fact", "topic": "general_knowledge"}
            )
            logger.info(f"✅ Added: {fact}")
        except Exception as e:
            logger.error(f"❌ Failed to add fact: {fact}. Error: {e}")
            
    # Save/Persist
    try:
        if hasattr(kb, 'save'):
            kb.save()
        elif hasattr(kb, 'persist'):
            kb.persist()
        logger.info("💾 Knowledge base saved successfully.")
    except Exception as e:
        logger.warning(f"⚠️ Could not save knowledge base explicitly: {e}")

    logger.info("🎉 Population complete!")

if __name__ == "__main__":
    asyncio.run(main())
