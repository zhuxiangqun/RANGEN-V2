#!/usr/bin/env python3
"""
表示层 - 负责用户界面和API接口
"""

import logging
import os
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from datetime import datetime
from src.core.research_request import ResearchRequest, ResearchResponse

logger = logging.getLogger(__name__)


class PresentationLayer:
    """表示层 - 负责用户界面和API接口"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("表示层初始化完成")
    
    def format_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化响应"""
        try:
            self.logger.info("响应格式化完成")
            return {"status": "success", "response": data}
        except Exception as e:
            self.logger.error(f"响应格式化失败: {e}")
            return {"status": "error", "error": str(e)}
    
    def process_api_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理API请求"""
        try:
            self.logger.info("API请求处理完成")
            return {"status": "success", "data": request_data}
        except Exception as e:
            self.logger.error(f"API请求处理失败: {e}")
            return {"status": "error", "error": str(e)}
    
    def process_web_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理Web请求"""
        try:
            self.logger.info("Web请求处理完成")
            return {"status": "success", "data": request_data}
        except Exception as e:
            self.logger.error(f"Web请求处理失败: {e}")
            return {"status": "error", "error": str(e)}


class PresentationInterface(ABC):
    """表示层接口"""
    
    @abstractmethod
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求"""
        try:
            # 验证请求数据
            if not self._validate_request_data(request_data):
                return self._create_error_response("Invalid request data")
            
            # 提取请求信息
            request_type = request_data.get('type', 'unknown')
            user_id = request_data.get('user_id', 'anonymous')
            query = request_data.get('query', '')
            
            # 根据请求类型处理
            if request_type == 'research_query':
                return self._process_research_query(request_data)
            elif request_type == 'data_analysis':
                return self._process_data_analysis(request_data)
            elif request_type == 'report_generation':
                return self._process_report_generation(request_data)
            else:
                return self._process_default_request(request_data)
                
        except Exception as e:
            return self._create_error_response(f"Request processing failed: {e}")
    
    def _validate_request_data(self, request_data: Dict[str, Any]) -> bool:
        """验证请求数据"""
        return isinstance(request_data, dict) and 'type' in request_data
    
    def _process_research_query(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理研究查询请求"""
        query = request_data.get('query', '')
        context = request_data.get('context', {})
        
        return {
            'success': True,
            'type': 'research_query',
            'query': query,
            'context': context,
            'timestamp': time.time()
        }
    
    def _process_data_analysis(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理数据分析请求"""
        data = request_data.get('data', [])
        analysis_type = request_data.get('analysis_type', 'basic')
        
        return {
            'success': True,
            'type': 'data_analysis',
            'data_count': len(data),
            'analysis_type': analysis_type,
            'timestamp': time.time()
        }
    
    def _process_report_generation(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理报告生成请求"""
        report_type = request_data.get('report_type', 'standard')
        parameters = request_data.get('parameters', {})
        
        return {
            'success': True,
            'type': 'report_generation',
            'report_type': report_type,
            'parameters': parameters,
            'timestamp': time.time()
        }
    
    def _process_default_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理默认请求"""
        return {
            'success': True,
            'type': 'default',
            'data': request_data,
            'timestamp': time.time()
        }
    
    def _create_error_response(self, message: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            'success': False,
            'error': message,
            'timestamp': time.time()
        }
    
    @abstractmethod
    def format_response(self, response: ResearchResponse) -> Dict[str, Any]:
        """格式化响应"""
        try:
            # 验证响应数据
            if not self._validate_response_data(response):
                return self._create_error_response("Invalid response data")
            
            # 提取响应信息
            response_type = getattr(response, 'type', 'unknown')
            data = getattr(response, 'data', None)
            success = getattr(response, 'success', False)
            
            # 根据响应类型格式化
            if response_type == 'research_result':
                return self._format_research_result(response)
            elif response_type == 'analysis_result':
                return self._format_analysis_result(response)
            elif response_type == 'report_result':
                return self._format_report_result(response)
            else:
                return self._format_default_response(response)
                
        except Exception as e:
            return self._create_error_response(f"Response formatting failed: {e}")
    
    def _validate_response_data(self, response: ResearchResponse) -> bool:
        """验证响应数据"""
        return response is not None and hasattr(response, 'success')
    
    def _format_research_result(self, response: ResearchResponse) -> Dict[str, Any]:
        """格式化研究结果"""
        return {
            'success': response.success,
            'type': 'research_result',
            'data': getattr(response, 'data', None),
            'metadata': getattr(response, 'metadata', {}),
            'timestamp': time.time()
        }
    
    def _format_analysis_result(self, response: ResearchResponse) -> Dict[str, Any]:
        """格式化分析结果"""
        return {
            'success': response.success,
            'type': 'analysis_result',
            'data': getattr(response, 'data', None),
            'confidence': getattr(response, 'confidence', 0.0),
            'timestamp': time.time()
        }
    
    def _format_report_result(self, response: ResearchResponse) -> Dict[str, Any]:
        """格式化报告结果"""
        return {
            'success': response.success,
            'type': 'report_result',
            'data': getattr(response, 'data', None),
            'format': getattr(response, 'format', 'text'),
            'timestamp': time.time()
        }
    
    def _format_default_response(self, response: ResearchResponse) -> Dict[str, Any]:
        """格式化默认响应"""
        return {
            'success': response.success,
            'type': 'default',
            'data': getattr(response, 'data', None),
            'timestamp': time.time()
        }

class ResearchAPI(PresentationInterface):
    """研究API接口"""
    
    def __init__(self, business_service):
        self.business_service = business_service
        self.logger = logging.getLogger(__name__)
    
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理API请求"""
        try:
            # 验证请求数据
            if not self._validate_request_data(request_data):
                return self._create_error_response("Invalid request data")
            
            # 创建研究请求
            request = ResearchRequest(
                request_id=request_data.get("request_id", ""),
                user_id=request_data.get("user_id", ""),
                query=request_data.get("query", ''),
                context=request_data.get("context", {})
            )
            
            # 调用业务层服务
            response = self.business_service.process_research(request)
            
            # 格式化响应
            return self.format_response(response)
            
        except Exception as e:
            self.logger.error(f"API请求处理失败: {e}")
            return self._create_error_response(str(e))
    
    def format_response(self, response: ResearchResponse) -> Dict[str, Any]:
        """格式化API响应"""
        return {
            "success": True,
            "data": {
                "result": response.result,
                "confidence": response.confidence,
                "metadata": response.metadata or {}
            },
            "timestamp": datetime.fromtimestamp(response.timestamp).isoformat() if response.timestamp else None
        }
    
    def _validate_request_data(self, request_data: Dict[str, Any]) -> bool:
        """验证请求数据 - 增强版"""
        try:
            # 基本类型验证
            if not isinstance(request_data, dict):
                self.logger.warning("请求数据不是字典类型")
                return False
            
            # 检查必要字段
            required_fields = ["query", "user_id"]
            for field in required_fields:
                if field not in request_data:
                    self.logger.warning(f"缺少必要字段: {field}")
                    return False
            
            # 验证字段类型
            if not isinstance(request_data.get("query"), str):
                self.logger.warning("query字段必须是字符串类型")
                return False
            
            if not isinstance(request_data.get("user_id"), str):
                self.logger.warning("user_id字段必须是字符串类型")
                return False
            
            # 验证字段内容
            query = request_data.get("query", "").strip()
            if not query:
                self.logger.warning("query字段不能为空")
                return False
            
            if len(query) > 1000:
                self.logger.warning("query字段长度超过限制")
                return False
            
            user_id = request_data.get("user_id", "").strip()
            if not user_id:
                self.logger.warning("user_id字段不能为空")
                return False
            
            # 验证可选字段
            if "context" in request_data:
                context = request_data["context"]
                if not isinstance(context, dict):
                    self.logger.warning("context字段必须是字典类型")
                    return False
            
            if "request_id" in request_data:
                request_id = request_data["request_id"]
                if not isinstance(request_id, str):
                    self.logger.warning("request_id字段必须是字符串类型")
                    return False
            
            # 验证查询内容质量
            if not self._validate_query_quality(query):
                self.logger.warning("查询内容质量不符合要求")
                return False
            
            # 验证用户权限
            if not self._validate_user_permissions(user_id):
                self.logger.warning("用户权限验证失败")
                return False
            
            # 验证请求频率
            if not self._validate_request_frequency(user_id):
                self.logger.warning("请求频率超过限制")
                return False
            
            # 验证请求大小
            if not self._validate_request_size(request_data):
                self.logger.warning("请求大小超过限制")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"请求数据验证失败: {e}")
            return False
    
    def _validate_query_quality(self, query: str) -> bool:
        """验证查询质量"""
        try:
            # 检查查询长度
            if len(query) < 3:
                return False
            
            # 检查是否包含有效字符
            if not any(c.isalnum() for c in query):
                return False
            
            # 检查是否包含恶意内容
            malicious_patterns = ['<script', 'javascript:', 'onload=', 'onerror=']
            if any(pattern in query.lower() for pattern in malicious_patterns):
                return False
            
            # 检查是否包含过多特殊字符
            special_char_count = sum(1 for c in query if not c.isalnum() and not c.isspace())
            if special_char_count > len(query) * 0.5:
                return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"查询质量验证失败: {e}")
            return False
    
    def _validate_user_permissions(self, user_id: str) -> bool:
        """验证用户权限"""
        try:
            # 这里可以实现用户权限验证逻辑
            # 目前返回True，实际应用中应该检查用户权限
            return True
            
        except Exception as e:
            self.logger.warning(f"用户权限验证失败: {e}")
            return False
    
    def _validate_request_frequency(self, user_id: str) -> bool:
        """验证请求频率"""
        try:
            # 这里可以实现请求频率验证逻辑
            # 目前返回True，实际应用中应该检查请求频率
            return True
            
        except Exception as e:
            self.logger.warning(f"请求频率验证失败: {e}")
            return False
    
    def _validate_request_size(self, request_data: Dict[str, Any]) -> bool:
        """验证请求大小"""
        try:
            # 计算请求大小
            import json
            request_size = len(json.dumps(request_data, ensure_ascii=False))
            
            # 检查是否超过限制（1MB）
            max_size = 1024 * 1024
            if request_size > max_size:
                return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"请求大小验证失败: {e}")
            return False
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            "success": False,
            "error": error_message,
            "data": None
        }

