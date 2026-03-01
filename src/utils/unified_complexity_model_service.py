#!/usr/bin/env python3
"""
统一复杂度判断和模型选择服务
集中管理查询复杂度判断和模型选择策略，避免重复计算
"""
import logging
import os
import json
import re
import time
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ComplexityLevel(Enum):
    """复杂度级别"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class ModelType(Enum):
    """模型类型"""
    FAST = "fast"  # deepseek-chat
    REASONING = "reasoning"  # deepseek-reasoner


@dataclass
class ComplexityResult:
    """复杂度判断结果"""
    level: ComplexityLevel
    score: float  # 0.0-10.0
    factors: list[str]
    needs_reasoning_chain: bool
    llm_judgment: Optional[str] = None  # LLM判断结果（如果使用）
    metadata: Optional[Dict[str, Any]] = None  # 扩展元数据（用于LLM统一分析）
    confidence: float = 0.8  # 分析置信度 0.0-1.0


@dataclass
class ModelSelectionResult:
    """模型选择结果"""
    model_type: ModelType
    use_thinking_mode: bool
    confidence: float  # 0.0-1.0
    reason: str


class UnifiedComplexityModelService:
    """统一复杂度判断和模型选择服务"""
    
    _instance: Optional['UnifiedComplexityModelService'] = None
    _initialized: bool = False
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化服务"""
        if self._initialized:
            return
        
        self.logger = logging.getLogger(__name__)
        self._initialized = True
        
        # 缓存（避免重复计算）
        self._complexity_cache: Dict[str, ComplexityResult] = {}
        self._model_selection_cache: Dict[str, ModelSelectionResult] = {}
        self._cache_ttl = 300  # 5分钟缓存
        
        # LLM集成（用于智能判断）
        self._fast_llm = None
        self._llm_integration = None
        self._initialize_llm()
        
        # ML/RL优化器
        self._adaptive_optimizer = None
        self._initialize_optimizer()
        
        # 配置
        self._config = {
            'use_llm_judgment': True,  # 优先使用LLM判断
            'llm_judgment_timeout': 5.0,  # LLM判断超时时间（秒）
            'complexity_thresholds': {
                'simple': 2.0,
                'medium': 4.0,
                'complex': 6.0
            },
            'model_selection_thresholds': {
                'fast_max_complexity': 4.0,
                'reasoning_min_complexity': 6.0,
                'evidence_quality_threshold': 0.85
            }
        }
        
        self.logger.info("✅ 统一复杂度判断和模型选择服务初始化完成")
    
    def _initialize_llm(self):
        """初始化LLM集成"""
        try:
            from src.core.llm_integration import LLMIntegration
            
            # 快速LLM（用于复杂度判断）
            fast_llm_config = {
                'llm_provider': 'deepseek',
                'api_key': os.getenv('DEEPSEEK_API_KEY', ''),
                'model': os.getenv('DEEPSEEK_FAST_MODEL', 'deepseek-chat'),
                'base_url': os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
            }
            self._fast_llm = LLMIntegration(fast_llm_config)
            
            # 推理LLM（用于复杂判断）
            reasoning_llm_config = {
                'llm_provider': 'deepseek',
                'api_key': os.getenv('DEEPSEEK_API_KEY', ''),
                'model': os.getenv('DEEPSEEK_MODEL', 'deepseek-reasoner'),
                'base_url': os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
            }
            self._llm_integration = LLMIntegration(reasoning_llm_config)
            
            self.logger.info("✅ LLM集成初始化成功")
        except Exception as e:
            self.logger.warning(f"LLM集成初始化失败: {e}")
    
    def _initialize_optimizer(self):
        """初始化ML/RL优化器"""
        try:
            from src.core.adaptive_optimizer import AdaptiveOptimizer
            self._adaptive_optimizer = AdaptiveOptimizer()
            self.logger.info("✅ ML/RL优化器初始化成功")
        except Exception as e:
            self.logger.warning(f"ML/RL优化器初始化失败: {e}")
    
    def assess_complexity(
        self,
        query: str,
        query_type: Optional[str] = None,
        evidence_count: int = 0,
        query_analysis: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> ComplexityResult:
        """评估查询复杂度 - 🚀 统一入口

        Args:
            query: 查询文本
            query_type: 查询类型（可选）
            evidence_count: 证据数量（可选）
            query_analysis: 查询分析结果（可选，避免重复分析）
            use_cache: 是否使用缓存

        Returns:
            ComplexityResult: 复杂度判断结果
        """
        # 检查缓存
        cache_key = f"{query}_{query_type}_{evidence_count}"
        if use_cache and cache_key in self._complexity_cache:
            cached_result = self._complexity_cache[cache_key]
            self.logger.debug(f"✅ 使用缓存的复杂度判断结果: {cached_result.level.value}")
            return cached_result

        try:
            # 🚀 新增：优先尝试LLM统一分析（最智能的方法）
            if self._config['use_llm_judgment'] and self._fast_llm:
                try:
                    unified_result = self._assess_with_llm_unified_analysis(query)
                    if unified_result:
                        self.logger.info(f"✅ LLM统一分析成功: {unified_result.level.value} (评分: {unified_result.score:.2f})")
                        if use_cache:
                            self._complexity_cache[cache_key] = unified_result
                        return unified_result
                except Exception as e:
                    self.logger.debug(f"LLM统一分析失败，回退到传统方法: {e}")

            # 🚀 回退：使用LLM判断（保持兼容性）
            if self._config['use_llm_judgment'] and self._fast_llm:
                llm_result = self._assess_complexity_with_llm(query, query_type, evidence_count)
                if llm_result:
                    # 缓存结果
                    if use_cache:
                        self._complexity_cache[cache_key] = llm_result
                    return llm_result

            # Fallback: 使用规则判断
            rule_result = self._assess_complexity_with_rules(query, query_type, evidence_count, query_analysis)

            # 缓存结果
            if use_cache:
                self._complexity_cache[cache_key] = rule_result

            return rule_result

        except Exception as e:
            self.logger.error(f"复杂度判断失败: {e}", exc_info=True)
            # 返回默认结果（中等复杂度）
            default_result = ComplexityResult(
                level=ComplexityLevel.MEDIUM,
                score=3.0,
                factors=["判断失败，使用默认值"],
                needs_reasoning_chain=True
            )
            return default_result
    
    def _assess_complexity_with_llm(
        self,
        query: str,
        query_type: Optional[str] = None,
        evidence_count: int = 0
    ) -> Optional[ComplexityResult]:
        """使用LLM判断复杂度
        
        🚀 改进：使用LLM返回三个复杂度级别（simple/medium/complex），而非仅yes/no
        """
        try:
            if not self._fast_llm:
                return None
            
            # 🚀 改进：使用更详细的LLM复杂度判断方法（返回simple/medium/complex）
            # 优先使用LLMIntegration的_estimate_query_complexity_with_llm方法
            if hasattr(self._fast_llm, '_estimate_query_complexity_with_llm'):
                try:
                    complexity_str = self._fast_llm._estimate_query_complexity_with_llm(
                        query=query,
                        evidence_count=evidence_count,
                        query_type=query_type
                    )

                    # 确保complexity_str是字符串类型
                    if isinstance(complexity_str, str):
                        pass  # 已经是字符串
                    elif isinstance(complexity_str, (int, float)):
                        complexity_str = str(complexity_str)  # 转换为字符串
                    else:
                        complexity_str = str(complexity_str) if complexity_str else ""
                    
                    if complexity_str:
                        complexity_lower = complexity_str.strip().lower()
                        
                        # 映射到ComplexityLevel
                        if "simple" in complexity_lower:
                            level = ComplexityLevel.SIMPLE
                            score = 2.0
                            needs_reasoning_chain = False
                        elif "complex" in complexity_lower:
                            level = ComplexityLevel.COMPLEX
                            score = 6.0
                            needs_reasoning_chain = True
                        elif "medium" in complexity_lower:
                            level = ComplexityLevel.MEDIUM
                            score = 4.0
                            needs_reasoning_chain = True
                        else:
                            # 默认中等复杂度
                            level = ComplexityLevel.MEDIUM
                            score = 4.0
                            needs_reasoning_chain = True
                        
                        result = ComplexityResult(
                            level=level,
                            score=score,
                            factors=[f"LLM判断: {complexity_str.strip()}"],
                            needs_reasoning_chain=needs_reasoning_chain,
                            llm_judgment=complexity_str.strip()
                        )
                        
                        self.logger.info(f"✅ LLM复杂度判断: {level.value} (评分: {score:.2f}, 需要推理链: {needs_reasoning_chain})")
                        print(f"✅ [复杂度判断] LLM判断结果: {level.value} (评分: {score:.2f})")
                        return result
                except Exception as e:
                    self.logger.debug(f"⚠️ LLM复杂度判断方法调用失败: {e}，使用简化方法")
            
            # Fallback: 使用简化的LLM判断（返回级别和评分）
            prompt = f"""分析以下查询的复杂度，返回JSON格式：{{"level": "simple/medium/complex", "score": 0.0-10.0, "reason": "判断原因"}}

**判断标准**：
- **simple** (评分: 1.0-3.0)：单步查询，直接事实检索。例如："法国的首都是什么？"
- **medium** (评分: 3.0-6.0)：多跳查询，但每步都是直接事实查找。例如："第15任第一夫人的母亲的名字"
- **complex** (评分: 6.0-10.0)：需要复杂推理、逻辑推导、计算、分析。例如："如果A和B相同，且C和D相同，那么..."

**评分细则**：
- simple: 1.0-3.0（单步查询）
- medium: 3.0-6.0（多跳查询，每步都是直接事实查找）
  - 3.0-4.0: 2-3步的多跳查询
  - 4.0-5.0: 4-5步的多跳查询
  - 5.0-6.0: 6+步的多跳查询或包含多个条件
- complex: 6.0-10.0（需要复杂推理）
  - 6.0-7.0: 需要简单推理或计算
  - 7.0-8.0: 需要复杂推理或多条件分析
  - 8.0-10.0: 需要深度推理、逻辑推导或大量数据处理

**查询**: {query[:500]}

返回JSON格式（只返回JSON，不要其他内容）:"""
            
            response = self._fast_llm._call_llm(prompt)
            
            if response:
                # 🚀 改进：尝试解析JSON格式的响应（包含精确评分）
                try:
                    # 尝试提取JSON
                    json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        complexity_data = json.loads(json_str)
                        
                        level_str = complexity_data.get('level', 'medium').lower()
                        score = float(complexity_data.get('score', 4.0))
                        reason = complexity_data.get('reason', 'LLM判断')
                        
                        # 确保评分在合理范围内
                        score = max(1.0, min(10.0, score))
                        
                        # 映射到ComplexityLevel
                        if "simple" in level_str:
                            level = ComplexityLevel.SIMPLE
                            needs_reasoning_chain = False
                        elif "complex" in level_str:
                            level = ComplexityLevel.COMPLEX
                            needs_reasoning_chain = True
                        else:
                            level = ComplexityLevel.MEDIUM
                            needs_reasoning_chain = True
                        
                        result = ComplexityResult(
                            level=level,
                            score=score,
                            factors=[f"LLM判断: {reason}"],
                            needs_reasoning_chain=needs_reasoning_chain,
                            llm_judgment=f"{level_str} (评分: {score:.2f}, 原因: {reason})"
                        )
                        
                        self.logger.info(f"✅ LLM复杂度判断: {level.value} (评分: {score:.2f}, 需要推理链: {needs_reasoning_chain})")
                        print(f"✅ [复杂度判断] LLM判断结果: {level.value} (评分: {score:.2f}, 原因: {reason})")
                        return result
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    self.logger.debug(f"⚠️ LLM返回的不是有效JSON，使用文本解析: {e}")
                
                # Fallback: 使用文本解析（向后兼容）
                response_lower = response.strip().lower()
                
                # 提取复杂度级别和可能的评分
                score = 4.0  # 默认评分
                if "simple" in response_lower and "complex" not in response_lower:
                    level = ComplexityLevel.SIMPLE
                    score = 2.0
                    needs_reasoning_chain = False
                elif "complex" in response_lower:
                    level = ComplexityLevel.COMPLEX
                    score = 6.0
                    needs_reasoning_chain = True
                elif "medium" in response_lower:
                    level = ComplexityLevel.MEDIUM
                    score = 4.0
                    needs_reasoning_chain = True
                else:
                    # 默认中等复杂度
                    level = ComplexityLevel.MEDIUM
                    score = 4.0
                    needs_reasoning_chain = True
                
                # 尝试从响应中提取数字评分（如果LLM返回了）
                score_match = re.search(r'score[:\s]*([\d.]+)', response_lower)
                if score_match:
                    try:
                        extracted_score = float(score_match.group(1))
                        if 1.0 <= extracted_score <= 10.0:
                            score = extracted_score
                    except ValueError:
                        pass
                
                result = ComplexityResult(
                    level=level,
                    score=score,
                    factors=[f"LLM判断: {response.strip()}"],
                    needs_reasoning_chain=needs_reasoning_chain,
                    llm_judgment=response.strip()
                )
                
                self.logger.info(f"✅ LLM复杂度判断: {level.value} (评分: {score:.2f}, 需要推理链: {needs_reasoning_chain})")
                print(f"✅ [复杂度判断] LLM判断结果: {level.value} (评分: {score:.2f}, 原因: {reason if 'reason' in locals() else '文本解析'})")
                return result
            
            return None
            
        except Exception as e:
            self.logger.warning(f"LLM复杂度判断失败: {e}")
            return None

    def _assess_with_llm_unified_analysis(self, query: str) -> Optional[ComplexityResult]:
        """🚀 LLM统一分析：一次性完成复杂度判断、类型识别、模型推荐

        这是一个革命性的方法，让LLM一次性完成所有分析，避免碎片化决策。

        Args:
            query: 查询文本

        Returns:
            ComplexityResult: 复杂度分析结果，如果失败返回None
        """
        try:
            # 构建统一分析提示词
            prompt = self._create_unified_analysis_prompt(query)

            # 调用LLM进行统一分析
            llm_response = self._call_llm_for_analysis(prompt)

            # 解析LLM响应
            analysis_result = self._parse_unified_analysis_response(llm_response, query)

            if analysis_result:
                self.logger.debug(f"LLM统一分析成功: 复杂度={analysis_result.level.value}, 评分={analysis_result.score}")
                return analysis_result

        except Exception as e:
            self.logger.debug(f"LLM统一分析失败: {e}")

        return None

    def _create_unified_analysis_prompt(self, query: str) -> str:
        """增强的统一分析提示词 - 包含更多上下文和分析维度"""
        from datetime import datetime

        return f"""
# 查询智能分析任务 - 增强版

你是一个专业的查询分析专家，需要对用户查询进行**全面、统一的分析**。

## 查询上下文
当前时间: {datetime.now().strftime('%Y-%m-%d')}
查询类型: 知识推理和检索
系统能力: 事实检索、多跳推理、数值计算、比较分析

## 查询内容
{query}

## 分析要求

请对查询进行**系统性分析**，特别注意以下几点：

### 🎯 复杂度分析核心要点
1. **步骤数量**: 完成查询需要多少独立步骤？
2. **推理类型**: 是事实检索、逻辑推理、计算还是比较？
3. **领域跨度**: 涉及几个不同领域？
4. **数据需求**: 需要什么类型的数据（实时、历史、专业）？

### 🎯 模型推荐核心规则
- **fast (deepseek-chat)**: 简单事实、单步检索、常识问题
- **reasoning (deepseek-reasoner)**: 多步推理、复杂逻辑、计算分析
- **thinking_mode**: 需要深度思考、不确定性高、涉及多个变量
- **thinking_depth**:
  * minimal: 简单问题，直接回答
  * standard: 中等复杂度，需要一些思考
  * deep: 非常复杂，需要深入分析

## 输出格式（严格的JSON）

{{
    "complexity": "simple/medium/complex",
    "complexity_score": 1.0-10.0,
    "query_type": "类型字符串",
    "query_type_confidence": 0.0-1.0,
    "reasoning_steps_estimate": 整数,
    "required_domains": ["领域1", "领域2"],
    "required_skills": ["技能1", "技能2"],
    "special_requirements": ["要求1", "要求2"],
    "recommended_model": "fast/reasoning/fast_with_thinking/reasoning_with_thinking",
    "use_thinking_mode": true/false,
    "thinking_depth": "minimal/standard/deep",
    "reasoning_chain_description": "用→分隔的推理步骤，例如: 步骤1→步骤2→步骤3",
    "potential_challenges": ["挑战1", "挑战2"],
    "confidence": 0.0-1.0
}}

## 📚 分析示例

### 示例1（简单）: "法国的首都是什么？"
{{
    "complexity": "simple",
    "complexity_score": 1.0,
    "query_type": "fact_retrieval",
    "reasoning_steps_estimate": 1,
    "recommended_model": "fast",
    "use_thinking_mode": false,
    "reasoning_chain_description": "检索法国首都",
    "confidence": 0.98
}}

### 示例2（中等）: "第15任第一夫人的母亲的名字"
{{
    "complexity": "medium",
    "complexity_score": 5.5,
    "query_type": "historical_relation",
    "reasoning_steps_estimate": 3,
    "recommended_model": "reasoning",
    "use_thinking_mode": false,
    "reasoning_chain_description": "查找第15任第一夫人→查找她的母亲→提取名字",
    "confidence": 0.85
}}

### 示例3（复杂）: "Bronte塔高度等于1847年Charlotte Bronte书籍的杜威分类号..."
{{
    "complexity": "complex",
    "complexity_score": 9.2,
    "query_type": "multi_domain",
    "reasoning_steps_estimate": 8,
    "recommended_model": "reasoning_with_thinking",
    "use_thinking_mode": true,
    "thinking_depth": "deep",
    "reasoning_chain_description": "识别1847年书籍→查找杜威分类号→提取数值→获取纽约建筑高度→排序列表→计算排名→验证时间→生成答案",
    "confidence": 0.92
}}

## 现在开始分析

请分析以下查询，返回严格的JSON格式：

查询: {query}

JSON响应:
"""

    def _call_llm_for_analysis(self, prompt: str) -> str:
        """统一的LLM调用方法 - 支持多种接口"""
        if self._fast_llm is None:
            raise RuntimeError("Fast LLM 未初始化")

        try:
            # 统一的LLM调用接口配置
            llm_methods = [
                ('generate', {'temperature': 0.1, 'max_tokens': 2000, 'timeout': 30}),
                ('_call_llm', {'temperature': 0.1, 'max_tokens': 2000}),
                ('call', {'temperature': 0.1, 'max_tokens': 2000}),
            ]

            import inspect

            for method_name, kwargs in llm_methods:
                if hasattr(self._fast_llm, method_name):
                    method = getattr(self._fast_llm, method_name)
                    sig = inspect.signature(method)

                    # 根据方法签名调整参数
                    call_kwargs = kwargs.copy()

                    # 检查参数名
                    if 'prompt' in sig.parameters:
                        call_kwargs['prompt'] = prompt
                    elif 'message' in sig.parameters:
                        call_kwargs['message'] = prompt
                    elif 'input' in sig.parameters:
                        call_kwargs['input'] = prompt
                    else:
                        # 尝试位置参数
                        call_kwargs = (prompt,) + tuple(kwargs.values())

                    try:
                        if isinstance(call_kwargs, tuple):
                            response = method(*call_kwargs)
                        else:
                            response = method(**call_kwargs)

                        if response:
                            return str(response)
                    except Exception as method_error:
                        self.logger.debug(f"方法 {method_name} 调用失败: {method_error}")
                        continue

            # 如果所有方法都失败
            raise RuntimeError("没有可用的LLM调用方法")

        except Exception as e:
            self.logger.error(f"LLM调用失败: {e}")
            raise

    def _parse_unified_analysis_response(self, response: str, query: str) -> Optional[ComplexityResult]:
        """解析LLM统一分析响应"""
        try:
            # 提取JSON
            json_str = self._extract_json_from_response(response)
            data = json.loads(json_str)

            # 验证必填字段
            required_fields = ['complexity', 'complexity_score']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"缺少必填字段: {field}")

            # 转换为ComplexityResult
            complexity_level = {
                'simple': ComplexityLevel.SIMPLE,
                'medium': ComplexityLevel.MEDIUM,
                'complex': ComplexityLevel.COMPLEX
            }.get(data['complexity'], ComplexityLevel.MEDIUM)

            # 构建因素描述
            factors = []
            if 'reasoning_steps_estimate' in data:
                factors.append(f"估计推理步骤: {data['reasoning_steps_estimate']}")
            if 'required_domains' in data and data['required_domains']:
                factors.append(f"涉及领域: {', '.join(data['required_domains'][:3])}")
            if 'query_type' in data:
                factors.append(f"查询类型: {data['query_type']}")
            if 'potential_challenges' in data and data['potential_challenges']:
                factors.append(f"潜在挑战: {len(data['potential_challenges'])}项")

            # 确定是否需要推理链
            needs_reasoning_chain = (
                complexity_level in [ComplexityLevel.MEDIUM, ComplexityLevel.COMPLEX] or
                data.get('reasoning_steps_estimate', 1) > 2
            )

            result = ComplexityResult(
                level=complexity_level,
                score=float(data['complexity_score']),
                factors=factors,
                needs_reasoning_chain=needs_reasoning_chain,
                # 扩展信息（用于后续处理）
                metadata={
                    'query_type': data.get('query_type'),
                    'query_type_confidence': data.get('query_type_confidence', 0.8),
                    'required_domains': data.get('required_domains', []),
                    'required_skills': data.get('required_skills', []),
                    'recommended_model': data.get('recommended_model'),
                    'use_thinking_mode': data.get('use_thinking_mode', False),
                    'reasoning_chain_description': data.get('reasoning_chain_description', ''),
                    'confidence': data.get('confidence', 0.8)
                }
            )

            return result

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            self.logger.debug(f"解析统一分析响应失败: {e}")
            return None

    def _extract_json_from_response(self, response: str) -> str:
        """从响应中提取JSON"""
        # 尝试直接解析
        try:
            json.loads(response)
            return response
        except json.JSONDecodeError:
            pass

        # 尝试提取JSON对象
        json_patterns = [
            r'```json\n(.*?)\n```',  # Markdown JSON代码块
            r'```\n(.*?)\n```',      # 普通代码块
            r'\{.*\}',               # JSON对象
        ]

        for pattern in json_patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                try:
                    json_str = match.group(1) if len(match.groups()) > 0 else match.group(0)
                    json.loads(json_str)  # 验证JSON有效性
                    return json_str
                except json.JSONDecodeError:
                    continue

        # 如果都无法解析，抛出异常
        raise ValueError("无法从响应中提取有效的JSON")

    def _assess_complexity_with_rules(
        self,
        query: str,
        query_type: Optional[str] = None,
        evidence_count: int = 0,
        query_analysis: Optional[Dict[str, Any]] = None
    ) -> ComplexityResult:
        """使用规则判断复杂度（Fallback）"""
        complexity_score = 0.0
        factors = []
        
        # 1. 基于查询类型判断
        if query_analysis:
            analysis_complexity = query_analysis.get("complexity", 0.5)
            if analysis_complexity >= 0.7:
                complexity_score += 3.0
                factors.append(f"查询类型复杂度高: {analysis_complexity:.2f}")
        
        complex_types = ["causal", "comparative", "analytical", "mathematical"]
        if query_type in complex_types:
            complexity_score += 2.0
            factors.append(f"复杂查询类型: {query_type}")
        
        # 2. 基于查询特征判断（多跳查询、多条件查询）
        query_lower = query.lower()
        
        # 多跳查询特征 - 改进版，更准确地识别推理复杂度
        multi_hop_indicators = [
            "whose", "who was", "what is the", "what was",
            "where", "when", "why", "how",
            "dewey", "decimal", "classification", "ranking", "rank",
            "height", "building", "tower", "published in"
        ]

        # 更智能的多跳检测
        multi_hop_score = 0.0
        found_indicators = []

        for indicator in multi_hop_indicators:
            if indicator in query_lower:
                found_indicators.append(indicator)
                # 根据关键词重要性给予不同权重
                if indicator in ["whose", "what is the", "what was"]:
                    multi_hop_score += 1.5  # 强多跳指示器
                elif indicator in ["dewey", "decimal", "classification", "ranking", "height"]:
                    multi_hop_score += 1.2  # 领域特定复杂指示器
                else:
                    multi_hop_score += 0.8  # 一般多跳指示器

        # 特殊模式识别
        if "same number as" in query_lower or "same as" in query_lower:
            multi_hop_score += 2.0  # 等值关系需要推理
            found_indicators.append("equality_relationship")

        if "among" in query_lower and ("buildings" in query_lower or "cities" in query_lower):
            multi_hop_score += 1.5  # 排名/比较查询
            found_indicators.append("ranking_query")

        if multi_hop_score > 0:
            complexity_score += min(multi_hop_score, 4.0)  # 最高加4分
            factors.append(f"推理复杂度高: {multi_hop_score:.1f}分 ({', '.join(found_indicators[:3])})")
        
        # 多条件查询特征
        multi_condition_indicators = [" and ", " or ", "both", "either", "neither", "以及", "或者"]
        if any(indicator in query_lower for indicator in multi_condition_indicators):
            complexity_score += 1.5
            factors.append("多条件查询特征")
        
        # 3. 基于查询长度判断
        word_count = len(query.split())
        if word_count > 20:
            complexity_score += 1.0
            factors.append(f"查询较长: {word_count}词")
        
        # 4. 基于证据数量判断
        if evidence_count > 10:
            complexity_score += 1.0
            factors.append(f"证据数量多: {evidence_count}")
        
        # 确定复杂度级别
        thresholds = self._config['complexity_thresholds']
        if complexity_score <= thresholds['simple']:
            level = ComplexityLevel.SIMPLE
            needs_reasoning_chain = False
        elif complexity_score <= thresholds['medium']:
            level = ComplexityLevel.MEDIUM
            needs_reasoning_chain = True
        else:
            level = ComplexityLevel.COMPLEX
            needs_reasoning_chain = True
        
        if not factors:
            factors.append("规则判断: 默认中等复杂度")
        
        result = ComplexityResult(
            level=level,
            score=complexity_score,
            factors=factors,
            needs_reasoning_chain=needs_reasoning_chain
        )
        
        self.logger.info(f"✅ 规则复杂度判断: {level.value} (评分: {complexity_score:.2f}, 需要推理链: {needs_reasoning_chain})")
        return result
    
    def select_model(
        self,
        query: str,
        complexity_result: ComplexityResult,
        evidence: Optional[list] = None,
        query_type: Optional[str] = None,
        use_cache: bool = True
    ) -> ModelSelectionResult:
        """选择模型 - 🚀 统一入口
        
        Args:
            query: 查询文本
            complexity_result: 复杂度判断结果
            evidence: 证据列表（可选，用于评估证据质量）
            query_type: 查询类型（可选）
            use_cache: 是否使用缓存
        
        Returns:
            ModelSelectionResult: 模型选择结果
        """
        # 检查缓存
        cache_key = f"{query}_{complexity_result.level.value}_{len(evidence) if evidence else 0}"
        if use_cache and cache_key in self._model_selection_cache:
            cached_result = self._model_selection_cache[cache_key]
            self.logger.debug(f"✅ 使用缓存的模型选择结果: {cached_result.model_type.value}")
            return cached_result
        
        try:
            # 🚀 1. 优先使用LLM统一分析的推荐
            llm_result = self._select_model_from_llm_analysis(complexity_result)
            if llm_result:
                if use_cache:
                    self._model_selection_cache[cache_key] = llm_result
                return llm_result

            # 🚀 2. 使用ML/RL优化器
            ml_result = self._select_model_with_ml_optimization(
                complexity_result, query_type, evidence
            )
            if ml_result:
                if use_cache:
                    self._model_selection_cache[cache_key] = ml_result
                return ml_result

            # 🚀 3. 传统规则判断
            traditional_result = self._select_model_with_traditional_logic(
                complexity_result, evidence, query_type
            )

            if use_cache:
                self._model_selection_cache[cache_key] = traditional_result

            return traditional_result
            
        except Exception as e:
            self.logger.error(f"模型选择失败: {e}", exc_info=True)
            # 返回默认结果（推理模型）
            return ModelSelectionResult(
                model_type=ModelType.REASONING,
                use_thinking_mode=False,
                confidence=0.5,
                reason="选择失败，使用默认推理模型"
            )

    def _select_model_from_llm_analysis(self, complexity_result: ComplexityResult) -> Optional[ModelSelectionResult]:
        """从LLM统一分析结果中选择模型"""
        if not complexity_result.metadata:
            return None

        metadata = complexity_result.metadata
        recommended_model = metadata.get('recommended_model')
        confidence = metadata.get('confidence', 0.8)
        use_thinking_mode = metadata.get('use_thinking_mode', False)

        if not recommended_model:
            return None

        # 映射LLM推荐到系统模型类型
        model_mapping = {
            'fast': ModelType.FAST,
            'reasoning': ModelType.REASONING,
            'fast_with_thinking': ModelType.FAST,
            'reasoning_with_thinking': ModelType.REASONING
        }

        if recommended_model not in model_mapping:
            self.logger.warning(f"未知的LLM模型推荐: {recommended_model}")
            return None

        # 生成详细的原因说明
        reasoning_chain = metadata.get('reasoning_chain_description', '')
        query_type = metadata.get('query_type', '未知类型')
        domains = ', '.join(metadata.get('required_domains', [])[:3])

        reason = f"LLM分析推荐: {recommended_model} (类型: {query_type}, 领域: {domains})"
        if reasoning_chain:
            # 计算推理步骤数量
            step_count = len(reasoning_chain.split('→')) if '→' in reasoning_chain else 1
            reason += f", 推理步骤: {step_count}步"

        return ModelSelectionResult(
            model_type=model_mapping[recommended_model],
            use_thinking_mode=use_thinking_mode,
            confidence=confidence,
            reason=reason
        )

    def _select_model_with_ml_optimization(
        self,
        complexity_result: ComplexityResult,
        query_type: Optional[str] = None,
        evidence: Optional[list] = None
    ) -> Optional[ModelSelectionResult]:
        """使用ML/RL优化器进行模型选择"""
        if not self._adaptive_optimizer or not query_type:
            return None

        try:
            thresholds = self._config['model_selection_thresholds']
            complexity_score = complexity_result.score

            optimized_model, complexity_threshold = self._adaptive_optimizer.get_optimized_model_selection(
                query_type, default_model='fast'
            )

            if optimized_model and complexity_threshold:
                # 根据优化的阈值调整
                if optimized_model == 'fast' and complexity_score <= complexity_threshold * 2:
                    thresholds['fast_max_complexity'] = complexity_threshold * 2
                    return ModelSelectionResult(
                        model_type=ModelType.FAST,
                        use_thinking_mode=False,
                        confidence=0.85,
                        reason=f"ML优化推荐快速模型（阈值: {complexity_threshold:.2f}）"
                    )
                elif optimized_model == 'reasoning' and complexity_score >= complexity_threshold:
                    thresholds['reasoning_min_complexity'] = complexity_threshold
                    use_thinking = complexity_score >= 4.0 or bool(evidence and len(evidence) > 3)
                    return ModelSelectionResult(
                        model_type=ModelType.REASONING,
                        use_thinking_mode=use_thinking,
                        confidence=0.9,
                        reason=f"ML优化推荐推理模型（阈值: {complexity_threshold:.2f}）"
                    )
        except Exception as e:
            self.logger.debug(f"ML/RL优化器选择失败: {e}")

        return None

    def _select_model_with_traditional_logic(
        self,
        complexity_result: ComplexityResult,
        evidence: Optional[list] = None,
        query_type: Optional[str] = None,
        use_cache: bool = True
    ) -> ModelSelectionResult:
        """传统模型选择逻辑（重构自原select_model方法）"""
        thresholds = self._config['model_selection_thresholds']
        complexity_score = complexity_result.score

        # 检查缓存
        cache_key = f"{complexity_result.level.value}_{len(evidence) if evidence else 0}"
        if use_cache and cache_key in self._model_selection_cache:
            cached_result = self._model_selection_cache[cache_key]
            self.logger.debug(f"✅ 使用缓存的传统模型选择结果: {cached_result.model_type.value}")
            return cached_result

        # 1. 简单任务：使用快速模型
        if complexity_score <= thresholds['fast_max_complexity']:
            result = ModelSelectionResult(
                model_type=ModelType.FAST,
                use_thinking_mode=False,
                confidence=0.9,
                reason=f"简单任务（复杂度评分: {complexity_score:.2f} <= {thresholds['fast_max_complexity']}）"
            )
            if use_cache:
                self._model_selection_cache[cache_key] = result
            return result

        # 2. 非常复杂的任务：使用推理模型
        if complexity_score >= thresholds['reasoning_min_complexity']:
            # 判断是否需要thinking mode
            use_thinking = complexity_score >= 4.0 or len(str(complexity_result)) > 100
            result = ModelSelectionResult(
                model_type=ModelType.REASONING,
                use_thinking_mode=use_thinking,
                confidence=0.95,
                reason=f"复杂任务（复杂度评分: {complexity_score:.2f} >= {thresholds['reasoning_min_complexity']}）"
            )
            if use_cache:
                self._model_selection_cache[cache_key] = result
            return result

        # 3. 中等复杂度任务：根据证据质量决定
        if evidence:
            relevance_scores = []
            for e in evidence[:5]:
                if hasattr(e, 'relevance_score'):
                    relevance_scores.append(e.relevance_score)
                elif isinstance(e, dict):
                    relevance_scores.append(e.get('relevance_score', 0.8))
                else:
                    relevance_scores.append(0.8)

            if relevance_scores:
                avg_relevance = sum(relevance_scores) / len(relevance_scores)
                if avg_relevance > thresholds['evidence_quality_threshold']:
                    # 高质量证据，使用快速模型
                    result = ModelSelectionResult(
                        model_type=ModelType.FAST,
                        use_thinking_mode=False,
                        confidence=0.8,
                        reason=f"中等复杂度但证据质量高（平均相关性: {avg_relevance:.2f} > {thresholds['evidence_quality_threshold']}）"
                    )
                    if use_cache:
                        self._model_selection_cache[cache_key] = result
                    return result

        # 默认：使用推理模型
        result = ModelSelectionResult(
            model_type=ModelType.REASONING,
            use_thinking_mode=False,
            confidence=0.7,
            reason=f"中等复杂度任务（复杂度评分: {complexity_score:.2f}）"
        )

        if use_cache:
            self._model_selection_cache[cache_key] = result

        return result
    
    def clear_cache(self):
        """清空缓存"""
        self._complexity_cache.clear()
        self._model_selection_cache.clear()
        self.logger.info("✅ 缓存已清空")


