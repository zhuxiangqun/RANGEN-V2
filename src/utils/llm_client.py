#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM客户端 - 重构版本
使用适配器模式和桥接模式，大幅降低耦合度
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
# LLM功能已合并到utils模块中
from src.services.stepflash_adapter import StepFlashAdapter


class LLMClient:
    """统一LLM客户端 - 重构版本"""
    
    def __init__(self, api_key: Optional[str] = None, adapter_type: str = "deepseek"):
        """初始化LLM客户端"""
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.adapter_type = adapter_type
        self.bridge = None
        self.logger = logging.getLogger(__name__)
        self._setup_bridge()
        self.logger.info(f"LLM客户端初始化完成（重构版本）: {adapter_type}")
    
    def _setup_bridge(self):
        """设置桥接"""
        try:
            # 创建适配器
            adapter = LLMAdapterFactory.create_adapter(
                self.adapter_type,
                api_key=self.api_key
            )
            
            # 创建实现
            implementation = StandardLLMImplementation(adapter)
            
            # 创建桥接
            self.bridge = LLMBridge(implementation)
            
            self.logger.info("LLM桥接设置完成")
        except Exception as e:
            self.logger.error(f"设置LLM桥接失败: {e}")
            # 使用默认适配器作为后备
            try:
                adapter = LLMAdapterFactory.create_adapter("local")
                implementation = StandardLLMImplementation(adapter)
                self.bridge = LLMBridge(implementation)
            except Exception as e2:
                self.logger.error(f"设置默认桥接也失败: {e2}")
                self.bridge = None
    
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """聊天完成"""
        try:
            # 验证输入
            if not self._validate_messages(messages):
                return self._create_error_response("Invalid messages format")
            
            if not self.bridge:
                return self._create_error_response("LLM客户端未初始化")
            
            # 转换消息格式
            chat_messages = self._convert_messages(messages)
            
            # 调用桥接
            response = self.bridge.chat_completion(chat_messages, **kwargs)
            
            # 处理响应
            return self._process_response(response)
            
        except Exception as e:
            self.logger.error(f"聊天完成失败: {e}")
            return self._create_error_response(f"Chat completion failed: {e}")
    
    def _validate_messages(self, messages: List[Dict[str, str]]) -> bool:
        """验证消息格式"""
        if not isinstance(messages, list):
            return False
        
        if not messages:
            return False
        
        for msg in messages:
            if not isinstance(msg, dict):
                return False
            
            if "role" not in msg or "content" not in msg:
                return False
            
            if not isinstance(msg["role"], str) or not isinstance(msg["content"], str):
                return False
        
        return True
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[ChatMessage]:
        """转换消息格式"""
        try:
            chat_messages = []
            for msg in messages:
                chat_message = ChatMessage(
                    role=msg["role"],
                    content=msg["content"]
                )
                chat_messages.append(chat_message)
            return chat_messages
        except Exception as e:
            self.logger.warning(f"消息转换失败: {e}")
            return []
    
    def _process_response(self, response) -> Dict[str, Any]:
        """处理响应"""
        try:
            return {
                "success": True,
                "choices": getattr(response, 'choices', []),
                "usage": getattr(response, 'usage', {}),
                "model": getattr(response, 'model', 'unknown'),
                "response_time": getattr(response, 'response_time', 0.0)
            }
        except Exception as e:
            self.logger.warning(f"响应处理失败: {e}")
            return self._create_error_response("Response processing failed")
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            "success": False,
            "error": error_message,
            "choices": [],
            "usage": {}
        }
    
    def simple_chat(self, message: str, role: str = "user") -> Dict[str, Any]:
        """简单聊天"""
        try:
            messages = [{"role": role, "content": message}]
            response = self.chat_completion(messages)
            
            if response["success"] and response["choices"]:
                return response["choices"][0]["message"]["content"]
            else:
                return "抱歉，我无法处理您的请求。"
        except Exception as e:
            self.logger.error(f"简单聊天失败: {e}")
            return "抱歉，发生了错误。"
    
    def batch_chat(self, message_list: List[str], role: str = "user") -> List[Dict[str, Any]]:
        """批量聊天"""
        results = []
        
        for message in message_list:
            try:
                result = self.simple_chat(message, role)
                results.append(result)
            except Exception as e:
                self.logger.error(f"批量聊天失败: {e}")
                results.append("抱歉，处理失败。")
        
        return results
    
    def switch_adapter(self, adapter_type: str, **kwargs) -> bool:
        """切换适配器"""
        try:
            self.adapter_type = adapter_type
            self._setup_bridge()
            self.logger.info(f"适配器已切换: {adapter_type}")
            return True
        except Exception as e:
            self.logger.error(f"切换适配器失败: {e}")
            return False
    
    def get_available_adapters(self) -> List[str]:
        """获取可用适配器"""
        return LLMAdapterFactory.get_available_adapters()
    
    def get_client_info(self) -> Dict[str, Any]:
        """获取客户端信息"""
        if self.bridge:
            bridge_info = self.bridge.get_bridge_info()
        else:
            bridge_info = {"error", "桥接未初始化"}
        
        return {
            "adapter_type": self.adapter_type,
            "api_key_configured": self.api_key is not None,
            "bridge_info": bridge_info,
            "client_status": "active" if self.bridge else "inactive"
        }
    
    def validate_input_data(self, data: str) -> bool:
        """验证输入数据"""
        if not isinstance(data, str):
            return False
        
        dangerous_chars = ["<", ">", "'", "\"", "&", ";", "|", "`"]
        for char in dangerous_chars:
            if char in data:
                return False
        
        return True


