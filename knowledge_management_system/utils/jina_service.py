#!/usr/bin/env python3
"""
统一的Jina服务 - 供知识库管理系统使用
提供Embedding和Rerank功能，统一使用Jina API
"""

import os
import requests
import hashlib
import json
from typing import Dict, List, Any, Optional, Union
import numpy as np
from pathlib import Path
import time
from requests.adapters import HTTPAdapter
from concurrent.futures import ThreadPoolExecutor, as_completed

# 导入Retry类（兼容不同版本）
try:
    from urllib3.util.retry import Retry
except ImportError:
    try:
        # 兼容旧版本的 requests
        from requests.packages.urllib3.util.retry import Retry  # type: ignore
    except ImportError:
        # 如果都失败，使用None（但会导致重试功能不可用）
        Retry = None  # type: ignore

from ..utils.logger import get_logger

logger = get_logger()

# 🆕 尝试导入sentence-transformers的CrossEncoder（本地rerank模型）
CROSS_ENCODER_AVAILABLE = False
try:
    # 延迟导入，避免在模块级别触发keras兼容性问题
    def _import_cross_encoder():
        from sentence_transformers import CrossEncoder
        return CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
    logger.debug("sentence-transformers可用，本地rerank模型可以使用")
except ImportError:
    logger.debug("sentence-transformers未安装，本地rerank模型不可用")
except Exception as e:
    logger.debug(f"sentence-transformers导入异常: {e}，本地rerank模型不可用")

# 🚀 加载 .env 文件（如果存在）
def _load_env_file():
    """从项目根目录加载 .env 文件"""
    try:
        from dotenv import load_dotenv
        # 查找项目根目录（向上查找包含 .env 文件的目录）
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent  # knowledge_management_system -> parent -> parent
        
        env_path = project_root / '.env'
        if env_path.exists():
            load_dotenv(env_path, override=False)  # override=False 表示不覆盖已存在的环境变量
            logger.debug(f"✅ 已从 .env 文件加载环境变量: {env_path}")
        else:
            # 如果没有找到，尝试在当前目录查找
            env_path = Path.cwd() / '.env'
            if env_path.exists():
                load_dotenv(env_path, override=False)
                logger.debug(f"✅ 已从当前目录 .env 文件加载环境变量: {env_path}")
    except ImportError:
        # python-dotenv 未安装，跳过
        pass
    except Exception as e:
        logger.debug(f"加载 .env 文件失败: {e}")

# 在模块导入时自动加载 .env 文件
_load_env_file()


class JinaService:
    """统一的Jina服务 - 提供Embedding和Rerank功能（知识库管理系统专用）"""
    
    def __init__(self):
        """初始化Jina服务"""
        # 🚀 优先级：.env文件 > 环境变量 > 配置文件（保持独立性）
        # 注意：.env 文件已在模块导入时加载
        self.api_key = os.getenv("JINA_API_KEY")
        
        # 如果没有从环境变量获取，尝试从独立配置文件读取
        if not self.api_key:
            try:
                import json
                # 🚀 修复：Path已在文件顶部导入，不需要重复导入
                config_path = Path(__file__).parent.parent / "config" / "system_config.json"
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        if "api_keys" in config and "jina" in config["api_keys"]:
                            self.api_key = config["api_keys"]["jina"]
            except Exception:
                pass  # 忽略配置文件读取错误
        
        self.base_url = os.getenv("JINA_BASE_URL", "https://api.jina.ai")
        self.logger = logger
        
        # 从环境变量读取模型配置
        self.default_embedding_model = os.getenv("JINA_EMBEDDING_MODEL", "jina-embeddings-v2-base-en")
        self.default_rerank_model = os.getenv("JINA_RERANK_MODEL", "jina-reranker-v2-base-multilingual")
        
        # 🆕 本地rerank模型（免费替代方案）
        self.local_rerank_model = None
        self.use_local_rerank = False
        
        # 🆕 优先使用本地rerank模型（完全免费，无需API密钥）
        # 尝试加载本地rerank模型
        if CROSS_ENCODER_AVAILABLE:
            try:
                # 使用环境变量指定模型，默认使用ms-marco-MiniLM-L-6-v2（速度快，精度好）
                local_rerank_model_name = os.getenv("LOCAL_RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
                
                # 🆕 尝试使用镜像源（如果网络有问题）
                hf_endpoint = os.getenv("HF_ENDPOINT")
                if not hf_endpoint:
                    # 默认使用镜像源，提高下载成功率
                    os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
                    logger.debug("使用HuggingFace镜像源: https://hf-mirror.com")
                
                logger.info(f"🔄 正在加载本地rerank模型: {local_rerank_model_name}...")
                # 🆕 优先尝试从本地缓存加载（避免网络连接）
                try:
                    # 首先尝试只使用本地文件（如果模型已下载）
                    # 🚀 修复：添加device参数，避免meta tensor错误
                    import torch
                    device = 'cpu'
                    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                        device = 'mps'
                    elif torch.cuda.is_available():
                        device = 'cuda'
                    
                    CrossEncoderClass = _import_cross_encoder()
                    self.local_rerank_model = CrossEncoderClass(
                        local_rerank_model_name,
                        local_files_only=True,
                        device=device  # 🚀 修复：明确指定设备，避免meta tensor错误
                    )
                    self.use_local_rerank = True
                    logger.info(f"✅ 已从本地缓存加载rerank模型: {local_rerank_model_name} "
                              f"(设备: {device})")
                except Exception as local_error:
                    # 如果本地加载失败，尝试网络下载（使用镜像源）
                    logger.debug(f"本地缓存加载失败，尝试网络下载: {local_error}")
                    # 🚀 修复：如果本地加载失败，可能是模型文件损坏
                    # 先清理缓存再重新下载
                    if "meta tensor" in str(local_error).lower() or "cannot copy" in str(local_error).lower():
                        logger.warning("⚠️ 检测到meta tensor错误，可能是模型文件损坏，建议清理缓存后重新下载")
                        cache_path = f"~/.cache/huggingface/hub/models--{local_rerank_model_name.replace('/', '--')}"
                        logger.warning(f"💡 清理命令: rm -rf {cache_path}")
                    
                    import torch
                    device = 'cpu'
                    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                        device = 'mps'
                    elif torch.cuda.is_available():
                        device = 'cuda'
                    
                    CrossEncoderClass = _import_cross_encoder()
                    self.local_rerank_model = CrossEncoderClass(
                        local_rerank_model_name,
                        local_files_only=False,
                        device=device  # 🚀 修复：明确指定设备，避免meta tensor错误
                    )
                    self.use_local_rerank = True
                    logger.info(f"✅ 已从网络加载rerank模型: {local_rerank_model_name} (设备: {device})")
                logger.info("💡 提示: 本地rerank模型完全免费，优先使用本地模型")
                if self.api_key:
                    msg = "ℹ️  Jina Rerank API已配置，但优先使用本地模型"
                    msg += "（如需使用Jina API，请设置环境变量 USE_JINA_RERANK_API=true）"
                    logger.info(msg)
            except Exception as e:
                logger.warning(f"⚠️ 加载本地rerank模型失败: {e}")
                logger.warning("💡 提示: 可以运行 scripts/download_local_model.py 手动下载模型")
                logger.warning("💡 提示: 或安装本地模型: pip install sentence-transformers")
                self.local_rerank_model = None
                self.use_local_rerank = False
        else:
            logger.warning("⚠️ sentence-transformers未安装，无法使用本地rerank模型")
            logger.warning("💡 提示: 安装本地模型: pip install sentence-transformers")
            self.local_rerank_model = None
            self.use_local_rerank = False
        
        # 如果本地rerank模型加载失败且没有Jina API，记录警告
        if not self.local_rerank_model and not self.api_key:
            warning_msg = "⚠️ 本地rerank模型加载失败且JINA_API_KEY未设置，rerank功能可能不可用"
            logger.warning(warning_msg)
        
        # 🚀 阶段3优化：改进重试策略
        # 🆕 优化：启用重试机制（默认3次），使用指数退避策略
        self.max_retries = int(os.getenv("JINA_MAX_RETRIES", "3"))  # 默认重试3次
        self.retry_delay = float(os.getenv("JINA_RETRY_DELAY", "1.0"))  # 初始延迟（秒）
        # 🚀 阶段3优化：增加超时时间到120秒，适应长文本向量化和网络不稳定的需求
        # 增加超时时间（从90秒增加到120秒）
        self.request_timeout = int(os.getenv("JINA_REQUEST_TIMEOUT", "120"))
        
        # 🚀 创建HTTP会话
        # 🆕 优化：如果禁用重试（max_retries=0），HTTPAdapter也显式设置为不重试
        self.session = requests.Session()
        if Retry is not None and self.max_retries > 0:
            retry_strategy = Retry(
                total=self.max_retries,
                backoff_factor=self.retry_delay,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["POST"],  # 只重试POST请求
                respect_retry_after_header=True
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self.session.mount("https://", adapter)
            self.session.mount("http://", adapter)
        elif Retry is None:
            self.logger.warning("⚠️ Retry类不可用，HTTP重试功能将被禁用")
            # 即使 Retry 不可用，也要显式禁用 HTTPAdapter 的重试
            adapter = HTTPAdapter(max_retries=0)
            self.session.mount("https://", adapter)
            self.session.mount("http://", adapter)
        else:
            # max_retries=0，显式禁用 HTTPAdapter 的重试
            # 🆕 重要：必须显式设置 max_retries=0，否则 HTTPAdapter 会使用默认重试策略
            adapter = HTTPAdapter(max_retries=0)
            self.session.mount("https://", adapter)
            self.session.mount("http://", adapter)
            self.logger.debug("ℹ️ 已禁用HTTP重试（max_retries=0）")
        
        # 统计信息
        self.stats: Dict[str, Union[int, float]] = {
            "embedding_calls": 0,
            "rerank_calls": 0,
            "embedding_success": 0,
            "rerank_success": 0,
            "embedding_errors": 0,
            "rerank_errors": 0,
            "embedding_retries": 0,
            "rerank_retries": 0
        }
        
        # 🚀 性能优化：查询Embedding缓存（避免重复调用Jina API）
        self._embedding_cache: Dict[str, Dict[str, Any]] = {}  # 内存缓存
        # 🚀 方案5.3：支持环境变量配置TTL
        # 默认24小时，可通过环境变量配置
        self._embedding_cache_ttl = int(os.getenv('EMBEDDING_CACHE_TTL', '86400'))
        self._embedding_cache_path = Path("data/learning/kms_embedding_cache.json")  # 持久化缓存路径
        self._embedding_cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._embedding_cache_hits = 0  # 缓存命中次数
        self._embedding_cache_misses = 0  # 缓存未命中次数
        self._embedding_cache_save_counter = 0  # 缓存保存计数器
        
        # 🚀 性能优化：加载持久化embedding缓存
        self._load_embedding_cache()
        
        # 🚀 性能优化：注册程序退出时保存缓存
        import atexit
        atexit.register(self._save_embedding_cache)
        
        if not self.api_key:
            self.logger.warning("⚠️ JINA_API_KEY未设置，Jina服务功能可能不可用")
    
    def get_embedding(self, text: str, model: Optional[str] = None) -> Optional[np.ndarray]:
        """
        获取单个文本的embedding向量（🚀 优化：带缓存）
        
        Args:
            text: 输入文本
            model: 模型名称（可选，默认使用JINA_EMBEDDING_MODEL）
            
        Returns:
            embedding向量（numpy数组），失败返回None
        """
        if not self.api_key:
            self.logger.warning("⚠️ JINA_API_KEY未设置，无法使用Jina embedding")
            return None
        
        if not text or not isinstance(text, str) or len(text.strip()) == 0:
            self.logger.warning("⚠️ 输入文本为空")
            return None
        
        model = model or self.default_embedding_model
        
        # 🚀 性能优化：检查embedding缓存
        cache_key = self._get_cache_key(text, model)
        current_time = time.time()
        
        # 检查内存缓存
        if cache_key in self._embedding_cache:
            cached = self._embedding_cache[cache_key]
            cache_time = cached.get('timestamp', 0)
            cache_age = current_time - cache_time
            
            # 检查缓存是否过期
            if cache_age < self._embedding_cache_ttl:
                self._embedding_cache_hits += 1
                # 转换为numpy数组并返回
                embedding_array = np.array(cached['embedding'], dtype=np.float32)
                
                # 🚀 P0优化：记录缓存命中（使用log_info提升日志级别，便于验证缓存机制）
                try:
                    from src.utils.research_logger import log_info
                    # 记录前20次缓存命中，之后每10次记录一次
                    if self._embedding_cache_hits <= 20 or self._embedding_cache_hits % 10 == 0:
                        text_preview = text[:50] + "..." if len(text) > 50 else text
                        cache_age_hours = cache_age / 3600
                        log_info(f"✅ KMS Embedding缓存命中 #{self._embedding_cache_hits}: "
                                f"文本='{text_preview}', 缓存年龄={cache_age_hours:.2f}小时")
                except ImportError:
                    if self._embedding_cache_hits <= 20 or self._embedding_cache_hits % 10 == 0:
                        text_snippet = text[:50] + "..." if len(text) > 50 else text
                        cache_age_h = cache_age / 3600
                        self.logger.info(f"✅ KMS Embedding缓存命中 #{self._embedding_cache_hits}: "
                                       f"文本='{text_snippet}', 缓存年龄={cache_age_h:.2f}小时")
                
                # 每10次命中记录一次统计
                if self._embedding_cache_hits % 10 == 0:
                    total_calls = self._embedding_cache_hits + self._embedding_cache_misses
                    if total_calls > 0:
                        hit_rate = (self._embedding_cache_hits / total_calls) * 100
                        try:
                            from src.utils.research_logger import log_info
                            cache_stats = (f"命中率={hit_rate:.1f}% "
                                          f"(命中={self._embedding_cache_hits}, "
                                          f"未命中={self._embedding_cache_misses})")
                            log_info(f"📊 KMS Embedding缓存统计: {cache_stats}")
                        except ImportError:
                            stats = (f"命中率={hit_rate:.1f}% "
                                    f"(命中={self._embedding_cache_hits}, "
                                    f"未命中={self._embedding_cache_misses})")
                            self.logger.info(f"📊 KMS Embedding缓存统计: {stats}")
                
                return embedding_array
            else:
                # 缓存过期，删除
                text_preview = text[:50] + "..." if len(text) > 50 else text
                cache_age_h = cache_age / 3600
                self.logger.debug(f"⏰ KMS Embedding缓存过期: 文本='{text_preview}', "
                                f"缓存年龄={cache_age_h:.2f}小时")
                del self._embedding_cache[cache_key]
        
        # 缓存未命中，调用Jina API
        self._embedding_cache_misses += 1
        embedding_start_time = time.time()
        
        # 🚀 性能监控：记录缓存未命中（前10次）
        if self._embedding_cache_misses <= 10:
            try:
                from src.utils.research_logger import log_info
                log_info(f"❌ KMS Embedding缓存未命中: 文本='{text[:50]}...'")
            except ImportError:
                self.logger.info(f"❌ KMS Embedding缓存未命中: 文本='{text[:50]}...'")
        
        try:
            self.stats["embedding_calls"] += 1
            
            # 对于超长文本，使用分块向量化
            MAX_TEXT_LENGTH = 8000
            if len(text) > MAX_TEXT_LENGTH:
                embedding = self._get_embedding_for_long_text(text, model, MAX_TEXT_LENGTH)
            else:
                result = self.get_embeddings([text], model)
                embedding = result[0] if result and len(result) > 0 else None
            
            if embedding is not None:
                embedding_time = time.time() - embedding_start_time
                
                # 🚀 性能监控：记录Jina API调用时间（超过5秒的警告）
                if embedding_time > 5.0:
                    text_snippet = text[:50] + "..." if len(text) > 50 else text
                    self.logger.warning(f"⚠️ KMS Jina Embedding调用耗时: {embedding_time:.2f}秒 "
                                      f"(文本='{text_snippet}')")
                elif self._embedding_cache_misses <= 10:
                    text_preview = text[:50] + "..." if len(text) > 50 else text
                    self.logger.debug(f"🔍 KMS Jina Embedding调用: {embedding_time:.2f}秒 "
                                    f"(文本='{text_preview}')")
                
                # 保存到缓存
                self._embedding_cache[cache_key] = {
                    'embedding': embedding.tolist(),  # 转换为列表以便JSON序列化
                    'timestamp': current_time,
                    'text_preview': text[:100],  # 保存文本预览用于调试
                    'model': model
                }
                
                # 🚀 性能优化：定期保存缓存（每10次调用保存一次）
                self._embedding_cache_save_counter += 1
                if self._embedding_cache_save_counter >= 10:
                    self._save_embedding_cache()
                    self._embedding_cache_save_counter = 0
                
                self.stats["embedding_success"] += 1
                return embedding
            else:
                self.stats["embedding_errors"] += 1
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Embedding失败: {type(e).__name__}: {e}")
            self.stats["embedding_errors"] += 1
            return None
    
    def get_embeddings(self, texts: List[str], model: Optional[str] = None) -> Optional[List[np.ndarray]]:
        """
        批量获取多个文本的embedding向量
        
        Args:
            texts: 输入文本列表
            model: 模型名称（可选，默认使用JINA_EMBEDDING_MODEL）
            
        Returns:
            embedding向量列表（numpy数组），失败返回None
        """
        if not self.api_key:
            self.logger.warning("⚠️ JINA_API_KEY未设置，无法使用Jina embedding")
            return None
        
        if not texts or len(texts) == 0:
            self.logger.warning("⚠️ 输入文本列表为空")
            return None
        
        # 过滤并验证文本
        # 🚀 性能优化：提高单次API调用的最大文本长度，减少分块处理
        # 从8000提高到12000，与批量处理的阈值保持一致，减少不必要的分块
        MAX_TEXT_LENGTH = 12000
        valid_texts = []
        original_indices = []
        
        for i, text in enumerate(texts):
            if not text or not isinstance(text, str):
                continue
            
            text = text.strip()
            if len(text) == 0:
                continue
            
            # 对于超长文本，标记需要特殊处理
            if len(text) > MAX_TEXT_LENGTH:
                # 超长文本将在后续处理中使用分块向量化
                # 先不加入valid_texts，稍后单独处理
                valid_texts.append(None)  # 占位符
                original_indices.append(i)
            else:
                valid_texts.append(text)
                original_indices.append(i)
        
        if len(valid_texts) == 0:
            self.logger.error("❌ 所有文本都被过滤，无法进行embedding")
            return None
        
        model = model or self.default_embedding_model
        
        # 分离正常文本和超长文本
        normal_texts = []
        long_text_indices = []  # 记录超长文本的原始索引和文本
        normal_text_indices = []
        
        for i, (orig_idx, text) in enumerate(zip(original_indices, valid_texts)):
            if text is None:
                # 这是超长文本，需要分块处理
                long_text_indices.append((orig_idx, texts[orig_idx]))
            else:
                normal_texts.append(text)
                normal_text_indices.append((i, orig_idx))
        
        # 🚀 性能优化：先检查缓存，只对未缓存的文本调用API
        cached_embeddings = {}  # 原始索引 -> embedding（从缓存获取）
        uncached_texts = []  # 未缓存的文本
        uncached_indices = []  # 未缓存文本的原始索引和文本
        
        if normal_texts:
            current_time = time.time()
            for (valid_idx, orig_idx), text in zip(normal_text_indices, normal_texts):
                cache_key = self._get_cache_key(text, model)
                
                # 检查缓存
                if cache_key in self._embedding_cache:
                    cached = self._embedding_cache[cache_key]
                    cache_time = cached.get('timestamp', 0)
                    if current_time - cache_time < self._embedding_cache_ttl:
                        # 缓存命中
                        cached_embeddings[orig_idx] = np.array(cached['embedding'], dtype=np.float32)
                        self._embedding_cache_hits += 1
                        continue
                
                # 缓存未命中，需要调用API
                uncached_texts.append(text)
                uncached_indices.append((valid_idx, orig_idx))
        
        # 处理正常文本（只处理未缓存的）
        all_embeddings_dict = cached_embeddings.copy()  # 先添加缓存的embedding
        
        if uncached_texts:
            # Jina API限制：每次请求最多512个文本项
            MAX_BATCH_SIZE = 512
            
            if len(uncached_texts) > MAX_BATCH_SIZE:
                uncached_count = len(uncached_texts)
                self.logger.info(f"ℹ️ 未缓存文本数量({uncached_count})超过Jina API限制({MAX_BATCH_SIZE})，将分批处理")
                total_batches = (len(uncached_texts) + MAX_BATCH_SIZE - 1) // MAX_BATCH_SIZE
                
                for batch_idx in range(total_batches):
                    start_idx = batch_idx * MAX_BATCH_SIZE
                    end_idx = min(start_idx + MAX_BATCH_SIZE, len(uncached_texts))
                    batch_texts = uncached_texts[start_idx:end_idx]
                    
                    batch_embeddings = self._get_embeddings_single_batch(batch_texts, model)
                    
                    if batch_embeddings is None:
                        self.logger.error(f"❌ 批次 {batch_idx + 1} 处理失败")
                        return None
                    
                    # 映射回原始索引并保存到缓存
                    current_time = time.time()
                    for emb_idx, (valid_idx, orig_idx) in enumerate(uncached_indices[start_idx:end_idx]):
                        if emb_idx < len(batch_embeddings):
                            embedding = batch_embeddings[emb_idx]
                            all_embeddings_dict[orig_idx] = embedding
                            
                            # 保存到缓存
                            text = uncached_texts[start_idx + emb_idx]
                            cache_key = self._get_cache_key(text, model)
                            self._embedding_cache[cache_key] = {
                                'embedding': embedding.tolist(),
                                'timestamp': current_time,
                                'text_preview': text[:100],
                                'model': model
                            }
                            self._embedding_cache_misses += 1
            else:
                batch_embeddings = self._get_embeddings_single_batch(uncached_texts, model)
                if batch_embeddings is None:
                    return None
                
                # 映射回原始索引并保存到缓存
                current_time = time.time()
                for emb_idx, (valid_idx, orig_idx) in enumerate(uncached_indices):
                    if emb_idx < len(batch_embeddings):
                        embedding = batch_embeddings[emb_idx]
                        all_embeddings_dict[orig_idx] = embedding
                        
                        # 保存到缓存
                        text = uncached_texts[emb_idx]
                        cache_key = self._get_cache_key(text, model)
                        self._embedding_cache[cache_key] = {
                            'embedding': embedding.tolist(),
                            'timestamp': current_time,
                            'text_preview': text[:100],
                            'model': model
                        }
                        self._embedding_cache_misses += 1
                
                # 🚀 性能优化：定期保存缓存（每10次调用保存一次）
                self._embedding_cache_save_counter += len(uncached_texts)
                if self._embedding_cache_save_counter >= 10:
                    self._save_embedding_cache()
                    self._embedding_cache_save_counter = 0
        
        # 处理超长文本（分块向量化）
        for orig_idx, long_text in long_text_indices:
            embedding = self._get_embedding_for_long_text(long_text, model, MAX_TEXT_LENGTH)
            if embedding is not None:
                all_embeddings_dict[orig_idx] = embedding
        
        # 映射回原始顺序
        result = []
        for i in range(len(texts)):
            result.append(all_embeddings_dict.get(i))
        
        return result
    
    def _get_embeddings_single_batch(self, texts: List[str], model: str) -> Optional[List[np.ndarray]]:
        """
        处理单个批次的embedding请求（带重试机制）
        
        Args:
            texts: 文本列表（最多512个）
            model: 模型名称
            
        Returns:
            embedding向量列表
        """
        url = f"{self.base_url}/v1/embeddings"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": model,
            "input": texts
        }
        
        # 🚀 重试机制：特别处理SSL错误
        # 🆕 优化：如果不启用重试（max_retries=0），直接尝试一次，失败即返回
        last_exception = None
        max_attempts = max(1, self.max_retries + 1)  # 至少尝试1次
        for attempt in range(max_attempts):
            try:
                # 使用带重试的会话
                response = self.session.post(
                    url, 
                    json=payload, 
                    headers=headers, 
                    timeout=self.request_timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if 'data' in result and len(result['data']) > 0:
                        embeddings = [np.array(item['embedding'], dtype=np.float32) for item in result['data']]
                        self.stats["embedding_success"] += 1
                        if attempt > 0:
                            self.logger.info(f"✅ 重试成功 (尝试 {attempt + 1}/{self.max_retries + 1})")
                        return embeddings
                    else:
                        self.logger.error("Jina API返回空数据")
                        self.stats["embedding_errors"] += 1
                        return None
                elif response.status_code == 429:
                    # 速率限制
                    error_text = response.text[:200] if response.text else "无错误详情"
                    if self.max_retries > 0 and attempt < self.max_retries:
                        # 🚀 阶段3优化：使用指数退避策略
                        retry_after = int(response.headers.get('Retry-After', self.retry_delay * (2 ** attempt)))
                        attempt_info = f"(尝试 {attempt + 1}/{self.max_retries + 1})"
                        self.logger.warning(f"⚠️ 速率限制，等待 {retry_after} 秒后重试 {attempt_info}")
                        self.stats["embedding_retries"] += 1
                        time.sleep(retry_after)
                        continue
                    else:
                        # 🚀 阶段3优化：不重试或重试次数用完，直接返回失败
                        if self.max_retries == 0:
                            self.logger.warning(f"⚠️ 速率限制（429，已禁用重试）: {error_text}，将记录失败条目供下次重新处理")
                        else:
                            self.logger.error(f"❌ 速率限制，已达到最大重试次数")
                        self.stats["embedding_errors"] += 1
                        return None
                else:
                    error_text = response.text[:200] if response.text else "无错误详情"
                    self.logger.error(f"Jina API调用失败: {response.status_code} - {error_text}")
                    self.stats["embedding_errors"] += 1
                    return None
                    
            except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as e:
                # SSL错误或连接错误
                last_exception = e
                if self.max_retries > 0 and attempt < self.max_retries:
                    # 🚀 阶段3优化：使用指数退避策略
                    delay = min(self.retry_delay * (2 ** attempt), 30)  # 最大延迟30秒，避免等待过久
                    retry_info = f"(尝试 {attempt + 1}/{self.max_retries + 1}): {type(e).__name__}"
                    logger.warning(f"⚠️ SSL/连接错误，{delay:.1f}秒后重试 {retry_info}")
                    self.stats["embedding_retries"] += 1
                    time.sleep(delay)
                    continue  # 继续重试
                else:
                    # 🚀 阶段3优化：不重试或重试次数用完，直接返回失败
                    if self.max_retries == 0:
                        self.logger.warning(f"⚠️ SSL/连接错误（已禁用重试）: {e}，将记录失败条目供下次重新处理")
                    else:
                        self.logger.error(f"❌ SSL/连接错误，已重试 {self.max_retries + 1} 次仍失败: {e}")
                    self.stats["embedding_errors"] += 1
                    return None
                    
            except requests.exceptions.Timeout as e:
                # 超时错误
                last_exception = e
                if self.max_retries > 0 and attempt < self.max_retries:
                    # 🚀 阶段3优化：使用指数退避策略，增加最大延迟时间
                    delay = min(self.retry_delay * (2 ** attempt), 30)  # 最大延迟30秒（从10秒增加到30秒），避免等待过久
                    timeout_info = f"（{self.request_timeout}秒），{delay:.1f}秒后重试"
                    logger.warning(f"⚠️ 请求超时{timeout_info} (尝试 {attempt + 1}/{self.max_retries + 1})")
                    self.stats["embedding_retries"] += 1
                    time.sleep(delay)
                    continue  # 继续重试
                else:
                    # 🚀 阶段3优化：不重试或重试次数用完，直接返回失败
                    if self.max_retries == 0:
                        self.logger.warning(f"⚠️ 请求超时（{self.request_timeout}秒，已禁用重试）: {e}，将记录失败条目供下次重新处理")
                    else:
                        total_timeout = self.request_timeout * (self.max_retries + 1)
                        logger.error(f"❌ 请求超时，已重试 {self.max_retries + 1} 次仍失败（总超时时间: {total_timeout}秒）: {e}")
                    self.stats["embedding_errors"] += 1
                    return None
                    
            except Exception as e:
                # 其他错误，不重试
                self.logger.error(f"❌ 文本向量化失败: {type(e).__name__}: {e}")
                self.stats["embedding_errors"] += 1
                return None
        
        # 所有重试都失败
        if last_exception:
            self.logger.error(f"❌ 文本向量化最终失败（已重试 {self.max_retries + 1} 次）: {last_exception}")
        self.stats["embedding_errors"] += 1
        return None
    
    def rerank(
        self, 
        query: str, 
        documents: List[str], 
        model: Optional[str] = None, 
        top_n: Optional[int] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        对文档列表进行重排序（🆕 优先使用本地模型，支持Jina API fallback）
        
        Args:
            query: 查询文本
            documents: 文档列表
            model: 模型名称（可选，默认使用JINA_RERANK_MODEL）
            top_n: 返回前N个结果（可选）
            
        Returns:
            重排序后的结果列表，每个元素包含index和score，失败返回None
        """
        if not query or not documents or len(documents) == 0:
            self.logger.warning("⚠️ 查询或文档列表为空")
            return None
        
        # 🆕 优先使用本地rerank模型（完全免费，无需API密钥）
        # 即使JINA_API_KEY设置了，也优先使用本地模型
        use_jina_api = os.getenv("USE_JINA_RERANK_API", "false").lower() == "true"
        
        # 🆕 优先使用本地模型（即使JINA_API_KEY设置了）
        if self.local_rerank_model and not use_jina_api:
            try:
                return self._rerank_with_local_model(query, documents, top_n)
            except Exception as e:
                self.logger.warning(f"⚠️ 本地rerank模型失败: {e}，尝试Jina API fallback")
                # 继续执行，尝试Jina API fallback
        
        # 如果明确要求使用Jina API，或者本地模型不可用，才使用Jina API
        if use_jina_api or not self.local_rerank_model:
            if not self.api_key:
                self.logger.warning("⚠️ JINA_API_KEY未设置且无本地rerank模型，无法使用rerank")
                return None
            
            model = model or self.default_rerank_model
        
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
        
        # 🚀 重试机制：特别处理SSL错误
        # 🆕 优化：如果不启用重试（max_retries=0），直接尝试一次，失败即返回
        last_exception = None
        max_attempts = max(1, self.max_retries + 1)  # 至少尝试1次
        for attempt in range(max_attempts):
            try:
                self.stats["rerank_calls"] += (1 if attempt == 0 else 0)  # 只在第一次调用时计数
                
                response = self.session.post(
                    url, 
                    headers=headers, 
                    json=payload, 
                    timeout=self.request_timeout
                )
                response.raise_for_status()
                
                data = response.json()
                results = data.get("results", [])
                
                self.stats["rerank_success"] += 1
                if attempt > 0:
                    self.logger.info(f"✅ Rerank重试成功 (尝试 {attempt + 1}/{self.max_retries + 1})")
                return results
                
            except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as e:
                last_exception = e
                if self.max_retries > 0 and attempt < self.max_retries:
                    # 🆕 只有在启用重试时才重试
                    delay = self.retry_delay * (2 ** attempt)
                    retry_msg = f"⚠️ Rerank SSL/连接错误，{delay:.1f}秒后重试 (尝试 {attempt + 1}/{self.max_retries + 1}): {type(e).__name__}"
                    logger.warning(retry_msg)
                    self.stats["rerank_retries"] += 1
                    time.sleep(delay)
                else:
                    # 🆕 不重试或重试次数用完，直接返回失败
                    if self.max_retries == 0:
                        self.logger.warning(f"⚠️ Rerank SSL/连接错误（已禁用重试）: {e}，将记录失败条目供下次重新处理")
                    else:
                        self.logger.error(f"❌ Rerank SSL/连接错误，已重试 {self.max_retries + 1} 次仍失败: {e}")
                    self.stats["rerank_errors"] += 1
                    return None
                    
            except requests.exceptions.Timeout as e:
                # 超时错误
                last_exception = e
                if self.max_retries > 0 and attempt < self.max_retries:
                    # 🆕 只有在启用重试时才重试
                    delay = min(self.retry_delay * (2 ** attempt), 10)  # 最大延迟10秒
                    logger.warning( f"⚠️ Rerank请求超时（{self.request_timeout}秒），{delay:.1f}秒后重试 (尝试 {attempt + 1}/{self.max_retries + 1})" )
                    self.stats["rerank_retries"] += 1
                    time.sleep(delay)
                else:
                    # 🆕 不重试或重试次数用完，直接返回失败
                    if self.max_retries == 0:
                        self.logger.warning(f"⚠️ Rerank请求超时（{self.request_timeout}秒，已禁用重试）: {e}，将记录失败条目供下次重新处理")
                    else:
                        total_timeout = self.request_timeout * (self.max_retries + 1)
                        logger.error(f"❌ Rerank请求超时，已重试 {self.max_retries + 1} 次仍失败（总超时时间: {total_timeout}秒）: {e}")
                    self.stats["rerank_errors"] += 1
                    return None
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"❌ Jina Rerank API请求失败: {e}")
                self.stats["rerank_errors"] += 1
                return None
                
            except Exception as e:
                self.logger.error(f"❌ Rerank处理失败: {type(e).__name__}: {e}")
                self.stats["rerank_errors"] += 1
                return None
        
        # 所有重试都失败
        if last_exception:
            self.logger.error(f"❌ Rerank最终失败（已重试 {self.max_retries + 1} 次）: {last_exception}")
            # Jina API失败，尝试本地模型fallback
            if self.local_rerank_model:
                self.logger.debug("⚠️ Jina API失败，切换到本地rerank模型")
                return self._rerank_with_local_model(query, documents, top_n)
        self.stats["rerank_errors"] += 1
        return None
    
    def _rerank_with_local_model(
        self, 
        query: str, 
        documents: List[str], 
        top_n: Optional[int] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """使用本地rerank模型进行重排序（免费fallback）"""
        if not self.local_rerank_model:
            return None
        
        try:
            rerank_start = time.time()
            
            # 构建query-document对
            pairs = [[query, doc] for doc in documents]
            
            # 使用CrossEncoder进行评分
            scores = self.local_rerank_model.predict(pairs)
            
            # 将分数转换为列表（如果返回的是numpy数组）
            if isinstance(scores, np.ndarray):
                scores = scores.tolist()
            elif not isinstance(scores, list):
                scores = [float(scores)]
            
            # 创建结果列表（index, score）
            results = []
            for i, score in enumerate(scores):
                results.append({
                    'index': i,
                    'score': float(score)
                })
            
            # 按分数降序排序
            results.sort(key=lambda x: x['score'], reverse=True)
            
            # 如果指定了top_n，只返回前N个
            if top_n is not None and top_n > 0:
                results = results[:top_n]
            
            rerank_time = time.time() - rerank_start
            
            # 🚀 性能监控：记录本地rerank耗时
            if rerank_time > 1.0:
                self.logger.warning(f"⚠️ 本地rerank耗时: {rerank_time:.2f}秒 (文档数={len(documents)})")
            else:
                self.logger.debug(f"✅ 本地rerank完成: {rerank_time:.3f}秒 (文档数={len(documents)})")
            
            return results
            
        except Exception as e:
            self.logger.error(f"本地rerank模型失败: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
    
    def _get_embedding_for_long_text(
        self, 
        text: str, 
        model: Optional[str], 
        max_length: int = 8000
    ) -> Optional[np.ndarray]:
        """
        对超长文本进行分块向量化并合并
        
        策略：
        1. 将文本分成多个块，每块max_length字符
        2. 块之间有重叠（1000字符）以保留上下文
        3. 对每块分别向量化
        4. 合并所有块的向量（平均合并）
        
        Args:
            text: 原始文本（超过max_length）
            model: 模型名称
            max_length: 单块最大长度（默认8000）
            
        Returns:
            合并后的embedding向量，失败返回None
        """
        if len(text) <= max_length:
            # 不需要分块，直接向量化
            result = self.get_embeddings([text], model)
            return result[0] if result and len(result) > 0 else None
        
        # 分块参数
        chunk_size = max_length
        overlap_size = 1000  # 重叠大小，保留上下文
        
        # 生成分块
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end]
            chunks.append(chunk)
            
            # 如果还没到末尾，下一块的开始位置需要重叠
            if end < len(text):
                start = end - overlap_size
            else:
                break
        
        if not chunks:
            self.logger.error("❌ 分块失败，无法生成有效块")
            return None
        
        self.logger.info(f"ℹ️ 文本过长（{len(text)}字符），分成{len(chunks)}块进行向量化")
        
        # 🚀 优化：并行向量化各块（如果块数>1），缩短总耗时
        # 🚀 优化：提高默认并发数，从2提升到5，加快分块向量化速度
        max_workers = min(len(chunks), int(os.getenv("JINA_MAX_CONCURRENT_REQUESTS", "5")))
        
        chunk_embeddings = []
        if len(chunks) > 1 and max_workers > 1:
            # 并行处理多个块
            self.logger.debug(f"🔄 并行向量化{len(chunks)}块（最多{max_workers}个并发请求）...")
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                future_to_chunk = {
                    executor.submit(self.get_embeddings, [chunk], model): (chunk_idx, chunk)
                    for chunk_idx, chunk in enumerate(chunks)
                }
                
                # 收集结果（保持顺序）
                results: List[Optional[np.ndarray]] = [None] * len(chunks)  # type: ignore
                for future in as_completed(future_to_chunk):
                    chunk_idx, chunk = future_to_chunk[future]
                    try:
                        result = future.result()
                        if result and len(result) > 0 and result[0] is not None:
                            results[chunk_idx] = result[0]  # type: ignore
                            self.logger.debug(f"✅ 第{chunk_idx + 1}块向量化完成")
                        else:
                            self.logger.warning(f"⚠️ 第{chunk_idx + 1}块向量化失败")
                    except Exception as e:
                        self.logger.warning(f"⚠️ 第{chunk_idx + 1}块向量化异常: {e}")
                
                # 过滤掉None值
                chunk_embeddings = [emb for emb in results if emb is not None]
        else:
            # 串行处理（单块或禁用并发）
            for chunk_idx, chunk in enumerate(chunks):
                result = self.get_embeddings([chunk], model)
                if result and len(result) > 0 and result[0] is not None:
                    chunk_embeddings.append(result[0])
                    # 🆕 内存优化：向量化后立即释放中间变量
                    del result
                else:
                    self.logger.warning(f"⚠️ 第{chunk_idx + 1}块向量化失败")
        
        if not chunk_embeddings:
            self.logger.error("❌ 所有块向量化都失败")
            return None
        
        # 合并向量（平均合并）
        # 可以改为加权合并，给开头和结尾更高的权重
        merged_embedding = np.mean(chunk_embeddings, axis=0)
        
        # 🆕 内存优化：合并后释放中间向量列表
        del chunk_embeddings
        
        self.logger.info(f"✅ 成功合并{len(chunks)}个块的向量（共{len(text)}字符）")
        
        return merged_embedding.astype(np.float32)
    
    def _get_cache_key(self, text: str, model: str) -> str:
        """生成缓存键"""
        key_string = f"{model}:{text}"
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    def _load_embedding_cache(self) -> None:
        """🚀 性能优化：从文件加载持久化embedding缓存"""
        try:
            if self._embedding_cache_path.exists():
                with open(self._embedding_cache_path, 'r', encoding='utf-8') as f:
                    loaded_cache = json.load(f)
                    
                    # 过滤过期缓存
                    current_time = time.time()
                    valid_cache = {}
                    expired_count = 0
                    
                    for key, value in loaded_cache.items():
                        if isinstance(value, dict):
                            cache_time = value.get('timestamp', 0)
                            cache_age = current_time - cache_time
                            # 只保留未过期的缓存
                            if cache_age < self._embedding_cache_ttl:
                                valid_cache[key] = value
                            else:
                                expired_count += 1
                    
                    self._embedding_cache = valid_cache
                    self.logger.info(f"✅ KMS Embedding缓存已从文件加载: {self._embedding_cache_path}")
                    self.logger.info(f"   总缓存条目: {len(loaded_cache)}条")
                    self.logger.info(f"   有效缓存: {len(valid_cache)}条 (TTL: {self._embedding_cache_ttl/3600:.1f}小时)")
                    self.logger.info(f"   过期缓存: {expired_count}条")
            else:
                self.logger.info(f"KMS Embedding缓存文件不存在，使用空缓存: {self._embedding_cache_path}")
        except Exception as e:
            self.logger.warning(f"加载KMS Embedding缓存失败，使用空缓存: {e}")
    
    def _save_embedding_cache(self) -> None:
        """🚀 性能优化：保存embedding缓存到文件"""
        try:
            # 确保目录存在
            self._embedding_cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 过滤过期缓存（只保存有效缓存）
            current_time = time.time()
            valid_cache = {}
            
            for key, value in self._embedding_cache.items():
                if isinstance(value, dict):
                    cache_time = value.get('timestamp', 0)
                    # 只保存未过期的缓存
                    if current_time - cache_time < self._embedding_cache_ttl:
                        valid_cache[key] = value
            
            # 保存缓存
            with open(self._embedding_cache_path, 'w', encoding='utf-8') as f:
                json.dump(valid_cache, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"KMS Embedding缓存已保存到: {self._embedding_cache_path} ({len(valid_cache)}条)")
        except Exception as e:
            self.logger.warning(f"保存KMS Embedding缓存失败: {e}")


# 单例实例
_jina_service_instance: Optional[JinaService] = None


def get_jina_service() -> JinaService:
    """
    获取Jina服务实例（单例）
    
    Returns:
        JinaService实例
    """
    global _jina_service_instance
    if _jina_service_instance is None:
        _jina_service_instance = JinaService()
    return _jina_service_instance

