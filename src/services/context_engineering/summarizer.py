"""
Enhanced Context Summarizer
Handles hierarchical context compression with NLP-enhanced multi-layer summarization.
V3 Feature: LLM+NLP driven hierarchical summarization with keyword extraction.
"""
from typing import List, Dict, Tuple, Optional, Any
from src.core.llm_integration import LLMIntegration
from src.services.logging_service import get_logger
import re
from collections import Counter

logger = get_logger(__name__)

class ContextSummarizer:
    """
    Enhanced Context Summarizer with multi-layer compression.
    V3 Implementation: Combines LLM abstraction, NLP extraction, and hierarchical summarization.
    """
    
    def __init__(self, llm: LLMIntegration):
        self.llm = llm
        self.nlp_available = False
        self._init_nlp()
    
    def _init_nlp(self):
        """Initialize NLP components if available"""
        try:
            # Try to import NLP libraries
            import nltk
            try:
                nltk.data.find('tokenizers/punkt')
                nltk.data.find('corpora/stopwords')
            except LookupError:
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
            
            self.nlp_available = True
            logger.info("NLP components initialized for enhanced summarization")
        except ImportError:
            logger.info("NLTK not available, using basic text processing")
            self.nlp_available = False
    
    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords using NLP if available, otherwise use basic frequency analysis"""
        if not text:
            return []
        
        if self.nlp_available:
            try:
                import nltk
                from nltk.corpus import stopwords
                from nltk.tokenize import word_tokenize
                
                # Tokenize and clean
                tokens = word_tokenize(text.lower())
                stop_words = set(stopwords.words('english'))
                words = [word for word in tokens if word.isalnum() and word not in stop_words]
                
                # Count frequencies
                word_freq = Counter(words)
                return [word for word, _ in word_freq.most_common(max_keywords)]
            except Exception as e:
                logger.debug(f"Keyword extraction failed: {e}")
                # Fallback to basic method
        
        # Basic frequency analysis
        words = re.findall(r'\b\w+\b', text.lower())
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being'}
        filtered = [word for word in words if word not in common_words and len(word) > 2]
        word_freq = Counter(filtered)
        return [word for word, _ in word_freq.most_common(max_keywords)]
    
    def _extractive_summary(self, text: str, max_sentences: int = 3) -> str:
        """Extractive summarization using sentence scoring"""
        if not text:
            return ""
        
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= max_sentences:
            return " ".join(sentences)
        
        # Score sentences by length and keyword presence
        keywords = self._extract_keywords(text, max_keywords=5)
        scored_sentences = []
        
        for i, sentence in enumerate(sentences):
            score = len(sentence.split())  # Length score
            keyword_score = sum(1 for keyword in keywords if keyword in sentence.lower())
            score += keyword_score * 10
            scored_sentences.append((score, i, sentence))
        
        # Select top sentences
        scored_sentences.sort(reverse=True)
        selected_indices = sorted([idx for _, idx, _ in scored_sentences[:max_sentences]])
        selected_sentences = [sentences[idx] for idx in selected_indices]
        
        return " ".join(selected_sentences)
    
    def _format_history(self, history: List[Dict]) -> Dict[str, Any]:
        """Format conversation history into structured data"""
        formatted = {
            "messages": [],
            "user_messages": [],
            "assistant_messages": [],
            "timestamps": []
        }
        
        for msg in history:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", 0)
            
            formatted["messages"].append({"role": role, "content": content})
            
            if role == "user":
                formatted["user_messages"].append(content)
            elif role in ["assistant", "system"]:
                formatted["assistant_messages"].append(content)
            
            formatted["timestamps"].append(timestamp)
        
        return formatted
    
    async def summarize(self, history: List[Dict], level: str = "standard") -> Dict[str, Any]:
        """
        Generate multi-layer summary of conversation history.
        
        Args:
            history: Conversation history
            level: Summary level - "brief", "standard", "detailed"
            
        Returns:
            Dictionary with multi-layer summary
        """
        if not history:
            return {"summary": "", "keywords": [], "extractive": "", "level": level}
        
        # Format history
        formatted_history = self._format_history(history)
        
        # Extract keywords from all user messages
        all_user_text = " ".join(formatted_history["user_messages"])
        keywords = self._extract_keywords(all_user_text)
        
        # Generate extractive summary
        all_text = " ".join([f"{msg['role']}: {msg['content']}" for msg in formatted_history["messages"]])
        extractive_summary = self._extractive_summary(all_text)
        
        # Generate abstractive summary using LLM
        abstractive_summary = await self._generate_abstractive_summary(formatted_history, level)
        
        # Compile multi-layer summary
        result = {
            "summary": abstractive_summary,
            "keywords": keywords[:10],  # Top 10 keywords
            "extractive": extractive_summary,
            "level": level,
            "message_count": len(history),
            "user_message_count": len(formatted_history["user_messages"]),
            "timestamp_range": {
                "start": min(formatted_history["timestamps"]) if formatted_history["timestamps"] else 0,
                "end": max(formatted_history["timestamps"]) if formatted_history["timestamps"] else 0
            }
        }
        
        logger.info(f"Generated multi-layer summary: {len(abstractive_summary)} chars, {len(keywords)} keywords")
        return result
    
    async def _generate_abstractive_summary(self, formatted_history: Dict[str, Any], level: str) -> str:
        """Generate abstractive summary using LLM"""
        conversation_text = ""
        for msg in formatted_history["messages"]:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            conversation_text += f"{role}: {content}\n"
        
        # Adjust prompt based on level
        if level == "brief":
            length_instruction = "one concise sentence"
        elif level == "detailed":
            length_instruction = "a comprehensive paragraph with key details"
        else:  # standard
            length_instruction = "a concise paragraph"
        
        prompt = f"""
Please summarize the following conversation history into {length_instruction}. 
Focus on key facts, decisions, user preferences, and action items. 
Ignore casual chit-chat and focus on substantive content.

Conversation:
{conversation_text}

Summary:
"""
        try:
            summary = self.llm._call_llm(prompt)
            return summary.strip()
        except Exception as e:
            logger.error(f"Abstractive summarization failed: {e}")
            return "Error generating summary."
