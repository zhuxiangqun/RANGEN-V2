"""
Context Summarizer
Handles hierarchical context compression.
"""
from typing import List, Dict
from src.core.llm_integration import LLMIntegration
from src.services.logging_service import get_logger

logger = get_logger(__name__)

class ContextSummarizer:
    """
    Compresses conversation history into summaries.
    """
    
    def __init__(self, llm: LLMIntegration):
        self.llm = llm
        
    async def summarize(self, history: List[Dict]) -> str:
        """
        Generate a concise summary of the conversation history.
        """
        if not history:
            return ""
            
        # Format history for the summarizer
        conversation_text = ""
        for msg in history:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            conversation_text += f"{role}: {content}\n"
            
        prompt = f"""
Please summarize the following conversation history into a single concise paragraph. 
Focus on key facts, decisions, and user preferences. Ignore casual chit-chat.

Conversation:
{conversation_text}

Summary:
"""
        try:
            summary = self.llm._call_llm(prompt) # Using internal method for now
            logger.info(f"Generated context summary: {summary[:50]}...")
            return summary
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return "Error generating summary."
