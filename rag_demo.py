#!/usr/bin/env python3
"""
RANGEN RAG System Demo - 展示知识检索能力
"""
import os
import sys
import json
import time
from typing import List, Dict, Any

# 设置环境变量
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['DEEPSEEK_API_KEY'] = 'sk-0694fb514e114ababb5e0a737a0602a8'
os.environ['LLM_PROVIDER'] = 'deepseek'
sys.path.insert(0, '/Users/apple/workdata/person/zy/RANGEN-main(syu-python)')

class SimpleRAGDemo:
    """简化的 RAG 系统演示"""
    
    def __init__(self):
        self.knowledge_base = self._create_knowledge_base()
        self.embedding_model = self._load_embedding_model()
        self.llm_client = self._create_llm_client()
    
    def _create_knowledge_base(self) -> List[Dict[str, str]]:
        """创建示例知识库"""
        return [
            {
                "id": "1",
                "title": "RANGEN V2 系统架构",
                "content": "RANGEN V2 是一个多智能体研究系统，采用模块化架构。核心组件包括：1) FastAPI 后端 API，2) Streamlit 聊天界面，3) LangGraph 工作流引擎，4) 多智能体协调器，5) 知识检索系统。系统支持 ReAct 推理循环，能够进行复杂的多步骤推理。",
                "category": "architecture"
            },
            {
                "id": "2", 
                "title": "LangGraph 工作流编排",
                "content": "LangGraph 是一个用于构建有状态、多智能体应用程序的库。在 RANGEN 中，LangGraph 负责编排智能体之间的工作流，支持条件分支、循环和并行执行。系统使用 StateGraph 来定义节点和边，实现复杂的推理流程。",
                "category": "workflow"
            },
            {
                "id": "3",
                "title": "多智能体协调机制",
                "content": "RANGEN 包含 14 个智能体组件，分为核心智能体、支持智能体和专门智能体。核心智能体包括推理智能体、验证智能体、引用智能体。支持智能体包括检索工具、上下文管理器、路由器。专门智能体处理特定任务如知识图谱构建。",
                "category": "agents"
            },
            {
                "id": "4",
                "title": "知识检索系统",
                "content": "RANGEN 的知识检索系统使用向量数据库存储和检索信息。支持本地 embedding 模型 all-mpnet-base-v2，也支持 Jina API。系统包含重排序功能，能够提高检索结果的相关性。知识库可以处理文本、图像等多模态数据。",
                "category": "retrieval"
            },
            {
                "id": "5",
                "title": "ReAct 推理引擎",
                "content": "ReAct (Reasoning + Acting) 是一种推理框架，结合了思维链推理和工具使用。RANGEN 的 ReAct 引擎让智能体能够：1) 分析问题，2) 制定推理步骤，3) 执行相应工具，4) 综合结果得出答案。支持多轮推理和自我修正。",
                "category": "reasoning"
            },
            {
                "id": "6",
                "title": "DeepSeek LLM 集成",
                "content": "RANGEN 集成了 DeepSeek LLM，包括 deepseek-reasoner 和 deepseek-chat 模型。deepseek-reasoner 专门用于复杂推理任务，deepseek-chat 用于一般对话。系统支持 API 密钥管理和错误处理，确保稳定的服务。",
                "category": "llm"
            },
            {
                "id": "7",
                "title": "本地模型支持",
                "content": "RANGEN 支持本地模型运行，包括 embedding 模型和 LLM。本地 embedding 模型使用 all-mpnet-base-v2，无需 API 密钥。系统也支持通过 Ollama 运行本地 LLM，如 llama3.2:3b。本地模型提供更好的隐私保护和成本控制。",
                "category": "local_models"
            },
            {
                "id": "8",
                "title": "质量评估机制",
                "content": "RANGEN 包含质量评估节点，对推理结果进行评分。评估标准包括：1) 答案准确性，2) 推理逻辑性，3) 证据充分性，4) 表达清晰度。质量评分低于阈值的回答会被重新推理。",
                "category": "quality"
            }
        ]
    
    def _load_embedding_model(self):
        """加载 embedding 模型"""
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-mpnet-base-v2')
            print("✅ Embedding model loaded successfully")
            return model
        except Exception as e:
            print(f"❌ Failed to load embedding model: {e}")
            return None
    
    def _create_llm_client(self):
        """创建 LLM 客户端"""
        try:
            from src.core.llm_integration import LLMIntegration
            config = {
                'llm_provider': 'deepseek',
                'api_key': os.getenv('DEEPSEEK_API_KEY'),
                'model': 'deepseek-chat'
            }
            client = LLMIntegration(config)
            print("✅ LLM client created successfully")
            return client
        except Exception as e:
            print(f"❌ Failed to create LLM client: {e}")
            return None
    
    def embed_query(self, query: str) -> List[float]:
        """将查询转换为向量"""
        if self.embedding_model:
            return self.embedding_model.encode(query).tolist()
        else:
            # 简单的词频向量作为后备
            words = query.lower().split()
            vocab = set()
            for doc in self.knowledge_base:
                vocab.update(doc['content'].lower().split())
            
            vector = [0.0] * len(vocab)
            for word in words:
                if word in vocab:
                    vector[list(vocab).index(word)] = 1.0
            return vector
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        import math
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def retrieve_documents(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """检索相关文档"""
        print(f"🔍 检索查询: '{query}'")
        
        # 嵌入查询
        query_vector = self.embed_query(query)
        
        # 计算相似度
        scored_docs = []
        for doc in self.knowledge_base:
            doc_vector = self.embed_query(doc['content'])
            similarity = self.cosine_similarity(query_vector, doc_vector)
            scored_docs.append({
                **doc,
                'similarity': similarity
            })
        
        # 排序并返回 top_k
        scored_docs.sort(key=lambda x: x['similarity'], reverse=True)
        return scored_docs[:top_k]
    
    def generate_response(self, query: str, retrieved_docs: List[Dict[str, Any]]) -> str:
        """基于检索结果生成回答"""
        if not self.llm_client:
            # 简单的基于规则的回答
            context = "\n".join([f"- {doc['title']}: {doc['content']}" for doc in retrieved_docs])
            return f"基于检索到的信息：\n{context}\n\n请参考以上信息回答您的问题。"
        
        # 使用 LLM 生成回答
        context = "\n".join([f"文档{i+1}: {doc['title']}\n{doc['content']}" for i, doc in enumerate(retrieved_docs)])
        
        prompt = f"""基于以下检索到的文档信息，请回答用户的问题。请使用文档中的信息，不要编造内容。

用户问题：{query}

检索到的文档：
{context}

请提供准确、简洁的回答："""
        
        try:
            response = self.llm_client._call_llm(prompt, max_tokens=300)
            return response or "抱歉，无法生成回答。"
        except Exception as e:
            print(f"❌ LLM 调用失败: {e}")
            return "抱歉，LLM 服务暂时不可用。"
    
    def process_query(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """处理查询的完整流程"""
        start_time = time.time()
        
        print(f"\n🎯 RAG 系统处理查询")
        print("=" * 50)
        
        # 1. 检索相关文档
        retrieved_docs = self.retrieve_documents(query, top_k)
        
        print(f"\n📚 检索到 {len(retrieved_docs)} 个相关文档:")
        for i, doc in enumerate(retrieved_docs):
            print(f"  {i+1}. {doc['title']} (相似度: {doc['similarity']:.3f})")
        
        # 2. 生成回答
        answer = self.generate_response(query, retrieved_docs)
        
        # 3. 返回结果
        processing_time = time.time() - start_time
        
        return {
            'query': query,
            'answer': answer,
            'retrieved_documents': retrieved_docs,
            'processing_time': processing_time,
            'top_k': top_k
        }

def main():
    """主函数"""
    print("🚀 RANGEN RAG 系统演示")
    print("=" * 50)
    
    # 创建 RAG 系统
    rag = SimpleRAGDemo()
    
    # 测试查询
    test_queries = [
        "RANGEN V2 的主要组件有哪些？",
        "LangGraph 在系统中起什么作用？",
        "系统支持哪些本地模型？",
        "质量评估机制如何工作？"
    ]
    
    for query in test_queries:
        result = rag.process_query(query, top_k=3)
        
        print(f"\n💡 查询结果:")
        print(f"问题: {result['query']}")
        print(f"处理时间: {result['processing_time']:.2f}秒")
        print(f"回答: {result['answer'][:200]}...")
        print("-" * 50)
    
    print("\n✅ RAG 系统演示完成！")

if __name__ == "__main__":
    main()