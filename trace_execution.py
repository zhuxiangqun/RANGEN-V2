
import asyncio
import sys
import os
import logging
from pathlib import Path
import json

# Add project root to sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Configure logging to capture EntryRouter output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Filter out some noisy logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

from src.unified_research_system import UnifiedResearchSystem, ResearchRequest
from src.core.entry_router import EntryRouter

async def run_single_query(query: str):
    print("\n" + "="*80)
    print(f"🔬 DIAGNOSTIC TRACE FOR QUERY:\n{query}")
    print("="*80 + "\n")

    # --- 1. Complexity Analysis ---
    print("\n" + "-"*40)
    print("📊 1. COMPLEXITY JUDGMENT")
    print("-"*40)
    
    try:
        router = EntryRouter(use_unified_workflow=True)
        # We access the internal service directly to get detailed complexity info
        if router._complexity_service:
            print("Running complexity assessment...")
            complexity_result = await asyncio.to_thread(
                router._complexity_service.assess_complexity,
                query=query,
                query_type=None,
                evidence_count=0,
                use_cache=False
            )
            print(f"Complexity Level: {complexity_result.level.value.upper()}")
            print(f"Score: {complexity_result.score}")
            print(f"Needs Reasoning Chain: {complexity_result.needs_reasoning_chain}")
            if complexity_result.llm_judgment:
                print(f"LLM Judgment: {complexity_result.llm_judgment}")
        else:
            print("Complexity Service not available, using fallback.")
            complexity = router._quick_analyze(query)
            print(f"Complexity Level: {complexity}")
            
    except Exception as e:
        print(f"❌ Error during complexity analysis: {e}")

    # --- 2. Execution ---
    print("\n" + "-"*40)
    print("🚀 2. EXECUTION TRACE")
    print("-"*40)
    
    system = UnifiedResearchSystem()
    # Ensure unified workflow is enabled
    system._use_unified_workflow = True
    
    try:
        req = ResearchRequest(query=query)
        result = await system.execute_research(req)
        
        # --- 3. Reasoning Steps & Answers ---
        print("\n" + "-"*40)
        print("👣 3. REASONING STEPS & ANSWERS")
        print("-"*40)
        
        metadata = result.metadata or {}
        
        # Decomposition
        decomposition = metadata.get('decomposition', {})
        if decomposition:
            print("\n🔹 Query Decomposition:")
            for i, sub_q in enumerate(decomposition.get('sub_queries', [])):
                print(f"  {i+1}. {sub_q}")
        else:
            print("\n🔹 No decomposition metadata found.")

        # Retrieval Trace
        retrieval_trace = metadata.get('retrieval_trace', [])
        if retrieval_trace:
            print("\n🔹 Knowledge Retrieval Results:")
            for item in retrieval_trace:
                status = "✅" if item.get('success') else "❌"
                print(f"  {status} Query: {item.get('sub_query')}")
                if item.get('success'):
                    print(f"     Found: {item.get('knowledge_count', 0)} knowledge items, {item.get('evidence_count', 0)} evidence items")
                else:
                    print(f"     Error: {item.get('error')}")
        else:
            print("\n🔹 No retrieval trace found.")

        # Reasoning Trace
        reasoning_trace = metadata.get('reasoning_trace', [])
        if reasoning_trace:
            print("\n🔹 Reasoning Steps:")
            for i, step in enumerate(reasoning_trace):
                # Handle different step formats
                if isinstance(step, dict):
                    content = step.get('content', str(step))
                    print(f"  Step {i+1}: {content}")
                else:
                    print(f"  Step {i+1}: {step}")
            
            # Reasoning Result/Answer
            reasoning_result = metadata.get('reasoning_result', {})
            print(f"\n🔹 Intermediate Reasoning Answer: {reasoning_result.get('final_answer')}")
        else:
            print("\n🔹 No reasoning trace found.")

        # --- 4. Final Answer ---
        print("\n" + "-"*40)
        print("🏁 4. FINAL ANSWER")
        print("-"*40)
        
        if result.success:
            print(f"{result.answer}")
        else:
            print(f"❌ Execution Failed: {result.error}")
            
    except Exception as e:
        print(f"❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()

async def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--mini-benchmark":
        mini_path = project_root / "data/frames-benchmark" / "mini_queries.json"
        try:
            data = json.loads(mini_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"❌ Failed to load mini_queries.json: {e}")
            return
        for item in data[:4]:
            q = str(item.get("query", "")).strip()
            if not q:
                continue
            await run_single_query(q)
        return

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "If my future wife has the same first name as the 15th first lady of the United States' mother and her last name is the same as the 15th president's, what is her name?"
    await run_single_query(query)

if __name__ == "__main__":
    asyncio.run(main())
