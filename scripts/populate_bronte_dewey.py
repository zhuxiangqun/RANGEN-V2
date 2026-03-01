import asyncio
import logging
from src.services.knowledge_retrieval_service import KnowledgeRetrievalService
from src.knowledge.vector_database import VectorKnowledgeBase

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def populate_knowledge():
    print("🚀 Starting Bronte Dewey knowledge population...")
    
    # 1. Initialize Service and Vector DB
    service = KnowledgeRetrievalService()
    service._initialize_knowledge_base()
    
    if not hasattr(service, 'vector_kb') or service.vector_kb is None:
        service.vector_kb = VectorKnowledgeBase()
        service.vector_kb.load()
    
    vector_kb = service.vector_kb
    
    # 2. Define Facts
    facts = [
        {
            "text": "The Dewey Decimal Classification (DDC) number for the Brontë family (Charlotte, Emily, and Anne Brontë) is 823.8.",
            "metadata": {"source": "manual_ingestion", "topic": "Literature", "entity": "Brontë family", "dewey": "823.8"}
        },
        {
            "text": "English fiction of the Victorian period (1837–1901) is classified under 823.8 in Dewey Decimal Classification.",
            "metadata": {"source": "manual_ingestion", "topic": "Literature", "dewey": "823.8"}
        },
        {
            "text": "1 foot is equal to 0.3048 meters.",
            "metadata": {"source": "manual_ingestion", "topic": "Conversion", "unit_from": "foot", "unit_to": "meter", "factor": 0.3048}
        }
    ]
    
    # 3. Add Facts
    print(f"📚 Adding {len(facts)} facts to knowledge base...")
    for fact in facts:
        success = vector_kb.add_knowledge(fact["text"], fact["metadata"], validate_quality=False)
        if success:
            print(f"✅ Added: {fact['text'][:50]}...")
        else:
            print(f"❌ Failed to add: {fact['text'][:50]}...")
            
    # 4. Save
    vector_kb.save()
    print(f"💾 Knowledge base saved. Total items: {vector_kb.size()}")
    
    # 5. Verify
    print("\n🔍 Verifying retrieval...")
    query = "What is the Dewey Decimal for the Bronte family?"
    results = vector_kb.search(query, top_k=3)
    for i, res in enumerate(results):
        print(f"{i+1}. {res['text']} (Dist: {res.get('distance', 'N/A')})")

if __name__ == "__main__":
    asyncio.run(populate_knowledge())
