#!/usr/bin/env python3
"""
文本模态处理器
使用Jina Embedding API进行文本向量化，支持本地模型fallback
"""

import os
import requests
import numpy as np
import threading
import time
from pathlib import Path
from typing import Any, Optional, List
from . import ModalityProcessor
from ..utils.logger import get_logger
# 🚀 统一使用Jina服务
from ..utils.jina_service import get_jina_service

logger = get_logger()

# 🆕 尝试导入sentence-transformers（免费本地模型）
SENTENCE_TRANSFORMERS_AVAILABLE = False
try:
    # 延迟导入，避免在模块级别触发keras兼容性问题
    def _import_sentence_transformer():
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
    logger.debug("sentence-transformers可用，本地模型可以使用")
except ImportError:
    logger.debug("sentence-transformers未安装，本地模型fallback不可用")
except Exception as e:
    logger.debug(f"sentence-transformers导入异常: {e}，本地模型fallback不可用")

# 🚀 P0修复：TextProcessor单例模式，避免重复加载embedding模型
_text_processor_instance: Optional['TextProcessor'] = None
_init_lock = threading.Lock()  # 🚀 P0修复：添加初始化锁，确保线程安全
_model_loading_lock = threading.Lock()  # 🚀 P0修复：添加模型加载锁，防止并发加载
_init_lock = threading.Lock()  # 🚀 P0修复：添加初始化锁，确保线程安全


