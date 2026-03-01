import os
#!/usr/bin/env python3
"""
分层研究系统 - 使用分层架构的完整系统
"""

import logging
from typing import Dict, Any, Optional
from src.core.research_request import ResearchRequest, ResearchResponse
from src.layers import DataLayer, BusinessLayer, PresentationLayer


class Component:
    """分层研究系统"""
    
    def __init__(self, data_service_type: str = "file"):
        self.logger = logging.getLogger(__name__)
        
        # 初始化各层
        self.data_layer = DataLayer()
        self.business_layer = BusinessLayer()
        self.presentation_layer = PresentationLayer()
        
        self.logger.info("分层研究系统初始化完成")
    
    def process_api_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理API请求"""
        try:
            # 验证请求数据
            if not self._validate_api_request(request_data):
                return self._create_error_response("Invalid API request data")
            
            # 处理请求
            result = self.presentation_layer.process_api_request(request_data)
            
            # 记录请求历史
            self._record_request("api", request_data, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"API请求处理失败: {e}")
            return self._create_error_response(f"API request processing failed: {e}")
    
    def _validate_api_request(self, request_data: Dict[str, Any]) -> bool:
        """验证API请求"""
        if not isinstance(request_data, dict):
            return False
        
        if not request_data.get('query'):
            return False
        
        return True
    
    def _create_error_response(self, message: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            'success': False,
            'error': message,
            'timestamp': time.time()
        }
    
    def _record_request(self, request_type: str, request_data: Dict[str, Any], result: Dict[str, Any]):
        """记录请求历史"""
        if not hasattr(self, 'request_history'):
            self.request_history = []
        
        self.request_history.append({
            'type': request_type,
            'request': request_data,
            'result': result,
            'timestamp': time.time()
        })
    
    def process_web_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理Web请求"""
        return self.presentation_layer.process_web_request(request_data)
    
    def process_research_directly(self, query: str, context: Optional[Dict[str, Any]] = None) -> ResearchResponse:
        """直接处理研究请求（跳过表示层）"""
        import time
        request = ResearchRequest(
            request_id=f"req_{int(time.time())}",
            query=query,
            user_id="system",
            context=context or {}
        )
        return self.business_layer.process_research_request(request)
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "system_type": "layered",
            "layers": {
                "data": {
                    "status": "active",
                    "info": {"data_dir": self.data_layer.data_dir}
                },
                "business": {
                    "status": "active",
                    "info": {"initialized": True}
                },
                "presentation": {
                    "status": "active",
                    "info": {"initialized": True}
                }
            },
            "architecture_quality": self._calculate_architecture_quality()
        }
    
    def _calculate_architecture_quality(self) -> Dict[str, Any]:
        """计算架构质量"""
        return {
            "layered_design": True,
            "separation_of_concerns": True,
            "dependency_direction": "correct",  # 表示层 -> 业务层 -> 数据层
            "coupling_level": "low",
            "cohesion_level": "high"
        }
    
    def get_layer_info(self, layer_name: str) -> Dict[str, Any]:
        """获取指定层的信息"""
        if layer_name in ["ui", "logic", "data"]:
            return {
                "name": "数据层",
                "responsibility": "数据访问和存储",
                "service_info": self.data_layer.get_data_service_info(),
                "status": "active"
            }
        else:
            return {"error": "Unknown layer"}
    
    def update_business_rules(self, new_rules: Dict[str, Any]) -> bool:
        """更新业务规则"""
        return self.business_layer.update_business_rules(new_rules)
    
    def save_research_history(self, response: ResearchResponse) -> bool:
        """保存研究历史"""
        try:
            self.data_layer.save_research_history(response)
            return True
        except Exception as e:
            self.logger.error(f"保存研究历史失败: {e}")
            return False
    
    def get_research_history(self, limit: int = 10) -> list:
        """获取研究历史"""
        return self.data_layer.get_research_history(limit)
    
    def get_architecture_benefits(self) -> Dict[str, Any]:
        """获取架构优势"""
        return {
            "maintainability": "高 - 各层职责清晰，易于维护",
            "testability": "高 - 可以独立测试每一层",
            "scalability": "高 - 可以独立扩展每一层",
            "flexibility": "高 - 可以替换实现而不影响其他层",
            "coupling": "低 - 层间依赖关系清晰",
            "cohesion": "高 - 每层内部高度内聚"
        }


# 便捷函数
def get_layered_research_system(data_service_type: str = "file") -> LayeredResearchSystem:
    """获取分层研究系统实例"""
    return LayeredResearchSystem(data_service_type)
