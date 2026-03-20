import asyncio
import json
import logging
import os
import sys
import traceback
import datetime

# Set environment variables
os.environ['JOBLIB_MULTIPROCESSING'] = '0'
os.environ["LOKY_MAX_CPU_COUNT"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
# Disable OpenTelemetry to prevent resource tracker warnings and hangs
os.environ["ENABLE_OPENTELEMETRY"] = "false"
os.environ["OTEL_SDK_DISABLED"] = "true"

sys.path.append(os.path.join(os.getcwd(), 'src'))
sys.path.append(os.getcwd())

from src.unified_research_system import UnifiedResearchSystem, ResearchRequest

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

q = {
    "id": "test_query_1",
    "text": "If my future wife has the same first name as the 15th first lady of the United States' mother and her last name is the same as the 15th president's, what is her name?"
}

def log_debug(msg):
    timestamp = datetime.datetime.now().isoformat()
    with open("debug_trace.log", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[{timestamp}] {msg}", flush=True)

async def main():
    log_debug(f"STARTING {q['id']}")
    system = UnifiedResearchSystem(enable_visualization_server=False)
    system._use_unified_workflow = True
    
    req = ResearchRequest(
        query=q['text'],
        context={
            'deep_reasoning_mode': True,
            'query_complexity': 'very_complex',
            'global_timeout': 1800.0,
            'needs_reasoning_chain': True
        },
        timeout=1800.0
    )
    
    log_debug("Executing research...")
    try:
        res = await system.execute_research(req)
        log_debug("Research execution finished.")
        
        output = {
            "query_id": q['id'],
            "query_text": q['text'],
            "status": "success" if res and res.success else "failed",
            "answer": res.answer if res else None,
            "reasoning": res.reasoning if res else None,
            "error": res.error if res else "Result is None"
        }
        
        # Save results
        abs_path = os.path.abspath("test_query_1_result_v2.json")
        print(f"Saving result to: {abs_path}")
        
        try:
            with open(abs_path, "w", encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            log_debug("File write completed.")
            print(f"Result saved to {abs_path}")
        except Exception as e:
            log_debug(f"Failed to save result: {e}")
            print(f"Failed to save result: {e}")
            
        print("FINISHED V2")
        
    except Exception as e:
        log_debug(f"EXCEPTION: {e}")
        traceback.print_exc()
    finally:
        log_debug("Shutting down system...")
        if 'system' in locals() and system:
            try:
                system.shutdown()
            except Exception as e:
                log_debug(f"Shutdown error: {e}")
        log_debug("Shutdown completed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
        log_debug("Main finished successfully.")
        sys.exit(0)
    except Exception as e:
        log_debug(f"Main wrapper exception: {e}")
        sys.exit(1)
