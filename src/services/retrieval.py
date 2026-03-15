"""
统一检索服务模块

合并以下服务:
- KnowledgeRetrievalService (knowledge_retrieval_service.py)
- EnhancedKnowledgeRetrievalService (enhanced_knowledge_retrieval.py)
- KnowledgeRetriever (knowledge_retriever.py)
- CognitiveRetrievalSystem (cognitive_retrieval_system.py)
- DynamicChunkingRetriever (dynamic_chunking_retriever.py)
- FAISSService (faiss_service.py)
- KnowledgeGraphService (knowledge_graph_service.py)

使用示例:
```python
from src.services.retrieval import RetrievalService

retrieval = RetrievalService()
results = retrieval.retrieve("query", top_k=5)
```
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass
import numpy as np


# ============== Enums ==============

class RetrievalMethod(str, Enum):
    """检索方法"""
    SEMANTIC = "semantic"      # 语义检索
    KEYWORD = "keyword"        # 关键词检索
    HYBRID = "hybrid"          # 混合检索
    KNOWLEDGE_GRAPH = "kg"    # 知识图谱
    COGNITIVE = "cognitive"    # 认知检索


class QueryType(str, Enum):
    """查询类型"""
    FACTUAL = "factual"       # 事实查询
    EXPLANATORY = "explanatory"  # 解释性查询
    COMPARISON = "comparison"  # 比较查询
    CAUSAL = "causal"        # 因果查询
    PROCEDURAL = "procedural"  # 过程查询


# ============== Data Classes ==============

@dataclass
class RetrievalChunk:
    """检索块"""
    text: str
    score: float
    source: str
    metadata: Dict[str, Any]


@dataclass
class RetrievalResult:
    """检索结果"""
    query: str
    method: RetrievalMethod
    chunks: List[RetrievalChunk]
    total_found: int
    processing_time: float


@dataclass
class KnowledgeGraphEntity:
    """知识图谱实体"""
    id: str
    name: str
    entity_type: str
    properties: Dict[str, Any]
    embeddings: Optional[np.ndarray] = None


@dataclass
class KnowledgeGraphRelation:
    """知识图谱关系"""
    source: str
    target: str
    relation_type: str
    properties: Dict[str, Any]


# ============== Main Class ==============

class RetrievalService:
    """
    统一检索服务
    
    支持:
    - 语义检索 (Semantic)
    - 关键词检索 (Keyword)
    - 混合检索 (Hybrid)
    - 知识图谱 (Knowledge Graph)
    - 认知检索 (Cognitive)
    - 动态分块 (Dynamic Chunking)
    """
    
    def __init__(self):
        self._index = None
        self._documents: List[str] = []
        self._metadata: List[Dict[str, Any]] = []
        self._kg_entities: Dict[str, KnowledgeGraphEntity] = {}
        self._kg_relations: List[KnowledgeGraphRelation] = []
        self._embeddings: Optional[np.ndarray] = None
    
    # ============== Indexing ==============
    
    def add_documents(
        self,
        documents: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """添加文档到索引"""
        self._documents.extend(documents)
        
        if metadata:
            self._metadata.extend(metadata)
        else:
            self._metadata.extend([{}] * len(documents))
    
    def build_index(self, method: RetrievalMethod = RetrievalMethod.SEMANTIC) -> None:
        """构建索引"""
        if not self._documents:
            return
        
        if method == RetrievalMethod.SEMANTIC:
            # Simple in-memory index (would use FAISS in production)
            self._index = {"type": "semantic", "size": len(self._documents)}
        elif method == RetrievalMethod.KEYWORD:
            # Keyword index
            self._index = {"type": "keyword", "size": len(self._documents)}
        elif method == RetrievalMethod.HYBRID:
            self._index = {"type": "hybrid", "size": len(self._documents)}
    
    def build_faiss_index(self, embeddings: np.ndarray) -> None:
        """构建 FAISS 索引"""
        try:
            import faiss
            dim = embeddings.shape[1]
            self._index = faiss.IndexFlatL2(dim)
            self._index.add(embeddings)
            self._embeddings = embeddings
        except ImportError:
            # Fallback to simple index
            self.build_index(RetrievalMethod.SEMANTIC)
    
    # ============== Retrieval ==============
    
    def retrieve(
        self,
        query: str,
        method: RetrievalMethod = RetrievalMethod.HYBRID,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> RetrievalResult:
        """检索"""
        import time
        start_time = time.time()
        
        if method == RetrievalMethod.SEMANTIC:
            chunks = self._semantic_search(query, top_k)
        elif method == RetrievalMethod.KEYWORD:
            chunks = self._keyword_search(query, top_k)
        elif method == RetrievalMethod.HYBRID:
            chunks = self._hybrid_search(query, top_k)
        elif method == RetrievalMethod.KNOWLEDGE_GRAPH:
            chunks = self._kg_search(query, top_k)
        elif method == RetrievalMethod.COGNITIVE:
            chunks = self._cognitive_search(query, top_k)
        else:
            chunks = self._semantic_search(query, top_k)
        
        # Apply filters
        if filters:
            chunks = [c for c in chunks if self._matches_filter(c, filters)]
        
        return RetrievalResult(
            query=query,
            method=method,
            chunks=chunks[:top_k],
            total_found=len(chunks),
            processing_time=time.time() - start_time
        )
    
    def _semantic_search(self, query: str, top_k: int) -> List[RetrievalChunk]:
        """语义检索"""
        # Simple TF-IDF like scoring (would use embeddings in production)
        results = []
        query_terms = set(query.lower().split())
        
        for i, doc in enumerate(self._documents):
            doc_terms = set(doc.lower().split())
            score = len(query_terms & doc_terms) / max(len(query_terms), 1)
            
            if score > 0:
                results.append(RetrievalChunk(
                    text=doc,
                    score=score,
                    source=f"doc_{i}",
                    metadata=self._metadata[i] if i < len(self._metadata) else {}
                ))
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def _keyword_search(self, query: str, top_k: int) -> List[RetrievalChunk]:
        """关键词检索"""
        results = []
        query_lower = query.lower()
        
        for i, doc in enumerate(self._documents):
            if query_lower in doc.lower():
                score = 1.0
                results.append(RetrievalChunk(
                    text=doc,
                    score=score,
                    source=f"doc_{i}",
                    metadata=self._metadata[i] if i < len(self._metadata) else {}
                ))
        
        return results[:top_k]
    
    def _hybrid_search(self, query: str, top_k: int) -> List[RetrievalChunk]:
        """混合检索 - 结合语义和关键词"""
        semantic = self._semantic_search(query, top_k * 2)
        keyword = self._keyword_search(query, top_k * 2)
        
        # Merge and rerank
        seen = {}
        for chunk in semantic + keyword:
            if chunk.text not in seen:
                seen[chunk.text] = chunk
            else:
                # Update score
                seen[chunk.text].score = max(seen[chunk.text].score, chunk.score)
        
        results = list(seen.values())
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def _kg_search(self, query: str, top_k: int) -> List[RetrievalChunk]:
        """知识图谱检索"""
        # Extract entities from query (simplified)
        query_entities = query.lower().split()
        
        results = []
        
        # Find related entities
        for entity_id, entity in self._kg_entities.items():
            if any(term in entity.name.lower() for term in query_entities):
                # Find relations
                for rel in self._kg_relations:
                    if rel.source == entity_id or rel.target == entity_id:
                        results.append(RetrievalChunk(
                            text=f"{entity.name} {rel.relation_type} ...",
                            score=0.9,
                            source=f"kg:{entity_id}",
                            metadata={"entity": entity.__dict__, "relation": rel.__dict__}
                        ))
        
        return results[:top_k]
    
    def _cognitive_search(self, query: str, top_k: int) -> List[RetrievalChunk]:
        """认知检索 - 多角度检索"""
        results = []
        
        # Multi-perspective retrieval
        perspectives = [
            ("definition", "What is X?"),
            ("example", "For example X"),
            ("comparison", "X vs Y"),
            ("cause", "Why X happens"),
            ("process", "How X works"),
        ]
        
        for perspective, reformulated in perspectives:
            # Reconstruct query
            reconstructed = query + " " + reformulated
            chunks = self._hybrid_search(reconstructed, top_k)
            
            for chunk in chunks:
                chunk.metadata["perspective"] = perspective
                results.append(chunk)
        
        # Deduplicate and rerank
        seen = {}
        for chunk in results:
            if chunk.text not in seen:
                seen[chunk.text] = chunk
            else:
                seen[chunk.text].score = max(seen[chunk.text].score, chunk.score)
        
        results = list(seen.values())
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def _matches_filter(self, chunk: RetrievalChunk, filters: Dict[str, Any]) -> bool:
        """检查是否匹配过滤器"""
        for key, value in filters.items():
            if key in chunk.metadata:
                if chunk.metadata[key] != value:
                    return False
        return True
    
    # ============== Knowledge Graph ==============
    
    def add_entity(
        self,
        id: str,
        name: str,
        entity_type: str,
        properties: Dict[str, Any],
        embeddings: Optional[np.ndarray] = None
    ) -> None:
        """添加实体到知识图谱"""
        entity = KnowledgeGraphEntity(
            id=id,
            name=name,
            entity_type=entity_type,
            properties=properties,
            embeddings=embeddings
        )
        self._kg_entities[id] = entity
    
    def add_relation(
        self,
        source: str,
        target: str,
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """添加关系到知识图谱"""
        relation = KnowledgeGraphRelation(
            source=source,
            target=target,
            relation_type=relation_type,
            properties=properties or {}
        )
        self._kg_relations.append(relation)
    
    def get_related_entities(
        self,
        entity_id: str,
        relation_type: Optional[str] = None,
        depth: int = 1
    ) -> List[KnowledgeGraphEntity]:
        """获取相关实体"""
        if entity_id not in self._kg_entities:
            return []
        
        visited = {entity_id}
        result = []
        queue = [(entity_id, 0)]
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_depth >= depth:
                continue
            
            for rel in self._kg_relations:
                next_id = None
                
                if rel.source == current_id and rel.target not in visited:
                    next_id = rel.target
                elif rel.target == current_id and rel.source not in visited:
                    next_id = rel.source
                
                if next_id and (relation_type is None or rel.relation_type == relation_type):
                    visited.add(next_id)
                    if next_id in self._kg_entities:
                        result.append(self._kg_entities[next_id])
                        queue.append((next_id, current_depth + 1))
        
        return result
    
    # ============== Dynamic Chunking ==============
    
    def dynamic_chunk(
        self,
        text: str,
        chunk_size: int = 512,
        overlap: int = 50
    ) -> List[str]:
        """动态分块"""
        # Simple character-based chunking
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                for punct in ['. ', '! ', '? ', '\n']:
                    last_punct = text[start:end].rfind(punct)
                    if last_punct != -1:
                        end = start + last_punct + 1
                        break
            
            chunks.append(text[start:end])
            start = end - overlap
        
        return chunks
    
    # ============== Summary ==============
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_documents": len(self._documents),
            "index_type": self._index.get("type") if self._index else None,
            "knowledge_graph_entities": len(self._kg_entities),
            "knowledge_graph_relations": len(self._kg_relations),
        }


# ============== Factory ==============

def get_retrieval_service() -> RetrievalService:
    """获取检索服务实例"""
    return RetrievalService()
