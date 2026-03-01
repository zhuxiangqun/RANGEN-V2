import asyncio
import json
import os
import sys

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.unified_research_system import UnifiedResearchSystem
from src.core.research_request import ResearchRequest

async def debug_specific_query():
    # Initialize system
    system = UnifiedResearchSystem()
    await system.initialize()
    
    query = "If my future wife has the same first name as the 15th first lady of the United States' mother and her surname is the same as the second assassinated president's mother's maiden name, what is my future wife's name?"
    
    print(f"\n{'='*50}")
    print(f"DEBUGGING QUERY: {query}")
    print(f"{'='*50}\n")
    
    request = ResearchRequest(
        query=query,
        request_id="debug_req_001",
        user_id="debug_user",
        context={
            "depth": "deep",
            "require_reasoning": True,
            "force_complex": True  # Hint to force complex path if applicable
        }
    )
    
    try:
        result = await system.execute_research(request)
        
        print(f"\n{'='*50}")
        print("EXECUTION RESULT")
        print(f"{'='*50}")
        print(f"Success: {result.success}")
        print(f"Answer: {result.answer}")
        print(f"Error: {result.error}")
        
        print(f"\n{'-'*20} Metadata / Trace {'-'*20}")
        metadata = result.metadata or {}
        if metadata:
            print(json.dumps(metadata, indent=2, ensure_ascii=False))
        else:
            print("No metadata returned.")
            
        print(f"\n{'-'*20} Knowledge {'-'*20}")
        for k in result.knowledge:
            print(f"- {k}")
        
        print(f"\n{'='*50}")
        print("STEP-BY-STEP TRACE")
        print(f"{'='*50}\n")

        decomposition = metadata.get("decomposition") if isinstance(metadata, dict) else None
        if isinstance(decomposition, dict):
            original_query = decomposition.get("original_query", "")
            sub_queries = decomposition.get("sub_queries") or []
            print("Decomposition:")
            print(f"  Original query: {original_query}")
            if sub_queries:
                print("  Sub-queries:")
                for i, sq in enumerate(sub_queries):
                    print(f"    [{i+1}] {sq}")
            else:
                print("  No sub-queries found.")
        else:
            print("Decomposition: not available.")

        retrieval_trace = metadata.get("retrieval_trace") if isinstance(metadata, dict) else None
        if isinstance(retrieval_trace, list) and retrieval_trace:
            print("\nRetrieval trace:")
            for i, entry in enumerate(retrieval_trace):
                if not isinstance(entry, dict):
                    print(f"  [{i+1}] {entry}")
                    continue
                sub_q = entry.get("sub_query", "")
                via = entry.get("via", "")
                success = entry.get("success")
                k_cnt = entry.get("knowledge_count")
                e_cnt = entry.get("evidence_count")
                s_cnt = entry.get("source_count")
                error = entry.get("error")
                print(f"  [{i+1}] sub_query: {sub_q}")
                print(f"       via: {via}, success: {success}")
                print(f"       knowledge: {k_cnt}, evidence: {e_cnt}, sources: {s_cnt}")
                if error:
                    print(f"       error: {error}")
        else:
            print("\nRetrieval trace: not available.")

        reasoning_result = metadata.get("reasoning_result") if isinstance(metadata, dict) else None
        reasoning_trace = metadata.get("reasoning_trace") if isinstance(metadata, dict) else None
        if not isinstance(reasoning_trace, list) and isinstance(reasoning_result, dict):
            data = reasoning_result.get("data")
            if isinstance(data, dict) and isinstance(data.get("steps"), list):
                reasoning_trace = data.get("steps")

        if isinstance(reasoning_trace, list) and reasoning_trace:
            print("\nReasoning trace:")
            for i, step in enumerate(reasoning_trace):
                print(f"\n  Step [{i+1}]:")
                if isinstance(step, dict):
                    print(json.dumps(step, indent=2, ensure_ascii=False))
                else:
                    print(step)
        else:
            print("\nReasoning trace: not available.")
            
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_specific_query())
