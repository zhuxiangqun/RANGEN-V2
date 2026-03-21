"""
多模态处理工具
封装MultimodalService，供标准Agent使用
"""

from typing import Dict, Any, Optional
import logging
import time

from .base_tool import BaseTool, ToolResult
from src.services.multimodal_service import MultimodalService

logger = logging.getLogger(__name__)


class MultimodalTool(BaseTool):
    """多模态处理工具 - 封装MultimodalService"""
    
    def __init__(self):
        super().__init__(
            tool_name="multimodal",
            description="处理多模态内容（图像、音频、视频等），支持编码、分析、理解等任务"
        )
        
        self._service = None
        logger.info("✅ 多模态处理工具初始化完成")
    
    def _get_service(self):
        """延迟初始化Service"""
        if self._service is None:
            try:
                self._service = MultimodalService()
                self.logger.info("✅ 多模态处理服务初始化成功")
            except Exception as e:
                self.logger.error(f"❌ 多模态处理服务初始化失败: {e}")
                raise
        return self._service
    
    async def call(self, input_data: str, task_type: str = "process", 
                   modality: str = "auto", query: str = "", **kwargs) -> ToolResult:
        """
        调用多模态处理服务
        
        Args:
            input_data: 输入数据（文件路径或数据）（必需）
            task_type: 任务类型（可选，默认"process"）
                - "encode": 编码为向量
                - "analyze": 分析内容（分类、检测等）
                - "understand": 理解内容（生成描述、提取信息等）
                - "process": 通用处理
            modality: 模态类型（可选，默认"auto"）
                - "auto": 自动检测
                - "image": 图像
                - "audio": 音频
                - "video": 视频
            query: 查询内容（可选，用于理解任务）
            **kwargs: 其他参数
            
        Returns:
            ToolResult: 工具执行结果
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"🖼️ 多模态处理工具调用: task_type={task_type}, modality={modality}, input_data={input_data[:100] if isinstance(input_data, str) else str(input_data)[:100]}...")
            
            if not input_data:
                return ToolResult(
                    success=False,
                    data=None,
                    error="未提供输入数据",
                    execution_time=time.time() - start_time
                )
            
            service = self._get_service()
            service_context = {
                "task_type": task_type,
                "input_data": input_data,
                "modality": modality,
                "query": query,
                **kwargs
            }
            
            result = await service.execute(service_context)
            
            # 转换AgentResult为ToolResult
            return ToolResult(
                success=result.success,
                data=result.data,
                error=result.error,
                execution_time=result.processing_time if hasattr(result, 'processing_time') else (time.time() - start_time),
                metadata={
                    "confidence": getattr(result, 'confidence', 0.0),
                    "task_type": task_type,
                    "modality": modality
                }
            )
        except Exception as e:
            self.logger.error(f"❌ 多模态处理工具调用失败: {e}", exc_info=True)
            self._record_call(False)
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """工具参数模式"""
        return {
            "type": "object",
            "properties": {
                "input_data": {
                    "type": "string",
                    "description": "输入数据（文件路径或数据）"
                },
                "task_type": {
                    "type": "string",
                    "enum": ["encode", "analyze", "understand", "process"],
                    "description": "任务类型：encode（编码为向量）、analyze（分析内容）、understand（理解内容）、process（通用处理）",
                    "default": "process"
                },
                "modality": {
                    "type": "string",
                    "enum": ["auto", "image", "audio", "video"],
                    "description": "模态类型：auto（自动检测）、image（图像）、audio（音频）、video（视频）",
                    "default": "auto"
                },
                "query": {
                    "type": "string",
                    "description": "查询内容（用于理解任务）",
                    "default": ""
                }
            },
            "required": ["input_data"]
        }
