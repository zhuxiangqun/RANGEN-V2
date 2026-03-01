
import sys
import logging
from pathlib import Path
import os

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)
except ImportError:
    pass

from src.knowledge.vector_database import VectorKnowledgeBase
from src.core.reasoning.answer_extraction.answer_extractor import AnswerExtractor
from src.core.llm_integration import LLMIntegration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import asyncio


def verify_step4():
    print("="*50)
    print("Verifying Step 4-6 Logic (James A. Garfield -> Eliza Ballou)")
    print("="*50)

    # 1. Initialize Knowledge Base
    print("\n1. Initializing VectorKnowledgeBase...")
    kb = VectorKnowledgeBase()
    # Force reload or ensure it uses the persistent storage
    # The VectorKnowledgeBase should load from disk if 'vector_store' exists
    
    # 2. Test Retrieval
    query_mother = "Who was the mother of James A. Garfield?"
    print(f"\n2. Retrieving evidence for: '{query_mother}'")
    raw_results = kb.search(query_mother, top_k=3)
    
    found_eliza = False
    evidence_items = []
    evidence_text = ""
    for item in raw_results:
        text = item.get("text", "")
        metadata = item.get("metadata", {})
        print(f"   - Found: {text[:100]}...")
        evidence_text += text + "\n"
        if "Eliza Ballou" in text:
            found_eliza = True
        # 构造 Evidence-like 结构，供 AnswerExtractor 使用
        evidence_items.append({
            "content": text,
            "source": metadata.get("source", "vector_db"),
            "confidence": 1.0,
            "relevance_score": 1.0,
            "evidence_type": metadata.get("topic", "fact"),
            "metadata": metadata,
        })
            
    if found_eliza:
        print("   ✅ CORRECT: 'Eliza Ballou' found in retrieved evidence.")
    else:
        print("   ❌ ERROR: 'Eliza Ballou' NOT found in retrieved evidence.")
        # If not found, we might need to rely on the manual population done earlier being persisted.
        # Assuming populate_15th_first_lady.py was run and FAISS index saved.

    # 3. Test Extraction
    print(f"\n3. Testing Answer Extraction with retrieved evidence...")
    
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        config = {
            "api_key": api_key,
            "model_name": "deepseek-chat",
            "temperature": 0.0,
        }
        llm_service = LLMIntegration(config)
        extractor = AnswerExtractor(llm_integration=llm_service)
    else:
        extractor = AnswerExtractor(llm_integration=None)
    
    # Run extraction (AnswerExtractor.extract 是 async)
    result = asyncio.run(
        extractor.extract(query=query_mother, evidence=evidence_items)
    )
    
    print(f"\n4. Extraction Result:")
    print(f"   - Answer: {result.answer}")
    print(f"   - Confidence: {result.confidence}")
    print(f"   - Source: {result.source}")
    
    if "Eliza Ballou" in result.answer:
        print("   ✅ SUCCESS: Correctly extracted 'Eliza Ballou'.")
    else:
        print("   ❌ FAILURE: Failed to extract 'Eliza Ballou'.")

    # 4. Test "Second Assassinated President" step
    query_president = "Who was the second president to be assassinated?"
    print(f"\n5. Testing Retrieval for: '{query_president}'")
    raw_pres = kb.search(query_president, top_k=3)
    
    found_garfield = False
    evidence_pres = []
    for item in raw_pres:
        text = item.get("text", "")
        metadata = item.get("metadata", {})
        print(f"   - Found: {text[:100]}...")
        if "Garfield" in text and "assassinated" in text:
            found_garfield = True
        evidence_pres.append({
            "content": text,
            "source": metadata.get("source", "vector_db"),
            "confidence": 1.0,
            "relevance_score": 1.0,
            "evidence_type": metadata.get("topic", "fact"),
            "metadata": metadata,
        })
            
    if found_garfield:
        print("   ✅ CORRECT: 'Garfield' found in retrieved evidence.")
        
        # Test Extraction
        result_pres = asyncio.run(
            extractor.extract(query=query_president, evidence=evidence_pres)
        )
        print(f"   - Extracted Answer: {result_pres.answer}")
        
        if "Garfield" in result_pres.answer:
            print("   ✅ SUCCESS: Correctly extracted 'James A. Garfield'.")
        else:
            print("   ❌ FAILURE: Failed to extract 'James A. Garfield'.")
            
    else:
        print("   ❌ ERROR: 'Garfield' NOT found in retrieved evidence.")

if __name__ == "__main__":
    verify_step4()
