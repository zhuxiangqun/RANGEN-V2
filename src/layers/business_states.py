#!/usr/bin/env python3
"""
业务层 - 状态模式实现
Business State Pattern Implementations

提供业务状态基类、具体状态实现、状态管理器
"""
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from src.core.services import get_core_logger


class BusinessState(ABC):
    """业务状态基类"""
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """处理数据"""
        try:
            # 验证输入数据
            if not self._validate_input(data):
                return self._create_error_result("Invalid input data")
            
            # 数据预处理
            processed_data = self._preprocess_data(data)
            
            # 执行主要处理逻辑
            result = self._execute_processing(processed_data)
            
            # 数据后处理
            final_result = self._postprocess_data(result)
            
            # 记录处理历史
            self._record_processing(data, final_result)
            
            return final_result
            
        except Exception as e:
            # 处理失败
            return self._create_error_result(f"Processing failed: {e}")
    
    def _validate_input(self, data: Any) -> bool:
        """验证输入数据"""
        if data is None:
            return False
        elif isinstance(data, (str, int, float, bool)):
            return True
        elif isinstance(data, (list, dict)):
            return len(data) > 0
        else:
            return False
    
    def _preprocess_data(self, data: Any) -> Any:
        """数据预处理"""
        if isinstance(data, str):
            # 字符串预处理
            return data.strip().lower()
        elif isinstance(data, dict):
            # 字典预处理
            return {k: v for k, v in data.items() if v is not None}
        elif isinstance(data, list):
            # 列表预处理
            return [item for item in data if item is not None]
        else:
            return data
    
    def _execute_processing(self, data: Any) -> Any:
        """执行主要处理逻辑"""
        if isinstance(data, str):
            # 字符串处理
            return f"Processed string: {data}"
        elif isinstance(data, dict):
            # 字典处理
            return {k: f"processed_{v}" for k, v in data.items()}
        elif isinstance(data, list):
            # 列表处理
            return [f"processed_{item}" for item in data]
        else:
            return f"Processed: {data}"
    
    def _postprocess_data(self, data: Any) -> Any:
        """数据后处理"""
        if isinstance(data, str):
            # 字符串后处理
            return data.upper()
        elif isinstance(data, dict):
            # 字典后处理
            return {k: str(v) for k, v in data.items()}
        elif isinstance(data, list):
            # 列表后处理
            return [str(item) for item in data]
        else:
            return str(data)
    
    def _record_processing(self, input_data: Any, output_data: Any):
        """记录处理历史"""
        if not hasattr(self, 'processing_history'):
            self.processing_history = []
        
        self.processing_history.append({
            'timestamp': time.time(),
            'input': input_data,
            'output': output_data,
            'success': True
        })
    
    def _create_error_result(self, message: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            'success': False,
            'error': message,
            'timestamp': time.time()
        }


class IdleState(BusinessState):
    """空闲状态"""
    
    def __init__(self):
        self.logger = get_core_logger("idle_state")
    
    def process(self, data: Any) -> Any:
        """处理空闲状态"""
        try:
            # 检查是否有待处理的数据
            if data is None or data == "":
                return {
                    "status": "idle", 
                    "message": "系统空闲，等待数据输入",
                    "timestamp": time.time(),
                    "ready_for_processing": True
                }
            
            # 预处理
            if isinstance(data, dict):
                required_fields = ['type', 'content']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    return {
                        "status": "idle",
                        "message": f"数据不完整，缺少字段: {missing_fields}",
                        "timestamp": time.time(),
                        "ready_for_processing": False,
                        "missing_fields": missing_fields
                    }
                
                return {
                    "status": "ready",
                    "message": "数据完整，准备处理",
                    "timestamp": time.time(),
                    "ready_for_processing": True,
                    "data_preview": {
                        "type": data.get('type'),
                        "content_length": len(str(data.get('content', ''))),
                        "has_metadata": 'metadata' in data
                    }
                }
            
            elif isinstance(data, str):
                if len(data.strip()) == 0:
                    return {
                        "status": "idle",
                        "message": "空字符串数据，系统空闲",
                        "timestamp": time.time(),
                        "ready_for_processing": False
                    }
                
                return {
                    "status": "ready",
                    "message": "字符串数据准备就绪",
                    "timestamp": time.time(),
                    "ready_for_processing": True,
                    "data_preview": {
                        "length": len(data),
                        "word_count": len(data.split()),
                        "is_json": data.strip().startswith(('{', '['))
                    }
                }
            
            else:
                return {
                    "status": "ready",
                    "message": f"数据类型 {type(data).__name__} 准备就绪",
                    "timestamp": time.time(),
                    "ready_for_processing": True,
                    "data_type": type(data).__name__
                }
                
        except Exception as e:
            self.logger.error(f"空闲状态处理失败: {e}")
            return {
                "status": "error",
                "message": f"处理失败: {str(e)}",
                "timestamp": time.time(),
                "ready_for_processing": False
            }


