"""
本地模型信息提取服务
用于开发环境，使用小型本地模型（如 DistilBERT）替代 Google Gemini API
"""
import logging
from typing import Dict, Any, List, Optional
import os

logger = logging.getLogger(__name__)

# 尝试导入 transformers
try:
    from transformers import (
        AutoTokenizer,
        AutoModelForSequenceClassification,
        AutoModelForTokenClassification,
        pipeline
    )
    import torch
    TRANSFORMERS_AVAILABLE = True
except (ImportError, PermissionError, OSError) as e:
    TRANSFORMERS_AVAILABLE = False
    logger.warning(f"transformers/torch not available or permission denied: {e}")
    logger.warning("Skipping multimodal features. Install with: pip install transformers torch")


class LocalModelExtractService:
    """本地模型信息提取服务
    
    使用小型本地模型（如 DistilBERT）进行信息提取，适用于开发环境。
    提供与 LangExtractService 兼容的接口。
    """
    
    def __init__(
        self,
        model_name: str = "distilbert-base-uncased",
        task: str = "ner",  # ner, text-classification, question-answering
        device: Optional[str] = None
    ):
        """初始化本地模型服务
        
        Args:
            model_name: 模型名称（HuggingFace 模型 ID）
                - distilbert-base-uncased: 轻量级 BERT，适合开发
                - bert-base-uncased: 标准 BERT
                - roberta-base: RoBERTa 模型
            task: 任务类型
                - ner: 命名实体识别
                - text-classification: 文本分类
                - question-answering: 问答
            device: 设备（'cpu', 'cuda', None=自动选择）
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "transformers is required for local models. "
                "Install with: pip install transformers torch"
            )
        
        self.model_name = model_name
        self.task = task
        
        # 自动选择设备
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        
        logger.info(f"🔄 [LocalModel] 初始化本地模型: {model_name} (task={task}, device={device})")
        
        # 初始化模型管道
        try:
            self.pipeline = pipeline(
                task=task,
                model=model_name,
                tokenizer=model_name,
                device=0 if device == "cuda" else -1
            )
            logger.info(f"✅ [LocalModel] 模型加载成功: {model_name}")
        except Exception as e:
            logger.error(f"❌ [LocalModel] 模型加载失败: {e}")
            raise
    
    async def extract_from_evidence(
        self,
        evidence: List[Dict[str, Any]],
        schema: Dict[str, Any],
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """从证据中提取结构化信息
        
        Args:
            evidence: 证据列表（格式：{"content": str, "source": str, ...}）
            schema: 提取的 schema 定义
            query: 查询文本（可选，用于上下文）
            
        Returns:
            提取结果：{
                "entities": [...],
                "relationships": [...],
                "sources": [...],
                "confidence": float
            }
        """
        try:
            # 合并证据文本
            evidence_text = "\n\n".join([
                f"[Source: {e.get('source', 'unknown')}]\n{e.get('content', '')}"
                for e in evidence
            ])
            
            # 使用本地模型提取
            if self.task == "ner":
                # 命名实体识别
                entities = self.pipeline(evidence_text)
                
                # 转换为统一格式
                extracted_entities = []
                for entity in entities:
                    if isinstance(entity, dict):
                        extracted_entities.append({
                            "text": entity.get("word", entity.get("entity", "")),
                            "type": entity.get("entity_group", entity.get("label", "UNKNOWN")),
                            "start": entity.get("start", 0),
                            "end": entity.get("end", 0),
                            "confidence": entity.get("score", 0.0)
                        })
                
                return {
                    "entities": extracted_entities,
                    "relationships": [],  # 本地模型通常不支持关系提取
                    "sources": [e.get("source", "unknown") for e in evidence],
                    "confidence": 0.7  # 默认置信度
                }
            
            elif self.task == "text-classification":
                # 文本分类
                result = self.pipeline(evidence_text)
                
                return {
                    "entities": [],
                    "relationships": [],
                    "sources": [e.get("source", "unknown") for e in evidence],
                    "classification": result,
                    "confidence": result.get("score", 0.0) if isinstance(result, dict) else 0.0
                }
            
            else:
                # 其他任务类型
                result = self.pipeline(evidence_text)
                
                return {
                    "entities": [],
                    "relationships": [],
                    "sources": [e.get("source", "unknown") for e in evidence],
                    "raw_result": result,
                    "confidence": 0.7
                }
                
        except Exception as e:
            logger.error(f"❌ [LocalModel] 提取失败: {e}")
            raise
    
    async def extract_answer_with_source(
        self,
        query: str,
        evidence: List[Dict[str, Any]],
        answer_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """提取答案并包含源定位信息
        
        Args:
            query: 查询文本
            evidence: 证据列表
            answer_schema: 答案的 schema（本地模型可能不支持复杂 schema）
            
        Returns:
            答案结果：{
                "answer": str,
                "sources": [...],
                "confidence": float,
                "extracted_entities": [...]
            }
        """
        try:
            # 对于问答任务，使用 question-answering pipeline
            if self.task == "question-answering":
                # 合并证据文本
                context = "\n\n".join([e.get("content", "") for e in evidence])
                
                # 问答提取
                result = self.pipeline(question=query, context=context)
                
                return {
                    "answer": result.get("answer", ""),
                    "sources": [e.get("source", "unknown") for e in evidence],
                    "confidence": result.get("score", 0.0),
                    "extracted_entities": []
                }
            else:
                # 对于其他任务，使用实体提取
                extraction_result = await self.extract_from_evidence(
                    evidence=evidence,
                    schema=answer_schema or {},
                    query=query
                )
                
                # 从实体中提取答案（简单策略：取第一个实体）
                answer = ""
                if extraction_result.get("entities"):
                    answer = extraction_result["entities"][0].get("text", "")
                
                return {
                    "answer": answer,
                    "sources": extraction_result.get("sources", []),
                    "confidence": extraction_result.get("confidence", 0.7),
                    "extracted_entities": extraction_result.get("entities", [])
                }
                
        except Exception as e:
            logger.error(f"❌ [LocalModel] 答案提取失败: {e}")
            raise
    
    async def extract_entities_with_locations(
        self,
        text: str,
        entity_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """提取实体并包含位置信息
        
        Args:
            text: 文本内容
            entity_types: 实体类型列表（本地模型可能不支持过滤）
            
        Returns:
            实体列表：[
                {
                    "text": str,
                    "type": str,
                    "start": int,
                    "end": int,
                    "confidence": float
                },
                ...
            ]
        """
        try:
            if self.task != "ner":
                # 如果不是 NER 任务，切换到 NER
                logger.warning("⚠️ [LocalModel] 当前模型不是 NER 模型，尝试使用 NER pipeline")
                ner_pipeline = pipeline(
                    task="ner",
                    model="distilbert-base-uncased",
                    device=0 if self.device == "cuda" else -1
                )
                entities = ner_pipeline(text)
            else:
                entities = self.pipeline(text)
            
            # 转换为统一格式
            result = []
            for entity in entities:
                if isinstance(entity, dict):
                    entity_type = entity.get("entity_group", entity.get("label", "UNKNOWN"))
                    
                    # 如果指定了实体类型，进行过滤
                    if entity_types and entity_type not in entity_types:
                        continue
                    
                    result.append({
                        "text": entity.get("word", entity.get("entity", "")),
                        "type": entity_type,
                        "start": entity.get("start", 0),
                        "end": entity.get("end", 0),
                        "confidence": entity.get("score", 0.0)
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"❌ [LocalModel] 实体提取失败: {e}")
            return []


class HybridExtractService:
    """混合提取服务
    
    根据环境自动选择使用本地模型（开发）或 LangExtract（生产）
    """
    
    def __init__(
        self,
        use_local_model: Optional[bool] = None,
        local_model_name: str = "distilbert-base-uncased",
        langextract_model: str = "gemini-1.5-pro"
    ):
        """初始化混合服务
        
        Args:
            use_local_model: 是否使用本地模型
                - None: 自动检测（根据 GOOGLE_API_KEY 是否存在）
                - True: 强制使用本地模型
                - False: 强制使用 LangExtract
            local_model_name: 本地模型名称
            langextract_model: LangExtract 模型名称
        """
        # 自动检测模式
        if use_local_model is None:
            use_local_model = os.getenv('GOOGLE_API_KEY') is None
        
        self.use_local_model = use_local_model
        
        if use_local_model:
            logger.info("🔧 [HybridExtract] 使用本地模型模式（开发环境）")
            self.service = LocalModelExtractService(model_name=local_model_name)
        else:
            logger.info("🔧 [HybridExtract] 使用 LangExtract 模式（生产环境）")
            try:
                from src.services.langextract_service import LangExtractService
                self.service = LangExtractService(model_name=langextract_model)
            except Exception as e:
                logger.warning(f"⚠️ [HybridExtract] LangExtract 初始化失败，降级到本地模型: {e}")
                self.service = LocalModelExtractService(model_name=local_model_name)
                self.use_local_model = True
    
    async def extract_from_evidence(
        self,
        evidence: List[Dict[str, Any]],
        schema: Dict[str, Any],
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """从证据中提取结构化信息"""
        return await self.service.extract_from_evidence(evidence, schema, query)
    
    async def extract_answer_with_source(
        self,
        query: str,
        evidence: List[Dict[str, Any]],
        answer_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """提取答案并包含源定位信息"""
        return await self.service.extract_answer_with_source(query, evidence, answer_schema)
    
    async def extract_entities_with_locations(
        self,
        text: str,
        entity_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """提取实体并包含位置信息"""
        return await self.service.extract_entities_with_locations(text, entity_types)

