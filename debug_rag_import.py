
import sys
import os
import traceback

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

try:
    print("Attempting to import RAGExpert...")
    from src.agents.rag_agent import RAGExpert
    print("RAGExpert imported successfully.")
    
    print("Attempting to instantiate RAGExpert...")
    agent = RAGExpert()
    print("RAGExpert instantiated successfully.")
    
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