class WebInterface(PresentationInterface):
    """Web界面接口"""
    
    def __init__(self, business_service):
        self.business_service = business_service
        self.logger = logging.getLogger(__name__)
    
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理Web请求"""
        try:
            # 验证请求数据
            if not self._validate_request_data(request_data):
                return self._create_error_response("Invalid request data")
            
            # 创建研究请求
            request = ResearchRequest(
                request_id=request_data.get("request_id", ""),
                user_id=request_data.get("user_id", ""),
                query=request_data.get("query", ''),
                context=request_data.get("context", {})
            )
            
            # 调用业务层服务
            response = self.business_service.process_research(request)
            
            # 格式化响应
            return self.format_response(response)
            
        except Exception as e:
            self.logger.error(f"Web请求处理失败: {e}")
            return self._create_error_response(str(e))
    
    def format_response(self, response: ResearchResponse) -> Dict[str, Any]:
        """格式化Web响应"""
        return {
            "status": "success",
            "html": f"<div class='result'>{response.result}</div>",
            "json": {
                "result": response.result,
                "confidence": response.confidence,
                "metadata": response.metadata or {}
            }
        }
    
    def _validate_request_data(self, request_data: Dict[str, Any]) -> bool:
        """验证请求数据"""
        try:
            # 基本验证逻辑
            if not isinstance(request_data, dict):
                return False
            
            # 检查必要字段
            required_fields = ["query", "user_id"]
            for field in required_fields:
                if field not in request_data:
                    return False
            
            return True
        except Exception:
            return False
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            "status": "error",
            "html": f"<div class='error'>{error_message}</div>",
            "json": {"error": error_message}
        }

class PresentationLayerManager:
    """表示层管理器"""
    
    def __init__(self, business_service):
        self.business_service = business_service
        self.api = ResearchAPI(business_service)
        self.web = WebInterface(business_service)
        self.logger = logging.getLogger(__name__)
    
    def process_api_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理API请求"""
        return self.api.process_request(request_data)
    
    def process_web_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理Web请求"""
        return self.web.process_request(request_data)
    
    def get_available_interfaces(self) -> Dict[str, Any]:
        """获取可用接口"""
        return {
            "api": {
                "status": "active",
                "info": "REST API接口"
            },
            "web": {
                "status": "active", 
                "info": "Web界面接口"
            }
        }
    
    def get_interface_stats(self) -> Dict[str, Any]:
        """获取接口统计"""
        return {
            "total_interfaces": 2,
            "active_interfaces": 2,
            "interface_types": ["api", "web"]
        }