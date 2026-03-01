"""
多模态处理服务
封装图像、音频、视频等多模态内容的处理功能

注意：这是一个服务组件，不是Agent。它提供多模态处理功能，可以被Agent使用。
"""

from typing import Dict, Any, List, Optional, Union
from enum import Enum
import logging
import time
import asyncio
import inspect

from src.agents.base_agent import BaseAgent, AgentResult, AgentConfig

logger = logging.getLogger(__name__)


class ModalityType(Enum):
    """模态类型"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    UNKNOWN = "unknown"


class MultimodalTaskType(Enum):
    """多模态任务类型"""
    ENCODE = "encode"  # 编码为向量
    ANALYZE = "analyze"  # 分析内容（分类、检测等）
    UNDERSTAND = "understand"  # 理解内容（生成描述、提取信息等）
    PROCESS = "process"  # 通用处理


class MultimodalService(BaseAgent):
    """多模态处理服务
    
    这是一个服务组件，不是Agent。它提供多模态处理功能，可以被Agent使用。
    """
    
    def __init__(self, agent_name: str = "MultimodalService"):
        config = AgentConfig(
            agent_id=agent_name,
            agent_type="multimodal"
        )
        super().__init__(agent_name, ["multimodal_processing", "image_processing", 
                                      "audio_processing", "video_processing"], config)
        
        self.config = config
        
        # 多模态处理器
        self.image_processor = None
        self.audio_processor = None
        self.video_processor = None
        self.computer_vision_engine = None
        
        # 初始化处理器
        self._initialize_processors()
        
        logger.info("✅ 多模态处理服务初始化完成")
    
    def _initialize_processors(self):
        """初始化多模态处理器"""
        try:
            # 初始化图像处理器
            try:
                from knowledge_management_system.modalities.image_processor import ImageProcessor
                self.image_processor = ImageProcessor()
                logger.info("✅ 图像处理器初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ 图像处理器初始化失败: {e}")
                self.image_processor = None
            
            # 初始化音频处理器
            try:
                from knowledge_management_system.modalities.audio_processor import AudioProcessor
                self.audio_processor = AudioProcessor()
                logger.info("✅ 音频处理器初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ 音频处理器初始化失败: {e}")
                self.audio_processor = None
            
            # 初始化视频处理器
            try:
                from knowledge_management_system.modalities.video_processor import VideoProcessor
                self.video_processor = VideoProcessor()
                logger.info("✅ 视频处理器初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ 视频处理器初始化失败: {e}")
                self.video_processor = None
            
            # 初始化计算机视觉引擎
            try:
                from src.ai.computer_vision_engine import ComputerVisionEngine
                self.computer_vision_engine = ComputerVisionEngine()
                logger.info("✅ 计算机视觉引擎初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ 计算机视觉引擎初始化失败: {e}")
                self.computer_vision_engine = None
                
        except Exception as e:
            logger.error(f"❌ 多模态处理器初始化失败: {e}", exc_info=True)
    
    def _detect_modality(self, context: Dict[str, Any]) -> ModalityType:
        """检测输入内容的模态类型"""
        # 检查是否有明确的模态类型
        modality_str = context.get("modality", "").lower()
        if modality_str:
            try:
                return ModalityType(modality_str)
            except ValueError:
                pass
        
        # 检查输入数据
        input_data = context.get("input_data") or context.get("data") or context.get("content")
        
        if input_data is None:
            return ModalityType.UNKNOWN
        
        # 根据文件扩展名或数据类型判断
        if isinstance(input_data, str):
            input_lower = input_data.lower()
            if any(ext in input_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']):
                return ModalityType.IMAGE
            elif any(ext in input_lower for ext in ['.mp3', '.wav', '.flac', '.ogg', '.m4a']):
                return ModalityType.AUDIO
            elif any(ext in input_lower for ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']):
                return ModalityType.VIDEO
            else:
                return ModalityType.TEXT
        
        # 根据数据类型判断
        import numpy as np
        if isinstance(input_data, np.ndarray):
            # 如果是numpy数组，根据维度判断
            if len(input_data.shape) == 3:  # 可能是图像 (H, W, C)
                return ModalityType.IMAGE
            elif len(input_data.shape) == 1:  # 可能是音频波形
                return ModalityType.AUDIO
        
        return ModalityType.UNKNOWN
    
    async def encode(self, context: Dict[str, Any]) -> AgentResult:
        """编码多模态内容为向量"""
        start_time = time.time()
        
        try:
            modality = self._detect_modality(context)
            input_data = context.get("input_data") or context.get("data") or context.get("content")
            
            if not input_data:
                return AgentResult(
                    success=False,
                    data=None,
                    error="未提供输入数据",
                    confidence=0.0,
                    processing_time=time.time() - start_time
                )
            
            vector = None
            
            if modality == ModalityType.IMAGE:
                if self.image_processor:
                    # 使用图像处理器编码
                    if hasattr(self.image_processor, 'encode'):
                        vector = self.image_processor.encode(input_data)
                elif self.computer_vision_engine:
                    # 使用计算机视觉引擎提取特征
                    if hasattr(self.computer_vision_engine, 'extract_features'):
                        result = self.computer_vision_engine.extract_features(input_data)
                        if result and hasattr(result, 'features'):
                            vector = result.features
            
            elif modality == ModalityType.AUDIO:
                if self.audio_processor and hasattr(self.audio_processor, 'encode'):
                    vector = self.audio_processor.encode(input_data)
            
            elif modality == ModalityType.VIDEO:
                if self.video_processor and hasattr(self.video_processor, 'encode'):
                    vector = self.video_processor.encode(input_data)
            
            elif modality == ModalityType.TEXT:
                # 文本编码应该由知识检索服务处理
                return AgentResult(
                    success=False,
                    data=None,
                    error="文本编码应由知识检索服务处理",
                    confidence=0.0,
                    processing_time=time.time() - start_time
                )
            
            if vector is not None:
                import numpy as np
                if isinstance(vector, np.ndarray):
                    vector = vector.tolist()
                
                return AgentResult(
                    success=True,
                    data={
                        "vector": vector,
                        "modality": modality.value,
                        "dimension": len(vector) if vector else 0
                    },
                    confidence=0.9,
                    processing_time=time.time() - start_time
                )
            else:
                return AgentResult(
                    success=False,
                    data=None,
                    error=f"无法编码{modality.value}模态内容（处理器未实现或未启用）",
                    confidence=0.0,
                    processing_time=time.time() - start_time
                )
                
        except Exception as e:
            logger.error(f"❌ 多模态编码失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    async def analyze(self, context: Dict[str, Any]) -> AgentResult:
        """分析多模态内容（分类、检测等）"""
        start_time = time.time()
        
        try:
            modality = self._detect_modality(context)
            input_data = context.get("input_data") or context.get("data") or context.get("content")
            task_type = context.get("task_type", "classification")  # classification, detection, etc.
            
            if not input_data:
                return AgentResult(
                    success=False,
                    data=None,
                    error="未提供输入数据",
                    confidence=0.0,
                    processing_time=time.time() - start_time
                )
            
            result_data = None
            
            if modality == ModalityType.IMAGE and self.computer_vision_engine:
                # 使用计算机视觉引擎分析图像
                if task_type == "classification":
                    if hasattr(self.computer_vision_engine, 'classify_image'):
                        result = self.computer_vision_engine.classify_image(input_data)
                        result_data = result
                elif task_type == "detection":
                    if hasattr(self.computer_vision_engine, 'detect_objects'):
                        result = self.computer_vision_engine.detect_objects(input_data)
                        result_data = result
                elif task_type == "ocr":
                    if hasattr(self.computer_vision_engine, 'extract_text'):
                        result = self.computer_vision_engine.extract_text(input_data)
                        result_data = result
            
            if result_data:
                return AgentResult(
                    success=True,
                    data={
                        "result": result_data,
                        "modality": modality.value,
                        "task_type": task_type
                    },
                    confidence=0.85,
                    processing_time=time.time() - start_time
                )
            else:
                return AgentResult(
                    success=False,
                    data=None,
                    error=f"无法分析{modality.value}模态内容（任务类型: {task_type}）",
                    confidence=0.0,
                    processing_time=time.time() - start_time
                )
                
        except Exception as e:
            logger.error(f"❌ 多模态分析失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    async def understand(self, context: Dict[str, Any]) -> AgentResult:
        """理解多模态内容（生成描述、提取信息等）"""
        start_time = time.time()
        
        try:
            modality = self._detect_modality(context)
            input_data = context.get("input_data") or context.get("data") or context.get("content")
            query = context.get("query", "")
            
            if not input_data:
                return AgentResult(
                    success=False,
                    data=None,
                    error="未提供输入数据",
                    confidence=0.0,
                    processing_time=time.time() - start_time
                )
            
            # 目前主要支持图像理解
            if modality == ModalityType.IMAGE and self.computer_vision_engine:
                # 提取图像特征和描述
                description = None
                features = None
                
                if hasattr(self.computer_vision_engine, 'describe_image'):
                    description = self.computer_vision_engine.describe_image(input_data)
                elif hasattr(self.computer_vision_engine, 'extract_features'):
                    result = self.computer_vision_engine.extract_features(input_data)
                    if result:
                        features = result
                
                return AgentResult(
                    success=True,
                    data={
                        "description": description,
                        "features": features,
                        "modality": modality.value,
                        "query": query
                    },
                    confidence=0.8,
                    processing_time=time.time() - start_time
                )
            else:
                return AgentResult(
                    success=False,
                    data=None,
                    error=f"暂不支持{modality.value}模态的内容理解",
                    confidence=0.0,
                    processing_time=time.time() - start_time
                )
                
        except Exception as e:
            logger.error(f"❌ 多模态理解失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    async def process(self, context: Dict[str, Any]) -> AgentResult:
        """通用多模态处理"""
        start_time = time.time()
        
        try:
            task_type = context.get("task_type", "encode")
            
            if task_type == "encode":
                return await self.encode(context)
            elif task_type == "analyze":
                return await self.analyze(context)
            elif task_type == "understand":
                return await self.understand(context)
            else:
                # 默认尝试编码
                return await self.encode(context)
                
        except Exception as e:
            logger.error(f"❌ 多模态处理失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行多模态处理任务（Service接口）"""
        task_type = context.get("task_type", "process")
        
        if task_type == "encode":
            return await self.encode(context)
        elif task_type == "analyze":
            return await self.analyze(context)
        elif task_type == "understand":
            return await self.understand(context)
        else:
            return await self.process(context)
    
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """处理查询 - 同步接口，保持功能完整性"""
        import asyncio
        
        try:
            # 准备上下文
            if context is None:
                context = {}
            
            # 如果query是文件路径或数据，作为input_data
            if query and not context.get("input_data"):
                context["input_data"] = query
            
            # 如果已经在事件循环中，使用 run_in_executor
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 在事件循环中，使用 run_in_executor
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.execute(context))
                        return future.result()
                else:
                    # 不在事件循环中，直接运行
                    return loop.run_until_complete(self.execute(context))
            except RuntimeError:
                # 没有事件循环，创建新的
                return asyncio.run(self.execute(context))
                
        except Exception as e:
            logger.error(f"❌ 多模态查询处理失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=0.0
            )

