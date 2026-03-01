"""
Local LLM Service - Powered by Phi-3 Mini & llama.cpp
负责本地推理、查询分类和预处理，作为云端大模型的"副驾驶"。
"""

import os
import time
import json
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

import asyncio
from asyncio import Semaphore

from src.core.utils.smart_model_manager import get_model_manager

# 🛡️ P4.5: 本地服务限流器 (防止本地模型过载)
# Note: SmartModelManager now handles memory limiting, but concurrency limiting is still useful here
_local_semaphore = Semaphore(5) # 允许5个并发请求

class LocalLLMService:
    """
    本地 LLM 服务 (Phi-3 Mini)
    
    功能:
    1. 复杂度分析 (Beta 计算)
    2. 简单问题直接回答
    3. 查询重写与 HyDE 生成
    4. 🛡️ 内置并发限流
    5. 🛡️ 使用 SmartModelManager 管理生命周期
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or os.getenv("PHI3_MODEL_PATH")
        if not self.model_path:
            # 默认路径
            self.model_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "models", 
                "Phi-3-mini-4k-instruct-q4.gguf"
            )
        
        # 不要立即加载，使用 SmartModelManager
        self.model_manager = get_model_manager()
        # Pre-check existence but don't load
        if not os.path.exists(self.model_path):
            logger.warning(f"⚠️ Phi-3 模型文件未找到: {self.model_path}")
            logger.warning("💡 请运行 scripts/setup_phi3.py 下载模型")

    @property
    def llm(self):
        """
        获取 LLM 实例（通过 SmartModelManager 按需加载）
        """
        def loader():
            if not os.path.exists(self.model_path):
                return None
                
            try:
                from llama_cpp import Llama
                logger.info(f"🔄 正在加载 Phi-3 Mini ({self.model_path})...")
                start_time = time.time()
                
                # 初始化模型
                model = Llama(
                    model_path=self.model_path,
                    n_ctx=4096,
                    n_gpu_layers=-1, 
                    verbose=False
                )
                logger.info(f"✅ Phi-3 加载完成，耗时 {time.time() - start_time:.2f}s")
                return model
            except ImportError:
                logger.error("❌ 未安装 llama-cpp-python")
                return None
            except Exception as e:
                logger.error(f"❌ Phi-3 加载失败: {e}")
                return None

        # 获取模型（自动处理缓存和LRU）
        return self.model_manager.get_model("phi3_mini", loader)

    def _ensure_model_loaded(self):
        """Deprecated: Logic moved to property 'llm' with SmartModelManager"""
        pass

    async def analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        """
        分析查询复杂度 (Beta) - 异步版本带限流
        返回: {"beta": float, "reason": str, "is_simple": bool}
        """
        if not self.llm:
            return {"beta": 1.0, "reason": "Local LLM not available", "is_simple": False}

        prompt = f"""<|user|>
Analyze the complexity of this query for a RAG system.
Query: "{query}"

Output ONLY a JSON object with:
- "beta": float (0.1=trivial, 0.5=moderate, 1.0=complex, 2.0=very complex)
- "confidence": float (0.0-1.0, how sure are you about this complexity?)
- "reason": short explanation
- "is_simple": boolean (true if beta < 0.4 AND confidence > 0.8)
<|end|>
<|assistant|>
"""
        # 🛡️ P4.5: 使用信号量进行限流
        # 注意: llama_cpp是同步的，为了不阻塞事件循环，我们在线程池中运行它
        # 但同时我们需要限制并发数量，避免CPU/内存爆炸
        async with _local_semaphore:
            try:
                # 将同步调用包装到线程池中
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, 
                    lambda: self.llm(
                        prompt, 
                        max_tokens=128, 
                        stop=["<|end|>"], 
                        temperature=0.1,
                        logprobs=1
                    )
                )
                
                text = response['choices'][0]['text'].strip()
                # 尝试解析 JSON
                # 简单的清理逻辑
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0]
                elif "{" in text:
                    text = text[text.find("{"):text.rfind("}")+1]
                    
                result = json.loads(text)
                
                # 🛡️ P4: 鲁棒性增强 - 确保 confidence 字段存在
                if "confidence" not in result:
                    result["confidence"] = 0.5 # Default low confidence
                    
                return result
            except Exception as e:
                logger.warning(f"复杂度分析失败: {e}")
                return {"beta": 1.0, "reason": "Analysis failed", "is_simple": False, "confidence": 0.0}

    def generate_response(self, query: str, context: str = "") -> str:
        """生成回答 (用于简单问题)"""
        if not self.llm:
            return "Local LLM not available."

        system_prompt = "You are a helpful AI assistant. Answer concisely."
        prompt = f"<|user|>\n{system_prompt}\nContext: {context}\n\nQuestion: {query}<|end|>\n<|assistant|>"
        
        try:
            response = self.llm(
                prompt,
                max_tokens=512,
                stop=["<|end|>"],
                temperature=0.7
            )
            return response['choices'][0]['text'].strip()
        except Exception as e:
            logger.error(f"生成回答失败: {e}")
            return "Error generating response."

    def generate_hyde(self, query: str) -> str:
        """生成 HyDE 假设文档"""
        if not self.llm:
            return ""
            
        prompt = f"<|user|>\nWrite a hypothetical passage that answers this question.\nQuestion: {query}<|end|>\n<|assistant|>"
        try:
            response = self.llm(
                prompt,
                max_tokens=256,
                stop=["<|end|>"],
                temperature=0.8
            )
            return response['choices'][0]['text'].strip()
        except Exception as e:
            logger.error(f"HyDE 生成失败: {e}")
            return ""