# 全局单例访问函数
_service_instance: Optional[UnifiedComplexityModelService] = None


def get_unified_complexity_model_service() -> UnifiedComplexityModelService:
    """获取统一复杂度判断和模型选择服务实例（单例）"""
    global _service_instance
    if _service_instance is None:
        _service_instance = UnifiedComplexityModelService()
    return _service_instance


class EnhancedUnifiedComplexityModelService(UnifiedComplexityModelService):
    """增强的统一复杂度模型服务（带学习和监控）"""

    def __init__(self):
        super().__init__()

        # 性能跟踪
        self.analysis_stats = {
            'total_queries': 0,
            'llm_unified_success': 0,
            'llm_fallback_success': 0,
            'rule_based_fallback': 0,
            'avg_analysis_time_ms': 0,
            'cache_hit_rate': 0.0
        }

        # 学习缓存
        self.learning_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0

        self.logger.info("✅ 增强统一复杂度服务初始化完成（带学习和监控）")

    def assess_complexity(self, query: str, **kwargs) -> ComplexityResult:
        """增强的复杂度分析（带学习和监控）"""
        self.analysis_stats['total_queries'] += 1
        start_time = time.time()

        try:
            # 1. 尝试从学习缓存中获取
            if kwargs.get('use_cache', True):
                learned_result = self._get_learned_analysis(query)
                if learned_result:
                    self.cache_hits += 1
                    self.logger.debug(f"使用学习缓存的分析结果")
                    return learned_result

            self.cache_misses += 1

            # 2. 调用父类的分析方法
            result = super().assess_complexity(query, **kwargs)

            # 3. 记录性能
            analysis_time = int((time.time() - start_time) * 1000)
            self._update_analysis_stats(result, analysis_time)

            # 4. 学习成功模式
            if result.confidence > 0.7:
                self._learn_from_success(query, result)

            return result

        except Exception as e:
            self.logger.error(f"增强分析失败: {e}")
            return super().assess_complexity(query, **kwargs)

    def _get_learned_analysis(self, query: str) -> Optional[ComplexityResult]:
        """从学习缓存中获取分析结果"""
        # 简单的基于查询模式的缓存
        query_key = self._generate_learning_key(query)
        return self.learning_cache.get(query_key)

    def _generate_learning_key(self, query: str) -> str:
        """生成学习缓存键"""
        # 提取查询模式（长度、关键词等）
        length = len(query)
        has_numbers = any(c.isdigit() for c in query)
        has_question = '?' in query
        complexity_indicators = sum(1 for word in ['whose', 'where', 'dewey', 'rank', 'height', 'building']
                                  if word.lower() in query.lower())

        return f"{length}_{has_numbers}_{has_question}_{complexity_indicators}"

    def _update_analysis_stats(self, result: ComplexityResult, analysis_time_ms: int):
        """更新分析统计"""
        # 更新平均时间
        total = self.analysis_stats['avg_analysis_time_ms'] * (self.analysis_stats['total_queries'] - 1)
        self.analysis_stats['avg_analysis_time_ms'] = (total + analysis_time_ms) / self.analysis_stats['total_queries']

        # 更新缓存命中率
        total_cache = self.cache_hits + self.cache_misses
        if total_cache > 0:
            self.analysis_stats['cache_hit_rate'] = self.cache_hits / total_cache

        # 根据分析来源更新统计
        if result.metadata:
            method = result.metadata.get('analysis_method', 'rule_based')
            if method == 'llm_unified':
                self.analysis_stats['llm_unified_success'] += 1
            elif method == 'llm_fallback':
                self.analysis_stats['llm_fallback_success'] += 1
            else:
                self.analysis_stats['rule_based_fallback'] += 1

    def _learn_from_success(self, query: str, result: ComplexityResult):
        """从成功的分析中学习"""
        if result.confidence < 0.8:
            return

        query_key = self._generate_learning_key(query)

        # 只缓存高置信度的结果
        if query_key not in self.learning_cache:
            self.learning_cache[query_key] = result
            self.logger.debug(f"学习到新的查询模式: {query_key}")

        # 限制缓存大小
        if len(self.learning_cache) > 100:
            # 移除最旧的条目（简单策略）
            oldest_key = next(iter(self.learning_cache))
            del self.learning_cache[oldest_key]

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return self.analysis_stats.copy()

    def clear_learning_cache(self):
        """清空学习缓存"""
        self.learning_cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        self.logger.info("✅ 学习缓存已清空")


# 增强服务单例
_enhanced_service_instance: Optional[UnifiedComplexityModelService] = None


def get_enhanced_complexity_model_service() -> EnhancedUnifiedComplexityModelService:
    """获取增强的统一复杂度判断和模型选择服务实例（单例）"""
    global _enhanced_service_instance
    if _enhanced_service_instance is None:
        _enhanced_service_instance = EnhancedUnifiedComplexityModelService()
    return _enhanced_service_instance  # type: ignore
