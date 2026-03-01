"""
Batch Evaluation Script for RANGEN
"""
import asyncio
import json
import time
import os
import sys
from typing import List, Dict, Any
from statistics import mean, median

# Add project root to path
sys.path.append(os.getcwd())

from src.core.context_manager import ContextManager
from src.core.configurable_router import ConfigurableRouter
from src.core.execution_coordinator import ExecutionCoordinator
from src.agents.tools.tool_registry import ToolRegistry
from src.agents.tools.retrieval_tool import RetrievalTool
from src.services.logging_service import get_logger

logger = get_logger("evaluator")

# Sample Dataset if file not found
SAMPLE_DATASET = [
    {"id": "1", "query": "What is the impact of quantum computing on cryptography?", "expected_keywords": ["Shor", "RSA", "encryption"]},
    {"id": "2", "query": "Explain the difference between ReAct and CoT prompting.", "expected_keywords": ["reasoning", "action", "chain of thought"]},
    {"id": "3", "query": "Who won the FIFA World Cup in 2022?", "expected_keywords": ["Argentina", "Messi"]}
]

class Evaluator:
    def __init__(self, dataset_path: str = None):
        self.dataset = self._load_dataset(dataset_path)
        self.coordinator = self._init_system()
        self.results = []

    def _load_dataset(self, path: str) -> List[Dict[str, Any]]:
        if path and os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        logger.warning("Dataset not found, using sample data.")
        return SAMPLE_DATASET

    def _init_system(self) -> ExecutionCoordinator:
        # Initialize system components
        # Note: This relies on .env or default config for LLM/KMS
        # If running in a CI/CD env without keys, ensure LLM_PROVIDER=mock is set
        context_manager = ContextManager()
        router = ConfigurableRouter()
        registry = ToolRegistry()
        
        # Register tools (Mock KMS if needed, or real one)
        # Here we instantiate RetrievalTool which might fail if no config
        try:
            retrieval_tool = RetrievalTool()
            registry.register_tool(retrieval_tool)
        except Exception as e:
            logger.warning(f"RetrievalTool init failed (expected if no DB): {e}")
            
        return ExecutionCoordinator(router, context_manager, registry)

    async def run_eval(self):
        logger.info(f"Starting evaluation on {len(self.dataset)} items...")
        
        for item in self.dataset:
            query = item["query"]
            expected = item.get("expected_keywords", [])
            
            logger.info(f"Processing: {query}")
            start_t = time.time()
            
            try:
                result = await self.coordinator.run_task(query)
                latency = time.time() - start_t
                
                final_answer = result.get("final_answer", "")
                steps = result.get("steps", [])
                
                # Basic specific metric: Keyword Match
                matches = [k for k in expected if k.lower() in final_answer.lower()]
                success = len(matches) > 0 or not expected # Pass if no expectations
                
                self.results.append({
                    "id": item["id"],
                    "query": query,
                    "latency": latency,
                    "success": success,
                    "steps_count": len(steps),
                    "matched_keywords": matches
                })
                
            except Exception as e:
                logger.error(f"Error processing {query}: {e}")
                self.results.append({
                    "id": item["id"],
                    "query": query,
                    "latency": time.time() - start_t,
                    "success": False,
                    "error": str(e)
                })

        self._print_summary()

    def _print_summary(self):
        total = len(self.results)
        successful = len([r for r in self.results if r["success"]])
        latencies = [r["latency"] for r in self.results]
        
        print("\n" + "="*50)
        print("EVALUATION SUMMARY")
        print("="*50)
        print(f"Total Queries: {total}")
        print(f"Success Rate:  {successful}/{total} ({successful/total*100:.1f}%)")
        if latencies:
            print(f"Avg Latency:   {mean(latencies):.2f}s")
            print(f"Median Latency:{median(latencies):.2f}s")
        print("="*50)
        
        # Save detailed results
        os.makedirs("evaluation_results", exist_ok=True)
        output_path = f"evaluation_results/run_{int(time.time())}.json"
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"Detailed results saved to {output_path}")

if __name__ == "__main__":
    # Check if a dataset path argument is provided
    dataset_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    evaluator = Evaluator(dataset_path)
    asyncio.run(evaluator.run_eval())
