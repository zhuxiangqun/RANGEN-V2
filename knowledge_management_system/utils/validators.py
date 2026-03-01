#!/usr/bin/env python3
"""
知识库管理系统数据验证模块
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
import json
from .logger import get_logger

logger = get_logger()


class KnowledgeValidator:
    """知识数据验证器"""
    
    @staticmethod
    def validate_text_knowledge(data: Dict[str, Any]) -> tuple:
        """
        验证文本知识数据
        
        Returns:
            (is_valid, error_message)
        """
        if not isinstance(data, dict):
            return False, "数据必须是字典格式"
        
        # 必须字段
        required_fields = ['content']
        for field in required_fields:
            if field not in data:
                return False, f"缺少必需字段: {field}"
        
        # 内容验证
        content = data.get('content', '')
        if not isinstance(content, str):
            return False, "content必须是字符串"
        
        if len(content.strip()) < 5:
            return False, "content内容太短（至少5个字符）"
        
        if len(content) > 10000000:
            return False, "content内容太长（最多10000000个字符）"
        
        return True, None
    
    @staticmethod
    def validate_image_knowledge(data: Dict[str, Any]) -> tuple:
        """
        验证图像知识数据
        
        Returns:
            (is_valid, error_message)
        """
        if not isinstance(data, dict):
            return False, "数据必须是字典格式"
        
        # 必须字段
        if 'image_path' not in data and 'image_data' not in data:
            return False, "缺少image_path或image_data字段"
        
        # 验证图像路径或数据
        if 'image_path' in data:
            image_path = Path(data['image_path'])
            if not image_path.exists():
                return False, f"图像文件不存在: {image_path}"
        
        return True, None
    
    @staticmethod
    def validate_metadata(data: Dict[str, Any]) -> tuple:
        """
        验证元数据
        
        Returns:
            (is_valid, error_message)
        """
        if not isinstance(data, dict):
            return False, "元数据必须是字典格式"
        
        # 可选但建议的字段
        suggested_fields = ['title', 'source', 'tags', 'category']
        
        return True, None


def validate_knowledge_data(data: Dict[str, Any], modality: str = "text") -> tuple:
    """
    验证知识数据（统一入口）
    
    Args:
        data: 知识数据
        modality: 模态类型 (text|image|audio|video)
    
    Returns:
        (is_valid, error_message)
    """
    validator = KnowledgeValidator()
    
    if modality == "text":
        return validator.validate_text_knowledge(data)
    elif modality == "image":
        return validator.validate_image_knowledge(data)
    elif modality in ["audio", "video"]:
        # 暂时返回True，后续实现
        return True, None
    else:
        return False, f"不支持的模态类型: {modality}"
