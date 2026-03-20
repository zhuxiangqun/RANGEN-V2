
import os
import asyncio
from src.core.llm_integration import LLMIntegration

async def verify_knowledge():
    # Mock config
    config = {
        "llm_provider": "deepseek",
        "model": "deepseek-reasoner",
        "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
        "base_url": "https://api.deepseek.com/v1"
    }
    
    llm = LLMIntegration(config)
    
    queries = [
        "Who is the 15th First Lady of the United States?",
        "Who is the mother of Harriet Lane?",
        "Who is the mother of the 15th First Lady of the United States?",
        "Who is the mother of the second assassinated president of the United States?",
        "What is the maiden name of James A. Garfield's mother?"
    ]
    
    print("🔍 Verifying Model Knowledge (DeepSeek Reasoner)...")
    for q in queries:
        print(f"\n❓ Query: {q}")
        try:
            # Use call_llm instead of get_response
            response = llm.call_llm(q)
            print(f"💡 Response: {response}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify_knowledge())
