
import asyncio
import os
import sys
import logging
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set environment variables for production simulation
os.environ['ENABLE_UNIFIED_WORKFLOW'] = 'true'
os.environ['LANGGRAPH_TRACING'] = 'false'

def print_json(data, label):
    try:
        print(f"\n--- {label} ---")
        if data:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print("(Empty or None)")
    except Exception:
        print(f"\n--- {label} (raw) ---")
        print(data)

async def run_diagnostics():
    logger.info("Starting benchmark diagnostics...")
    
    try:
        from src.unified_research_system import create_unified_research_system, ResearchRequest
        all_results = []
        
        # Initialize system
        logger.info("Initializing UnifiedResearchSystem...")
        system = await create_unified_research_system(enable_visualization_server=False)
        
        if not system._unified_workflow:
            logger.error("UnifiedResearchWorkflow failed to initialize!")
            return False
            
        logger.info("UnifiedResearchSystem initialized successfully.")
        
        # Execute queries
        queries = [
            "If my future wife has the same first name as the 15th first lady of the United States' mother and her surname is the same as the second assassinated president's mother's maiden name, what is my future wife's name?",
            "Imagine there is a building called Bronte tower whose height in feet is the same number as the dewey decimal classification for the Charlotte Bronte book that was published in 1847. Where would this building rank among tallest buildings in New York City, as of August 2024?",
            "How many years earlier would Punxsutawney Phil have to be canonically alive to have made a Groundhog Day prediction in the same state as the US capitol?",
            "As of August 1, 2024, which country were holders of the FIFA World Cup the last time the UEFA Champions League was won by a club from London?"
        ]
        
        for i, query in enumerate(queries, 1):
            logger.info(f"\n{'='*50}")
            logger.info(f"DIAGNOSING QUERY {i}")
            logger.info(f"Query: {query}")
            logger.info(f"{'='*50}")
            
            request = ResearchRequest(query=query)
            # execute_research returns ResearchResult
            result = await system.execute_research(request)
            
            logger.info(f"Success: {result.success}")
            logger.info(f"Answer: {result.answer}")
            
            # Inspect metadata
            metadata = result.metadata or {}
            
            # Check Retrieval
            sources = result.knowledge
            print_json(sources, "RETRIEVED SOURCES")
            
            # Check Reasoning (if available in metadata)
            # In langgraph_agent_nodes.py we save 'reasoning_result' to state['metadata']
            reasoning_result = metadata.get('reasoning_result', {})
            print_json(reasoning_result, "REASONING RESULT")
            
            if not result.answer or "Information not found" in str(result.answer) or result.answer is None:
                logger.warning("Query failed to produce a valid answer.")
                # Gap Analysis
                if sources:
                    logger.info("GAP ANALYSIS: Evidence was retrieved but reasoning failed.")
                    logger.info("Possible causes: Prompt issue, Context length limit, or Logic failure.")
                else:
                    logger.info("GAP ANALYSIS: No evidence retrieved. Retrieval failure.")
            else:
                logger.info("Query successful.")
                
            # Print Reasoning Trace if available
            if reasoning_result and isinstance(reasoning_result, dict):
                output = reasoning_result.get('output', {})
                if output and isinstance(output, dict):
                    trace = output.get('trace')
                    if trace:
                        print(f"\n--- REASONING TRACE ---\n{trace}\n")
                    else:
                        # Try to find steps or thoughts in data
                        data = reasoning_result.get('data', {})
                        if isinstance(data, dict):
                             print_json(data, "REASONING DATA")

            summary = {
                "index": i,
                "query": query,
                "success": result.success,
                "answer": result.answer,
                "knowledge": sources,
                "reasoning_result": reasoning_result,
                "error": result.error,
                "metadata": result.metadata,
            }
            all_results.append(summary)

        output_path = Path(__file__).parent / "benchmark_diagnostics.json"
        try:
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)
            logger.info(f"Diagnostics summary written to {output_path}")
        except Exception as e:
            logger.error(f"Failed to write diagnostics summary: {e}")

    except Exception as e:
        logger.error(f"Diagnostics failed with exception: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    asyncio.run(run_diagnostics())
