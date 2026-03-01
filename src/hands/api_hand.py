#!/usr/bin/env python3
"""
API集成Hands
"""

import aiohttp
import json
import logging
from typing import Dict, List, Any, Optional

from .base import BaseHand, HandCategory, HandSafetyLevel, HandExecutionResult


class APIRequestHand(BaseHand):
    """API请求Hand"""
    
    def __init__(self):
        super().__init__(
            name="api_request",
            description="发送HTTP API请求",
            category=HandCategory.API_INTEGRATION,
            safety_level=HandSafetyLevel.MODERATE
        )
        
        # 默认会话
        self.session = None
    
    def validate_parameters(self, **kwargs) -> bool:
        """验证参数"""
        required = ["url", "method"]
        return all(key in kwargs for key in required)
    
    async def execute(self, **kwargs) -> HandExecutionResult:
        """执行API请求"""
        try:
            url = kwargs["url"]
            method = kwargs["method"].upper()
            headers = kwargs.get("headers", {})
            data = kwargs.get("data")
            params = kwargs.get("params", {})
            timeout = kwargs.get("timeout", 30)
            
            # 创建会话（如果需要）
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # 准备请求数据
            request_data = None
            if data is not None:
                if isinstance(data, (dict, list)):
                    request_data = json.dumps(data)
                    headers.setdefault("Content-Type", "application/json")
                else:
                    request_data = str(data)
            
            # 发送请求
            async with self.session.request(
                method=method,
                url=url,
                headers=headers,
                data=request_data,
                params=params,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                # 读取响应
                response_text = await response.text()
                
                # 尝试解析JSON
                response_data = None
                try:
                    if response_text:
                        response_data = json.loads(response_text)
                except json.JSONDecodeError:
                    response_data = response_text
                
                # 记录详情
                request_info = {
                    "url": url,
                    "method": method,
                    "status": response.status,
                    "headers": dict(response.headers),
                    "size": len(response_text),
                    "time_taken": 0.0  # 可以通过装饰器添加
                }
                
                return HandExecutionResult(
                    hand_name=self.name,
                    success=200 <= response.status < 300,
                    output={
                        "response": response_data,
                        "status_code": response.status,
                        "request": request_info,
                        "raw_text": response_text if not isinstance(response_data, str) else None
                    },
                    error=None if 200 <= response.status < 300 else f"HTTP {response.status}: {response_text[:100]}",
                    validation_results={
                        "http_status": response.status,
                        "content_type": response.headers.get("Content-Type", ""),
                        "successful": 200 <= response.status < 300
                    }
                )
                
        except Exception as e:
            return HandExecutionResult(
                hand_name=self.name,
                success=False,
                output=None,
                error=f"API请求失败: {e}"
            )
    
    async def safety_check(self, **kwargs) -> bool:
        """安全检查"""
        url = kwargs.get("url", "")
        
        # 避免敏感或危险的URL
        dangerous_patterns = [
            "localhost",
            "127.0.0.1",
            "192.168.",
            "10.",
            "172.16.",
            "file://",
            "data:",
            "javascript:"
        ]
        
        for pattern in dangerous_patterns:
            if pattern in url.lower():
                self.logger.warning(f"检测到潜在危险URL模式: {pattern}")
                return False
        
        # 检查方法
        method = kwargs.get("method", "").upper()
        if method in ["DELETE", "PUT", "PATCH"]:
            self.logger.info(f"非只读HTTP方法: {method}")
            return self._check_moderate_safety(kwargs)
        
        return True
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """清理会话"""
        if self.session:
            await self.session.close()
            self.session = None


class WebhookHand(BaseHand):
    """Webhook处理Hand"""
    
    def __init__(self):
        super().__init__(
            name="webhook",
            description="处理和发送Webhook",
            category=HandCategory.API_INTEGRATION,
            safety_level=HandSafetyLevel.MODERATE
        )
    
    def validate_parameters(self, **kwargs) -> bool:
        """验证参数"""
        required = ["url", "event"]
        return all(key in kwargs for key in required)
    
    async def execute(self, **kwargs) -> HandExecutionResult:
        """执行Webhook操作"""
        try:
            url = kwargs["url"]
            event = kwargs["event"]
            payload = kwargs.get("payload", {})
            headers = kwargs.get("headers", {})
            
            # 准备Webhook数据
            webhook_data = {
                "event": event,
                "timestamp": kwargs.get("timestamp"),
                "payload": payload,
                "source": kwargs.get("source", "rangen_system")
            }
            
            # 发送Webhook
            request_hand = APIRequestHand()
            result = await request_hand.execute(
                url=url,
                method="POST",
                headers=headers,
                data=webhook_data,
                timeout=kwargs.get("timeout", 10)
            )
            
            if result.success:
                return HandExecutionResult(
                    hand_name=self.name,
                    success=True,
                    output={
                        "webhook_sent": True,
                        "event": event,
                        "url": url,
                        "api_response": result.output
                    },
                    validation_results={
                        "webhook_delivered": True,
                        "response_status": result.output.get("status_code", 0) if result.output else 0
                    }
                )
            else:
                return HandExecutionResult(
                    hand_name=self.name,
                    success=False,
                    output=None,
                    error=f"Webhook发送失败: {result.error}"
                )
                
        except Exception as e:
            return HandExecutionResult(
                hand_name=self.name,
                success=False,
                output=None,
                error=f"Webhook处理失败: {e}"
            )


class ExternalAPIIntegrationHand(BaseHand):
    """外部API集成Hand"""
    
    def __init__(self):
        super().__init__(
            name="external_api_integration",
            description="集成外部API服务",
            category=HandCategory.API_INTEGRATION,
            safety_level=HandSafetyLevel.MODERATE
        )
        
        # 内置API配置
        self.api_configs = {
            "openai": {
                "base_url": "https://api.openai.com/v1",
                "auth_header": "Authorization: Bearer {api_key}"
            },
            "anthropic": {
                "base_url": "https://api.anthropic.com/v1",
                "auth_header": "x-api-key: {api_key}"
            },
            "github": {
                "base_url": "https://api.github.com",
                "auth_header": "Authorization: token {api_key}"
            },
            "gitlab": {
                "base_url": "https://gitlab.com/api/v4",
                "auth_header": "PRIVATE-TOKEN: {api_key}"
            }
        }
    
    def validate_parameters(self, **kwargs) -> bool:
        """验证参数"""
        required = ["api_name", "endpoint"]
        return all(key in kwargs for key in required)
    
    async def execute(self, **kwargs) -> HandExecutionResult:
        """执行外部API集成"""
        try:
            api_name = kwargs["api_name"]
            endpoint = kwargs["endpoint"]
            api_key = kwargs.get("api_key")
            method = kwargs.get("method", "GET")
            data = kwargs.get("data", {})
            
            # 获取API配置
            if api_name not in self.api_configs:
                return HandExecutionResult(
                    hand_name=self.name,
                    success=False,
                    output=None,
                    error=f"不支持的API: {api_name}"
                )
            
            config = self.api_configs[api_name]
            base_url = config["base_url"]
            auth_template = config["auth_header"]
            
            # 构建完整URL
            url = f"{base_url}{endpoint}"
            
            # 准备headers
            headers = {}
            if api_key:
                headers_str = auth_template.format(api_key=api_key)
                header_key, header_value = headers_str.split(":", 1)
                headers[header_key.strip()] = header_value.strip()
            
            # 添加默认headers
            headers.setdefault("Content-Type", "application/json")
            
            # 使用APIRequestHand发送请求
            request_hand = APIRequestHand()
            result = await request_hand.execute(
                url=url,
                method=method,
                headers=headers,
                data=data,
                timeout=kwargs.get("timeout", 30)
            )
            
            if result.success:
                return HandExecutionResult(
                    hand_name=self.name,
                    success=True,
                    output={
                        "api": api_name,
                        "endpoint": endpoint,
                        "api_response": result.output,
                        "config_used": {
                            "base_url": base_url,
                            "method": method
                        }
                    },
                    validation_results={
                        "api_integration_successful": True,
                        "response_format": "json" if isinstance(result.output.get("response"), (dict, list)) else "raw"
                    }
                )
            else:
                return HandExecutionResult(
                    hand_name=self.name,
                    success=False,
                    output=None,
                    error=f"{api_name} API调用失败: {result.error}"
                )
                
        except Exception as e:
            return HandExecutionResult(
                hand_name=self.name,
                success=False,
                output=None,
                error=f"外部API集成失败: {e}"
            )
    
    def register_api(self, api_name: str, base_url: str, auth_header: str) -> bool:
        """注册新的API配置"""
        try:
            self.api_configs[api_name] = {
                "base_url": base_url,
                "auth_header": auth_header
            }
            self.logger.info(f"注册API: {api_name}")
            return True
        except Exception as e:
            self.logger.error(f"注册API失败 {api_name}: {e}")
            return False


class DataProcessingHand(BaseHand):
    """数据处理Hand"""
    
    def __init__(self):
        super().__init__(
            name="data_processing",
            description="处理数据",
            category=HandCategory.DATA_PROCESSING,
            safety_level=HandSafetyLevel.SAFE
        )
    
    def validate_parameters(self, **kwargs) -> bool:
        """验证参数"""
        return True  # 所有参数都是可选的，但需要至少有一个操作
    
    async def execute(self, **kwargs) -> HandExecutionResult:
        """执行数据处理"""
        try:
            operation = kwargs.get("operation", "transform")
            data = kwargs.get("data")
            
            if data is None:
                return HandExecutionResult(
                    hand_name=self.name,
                    success=False,
                    output=None,
                    error="未提供数据"
                )
            
            result = None
            
            if operation == "transform":
                # 数据转换
                result = await self._transform_data(data, kwargs.get("transform_rules", {}))
            
            elif operation == "filter":
                # 数据过滤
                result = await self._filter_data(data, kwargs.get("filter_criteria", {}))
            
            elif operation == "aggregate":
                # 数据聚合
                result = await self._aggregate_data(data, kwargs.get("aggregate_by", ""), kwargs.get("operation", "sum"))
            
            elif operation == "validate":
                # 数据验证
                result = await self._validate_data(data, kwargs.get("validation_rules", {}))
            
            elif operation == "format":
                # 数据格式化
                result = await self._format_data(data, kwargs.get("format_spec", {}))
            
            else:
                return HandExecutionResult(
                    hand_name=self.name,
                    success=False,
                    output=None,
                    error=f"不支持的数据操作: {operation}"
                )
            
            return HandExecutionResult(
                hand_name=self.name,
                success=True,
                output=result,
                validation_results={
                    "operation_performed": operation,
                    "input_type": type(data).__name__,
                    "output_type": type(result).__name__ if result else None
                }
            )
            
        except Exception as e:
            return HandExecutionResult(
                hand_name=self.name,
                success=False,
                output=None,
                error=f"数据处理失败: {e}"
            )
    
    async def _transform_data(self, data: Any, rules: Dict[str, Any]) -> Any:
        """转换数据"""
        # 简单的数据转换逻辑
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if key in rules:
                    # 应用转换规则
                    transform_func = rules[key]
                    if callable(transform_func):
                        result[key] = transform_func(value)
                    elif isinstance(transform_func, str):
                        if transform_func == "uppercase" and isinstance(value, str):
                            result[key] = value.upper()
                        elif transform_func == "lowercase" and isinstance(value, str):
                            result[key] = value.lower()
                        elif transform_func == "int" and isinstance(value, (str, float)):
                            result[key] = int(value)
                        elif transform_func == "float" and isinstance(value, (str, int)):
                            result[key] = float(value)
                        else:
                            result[key] = value
                    else:
                        result[key] = value
                else:
                    result[key] = value
            return result
        
        elif isinstance(data, list):
            return [await self._transform_data(item, rules) for item in data]
        
        else:
            return data
    
    async def _filter_data(self, data: Any, criteria: Dict[str, Any]) -> Any:
        """过滤数据"""
        if isinstance(data, list):
            filtered = []
            for item in data:
                if isinstance(item, dict):
                    include = True
                    for key, condition in criteria.items():
                        if key in item:
                            if not self._evaluate_condition(item[key], condition):
                                include = False
                                break
                    if include:
                        filtered.append(item)
            return filtered
        
        elif isinstance(data, dict):
            # 过滤字典
            return {k: v for k, v in data.items() if self._evaluate_condition(v, criteria.get(k, {}))}
        
        else:
            return data
    
    def _evaluate_condition(self, value: Any, condition: Any) -> bool:
        """评估条件"""
        if condition is None:
            return True
        
        if isinstance(condition, dict):
            # 复杂条件
            if "equals" in condition:
                return value == condition["equals"]
            elif "contains" in condition and isinstance(value, str):
                return condition["contains"] in value
            elif "gt" in condition and isinstance(value, (int, float)):
                return value > condition["gt"]
            elif "lt" in condition and isinstance(value, (int, float)):
                return value < condition["lt"]
        
        return True
    
    async def _aggregate_data(self, data: Any, aggregate_by: str, operation: str) -> Dict[str, Any]:
        """聚合数据"""
        if not isinstance(data, list):
            return {"error": "数据必须是列表"}
        
        result = {}
        
        for item in data:
            if isinstance(item, dict) and aggregate_by in item:
                key = item[aggregate_by]
                if key not in result:
                    result[key] = []
                result[key].append(item)
        
        # 应用聚合操作
        aggregated = {}
        for key, items in result.items():
            if operation == "count":
                aggregated[key] = len(items)
            elif operation == "sum":
                # 尝试求和数值字段
                numeric_values = []
                for item in items:
                    for k, v in item.items():
                        if k != aggregate_by and isinstance(v, (int, float)):
                            numeric_values.append(v)
                aggregated[key] = sum(numeric_values) if numeric_values else 0
            elif operation == "avg":
                numeric_values = []
                for item in items:
                    for k, v in item.items():
                        if k != aggregate_by and isinstance(v, (int, float)):
                            numeric_values.append(v)
                aggregated[key] = sum(numeric_values) / len(numeric_values) if numeric_values else 0
        
        return aggregated
    
    async def _validate_data(self, data: Any, rules: Dict[str, Any]) -> Dict[str, Any]:
        """验证数据"""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        if isinstance(data, dict):
            for key, rule in rules.items():
                if key in data:
                    value = data[key]
                    
                    if "required" in rule and rule["required"] and value is None:
                        validation_results["valid"] = False
                        validation_results["errors"].append(f"字段 {key} 是必需的")
                    
                    if "type" in rule:
                        expected_type = rule["type"]
                        actual_type = type(value).__name__
                        if actual_type != expected_type:
                            validation_results["warnings"].append(
                                f"字段 {key} 类型不匹配: 期望 {expected_type}, 实际 {actual_type}"
                            )
        
        return validation_results
    
    async def _format_data(self, data: Any, format_spec: Dict[str, Any]) -> Any:
        """格式化数据"""
        output_format = format_spec.get("format", "json")
        
        if output_format == "json":
            import json
            return json.dumps(data, indent=2, ensure_ascii=False)
        
        elif output_format == "csv":
            # 简单的CSV格式化
            if isinstance(data, list) and data and isinstance(data[0], dict):
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
                return output.getvalue()
        
        elif output_format == "yaml":
            try:
                import yaml
                return yaml.dump(data, allow_unicode=True)
            except ImportError:
                return "YAML格式化需要PyYAML库"
        
        return data


# 测试函数
async def test_api_hands():
    """测试API Hands"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("🌐 测试API Hands")
    print("=" * 60)
    
    try:
        # 测试APIRequestHand
        print("\n📡 测试APIRequestHand...")
        api_hand = APIRequestHand()
        
        # 测试GET请求
        result = await api_hand.execute(
            url="https://httpbin.org/get",
            method="GET",
            params={"test": "hello"}
        )
        
        print(f"API请求: {'成功' if result.success else '失败'}")
        if result.success:
            print(f"  状态码: {result.output.get('status_code')}")
            response = result.output.get('response')
            if isinstance(response, dict) and 'args' in response:
                print(f"  参数: {response['args']}")
        
        # 测试DataProcessingHand
        print("\n📊 测试DataProcessingHand...")
        data_hand = DataProcessingHand()
        
        test_data = [
            {"name": "Alice", "age": 25, "score": 85},
            {"name": "Bob", "age": 30, "score": 92},
            {"name": "Charlie", "age": 28, "score": 78}
        ]
        
        result = await data_hand.execute(
            operation="aggregate",
            data=test_data,
            aggregate_by="age",
            count_by="age"
        )
        
        print(f"数据处理: {'成功' if result.success else '失败'}")
        if result.success:
            print(f"  聚合结果: {result.output}")
        
        # 测试WebhookHand
        print("\n🔗 测试WebhookHand...")
        webhook_hand = WebhookHand()
        
        result = await webhook_hand.execute(
            url="https://httpbin.org/post",
            event="test_event",
            payload={"message": "Test webhook"}
        )
        
        print(f"Webhook发送: {'成功' if result.success else '失败'}")
        if result.success:
            print(f"  事件: {result.output.get('event')}")
            print(f"  响应状态: {result.output.get('api_response', {}).get('status_code')}")
        
        print("\n✅ API Hands测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(test_api_hands())