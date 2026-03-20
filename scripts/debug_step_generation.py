
import asyncio
import logging
import os
import sys
from typing import Dict, Any

# Add project root to sys.path
sys.path.append(os.getcwd())

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.core.reasoning.step_generator import StepGenerator
from src.core.reasoning.prompt_generator import PromptGenerator
from src.core.llm_integration import create_llm_integration
from src.utils.unified_context_engineering_center import get_unified_context_engineering_center
from src.core.reasoning.context_manager import ContextManager
from src.core.reasoning.cache_manager import CacheManager
from src.core.reasoning.subquery_processor import SubQueryProcessor
from src.utils.prompt_engine import PromptEngine
from dotenv import load_dotenv

async def main():
    load_dotenv()
    
    # Initialize components
    llm_config = {
        'llm_provider': 'deepseek',
        'api_key': os.getenv('DEEPSEEK_API_KEY', ''),
        'model': os.getenv('DEEPSEEK_MODEL', 'deepseek-reasoner'),
        'base_url': os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
    }
    llm_integration = create_llm_integration(llm_config)
    
    prompt_engine = PromptEngine(llm_integration=llm_integration)
    
    # Register templates (mocking _register_reasoning_templates)
    # Assuming templates are loaded from file or defaults
    
    context_engineering = get_unified_context_engineering_center()
    cache_manager = CacheManager()
    context_manager = ContextManager(context_engineering, cache_manager)
    
    subquery_processor = SubQueryProcessor(
        context_manager=context_manager,
        llm_integration=llm_integration,
        cache_manager=cache_manager
    )
    
    prompt_generator = PromptGenerator(
        prompt_engineering=prompt_engine,
        llm_integration=llm_integration,
        context_manager=context_manager
    )
    
    step_generator = StepGenerator(
        llm_integration=llm_integration,
        prompt_generator=prompt_generator,
        context_manager=context_manager,
        subquery_processor=subquery_processor,
        cache_manager=cache_manager
    )
    
    # Mock LLM to inspect prompt
    original_call_llm = llm_integration.call_llm
    
    def mock_call_llm(prompt, **kwargs):
        print("\n[MOCK LLM] Prompt received:")
        print("-" * 40)
        print(prompt)
        print("-" * 40)
        # Return a valid dummy response to let the flow continue
        return """
{
  "steps": [
    {
      "type": "evidence_gathering",
      "description": "Find the second assassinated president",
      "sub_query": "Who was the second assassinated president of the US?"
    },
    {
      "type": "evidence_gathering",
      "description": "Find the mother of the president",
      "sub_query": "Who was the mother of [step 1 result]?"
    },
    {
      "type": "evidence_gathering",
      "description": "Find the maiden name",
      "sub_query": "What was the maiden name of [step 2 result]?"
    }
  ]
}
"""

    llm_integration.call_llm = mock_call_llm
    # Also mock _call_llm for internal calls if needed
    llm_integration._call_llm = mock_call_llm
    
    query = "What is the maiden name of the second assassinated president's mother?"
    context = {"query": query}
    
    print(f"\nGenerating steps for query: {query}")
    
    try:
        steps = step_generator.execute_reasoning_steps_with_prompts(query, context, query)
        
        print(f"\nGenerated {len(steps)} steps:")
        for i, step in enumerate(steps):
            print(f"Step {i+1}:")
            print(f"  Type: {step.get('type')}")
            print(f"  Description: {step.get('description')}")
            print(f"  Sub-query: {step.get('sub_query')}")
            print(f"  Depends on: {step.get('depends_on')}")
            print("-" * 30)
            
    except Exception as e:
        logger.error(f"Error generating steps: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
