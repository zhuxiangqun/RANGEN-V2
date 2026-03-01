
import logging
import time
import json
from typing import Dict, Any, List, Optional, Tuple
from src.agents.base_agent import AgentResult
from src.services.retrieval_utils import KnowledgeSource

logger = logging.getLogger(__name__)

class KnowledgeRetriever:
    def __init__(self, service_ref):
        self.service = service_ref
        if hasattr(service_ref, 'chunking_retriever'):
            self.chunking_retriever = service_ref.chunking_retriever

    def _is_result_noisy(self, res: Dict[str, Any]) -> bool:
        """检查结果是否为噪声"""
        content = (res.get("content") or res.get("text") or "").lower()
        title = (res.get("entity_name") or res.get("title") or "").lower()
        
        # Blacklist phrases
        blacklist_phrases = [
            "united states the white house",
            "united states argued december",
            "united states's wife",
            "united states capitol (location)",
            "united states capitol",
            "globalpolicy.org",
            "globalpolicy",
        ]
        
        # Filter citations starting with ↑ or ^
        if content.strip().startswith("↑") or content.strip().startswith("^"):
            return True
        
        # Filter short citations
        if len(content) < 200 and ("citation" in content or "retrieved" in content or "archived" in content):
            return True

        for p in blacklist_phrases:
            if p in content or p in title:
                return True
        return False

    async def get_kms_knowledge_single_round(
        self,
        query: str,
        analysis: Dict[str, Any],
        detailed_query_type: str,
        round_num: int = 0,
        use_rerank: bool = True,
        use_llamaindex: bool = True
    ) -> Optional[Dict[str, Any]]:
        """单轮检索 - 重构版"""
        try:
            if not self.service.kms_service:
                return None
            
            top_k = getattr(self.service, 'top_k', 5) or 5
            
            # Log start
            logger.info(f"🔍 [KnowledgeRetriever] Searching for: {query[:50]}...")
            
            # Query KMS
            results = self.service.kms_service.query_knowledge(
                query=query,
                modality="text",
                top_k=top_k * 3, # fetch more for filtering
                similarity_threshold=0.0,
                use_rerank=use_rerank,
                use_graph=False,
                use_llamaindex=use_llamaindex
            )
            
            # Initial filtering
            if results:
                original_len = len(results)
                results = [r for r in results if not self._is_result_noisy(r)]
                if len(results) < original_len:
                    logger.info(f"ℹ️ [KnowledgeRetriever] Filtered {original_len - len(results)} noisy results")

            # Validation (Delegated to service)
            validated_results = []
            if results:
                for res in results:
                    # Use service's validation if available
                    if hasattr(self.service, '_validate_result_multi_dimension'):
                        if self.service._validate_result_multi_dimension(res, query, detailed_query_type):
                            validated_results.append(res)
                    else:
                        validated_results.append(res)

            # Dynamic Chunking (Simplified/Delegated)
            # If chunking retriever exists, use it on long docs
            if validated_results and hasattr(self, 'chunking_retriever') and self.chunking_retriever:
                 try:
                     long_docs = [r for r in validated_results if len(r.get('content', '') or '') > 2000]
                     if long_docs:
                         chunked = self.chunking_retriever.retrieve_with_chunking(query, long_docs, top_k=5)
                         short_docs = [r for r in validated_results if len(r.get('content', '') or '') <= 2000]
                         validated_results = short_docs + chunked
                 except Exception as e:
                     logger.warning(f"Chunking failed: {e}")

            # Final Filtering (CRITICAL STEP)
            validated_results = [r for r in validated_results if not self._is_result_noisy(r)]
            
            # Format results
            return self._format_and_compress_results(validated_results, query, detailed_query_type)

        except Exception as e:
            logger.error(f"KMS retrieval failed in KnowledgeRetriever: {e}", exc_info=True)
            return None

    def _format_and_compress_results(self, results, query, query_type, log_info=None):
        """格式化结果"""
        sources = []
        for r in results:
            sources.append({
                'content': r.get('content', ''),
                'similarity_score': r.get('similarity', 0.0) or r.get('similarity_score', 0.0),
                'source': r.get('source', 'kms'),
                'metadata': r.get('metadata', {})
            })
        
        # Sort by score
        sources.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return {
            'sources': sources[:10], # Limit to 10
            'content': json.dumps(sources[:10], ensure_ascii=False) if sources else "",
            'confidence': sources[0]['similarity_score'] if sources else 0.0,
            'metadata': {}
        }

    def extract_relationship_queries(self, query: str) -> Tuple[str, str]:
        """从关系查询中提取主要实体查询和关系实体查询"""
        try:
            import re
            query_lower = query.lower()
            
            # Simple heuristic implementation
            if "'s mother" in query_lower:
                parts = query_lower.split("'s mother")
                entity = parts[0].strip()
                return (f"Who is {entity}?", query)
            elif "mother of" in query_lower:
                parts = query_lower.split("mother of")
                entity = parts[1].strip()
                return (f"Who is {entity}?", query)
            
            return (query, query)
        except Exception:
            return (query, query)

    async def get_kms_knowledge(self, query: str, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Main entry point for KMS knowledge retrieval"""
        detailed_query_type = analysis.get('query_type', 'general')
        return await self.get_kms_knowledge_single_round(query, analysis, detailed_query_type)

    async def retrieve_from_wiki(self, query: str, analysis: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AgentResult:
        start_time = time.time()
        try:
            data = None
            if hasattr(self.service, "_get_wiki_knowledge"):
                data = self.service._get_wiki_knowledge(query, analysis)
            success = bool(data)
            confidence = 0.0
            if isinstance(data, dict):
                raw_conf = data.get("confidence")
                if raw_conf is not None:
                    try:
                        confidence = float(raw_conf)
                    except Exception:
                        confidence = 0.0
            processing_time = time.time() - start_time
            return AgentResult(
                success=success,
                data=data,
                confidence=confidence,
                processing_time=processing_time,
                metadata={"source": "wiki", "analysis": analysis, "context": context} if context is not None else {"source": "wiki", "analysis": analysis},
                error=None if success else "Wiki知识检索失败或未找到结果"
            )
        except Exception as e:
            processing_time = time.time() - start_time
            logger.warning(f"[KnowledgeRetriever] Wiki retrieval failed: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                confidence=0.0,
                processing_time=processing_time,
                metadata={"source": "wiki", "analysis": analysis, "context": context} if context is not None else {"source": "wiki", "analysis": analysis},
                error=str(e)
            )

    async def retrieve_from_faiss(self, query: str, analysis: Dict[str, Any], *args, **kwargs) -> Optional[Dict[str, Any]]:
        """Retrieve from FAISS (Delegated to service)"""
        if hasattr(self.service, '_get_faiss_knowledge'):
            return await self.service._get_faiss_knowledge(query, analysis)
        return None

    async def retrieve_from_fallback(self, query: str, analysis: Dict[str, Any], *args, **kwargs) -> Optional[Dict[str, Any]]:
        """Retrieve fallback knowledge (Delegated to service)"""
        if hasattr(self.service, '_get_fallback_knowledge'):
            return self.service._get_fallback_knowledge(query, analysis)
        return None
