import asyncio
import json
import traceback
import sys
import os
import time

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from src.unified_research_system import UnifiedResearchSystem, ResearchRequest
from src.core.entry_router import EntryRouter

queries = [
    {
        "id": "test_query_1",
        "text": "Imagine there is a building called Bronte tower whose height in feet is the same number as the dewey decimal classification for the Charlotte Bronte book that was published in 1847. Where would this building rank among tallest buildings in New York City, as of August 2024?"
    },
    {
        "id": "test_query_2",
        "text": "How many years earlier would Punxsutawney Phil have to be canonically alive to have made a Groundhog Day prediction in the same state as the US capitol?"
    },
    {
        "id": "test_query_3",
        "text": "As of August 1, 2024, which country were holders of the FIFA World Cup the last time the UEFA Champions League was won by a club from London?"
    }
]

async def run_single_query(q_data):
    q_text = q_data["text"]
    q_id = q_data["id"]
    print(f"\n{'='*50}", flush=True)
    print(f"Running Query: {q_id}", flush=True)
    print(f"Query Text: {q_text}", flush=True)
    print(f"{'='*50}\n", flush=True)
    
    result_data = {
        "query_id": q_id,
        "query": q_text,
        "complexity": None,
        "reasoning_trace": [],
        "intermediate_answer": None,
        "final_answer": None,
        "success": False,
        "error": None
    }

    try:
        # 1. Complexity Assessment
        print(f"[{q_id}] Assessing complexity...", flush=True)
        router = EntryRouter(use_unified_workflow=True)
        if router._complexity_service:
            comp = await asyncio.to_thread(
                router._complexity_service.assess_complexity,
                q_text,
                None,
                0,
                False,
            )
            result_data["complexity"] = {
                "level": getattr(comp.level, "value", None) if comp else None,
                "score": getattr(comp, "score", None) if comp else None,
                "needs_reasoning_chain": getattr(comp, "needs_reasoning_chain", None) if comp else None,
            }
            print(f"[{q_id}] Complexity Level: {result_data['complexity']['level']}", flush=True)
            print(f"[{q_id}] Complexity Score: {result_data['complexity']['score']}", flush=True)
        
        # 2. Execution
        print(f"[{q_id}] Executing unified workflow...", flush=True)
        system = UnifiedResearchSystem()
        system._use_unified_workflow = True
        req = ResearchRequest(query=q_text)
        res = await system.execute_research(req)
        
        meta = res.metadata or {}
        result_data["reasoning_trace"] = meta.get("reasoning_trace", [])
        result_data["intermediate_answer"] = meta.get("reasoning_result", {}).get("final_answer")
        result_data["final_answer"] = res.answer
        result_data["success"] = res.success
        result_data["error"] = res.error
        
        print(f"[{q_id}] Execution finished. Success: {res.success}", flush=True)
        print(f"[{q_id}] Final Answer: {res.answer}", flush=True)
        
        # Write to file
        with open("final_verification.jsonl", "a") as f:
            f.write(json.dumps(result_data, ensure_ascii=False) + "\n")
            
    except Exception as e:
        print(f"[{q_id}] Error: {str(e)}", flush=True)
        result_data["error"] = str(e)
        result_data["traceback"] = traceback.format_exc()
        with open("final_verification.jsonl", "a") as f:
            f.write(json.dumps(result_data, ensure_ascii=False) + "\n")

async def main():
    # Clear file
    with open("final_verification.jsonl", "w") as f:
        pass
        
    for q in queries:
        await run_single_query(q)
        print(f"Finished {q['id']}, waiting 5s...", flush=True)
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
