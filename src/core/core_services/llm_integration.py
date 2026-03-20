"""
LLM Integration Module - For intelligent semantic judgment
"""

import os
from typing import Optional, Dict, Any, Protocol
import requests
import json
import time
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.services.logging_service import get_logger
from src.core.utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from abc import ABC, abstractmethod
from src.services.stepflash_adapter import StepFlashAdapter

# Use standard logger
logger = get_logger(__name__)


class UnifiedLLMInterface(Protocol):
    """统一LLM接口协议

    所有LLM类都应该实现以下方法以确保接口统一性。
    """

    def call_llm(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Optional[str]:
        """主要LLM调用接口（无下划线）"""
        ...

    def _call_llm(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Optional[str]:
        """内部LLM调用接口（有下划线）"""
        ...

    def _call_deepseek(self, prompt: str, enable_thinking_mode: bool = True, **kwargs) -> Optional[str]:
        """DeepSeek专用接口（可选）"""
        ...

def create_llm_integration(config: Dict[str, Any]) -> 'LLMIntegration':
    """Factory function to create LLMIntegration instance"""
    return LLMIntegration(config)

class LLMIntegration(UnifiedLLMInterface):
    """LLM Integration Class - Supports multiple LLM services (DeepSeek, OpenAI compatible)"""
    
    # Constants for error messages
    ERROR_LLM_CALL_FAILED = "LLM call failed"
    ERROR_EMPTY_RESPONSE = "Empty response received"
    ERROR_TIMEOUT = "Request timeout"
    ERROR_NETWORK = "Network error"
    ERROR_CIRCUIT_OPEN = "Circuit Breaker is OPEN"
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm_provider = config.get('llm_provider', 'deepseek')
        
        # 🚀 强制限制：仅允许 DeepSeek 作为外部LLM，允许本地模型
        # 将除本地模型和mock外的所有外部提供商重定向到 DeepSeek
        allowed_external_providers = {'deepseek', 'mock'}
        is_local_model = 'local' in self.llm_provider.lower()
        
        if self.llm_provider not in allowed_external_providers and not is_local_model:
            logger.info(f"⚠️ 重定向外部提供商 '{self.llm_provider}' 到 'deepseek'（外部LLM只使用DeepSeek）")
            self.llm_provider = 'deepseek'
        
        # 根据提供商选择API密钥
        if self.llm_provider == 'deepseek':
            self.api_key = config.get('api_key', os.getenv('DEEPSEEK_API_KEY', ''))
        elif self.llm_provider == 'mock':
            self.api_key = 'mock'  # 模拟模式
        else:
            # 本地模型或其他提供商，尝试从配置或环境变量获取API密钥
            # 本地模型可能不需要API密钥
            self.api_key = config.get('api_key', '')
        
        # 我们不再使用 config 中的 'model' 作为绝对真理，而是根据 provider 强制选择
        # 如果用户试图使用 gpt-4，我们会自动重定向到 deepseek-chat 或 deepseek-reasoner
        self.model = config.get('model', 'deepseek-reasoner')
        
        # 验证并规范化模型名称（仅针对DeepSeek外部LLM）
        # 允许的DeepSeek模型列表：deepseek-reasoner (R1), deepseek-chat (V3)
        if self.llm_provider == 'deepseek':
            valid_models = ['deepseek-reasoner', 'deepseek-chat']
            if self.model not in valid_models:
                logger.warning(f"⚠️ 模型 '{self.model}' 不在允许列表 {valid_models} 中。默认使用 'deepseek-reasoner'")
                self.model = 'deepseek-reasoner'
        
        # Last reasoning content trace
        self._last_reasoning_content = None
        
        # 🛡️ P4.5: Initialize Circuit Breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5, 
            recovery_timeout=60, 
            name=f"CB-{self.llm_provider}"
        )
        
        # Base URL Handling - 根据提供商选择
        if self.llm_provider == 'deepseek':
            base_url_raw = config.get('base_url', os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1'))
        elif self.llm_provider == 'mock':
            base_url_raw = 'http://mock-api/v1'  # 模拟API地址，实际不会调用
        else:
            # 本地模型：使用配置中的base_url，或默认本地Ollama地址
            base_url_raw = config.get('base_url', 'http://localhost:11434/v1')
        
        # 规范化URL（确保以/v1结尾）
        base_url_raw = base_url_raw.rstrip('/')
        if not base_url_raw.endswith('/v1'):
            # 自动追加/v1（如果缺失）
            if not base_url_raw.endswith('/beta'):
                base_url_raw += '/v1'
        self.base_url = base_url_raw
        
        logger.info(f"LLM Integration initialized: provider={self.llm_provider}, model={self.model}, base_url={self.base_url}")

        if not self.api_key:
            logger.warning("⚠️ API Key not found in config or environment variables.")

    def _execute_request(self, url: str, headers: Dict, data: Dict, timeout: int) -> Dict:
        """Internal method to execute request, wrapped by CircuitBreaker"""
        start_time = time.time()
        response = requests.post(url, headers=headers, json=data, timeout=timeout)
        response.raise_for_status()
        
        result_json = response.json()
        execution_time = time.time() - start_time
        logger.debug(f"LLM call successful ({execution_time:.2f}s)")
        return result_json

    def _call_llm(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Optional[str]:
        """
        Generic LLM call method.
        Supports: DeepSeek, OpenAI-compatible APIs, Step-3.5-Flash.
        Wrapped with Circuit Breaker for resilience.
        """
        # Mock Mode Check
        if self.llm_provider == "mock" or self.api_key == "mock":
            logger.info("[MockLLM] Returning mock response")
            return f"Mock response for: {prompt[:50]}..."
        
        # Step-3.5-Flash 适配器调用（已被重定向到DeepSeek）
        if self.llm_provider == "stepflash":
            # 由于策略要求外部LLM只使用DeepSeek，stepflash已被重定向
            logger.warning(f"⚠️ Step-3.5-Flash已被重定向到DeepSeek（外部LLM只使用DeepSeek）")
            # 继续执行后续的DeepSeek处理逻辑

        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key and self.api_key.strip():
            headers["Authorization"] = f"Bearer {self.api_key.strip()}"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if isinstance(prompt, list):
            messages.extend(prompt)
        else:
            messages.append({"role": "user", "content": prompt})

        max_prompt_chars = kwargs.get("max_prompt_chars", 50000)
        try:
            max_prompt_chars = int(max_prompt_chars)
        except Exception:
            max_prompt_chars = 50000
        if max_prompt_chars > 0:
            for msg in messages:
                content = msg.get("content")
                if isinstance(content, str) and len(content) > max_prompt_chars:
                    msg["content"] = content[:max_prompt_chars]

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2000),
            "stream": False
        }
        
        # 🚀 强制启用 JSON 模式 (如果参数请求)
        if kwargs.get("response_format"):
            data["response_format"] = kwargs.get("response_format")
        
        # 自动检测是否需要 JSON 模式 (DeepSeek 支持 {"type": "json_object"})
        elif "json" in prompt.lower() or (system_prompt and "json" in system_prompt.lower()):
             # 只有当模型支持时才启用 (DeepSeek V2/Coder/Chat 通常支持)
             # 为了安全起见，我们暂时只对明确要求的调用启用，或者在此处做个软性尝试
             pass

        # Specific handling for DeepSeek Reasoner (beta features if needed)
        # e.g. "enable_reasoning": True (hypothetically)
        
        url = f"{self.base_url}/chat/completions"
        # 🚀 增加默认超时时间，特别是对于推理模型
        default_timeout = 180 if "reasoner" in self.model else 90
        timeout = kwargs.get("timeout", default_timeout)
        
        # 🚀 P0改进：添加重试逻辑（针对网络错误和超时）
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                # 🛡️ P4.5: Use Circuit Breaker to execute request
                result_json = self.circuit_breaker.call(
                    self._execute_request,
                    url=url,
                    headers=headers,
                    data=data,
                    timeout=timeout
                )
                
                # Extract content
                if "choices" in result_json and len(result_json["choices"]) > 0:
                    choice = result_json["choices"][0]
                    message = choice.get("message", {})
                    content = message.get("content", "")
                    
                    # Capture reasoning content if available (DeepSeek specific)
                    if "reasoning_content" in message:
                        self._last_reasoning_content = message["reasoning_content"]
                    
                    return content
                else:
                    logger.error(f"{self.ERROR_EMPTY_RESPONSE}: {json.dumps(result_json, ensure_ascii=False)}")
                    return None
                    
            except CircuitBreakerOpenError:
                logger.warning(f"{self.ERROR_CIRCUIT_OPEN}: Request rejected fast.")
                # Return None to trigger fallback in RealReasoningEngine
                return None
                
            except requests.exceptions.RequestException as e:
                # 只在最后一次尝试时记录错误
                if attempt == max_retries - 1:
                    logger.error(f"{self.ERROR_NETWORK}: {str(e)} (Max retries reached)")
                    return None
                
                logger.warning(f"LLM call failed (Attempt {attempt+1}/{max_retries}): {e}. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                retry_delay *= 2  # 指数退避
                
            except Exception as e:
                logger.error(f"{self.ERROR_LLM_CALL_FAILED}: {str(e)}")
                return None
        
        return None

    def call_llm(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Optional[str]:
        """Alias for _call_llm for external use - 统一接口"""
        return self._call_llm(prompt, system_prompt, **kwargs)

    def _call_deepseek(self, prompt: str, enable_thinking_mode: bool = True, **kwargs) -> Optional[str]:
        """
        Specialized method for DeepSeek Reasoner (R1).
        Ensures 'deepseek-reasoner' model is used and handles reasoning content.
        Compatible with StepGenerator's expectation.
        """
        # Save original model to restore later
        original_model = self.model
        
        try:
            # Force reasoning model if thinking mode is enabled
            if enable_thinking_mode:
                # 只有当当前模型不是 reasoner 时才切换，避免不必要的属性赋值
                if self.model != 'deepseek-reasoner':
                    logger.info(f"🧠 Switching to 'deepseek-reasoner' for thinking mode (was {self.model})")
                    self.model = 'deepseek-reasoner'
            
            # Call generic LLM method
            # 注意：_call_llm 会自动处理 reasoning_content
            return self._call_llm(prompt, **kwargs)
            
        finally:
            # Restore original model
            self.model = original_model

    def _estimate_query_complexity_with_llm(self, query: str, **kwargs) -> int:
        """Estimate query complexity using LLM (simple proxy)"""
        # This is a stub implementation. In real scenario, it should call LLM to analyze complexity.
        # For now, we use a simple heuristic based on length and keywords.
        complexity = 1
        if len(query) > 100: complexity += 1
        if len(query) > 200: complexity += 1
        if any(w in query.lower() for w in ["analyze", "compare", "evaluate", "why", "how"]): complexity += 1
        if any(w in query.lower() for w in ["multi-step", "reasoning", "chain"]): complexity += 1
        return min(complexity, 5)

    def generate_response(self, query: str) -> str:
        """生成回答（兼容 Phi-3 接口）"""
        return self._call_llm(query) or "No response"

    async def analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        """分析查询复杂度 (Phase 2 Requirement)"""
        # 使用更严格的 Prompt 要求 JSON 格式
        prompt = f"""
        You are a Query Complexity Analyzer. Analyze the following user query carefully.
        
        Query: "{query}"
        
        Determine if this query is "simple" (can be answered directly with internal knowledge, no multi-step reasoning needed) or "complex" (requires external knowledge, multi-step reasoning, or tool use).
        
        Consider:
        1. Query length and structure.
        2. Need for real-time data or specific domain knowledge (Complex).
        3. Multi-hop reasoning requirements (Complex).
        4. Ambiguity or need for clarification (Complex).
        
        Respond ONLY with a valid JSON object in the following format:
        {{
            "beta": <float, 0.0-1.0, lower is simpler>,
            "is_simple": <boolean>,
            "confidence": <float, 0.0-1.0>,
            "reasoning": "<short explanation>"
        }}
        """
        
        try:
            # 强制使用 JSON 模式（如果模型支持）或通过 Prompt 约束
            response = self._call_llm(prompt, temperature=0.1)
            
            if not response:
                raise ValueError("Empty response from LLM")
                
            # 尝试提取 JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
                
                # 确保字段存在
                result.setdefault("beta", 0.5)
                result.setdefault("is_simple", False)
                result.setdefault("confidence", 0.5)
                
                return result
            else:
                # 如果无法解析 JSON，回退到基于关键词的简单判断
                logger.warning(f"Could not parse JSON from complexity analysis: {response[:100]}...")
                is_simple = "simple" in response.lower() and "complex" not in response.lower()
                return {
                    "beta": 0.3 if is_simple else 0.7,
                    "is_simple": is_simple,
                    "confidence": 0.6,
                    "reasoning": "Fallback parsing"
                }
                
        except Exception as e:
            logger.warning(f"Complexity analysis failed: {e}")
            # Fallback heuristic
            length = len(query)
            # 增加基于关键词的启发式判断
            complex_keywords = ["if", "when", "how", "compare", "difference", "step", "reason", "plan", "analyze"]
            has_complex_keywords = any(k in query.lower() for k in complex_keywords)
            
            is_simple = length < 50 and not has_complex_keywords
            return {
                "beta": 0.2 if is_simple else 0.8,
                "is_simple": is_simple,
                "confidence": 0.5,
                "reasoning": "Heuristic fallback"
            }
