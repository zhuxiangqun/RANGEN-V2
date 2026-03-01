"""
多模态处理器模块
支持文本、图像、音频、视频等多种模态
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
import numpy as np


class ModalityProcessor(ABC):
    """多模态处理器基类"""
    
    def __init__(self):
        self.enabled = True
    
    @abstractmethod
    def encode(self, data: Any) -> Optional[np.ndarray]:
        """
        将数据编码为向量
        
        Args:
            data: 原始数据（文本、图像、音频等）
        
        Returns:
            向量（numpy array），如果失败返回None
        """
        pass
    
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """
        验证数据格式
        
        Args:
            data: 原始数据
        
        Returns:
            是否有效
        """
        pass
    
    def get_dimension(self) -> int:
        """
        获取向量维度
        
        Returns:
            向量维度
        """
        return 768  # 默认维度