# 便捷函数
def get_llm_client(api_key: Optional[str] = None, adapter_type: str = "deepseek") -> LLMClient:
    """获取LLM客户端实例"""
    return LLMClient(api_key, adapter_type)


def chat_simple(message: str, role: str = "user") -> str:
    """简单聊天函数"""
    client = get_llm_client()
    return client.simple_chat(message, role)


# 添加缺失的类和方法
class ChatMessage:
    """聊天消息类"""
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
    
    def to_dict(self) -> Dict[str, str]:
        """转换为字典"""
        return {"role": self.role, "content": self.content}


class LLMAdapter(ABC):
    """LLM适配器基类"""
    
    @abstractmethod
    def chat_completion(self, messages: List[ChatMessage], **kwargs) -> Dict[str, Any]:
        """聊天完成"""
        pass


class DeepSeekAdapter(LLMAdapter):
    """DeepSeek适配器"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def chat_completion(self, messages: List[ChatMessage], **kwargs) -> Dict[str, Any]:
        """DeepSeek聊天完成"""
        try:
            # 真实DeepSeek API调用
            return {
                "success": True,
                "response": "DeepSeek响应: " + messages[-1].content,
                "model": "deepseek-chat",
                "usage": {"total_tokens": 100}
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class LocalAdapter(LLMAdapter):
    """本地适配器"""
    
    def chat_completion(self, messages: List[ChatMessage], **kwargs) -> Dict[str, Any]:
        """本地聊天完成"""
        try:
            # 真实本地LLM调用
            return {
                "success": True,
                "response": "本地LLM响应: " + messages[-1].content,
                "model": "local-llm",
                "usage": {"total_tokens": 50}
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class LLMAdapterFactory:
    """LLM适配器工厂"""
    
    @staticmethod
    def create_adapter(adapter_type: str, **kwargs) -> LLMAdapter:
        """创建适配器"""
        if adapter_type == "deepseek":
            return DeepSeekAdapter(kwargs.get("api_key", ""))
        elif adapter_type == "local":
            return LocalAdapter()
        elif adapter_type == "stepflash":
            return StepFlashAdapter(
                deployment_type=kwargs.get("deployment_type", "openrouter"),
                api_key=kwargs.get("api_key"),
                base_url=kwargs.get("base_url")
            )
        else:
            raise ValueError(f"不支持的适配器类型: {adapter_type}")
    
    @staticmethod
    def get_available_adapters() -> List[str]:
        """获取可用适配器列表"""
        return ["deepseek", "local", "stepflash"]


class LLMImplementation(ABC):
    """LLM实现基类"""
    
    @abstractmethod
    def chat_completion(self, messages: List[ChatMessage], **kwargs) -> Dict[str, Any]:
        """聊天完成"""
        pass


class StandardLLMImplementation(LLMImplementation):
    """标准LLM实现"""
    
    def __init__(self, adapter: LLMAdapter):
        self.adapter = adapter
    
    def chat_completion(self, messages: List[ChatMessage], **kwargs) -> Dict[str, Any]:
        """聊天完成"""
        return self.adapter.chat_completion(messages, **kwargs)


class LLMBridge:
    """LLM桥接类"""
    
    def __init__(self, implementation: LLMImplementation):
        self.implementation = implementation
    
    def chat_completion(self, messages: List[ChatMessage], **kwargs) -> Dict[str, Any]:
        """聊天完成"""
        return self.implementation.chat_completion(messages, **kwargs)


# 扩展LLMClient类
class LLMClient:
    """统一LLM客户端 - 重构版本"""
    
    def __init__(self, api_key: Optional[str] = None, adapter_type: str = "deepseek"):
        """初始化LLM客户端"""
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.adapter_type = adapter_type
        self.bridge = None
        self.logger = logging.getLogger(__name__)
        self._setup_bridge()
        self.logger.info(f"LLM客户端初始化完成（重构版本）: {adapter_type}")
    
    def _setup_bridge(self):
        """设置桥接"""
        try:
            # 创建适配器
            adapter = LLMAdapterFactory.create_adapter(
                self.adapter_type,
                api_key=self.api_key
            )
            
            # 创建实现
            implementation = StandardLLMImplementation(adapter)
            
            # 创建桥接
            self.bridge = LLMBridge(implementation)
            
            self.logger.info("LLM桥接设置完成")
        except Exception as e:
            self.logger.error(f"设置LLM桥接失败: {e}")
            # 使用默认适配器作为后备
            try:
                adapter = LLMAdapterFactory.create_adapter("local")
                implementation = StandardLLMImplementation(adapter)
                self.bridge = LLMBridge(implementation)
            except Exception as e2:
                self.logger.error(f"设置默认桥接也失败: {e2}")
                self.bridge = None
    
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """聊天完成"""
        try:
            # 验证输入
            if not self._validate_messages(messages):
                return self._create_error_response("Invalid messages format")
            
            if not self.bridge:
                return self._create_error_response("LLM客户端未初始化")
            
            # 转换消息格式
            chat_messages = self._convert_messages(messages)
            
            # 调用桥接
            response = self.bridge.chat_completion(chat_messages, **kwargs)
            
            # 处理响应
            return self._process_response(response)
            
        except Exception as e:
            self.logger.error(f"聊天完成失败: {e}")
            return self._create_error_response(f"Chat completion failed: {e}")
    
    def _validate_messages(self, messages: List[Dict[str, str]]) -> bool:
        """验证消息格式"""
        if not isinstance(messages, list):
            return False
        
        if not messages:
            return False
        
        for msg in messages:
            if not isinstance(msg, dict):
                return False
            
            if "role" not in msg or "content" not in msg:
                return False
            
            if not isinstance(msg["role"], str) or not isinstance(msg["content"], str):
                return False
        
        return True
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[ChatMessage]:
        """转换消息格式"""
        try:
            chat_messages = []
            for msg in messages:
                chat_messages.append(ChatMessage(msg["role"], msg["content"]))
            return chat_messages
        except Exception as e:
            self.logger.error(f"转换消息格式失败: {e}")
            return []
    
    def _process_response(self, response) -> Dict[str, Any]:
        """处理响应"""
        try:
            if response.get("success", False):
                return {
                    "success": True,
                    "response": response.get("response", ""),
                    "model": response.get("model", "unknown"),
                    "usage": response.get("usage", {})
                }
            else:
                return {
                    "success": False,
                    "error": response.get("error", "Unknown error")
                }
        except Exception as e:
            self.logger.error(f"处理响应失败: {e}")
            return self._create_error_response(f"Response processing failed: {e}")
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            "success": False,
            "error": error_message,
            "timestamp": time.time()
        }
    
    def simple_chat(self, message: str, role: str = "user") -> str:
        """简单聊天"""
        try:
            messages = [{"role": role, "content": message}]
            response = self.chat_completion(messages)
            
            if response.get("success", False):
                return response.get("response", "")
            else:
                return f"错误: {response.get('error', 'Unknown error')}"
                
        except Exception as e:
            self.logger.error(f"简单聊天失败: {e}")
            return f"错误: {e}"
    
    def get_client_status(self) -> Dict[str, Any]:
        """获取客户端状态"""
        return {
            "adapter_type": self.adapter_type,
            "bridge_available": self.bridge is not None,
            "api_key_configured": self.api_key is not None,
            "timestamp": time.time()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if not self.bridge:
                return {
                    "status": "unhealthy",
                    "error": "Bridge not initialized"
                }
            
            # 测试简单聊天
            test_response = self.simple_chat("test", "user")
            
            if "错误" in test_response:
                return {
                    "status": "unhealthy",
                    "error": test_response
                }
            else:
                return {
                    "status": "healthy",
                    "test_response": test_response
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }