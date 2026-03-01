
import asyncio
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set environment variables for production simulation
os.environ['ENABLE_UNIFIED_WORKFLOW'] = 'true'
os.environ['LANGGRAPH_TRACING'] = 'true'  # To trigger OpenTelemetry logic if configured

async def simulate_production():
    logger.info("Starting production simulation...")
    
    try:
        from src.unified_research_system import create_unified_research_system, ResearchRequest
        
        # Initialize system
        logger.info("Initializing UnifiedResearchSystem...")
        system = await create_unified_research_system(enable_visualization_server=False)
        
        # Check if unified workflow is initialized
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
        
        all_success = True
        for i, query in enumerate(queries, 1):
            logger.info(f"\n--- Executing Query {i} ---")
            logger.info(f"Query: {query}")
            
            request = ResearchRequest(query=query)
            result = await system.execute_research(request)
            
            logger.info(f"Query {i} execution completed.")
            logger.info(f"Success: {result.success}")
            logger.info(f"Answer: {result.answer}")
            
            if not result.success or not result.answer:
                logger.error(f"Query {i} failed or no answer returned.")
                all_success = False
        
        if all_success:
            logger.info("\nAll production simulation queries passed!")
            return True
        else:
            logger.error("\nSome queries failed.")
            return False
            
    except Exception as e:
        logger.error(f"Production simulation failed with exception: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = asyncio.run(simulate_production())
    sys.exit(0 if success else 1)