class ProcessingState(BusinessState):
    """处理状态"""
    
    def __init__(self):
        self.logger = get_core_logger("processing_state")
    
    def process(self, data: Any) -> Any:
        """处理处理状态"""
        try:
            start_time = time.time()
            
            # 验证输入数据
            if data is None:
                return {
                    "status": "error",
                    "message": "处理失败：输入数据为空",
                    "timestamp": time.time(),
                    "processing_time": 0
                }
            
            # 根据数据类型进行不同的处理
            if isinstance(data, dict):
                result = self._process_dict_data(data)
            elif isinstance(data, str):
                result = self._process_string_data(data)
            elif isinstance(data, (list, tuple)):
                result = self._process_list_data(list(data))
            else:
                result = self._process_other_data(data)
            
            processing_time = time.time() - start_time
            
            return {
                "status": "completed",
                "message": "处理完成",
                "timestamp": time.time(),
                "processing_time": processing_time,
                "result": result,
                "data_type": type(data).__name__,
                "data_size": len(str(data)) if hasattr(data, '__len__') else 0
            }
            
        except Exception as e:
            self.logger.error(f"处理状态执行失败: {e}")
            return {
                "status": "error",
                "message": f"处理失败: {str(e)}",
                "timestamp": time.time(),
                "processing_time": time.time() - start_time if 'start_time' in locals() else 0
            }
    
    def _process_dict_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理字典数据"""
        processed = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                processed[key] = value.strip()
            elif isinstance(value, (int, float)):
                processed[key] = value
            elif isinstance(value, dict):
                processed[key] = self._process_dict_data(value)
            elif isinstance(value, (list, tuple)):
                processed[key] = self._process_list_data(list(value))
            else:
                processed[key] = str(value)
        
        processed['_metadata'] = {
            'processed_at': time.time(),
            'key_count': len(data),
            'has_nested_data': any(isinstance(v, (dict, list)) for v in data.values())
        }
        
        return processed
    
    def _process_string_data(self, data: str) -> Dict[str, Any]:
        """处理字符串数据"""
        processed = {
            'content': data.strip(),
            'length': len(data),
            'word_count': len(data.split()),
            'line_count': len(data.splitlines()),
            'is_json': data.strip().startswith(('{', '[')),
            'has_special_chars': any(c in data for c in "!@#$%^&*()"),
            '_metadata': {
                'processed_at': time.time(),
                'data_type': 'string'
            }
        }
        
        if processed['is_json']:
            try:
                import json
                parsed = json.loads(data)
                processed['parsed_json'] = parsed
            except json.JSONDecodeError:
                processed['json_parse_error'] = True
        
        return processed
    
    def _process_list_data(self, data: List[Any]) -> Dict[str, Any]:
        """处理列表数据"""
        processed = {
            'items': [],
            'count': len(data),
            'item_types': list(set(type(item).__name__ for item in data)),
            '_metadata': {
                'processed_at': time.time(),
                'data_type': 'list'
            }
        }
        
        for i, item in enumerate(data):
            if isinstance(item, dict):
                processed['items'].append(self._process_dict_data(item))
            elif isinstance(item, str):
                processed['items'].append(self._process_string_data(item))
            else:
                processed['items'].append(str(item))
        
        return processed
    
    def _process_other_data(self, data: Any) -> Dict[str, Any]:
        """处理其他类型数据"""
        return {
            'value': str(data),
            'type': type(data).__name__,
            'repr': repr(data),
            '_metadata': {
                'processed_at': time.time(),
                'data_type': 'other'
            }
        }


class ErrorState(BusinessState):
    """错误状态"""
    
    def __init__(self):
        self.logger = get_core_logger("error_state")
    
    def process(self, data: Any) -> Any:
        """处理错误状态"""
        try:
            error_info = {
                "status": "error",
                "message": "系统处于错误状态",
                "timestamp": time.time(),
                "error_state": True,
                "data_received": data is not None,
                "data_type": type(data).__name__ if data is not None else "None"
            }
            
            if data is None:
                error_info["error_reason"] = "输入数据为空"
                error_info["suggestion"] = "请提供有效的输入数据"
            elif isinstance(data, dict):
                required_fields = ['type', 'content']
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    error_info["error_reason"] = f"数据不完整，缺少字段: {missing_fields}"
                    error_info["suggestion"] = "请提供包含必要字段的完整数据"
                else:
                    error_info["error_reason"] = "数据格式正确但处理失败"
                    error_info["suggestion"] = "请检查数据内容是否符合业务规则"
            elif isinstance(data, str):
                if len(data.strip()) == 0:
                    error_info["error_reason"] = "输入字符串为空"
                    error_info["suggestion"] = "请提供非空字符串数据"
                else:
                    error_info["error_reason"] = "字符串数据格式问题"
                    error_info["suggestion"] = "请检查字符串格式是否正确"
            else:
                error_info["error_reason"] = f"不支持的数据类型: {type(data).__name__}"
                error_info["suggestion"] = "请提供字典或字符串类型的数据"
            
            error_info["recovery_suggestions"] = [
                "检查输入数据格式",
                "验证数据完整性",
                "重新初始化系统状态",
                "联系技术支持"
            ]
            
            self.logger.error(f"错误状态处理: {error_info['error_reason']}")
            
            return error_info
            
        except Exception as e:
            self.logger.error(f"错误状态处理失败: {e}")
            return {
                "status": "critical_error",
                "message": f"错误状态处理失败: {str(e)}",
                "timestamp": time.time(),
                "error_state": True,
                "critical_error": True
            }


class BusinessStateManager:
    """业务状态管理器"""
    
    def __init__(self):
        self.current_state: BusinessState = IdleState()
        self.states = {
            'idle': IdleState(),
            'processing': ProcessingState(),
            'error': ErrorState()
        }
        self.logger = get_core_logger("business_state_manager")
    
    def set_state(self, state_name: str) -> bool:
        """设置状态"""
        try:
            if state_name not in self.states:
                self.logger.warning(f"未知状态: {state_name}")
                return False
            
            old_state = self.current_state.__class__.__name__
            self.current_state = self.states[state_name]
            new_state = self.current_state.__class__.__name__
            
            self.logger.info(f"状态转换: {old_state} -> {new_state}")
            
            if hasattr(self.current_state, 'on_enter'):
                self.current_state.on_enter()
            
            return True
            
        except Exception as e:
            self.logger.error(f"状态设置失败: {e}")
            return False
    
    def process(self, data: Any) -> Any:
        """处理数据"""
        try:
            if self.current_state is None:
                self.logger.error("当前状态为空，设置为错误状态")
                self.set_state('error')
                return {"status": "error", "message": "状态管理器未初始化"}
            
            start_time = time.time()
            self.logger.debug(f"开始处理数据，当前状态: {self.current_state.__class__.__name__}")
            
            result = self.current_state.process(data)
            
            processing_time = time.time() - start_time
            self.logger.debug(f"数据处理完成，耗时: {processing_time:.3f}秒")
            
            if isinstance(result, dict):
                status = result.get('status', '')
                if status == 'ready' and self.current_state.__class__.__name__ == 'IdleState':
                    self.set_state('processing')
                elif status == 'error' and self.current_state.__class__.__name__ != 'ErrorState':
                    self.set_state('error')
                elif status == 'completed' and self.current_state.__class__.__name__ == 'ProcessingState':
                    self.set_state('idle')
            
            if isinstance(result, dict):
                result['processing_time'] = processing_time
                result['state_manager'] = self.current_state.__class__.__name__
                result['timestamp'] = time.time()
            
            return result
            
        except Exception as e:
            self.logger.error(f"数据处理失败: {e}")
            self.set_state('error')
            return {
                "status": "error",
                "message": f"数据处理失败: {str(e)}",
                "timestamp": time.time(),
                "state_manager": "ErrorState"
            }
