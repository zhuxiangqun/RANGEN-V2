#!/usr/bin/env python3
"""
统一的Jina服务 - Embedding和Rerank统一接口
替代所有sentence-transformers的使用，统一使用Jina API
"""
import os
import logging
import time
from typing import Dict, List, Any, Optional, Union
import numpy as np
import requests

logger = logging.getLogger(__name__)


class UnifiedJinaService:
    """统一的Jina服务 - 提供Embedding和Rerank功能"""
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化Jina服务（🚀 优化：从.env文件读取配置）"""
        # 🚀 确保从.env文件加载配置
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass  # python-dotenv未安装，跳过
        
        self.api_key = api_key or os.getenv("JINA_API_KEY")
        self.base_url = os.getenv("JINA_BASE_URL", "https://api.jina.ai")
        self.logger = logging.getLogger(__name__)
        
        # 从环境变量读取模型配置（.env文件已定义）
        self.default_embedding_model = os.getenv("JINA_EMBEDDING_MODEL", "jina-embeddings-v2-base-en")
        self.default_rerank_model = os.getenv("JINA_RERANK_MODEL", "jina-reranker-v2-base-multilingual")
        
        # 统计信息（明确类型为Dict[str, Union[int, float]]）
        self.stats: Dict[str, Union[int, float]] = {
            "embedding_calls": 0,
            "rerank_calls": 0,
            "embedding_success": 0,
            "rerank_success": 0,
            "embedding_errors": 0,
            "rerank_errors": 0
        }
    
    def get_embedding(self, text: str, model: Optional[str] = None) -> Optional[np.ndarray]:
        """获取单个文本的embedding向量
        
        Args:
            text: 输入文本
            model: 模型名称（可选，默认使用JINA_EMBEDDING_MODEL）
            
        Returns:
            embedding向量（numpy数组），失败返回None
        """
        if not self.api_key:
            self.logger.warning("⚠️ JINA_API_KEY未设置，无法使用Jina embedding")
            self.logger.warning("   建议：检查.env文件中的JINA_API_KEY配置")
            return None
        
        if not text or not isinstance(text, str) or len(text.strip()) == 0:
            self.logger.warning("⚠️ 输入文本为空")
            return None
        
        try:
            self.stats["embedding_calls"] += 1
            result = self.get_embeddings([text], model)
            
            if result and len(result) > 0:
                self.stats["embedding_success"] += 1
                return result[0]
            else:
                self.stats["embedding_errors"] += 1
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Embedding失败: {type(e).__name__}: {e}")
            self.stats["embedding_errors"] += 1
            return None
    
    def get_embeddings(self, texts: List[str], model: Optional[str] = None) -> Optional[List[np.ndarray]]:
        """批量获取多个文本的embedding向量
        
        Args:
            texts: 输入文本列表
            model: 模型名称（可选，默认使用JINA_EMBEDDING_MODEL）
            
        Returns:
            embedding向量列表（numpy数组），失败返回None
        """
        if not self.api_key:
            self.logger.warning("⚠️ JINA_API_KEY未设置，无法使用Jina embedding")
            self.logger.warning("   建议：检查.env文件中的JINA_API_KEY配置")
            return None
        
        # 🚀 检查API密钥格式（Jina API密钥通常以"jina_"开头）
        if not self.api_key.startswith("jina_"):
            self.logger.warning(f"⚠️ API密钥格式可能不正确（应以'jina_'开头）")
        
        if not texts or len(texts) == 0:
            self.logger.warning("⚠️ 输入文本列表为空")
            return None
        
        # 🚀 过滤并验证文本：移除空文本，检查长度限制
        # Jina Embeddings v2支持最长8192个字符，但为安全起见，设置为8000
        MAX_TEXT_LENGTH = 8000
        valid_texts = []
        original_indices = []
        
        for i, text in enumerate(texts):
            if not text or not isinstance(text, str):
                self.logger.warning(f"⚠️ 跳过无效文本（索引{i}）: 类型={type(text)}")
                continue
            
            text = text.strip()
            if len(text) == 0:
                self.logger.warning(f"⚠️ 跳过空文本（索引{i}）")
                continue
            
            # 🚀 检查文本长度，超长则截断并警告
            if len(text) > MAX_TEXT_LENGTH:
                self.logger.warning(f"⚠️ 文本过长（{len(text)}字符），截断至{MAX_TEXT_LENGTH}字符（索引{i}）")
                text = text[:MAX_TEXT_LENGTH]
            
            valid_texts.append(text)
            original_indices.append(i)
        
        if len(valid_texts) == 0:
            self.logger.error("❌ 所有文本都被过滤，无法进行embedding")
            return None
        
        if len(valid_texts) != len(texts):
            self.logger.info(f"ℹ️ 过滤后文本数量: {len(valid_texts)}/{len(texts)}")
        
        model = model or self.default_embedding_model
        
        # 🚀 Jina API限制：每次请求最多512个文本项，超过需要分批处理
        MAX_BATCH_SIZE = 512
        all_embeddings = []
        
        # 如果文本数量超过限制，分批处理
        if len(valid_texts) > MAX_BATCH_SIZE:
            self.logger.info(f"ℹ️ 文本数量({len(valid_texts)})超过Jina API限制({MAX_BATCH_SIZE})，将分批处理")
            total_batches = (len(valid_texts) + MAX_BATCH_SIZE - 1) // MAX_BATCH_SIZE
            
            for batch_idx in range(total_batches):
                start_idx = batch_idx * MAX_BATCH_SIZE
                end_idx = min(start_idx + MAX_BATCH_SIZE, len(valid_texts))
                batch_texts = valid_texts[start_idx:end_idx]
                
                self.logger.debug(f"📦 处理批次 {batch_idx + 1}/{total_batches}: 文本数量={len(batch_texts)}")
                
                # 递归调用处理单个批次
                batch_embeddings = self._get_embeddings_single_batch(batch_texts, model)
                
                if batch_embeddings is None:
                    self.logger.error(f"❌ 批次 {batch_idx + 1} 处理失败")
                    return None
                
                all_embeddings.extend(batch_embeddings)
        else:
            # 文本数量在限制内，直接处理
            all_embeddings = self._get_embeddings_single_batch(valid_texts, model)
            if all_embeddings is None:
                return None
        
        # 🚀 如果有文本被过滤，需要扩展embeddings列表以匹配原始输入
        if len(valid_texts) < len(texts):
            # 为被过滤的文本位置插入None或零向量
            full_embeddings = [None] * len(texts)
            for orig_idx, emb in zip(original_indices, all_embeddings):
                full_embeddings[orig_idx] = emb
            return [e for e in full_embeddings if e is not None] if any(e is not None for e in full_embeddings) else None
        
        return all_embeddings if all_embeddings else None
    
    def _get_embeddings_single_batch(self, texts: List[str], model: str) -> Optional[List[np.ndarray]]:
        """处理单个批次的embedding请求（内部方法，不验证输入）
        
        Args:
            texts: 输入文本列表（已验证，数量不超过512）
            model: 模型名称
            
        Returns:
            embedding向量列表（numpy数组），失败返回None
        """
        try:
            url = f"{self.base_url}/v1/embeddings"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "input": texts
            }
            
            # 🚀 记录请求详情（不记录完整文本，只记录元数据）
            self.logger.debug(f"📤 Jina Embedding请求: 模型={model}, 文本数量={len(texts)}, URL={url}")
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            # 🚀 改进的错误处理：获取详细的错误信息
            # 先检查状态码，如果失败则记录详细信息并抛出异常
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    if isinstance(error_data, dict):
                        error_detail = error_data.get("detail", error_data.get("message", str(error_data)))
                        error_msg = f"{error_msg}: {error_detail}"
                    else:
                        error_msg = f"{error_msg}: {response.text[:200]}"  # 限制错误信息长度
                except Exception:
                    error_msg = f"{error_msg}: {response.text[:200]}"
                
                self.logger.error(f"❌ Jina Embedding API请求失败: {error_msg}")
                # 🚀 优化：添加配置检查建议
                if response.status_code == 401:
                    self.logger.error("   建议：检查.env文件中的JINA_API_KEY配置是否正确")
                elif response.status_code == 404:
                    self.logger.error("   建议：检查.env文件中的JINA_BASE_URL配置，应为 'https://api.jina.ai'")
                self.logger.debug(f"   请求URL: {url}")
                self.logger.debug(f"   请求模型: {model}")
                self.logger.debug(f"   文本数量: {len(texts)}")
                if len(texts) > 0:
                    self.logger.debug(f"   第一个文本预览: {texts[0][:100]}...")
                self.logger.debug(f"   响应状态: {response.status_code}")
                
                # 抛出HTTPError以便异常处理块捕获
                try:
                    response.raise_for_status()
                except requests.exceptions.HTTPError:
                    # 重新抛出，让except块处理
                    raise
            
            data = response.json()
            embeddings = []
            
            for item in data.get("data", []):
                emb = item.get("embedding")
                if emb:
                    embeddings.append(np.array(emb, dtype=np.float32))
            
            if len(embeddings) != len(texts):
                self.logger.warning(f"⚠️ 返回的embedding数量({len(embeddings)})与输入文本数量({len(texts)})不匹配")
            
            return embeddings if embeddings else None
            
        except requests.exceptions.HTTPError as e:
            # HTTP错误（包括422）
            error_detail = str(e)
            try:
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_data = e.response.json()
                        if isinstance(error_data, dict):
                            error_detail = error_data.get("detail", error_data.get("message", str(error_data)))
                    except (ValueError, AttributeError):
                        # 如果不是JSON格式，使用响应文本
                        error_detail = f"{e.response.status_code}: {e.response.text[:200]}"
            except Exception:
                pass
            
            self.logger.error(f"❌ Jina Embedding API HTTP错误: {error_detail}")
            # 🚀 优化：添加配置检查建议
            if "401" in error_detail or "Unauthorized" in error_detail:
                self.logger.error("   建议：检查.env文件中的JINA_API_KEY配置是否正确")
            elif "404" in error_detail:
                self.logger.error("   建议：检查.env文件中的JINA_BASE_URL配置，应为 'https://api.jina.ai'")
            self.logger.debug(f"   请求模型: {model}")
            self.logger.debug(f"   文本数量: {len(texts)}")
            if len(texts) > 0:
                self.logger.debug(f"   第一个文本长度: {len(texts[0])}字符")
            self.stats["embedding_errors"] += 1
            return None
        except requests.exceptions.RequestException as e:
            # 网络错误、超时等
            self.logger.error(f"❌ Jina Embedding API请求失败: {type(e).__name__}: {e}")
            self.stats["embedding_errors"] += 1
            return None
        except Exception as e:
            self.logger.error(f"❌ Embedding处理失败: {type(e).__name__}: {e}", exc_info=True)
            self.stats["embedding_errors"] += 1
            return None
    
    def rerank(self, query: str, documents: List[str], 
               model: Optional[str] = None, 
               top_n: Optional[int] = None) -> Optional[List[Dict[str, Any]]]:
        """对文档列表进行重排序
        
        Args:
            query: 查询文本
            documents: 文档列表
            model: 模型名称（可选，默认使用JINA_RERANK_MODEL）
            top_n: 返回前N个结果（可选）
            
        Returns:
            重排序后的结果列表，每个元素包含index和score，失败返回None
        """
        if not self.api_key:
            self.logger.warning("⚠️ JINA_API_KEY未设置，无法使用Jina rerank")
            self.logger.warning("   建议：检查.env文件中的JINA_API_KEY配置")
            return None
        
        if not query or not documents or len(documents) == 0:
            self.logger.warning("⚠️ 查询或文档列表为空")
            return None
        
        model = model or self.default_rerank_model
        
        try:
            self.stats["rerank_calls"] += 1
            
            url = f"{self.base_url}/v1/rerank"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "query": query,
                "documents": documents,
                "top_n": top_n or len(documents)
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            self.stats["rerank_success"] += 1
            return results
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Jina Rerank API请求失败: {e}")
            self.stats["rerank_errors"] += 1
            return None
        except Exception as e:
            self.logger.error(f"❌ Rerank处理失败: {e}")
            self.stats["rerank_errors"] += 1
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        
        # 计算成功率
        if stats["embedding_calls"] > 0:
            stats["embedding_success_rate"] = stats["embedding_success"] / stats["embedding_calls"]
        else:
            stats["embedding_success_rate"] = 0.0
        
        if stats["rerank_calls"] > 0:
            stats["rerank_success_rate"] = stats["rerank_success"] / stats["rerank_calls"]
        else:
            stats["rerank_success_rate"] = 0.0
        
        return stats


# 全局单例实例
_jina_service_instance: Optional[UnifiedJinaService] = None


def get_jina_service() -> UnifiedJinaService:
    """获取全局Jina服务实例（单例模式）"""
    global _jina_service_instance
    if _jina_service_instance is None:
        _jina_service_instance = UnifiedJinaService()
    return _jina_service_instance