class TextProcessor(ModalityProcessor):
    """文本处理器 - 使用Jina Embedding API，支持本地模型fallback（单例模式）"""
    
    def __new__(cls):
        """单例模式：确保只有一个TextProcessor实例，避免重复加载embedding模型"""
        global _text_processor_instance
        if _text_processor_instance is None:
            _text_processor_instance = super().__new__(cls)
            _text_processor_instance._initialized = False
        return _text_processor_instance
    
    def __init__(self):
        # 🚀 P0修复：单例模式 + 线程安全，避免重复初始化和并发加载模型
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        # 🚀 P0修复：使用锁确保只有一个线程能执行初始化
        global _init_lock
        with _init_lock:
            # 双重检查：再次确认是否已初始化（防止并发初始化）
            if hasattr(self, '_initialized') and self._initialized:
                return
            
            super().__init__()
            # 🚀 统一使用Jina服务
            self.jina_service = get_jina_service()
            self.api_key = self.jina_service.api_key
            self.base_url = self.jina_service.base_url
            self.model = self.jina_service.default_embedding_model
            self.dimension = 768  # Jina v2默认维度
            
            # 🆕 本地模型fallback（免费替代方案）
            self.local_model = None
            self.use_local_model = False
            
            # 🆕 优先使用本地模型（完全免费，无需API密钥）
            # 尝试加载本地模型
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                self._load_local_model_safely()
            
            self._initialized = True
    
    def _check_model_file_complete(self, model_name: str, max_wait_time: int = 300) -> bool:
        """🚀 P0修复：检查模型文件是否完整（如果正在下载，等待下载完成）
        
        Args:
            model_name: 模型名称
            max_wait_time: 最大等待时间（秒）
            
        Returns:
            如果模型文件完整返回True，否则返回False
        """
        try:
            import os
            
            # 获取模型缓存路径
            cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
            
            # 🚀 修复：HuggingFace 会将模型名称自动解析为 sentence-transformers/{model_name}
            # 所以需要检查两种可能的路径格式
            possible_paths = [
                f"models--{model_name.replace('/', '--')}",  # 原始格式
                f"models--sentence-transformers--{model_name.replace('/', '--')}",  # sentence-transformers 格式
            ]
            
            model_cache_path = None
            for path_name in possible_paths:
                path = os.path.join(cache_dir, path_name)
                if os.path.exists(path):
                    model_cache_path = path
                    break
            
            # 检查模型目录是否存在
            if not model_cache_path:
                return False
            
            # 检查关键文件（model.safetensors 或 pytorch_model.bin）
            key_files = ["model.safetensors", "pytorch_model.bin"]
            found_key_file = None
            
            # 搜索关键文件（可能在子目录中）
            for root, dirs, files in os.walk(model_cache_path):
                for key_file in key_files:
                    if key_file in files:
                        found_key_file = os.path.join(root, key_file)
                        break
                if found_key_file:
                    break
            
            if not found_key_file:
                # 没有找到关键文件，可能还在下载
                return False
            
            # 检查文件大小（如果文件太小，可能还在下载或损坏）
            file_size = os.path.getsize(found_key_file)
            if file_size < 1024:  # 小于1KB，可能是空文件或损坏
                logger.warning(f"⚠️ 模型文件大小异常: {file_size} 字节")
                return False
            
            # 🚀 P0修复：检查文件是否正在被写入（通过检查文件大小是否稳定）
            initial_size = file_size
            time.sleep(1.0)  # 等待1秒
            current_size = os.path.getsize(found_key_file)
            
            if current_size != initial_size:
                # 文件大小变化，说明正在下载
                filename = os.path.basename(found_key_file)
                progress = f"({initial_size} -> {current_size} 字节)"
                logger.info(f"⏳ 检测到模型文件正在下载: {filename} {progress}")
                # 等待下载完成
                wait_start = time.time()
                check_count = 0
                while time.time() - wait_start < max_wait_time:
                    time.sleep(2)  # 每2秒检查一次
                    check_count += 1
                    current_size = os.path.getsize(found_key_file)
                    
                    if current_size == initial_size:
                        # 文件大小稳定，下载完成
                        filename = os.path.basename(found_key_file)
                        wait_time = check_count * 2
                        logger.info(f"✅ 模型文件下载完成: {filename} "
                                  f"({current_size} 字节，等待了 {wait_time} 秒)")
                        return True
                    
                    # 更新大小（继续监控）
                    if check_count % 5 == 0:  # 每10秒记录一次进度
                        filename = os.path.basename(found_key_file)
                        wait_time = check_count * 2
                        logger.info(f"⏳ 模型文件下载中: {filename} "
                                  f"({current_size} 字节，已等待 {wait_time} 秒)")
                    initial_size = current_size
                else:
                    filename = os.path.basename(found_key_file)
                    logger.warning(f"⚠️ 等待模型文件下载超时: {filename} (已等待 {max_wait_time} 秒)")
                    return False
            
            # 文件大小稳定，认为下载完成
            return True
        except Exception as e:
            logger.debug(f"检查模型文件完整性失败: {e}")
            return False
    
    def _load_local_model_safely(self):
        """🚀 P0修复：线程安全地加载本地模型"""
        global _model_loading_lock
        
        # 使用模型加载锁，确保只有一个线程能加载模型
        with _model_loading_lock:
            # 再次检查是否已加载（防止并发加载）
            if self.local_model is not None and self.use_local_model:
                return
            
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                logger.warning("⚠️ sentence-transformers未安装，无法使用本地模型")
                logger.warning("💡 提示: 安装本地模型: pip install sentence-transformers")
                self.local_model = None
                self.use_local_model = False
                return
            
            try:
                # 使用环境变量指定模型，默认使用all-mpnet-base-v2（768维，与Jina v2相同）
                local_model_name = os.getenv("LOCAL_EMBEDDING_MODEL", "all-mpnet-base-v2")
                
                # 🆕 尝试使用镜像源（如果网络有问题）
                hf_endpoint = os.getenv("HF_ENDPOINT")
                if not hf_endpoint:
                    # 默认使用镜像源，提高下载成功率
                    os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
                    logger.debug("使用HuggingFace镜像源: https://hf-mirror.com")
                
                logger.info(f"🔄 正在加载本地embedding模型: {local_model_name}...")
                
                # 🚀 P0修复：检查模型文件是否完整（如果正在下载，等待下载完成）
                if not self._check_model_file_complete(local_model_name):
                    logger.warning(f"⚠️ 模型文件不完整或不存在，将尝试下载: {local_model_name}")
                
                # 🆕 优先尝试从本地缓存加载（避免网络连接）
                try:
                    # 🚀 M2/MPS 优化：先尝试在 CPU 上加载，然后移动到 MPS
                    # （避免 meta tensor 错误）
                    import torch
                    target_device = 'cpu'
                    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                        target_device = 'mps'
                    elif torch.cuda.is_available():
                        target_device = 'cuda'
                    
                    # 🚀 M2/MPS 修复：对于 MPS 设备，直接加载到 MPS
                    # （避免先加载到CPU再移动导致的meta tensor错误）
                    # 如果MPS加载失败，自动降级到CPU
                    # 🚀 修复：使用标志变量避免重复日志记录
                    model_loaded_with_device_log = False
                    
                    # 🚀 P0修复：优先使用CPU设备（最稳定），避免meta tensor错误
                    # 如果MPS可用，先尝试MPS，失败后强制使用CPU
                    if target_device == 'mps':
                        try:
                            # 🚀 修复：直接加载到MPS，避免meta tensor错误
                            logger.debug("🔄 MPS设备：尝试加载模型到MPS...")
                            SentenceTransformerClass = _import_sentence_transformer()
                            self.local_model = SentenceTransformerClass(
                                local_model_name, 
                                local_files_only=True,
                                device='mps'  # 直接加载到 MPS
                            )
                            # 🚀 P0修复：立即验证模型是否正常工作
                            test_embedding = self.local_model.encode("test", convert_to_numpy=True)
                            if test_embedding is None or len(test_embedding) == 0:
                                raise ValueError("模型验证失败：编码返回空结果")
                            self.dimension = self.local_model.get_sentence_embedding_dimension()
                            self.use_local_model = True
                            logger.info(f"✅ 已从本地缓存加载模型到MPS: {local_model_name} "
                                      f"(维度: {self.dimension})")
                            model_loaded_with_device_log = True
                        except Exception as mps_error:
                            # 如果 MPS 加载失败，强制使用 CPU（最稳定）
                            error_msg = str(mps_error).lower()
                            if "meta tensor" in error_msg or "cannot copy" in error_msg:
                                logger.warning(f"⚠️ MPS设备加载失败（meta tensor错误），强制使用CPU设备: "
                                             f"{mps_error}")
                            else:
                                logger.warning(f"⚠️ MPS设备加载失败，降级到CPU设备: {mps_error}")
                            # 🚀 P0修复：强制使用CPU，确保系统能够正常工作
                            try:
                                SentenceTransformerClass = _import_sentence_transformer()
                                self.local_model = SentenceTransformerClass(
                                    local_model_name, 
                                    local_files_only=True,
                                    device='cpu'  # 强制使用 CPU（最稳定）
                                )
                                # 🚀 P0修复：立即验证模型是否正常工作
                                test_embedding = self.local_model.encode("test", convert_to_numpy=True)
                                if test_embedding is None or len(test_embedding) == 0:
                                    raise ValueError("模型验证失败：编码返回空结果")
                                target_device = 'cpu'  # 降级到 CPU
                                self.dimension = self.local_model.get_sentence_embedding_dimension()
                                self.use_local_model = True
                                logger.info(f"✅ 已从本地缓存加载模型到CPU: {local_model_name} "
                                      f"(维度: {self.dimension})")
                                model_loaded_with_device_log = True
                            except Exception as cpu_error:
                                # CPU加载也失败，可能是模型文件损坏
                                logger.error(f"❌ CPU设备加载也失败: {cpu_error}")
                                # 🚀 P0修复：如果是meta tensor错误，标记需要清理缓存
                                if "meta tensor" in str(cpu_error).lower() or "cannot copy" in str(cpu_error).lower():
                                    logger.error("💡 检测到meta tensor错误，模型文件可能损坏，"
                                               "将在后续步骤清理缓存")
                                raise cpu_error
                    else:
                        # 非 MPS 设备，直接加载到目标设备
                        SentenceTransformerClass = _import_sentence_transformer()
                        self.local_model = SentenceTransformerClass(
                            local_model_name,
                            local_files_only=True,
                            device=target_device
                        )
                    
                    # 🚀 修复：只有在未记录设备信息时才记录通用日志
                    if not model_loaded_with_device_log:
                        self.dimension = self.local_model.get_sentence_embedding_dimension()
                        self.use_local_model = True
                        logger.info(f"✅ 已从本地缓存加载模型: {local_model_name} "
                                  f"(维度: {self.dimension}, 设备: {target_device})")
                    else:
                        # 确保dimension和use_local_model已设置（MPS/CPU路径已设置）
                        if not hasattr(self, 'dimension') or not hasattr(self, 'use_local_model'):
                            self.dimension = self.local_model.get_sentence_embedding_dimension()
                            self.use_local_model = True
                except Exception as local_error:
                    # 如果本地加载失败，尝试网络下载（使用镜像源）
                    logger.debug(f"本地缓存加载失败，尝试网络下载: {local_error}")
                    # 🚀 修复：如果本地加载失败，可能是模型文件损坏
                    # 先清理缓存再重新下载
                    if "meta tensor" in str(local_error).lower() or "cannot copy" in str(local_error).lower():
                        logger.warning("⚠️ 检测到meta tensor错误，可能是模型文件损坏，"
                                     "尝试清理缓存后重新下载")
                        # 自动清理损坏的缓存
                        import shutil
                        model_cache_name = local_model_name.replace('/', '--')
                        cache_dir = f"~/.cache/huggingface/hub/models--sentence-transformers--{model_cache_name}"
                        cache_path = os.path.expanduser(cache_dir)
                        if os.path.exists(cache_path):
                            try:
                                shutil.rmtree(cache_path)
                                logger.info(f"✅ 已清理损坏的模型缓存: {cache_path}")
                            except Exception as cleanup_error:
                                logger.warning(f"⚠️ 清理缓存失败: {cleanup_error}")
                                logger.warning(f"💡 请手动清理: rm -rf {cache_path}")
                    
                    import torch
                    device = 'cpu'
                    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                        device = 'mps'
                    elif torch.cuda.is_available():
                        device = 'cuda'
                    
                    try:
                        # 🚀 修复：重新下载模型（不使用 local_files_only）
                        # 🚀 M2/MPS 优化：对于 MPS 设备，先加载到 CPU，再移动到 MPS
                        logger.info(f"🔄 重新下载模型: {local_model_name}...")
                        
                        # 🚀 P0修复：优先使用CPU设备（最稳定），避免meta tensor错误
                        # 如果MPS可用，先尝试MPS，失败后强制使用CPU
                        if device == 'mps':
                            try:
                                logger.debug("🔄 MPS设备：尝试从网络加载模型到MPS...")
                                SentenceTransformerClass = _import_sentence_transformer()
                                self.local_model = SentenceTransformerClass(
                                    local_model_name, 
                                    local_files_only=False,
                                    device='mps'  # 直接加载到 MPS
                                )
                                # 🚀 P0修复：立即验证模型是否正常工作
                                test_embedding = self.local_model.encode("test", convert_to_numpy=True)
                                if test_embedding is None or len(test_embedding) == 0:
                                    raise ValueError("模型验证失败：编码返回空结果")
                                self.dimension = self.local_model.get_sentence_embedding_dimension()
                                self.use_local_model = True
                                logger.info(f"✅ 已从网络重新下载模型到MPS: {local_model_name} "
                                          f"(维度: {self.dimension})")
                            except Exception as mps_error:
                                # 如果 MPS 加载失败，强制使用 CPU（最稳定）
                                error_msg = str(mps_error).lower()
                                if "meta tensor" in error_msg or "cannot copy" in error_msg:
                                    logger.warning(f"⚠️ MPS设备加载失败（meta tensor错误），强制使用CPU设备: "
                                             f"{mps_error}")
                                else:
                                    logger.warning(f"⚠️ MPS设备加载失败，降级到CPU设备: {mps_error}")
                                # 🚀 P0修复：强制使用CPU，确保系统能够正常工作
                                try:
                                    SentenceTransformerClass = _import_sentence_transformer()
                                    self.local_model = SentenceTransformerClass(
                                        local_model_name, 
                                        local_files_only=False,
                                        device='cpu'  # 强制使用 CPU（最稳定）
                                    )
                                    # 🚀 P0修复：立即验证模型是否正常工作
                                    test_embedding = self.local_model.encode("test", convert_to_numpy=True)
                                    if test_embedding is None or len(test_embedding) == 0:
                                        raise ValueError("模型验证失败：编码返回空结果")
                                    device = 'cpu'  # 降级到 CPU
                                    self.dimension = self.local_model.get_sentence_embedding_dimension()
                                    self.use_local_model = True
                                    logger.info(f"✅ 已从网络重新下载模型到CPU: {local_model_name} "
                                              f"(维度: {self.dimension})")
                                except Exception as cpu_error:
                                    # CPU加载也失败
                                    logger.error(f"❌ CPU设备加载也失败: {cpu_error}")
                                    raise cpu_error
                        else:
                            # 非 MPS 设备，直接加载到目标设备
                            SentenceTransformerClass = _import_sentence_transformer()
                            self.local_model = SentenceTransformerClass(
                                local_model_name, 
                                local_files_only=False,
                                device=device
                            )
                            # 🚀 P0修复：立即验证模型是否正常工作
                            test_embedding = self.local_model.encode("test", convert_to_numpy=True)
                            if test_embedding is None or len(test_embedding) == 0:
                                raise ValueError("模型验证失败：编码返回空结果")
                        
                        self.dimension = self.local_model.get_sentence_embedding_dimension()
                        self.use_local_model = True
                        logger.info(f"✅ 已从网络重新下载模型: {local_model_name} "
                                  f"(维度: {self.dimension}, 设备: {device})")
                    except Exception as download_error:
                        logger.error(f"❌ 网络下载模型也失败: {download_error}")
                        # 🚀 P0修复：如果仍然失败，强制使用 CPU 设备（最稳定）
                        if device != 'cpu':
                            logger.warning(f"⚠️ 尝试使用 CPU 设备重新加载模型（最稳定方案）")
                            try:
                                SentenceTransformerClass = _import_sentence_transformer()
                                self.local_model = SentenceTransformerClass(
                                    local_model_name, 
                                    local_files_only=False,
                                    device='cpu'  # 强制使用 CPU
                                )
                                # 🚀 P0修复：立即验证模型是否正常工作
                                test_embedding = self.local_model.encode("test", convert_to_numpy=True)
                                if test_embedding is None or len(test_embedding) == 0:
                                    raise ValueError("模型验证失败：编码返回空结果")
                                self.dimension = self.local_model.get_sentence_embedding_dimension()
                                self.use_local_model = True
                                logger.info(f"✅ 使用 CPU 设备成功加载模型: {local_model_name} "
                                          f"(维度: {self.dimension})")
                            except Exception as cpu_error:
                                logger.error(f"❌ CPU 设备加载也失败: {cpu_error}")
                                # 🚀 P0修复：提供详细的错误信息和解决方案
                                logger.error("💡 解决方案:")
                                cache_cmd = "~/.cache/huggingface/hub/models--sentence-transformers--all-mpnet-base-v2"
                                logger.error(f"   1. 清理模型缓存: rm -rf {cache_cmd}")
                                logger.error("   2. 重新运行系统，让系统自动下载模型")
                                logger.error("   3. 或者设置JINA_API_KEY环境变量使用Jina API")
                                raise download_error
                        else:
                            # 🚀 P0修复：提供详细的错误信息和解决方案
                            logger.error("💡 解决方案:")
                            cache_path = "~/.cache/huggingface/hub/models--sentence-transformers--all-mpnet-base-v2"
                            logger.error(f"   1. 清理模型缓存: rm -rf {cache_path}")
                            logger.error("   2. 重新运行系统，让系统自动下载模型")
                            logger.error("   3. 或者设置JINA_API_KEY环境变量使用Jina API")
                            raise download_error
                logger.info("💡 提示: 本地模型完全免费，优先使用本地模型")
                if self.api_key:
                    msg = "ℹ️  Jina API已配置，但优先使用本地模型"
                    msg += "（如需使用Jina API，请设置环境变量 USE_JINA_API=true）"
                    logger.info(msg)
            except Exception as e:
                logger.warning(f"⚠️ 加载本地模型失败: {e}")
                logger.warning("💡 提示: 可以运行 scripts/download_local_model.py 手动下载模型")
                logger.warning("💡 提示: 或安装本地模型: pip install sentence-transformers")
                self.local_model = None
                self.use_local_model = False
            
            # 如果本地模型加载失败且没有Jina API，记录警告
            if not self.local_model and not self.api_key:
                logger.error("❌ 本地模型加载失败且JINA_API_KEY未设置，无法进行文本向量化")
    
    def encode(self, data: Any) -> Optional[np.ndarray]:
        """
        将文本编码为向量（🆕 优先使用本地模型，支持Jina API fallback）
        
        Args:
            data: 文本字符串或文本列表
        
        Returns:
            向量（numpy array），如果失败返回None
        """
        # 🆕 优先使用本地模型（完全免费，无需API密钥）
        # 即使JINA_API_KEY设置了，也优先使用本地模型
        use_jina_api = os.getenv("USE_JINA_API", "false").lower() == "true"
        
        # 🆕 优先使用本地模型（即使JINA_API_KEY设置了）
        if self.local_model and not use_jina_api:
            try:
                return self._encode_with_local_model(data)
            except Exception as e:
                logger.warning(f"⚠️ 本地模型向量化失败: {e}，尝试Jina API fallback")
                # 继续执行，尝试Jina API fallback
        
        # 如果明确要求使用Jina API，或者本地模型不可用，才使用Jina API
        if use_jina_api or not self.local_model:
            if self.api_key:
                try:
                    # 支持单个文本或文本列表
                    if isinstance(data, str):
                        # 🚀 使用统一的Jina服务
                        embedding = self.jina_service.get_embedding(data, self.model)
                        if embedding is not None:
                            return embedding
                    elif isinstance(data, list):
                        # 🚀 使用统一的Jina服务（批量处理）
                        embeddings = self.jina_service.get_embeddings(data, self.model)
                        if embeddings and len(embeddings) > 0:
                            # 过滤None值
                            valid_embeddings = [e for e in embeddings if e is not None]
                            if valid_embeddings:
                                return np.array(valid_embeddings)
                    
                    # Jina API失败，尝试本地模型fallback
                    if self.local_model:
                        logger.debug("⚠️ Jina API失败，切换到本地模型")
                        return self._encode_with_local_model(data)
                    else:
                        logger.error("Jina API失败且无本地模型fallback")
                        return None
                        
                except Exception as e:
                    logger.warning(f"⚠️ Jina API调用失败: {e}，尝试本地模型fallback")
                    if self.local_model:
                        return self._encode_with_local_model(data)
                    else:
                        logger.error(f"文本向量化失败: {e}")
                        return None
            else:
                # 没有Jina API，必须使用本地模型
                if self.local_model:
                    return self._encode_with_local_model(data)
                else:
                    logger.error("JINA_API_KEY未设置且无本地模型，无法进行文本向量化")
                    logger.error("💡 解决方案: 1) 设置JINA_API_KEY 或 "
                               "2) 安装sentence-transformers: pip install sentence-transformers")
                    return None
        else:
            # 🆕 优先使用本地模型
            try:
                result = self._encode_with_local_model(data)
                if result is not None:
                    return result
            except Exception as e:
                logger.warning(f"⚠️ 本地模型向量化失败: {e}，尝试Jina API fallback")
            
            # 本地模型失败，尝试Jina API fallback
            if self.api_key:
                try:
                    if isinstance(data, str):
                        embedding = self.jina_service.get_embedding(data, self.model)
                        if embedding is not None:
                            logger.debug("✅ 使用Jina API fallback成功")
                            return embedding
                    elif isinstance(data, list):
                        embeddings = self.jina_service.get_embeddings(data, self.model)
                        if embeddings and len(embeddings) > 0:
                            valid_embeddings = [e for e in embeddings if e is not None]
                            if valid_embeddings:
                                logger.debug("✅ 使用Jina API fallback成功")
                                return np.array(valid_embeddings)
                except Exception as e:
                    logger.error(f"❌ Jina API fallback也失败: {e}")
            
            logger.error("❌ 本地模型和Jina API都失败，无法进行文本向量化")
            return None
    
    def _encode_with_local_model(self, data: Any) -> Optional[np.ndarray]:
        """使用本地模型进行向量化（免费fallback）"""
        if not self.local_model:
            return None
        
        try:
            # 🚀 MPS优化：对于MPS设备，使用更大的batch_size以充分利用GPU
            import torch
            batch_size = 32  # 默认batch_size
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                # 检查模型是否在MPS设备上
                model_device = None
                if hasattr(self.local_model, '_modules'):
                    for module in self.local_model._modules.values():
                        if hasattr(module, 'device'):
                            model_device = module.device
                            break
                
                if model_device and 'mps' in str(model_device):
                    # MPS设备，使用更大的batch_size以充分利用GPU
                    batch_size = 128  # MPS设备使用更大的batch_size
                    logger.debug(f"🚀 MPS设备检测到，使用batch_size={batch_size}以充分利用GPU")
            
            if isinstance(data, str):
                embedding = self.local_model.encode(data, convert_to_numpy=True,
                                                   batch_size=batch_size, show_progress_bar=False)
                return embedding
            elif isinstance(data, list):
                embeddings = self.local_model.encode(data, convert_to_numpy=True,
                                                    batch_size=batch_size, show_progress_bar=False)
                return np.array(embeddings)
            else:
                logger.error(f"不支持的数据类型: {type(data)}")
                return None
        except Exception as e:
            logger.error(f"本地模型向量化失败: {e}")
            return None
    
    def validate(self, data: Any) -> bool:
        """
        验证文本数据格式
        
        Args:
            data: 文本数据
        
        Returns:
            是否有效
        """
        if isinstance(data, str):
            return len(data.strip()) > 0
        elif isinstance(data, list):
            return all(isinstance(item, str) and len(item.strip()) > 0 for item in data)
        return False
    
    def get_dimension(self) -> int:
        """获取向量维度"""
        # 确保返回有效的int类型，默认使用Jina v2的768维度
        if hasattr(self, 'dimension') and isinstance(self.dimension, int) and self.dimension > 0:
            return self.dimension
        return 768  # Jina v2默认维度


# 🚀 P0修复：提供获取TextProcessor单例的函数
def get_text_processor() -> TextProcessor:
    """获取TextProcessor单例实例（批次级别共享embedding模型）"""
    global _text_processor_instance
    if _text_processor_instance is None:
        _text_processor_instance = TextProcessor()
    return _text_processor_instance

