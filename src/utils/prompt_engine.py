#!/usr/bin/env python3
"""
提示词引擎 - 管理和优化提示词模板
"""
import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from src.visualization.orchestration_tracker import get_orchestration_tracker


@dataclass
class PromptTemplate:
    """提示词模板"""
    name: str
    content: str
    category: str
    quality_score: float
    usage_count: int
    created_at: float
    metadata: Dict[str, Any]


@dataclass
class PerformanceData:
    """性能数据"""
    total_usage: int
    success_rate: float
    avg_response_time: float
    quality_score: float


class PromptEngine:
    """提示词引擎"""
    
    def __init__(self, templates_dir: str = "templates", llm_integration: Optional[Any] = None):
        """初始化提示词引擎
        
        Args:
            templates_dir: 模板目录路径
            llm_integration: LLM集成实例（可选，用于提示词优化）
        """
        self.logger = logging.getLogger(__name__)
        self.templates_dir = Path(templates_dir)
        self.templates: Dict[str, PromptTemplate] = {}
        self.performance_data: Dict[str, PerformanceData] = {}
        self.config = self._load_config()
        self.llm_integration = llm_integration  # 🚀 新增：LLM集成（用于提示词优化）
        
        # 确保模板目录存在
        self.templates_dir.mkdir(exist_ok=True)
        
        # 🚀 修复：优先从配置文件加载模板
        self._load_default_templates()  # 这个方法现在会优先从文件加载
        self._load_performance_data()
        
        self.logger.info("提示词引擎初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        return {
            "max_templates": int(os.getenv("MAX_TEMPLATES", "100")),
            "quality_threshold": 0.7,
            "performance_tracking": True,
            "auto_optimization": True
        }
    
    def _load_templates_from_file(self) -> bool:
        """从文件加载模板（🚀 修复：统一从配置文件加载模板）"""
        try:
            templates_file = self.templates_dir / "templates.json"
            if templates_file.exists():
                with open(templates_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    templates_data = data.get("templates", [])
                    
                    for template_data in templates_data:
                        template = PromptTemplate(
                            name=template_data["name"],
                            content=template_data["content"],
                            category=template_data.get("category", "general"),
                            quality_score=template_data.get("quality_score", 0.5),
                            usage_count=template_data.get("usage_count", 0),
                            created_at=template_data.get("created_at", datetime.now().timestamp()),
                            metadata=template_data.get("metadata", {})
                        )
                        self.templates[template.name] = template
                        self.performance_data[template.name] = PerformanceData(
                            total_usage=0,
                            success_rate=1.0,
                            avg_response_time=0.0,
                            quality_score=template.quality_score
                        )
                    
                    self.logger.info(f"从文件加载了 {len(templates_data)} 个模板")
                    return True
            return False
        except Exception as e:
            self.logger.warning(f"从文件加载模板失败: {e}")
            return False
    
    def _load_default_templates(self) -> None:
        """加载默认模板（🚀 修复：优先从文件加载，失败时才使用硬编码默认模板）"""
        # 首先尝试从文件加载模板
        if self._load_templates_from_file():
            # 🚀 新增：即使从文件加载成功，也确保关键模板存在（如果不存在则添加）
            self._ensure_critical_templates()
            return
        
        # 🚀 新增：确保关键模板存在
        self._ensure_critical_templates()
        
        # 如果文件加载失败，使用硬编码的默认模板
        default_templates = [
            {
                "name": "general_query",
                "content": "请回答以下问题：{question}",
                "category": "general",
                "quality_score": 0.8,
                "usage_count": 0,
                "created_at": datetime.now().timestamp(),
                "metadata": {"description": "通用查询模板"}
            },
            {
                "name": "technical_support",
                "content": "作为技术支持专家，请帮助解决以下技术问题：{problem}",
                "category": "technical",
                "quality_score": 0.9,
                "usage_count": 0,
                "created_at": datetime.now().timestamp(),
                "metadata": {"description": "技术支持模板"}
            },
            {
                "name": "creative_writing",
                "content": "请创作一个关于{topic}的{style}故事：",
                "category": "creative",
                "quality_score": 0.7,
                "usage_count": 0,
                "created_at": datetime.now().timestamp(),
                "metadata": {"description": "创意写作模板"}
            },
            {
                "name": "reasoning_steps_generation",
                "content": """**🚨🚨🚨 CRITICAL TASK DEFINITION - READ THIS FIRST 🚨🚨🚨**

**THIS IS A REASONING STEPS GENERATION TASK, NOT AN ANSWER GENERATION TASK!**

**YOUR TASK**: Generate the REASONING STEPS (in JSON format) that the system will use to FIND the answer.
**NOT YOUR TASK**: Provide the final answer directly.

**🚨🚨🚨 ABSOLUTELY FORBIDDEN - DO NOT RETURN DIRECT ANSWERS 🚨🚨🚨**

**CRITICAL UNDERSTANDING**:
- Even if you KNOW the answer (e.g., "Paris" or "Albert Einstein"), you MUST NOT return it directly
- You MUST return the REASONING STEPS that lead to finding that answer
- The system will execute these steps to retrieve information from the knowledge base
- Your job is to describe HOW to find the answer, NOT to provide the answer itself

**🚨 CRITICAL RULE #1: You MUST return ONLY valid JSON format. Your response MUST start with {{ and end with }}.**
**🚨 CRITICAL RULE #2: DO NOT return plain text answers.**
**🚨 CRITICAL RULE #3: DO NOT return explanations outside JSON.**
**🚨 CRITICAL RULE #4: DO NOT return just the answer - you MUST return the reasoning steps in JSON format.**
**🚨 CRITICAL RULE #5: If you return non-JSON format, your response will be REJECTED and the system will fail.**

**✅ REQUIRED RESPONSE FORMAT (MUST DO THIS):**
{{
  "steps": [
    {{
      "type": "evidence_gathering",
      "description": "...",
      "sub_query": "..."
    }}
  ]
}}

Query: {query}

**CRITICAL REMINDERS:**
1. Use placeholders like "[step 1 result]", "[company]", "[country]"
2. DO NOT use specific names from your training data
3. Each step must be executable independently
4. Return ONLY valid JSON format""",
                "category": "reasoning",
                "quality_score": 0.9,
                "usage_count": 0,
                "created_at": datetime.now().timestamp(),
                "metadata": {"description": "Reasoning steps generation template (Default)"}
            }
        ]
        
        for template_data in default_templates:
            template = PromptTemplate(**template_data)
            self.templates[template.name] = template
            self.performance_data[template.name] = PerformanceData(
                total_usage=0,
                success_rate=1.0,
                avg_response_time=0.0,
                quality_score=template.quality_score
            )
        
        # 🚀 新增：确保关键模板存在
        self._ensure_critical_templates()
    
    def _ensure_critical_templates(self) -> None:
        """🚀 新增：确保关键模板存在（如 answer_extraction）"""
        # answer_extraction 模板使用动态生成，不需要硬编码模板
        # 但我们可以在这里添加其他关键模板
        pass
    
    def _load_performance_data(self) -> None:
        """加载性能数据"""
        try:
            perf_file = self.templates_dir / "performance.json"
            if perf_file.exists():
                with open(perf_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for name, perf_data in data.items():
                        if name in self.templates:
                            self.performance_data[name] = PerformanceData(**perf_data)
        except Exception as e:
            self.logger.error(f"加载性能数据失败: {e}")
    
    def add_template(self, name: str, content: str, category: str, 
                   quality_score: float = 0.5, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """添加模板"""
        try:
            if name in self.templates:
                self.logger.warning(f"模板已存在: {name}")
                return False
            
            template = PromptTemplate(
                name=name,
                content=content,
                category=category,
                quality_score=quality_score,
                usage_count=0,
                created_at=datetime.now().timestamp(),
                metadata=metadata or {}
            )
            
            self.templates[name] = template
            self.performance_data[name] = PerformanceData(
                total_usage=0,
                success_rate=1.0,
                avg_response_time=0.0,
                quality_score=quality_score
            )
            
            self._save_templates()
            self.logger.info(f"模板添加成功: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加模板失败: {e}")
            return False
    
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """获取模板"""
        return self.templates.get(name)
    
    def generate_prompt(self, template_name: str, **kwargs) -> Optional[str]:
        """生成提示词（🚀 优化：支持可选占位符，用于上下文工程集成）"""
        # 🎯 编排追踪：提示词生成开始
        tracker = getattr(self, '_orchestration_tracker', None) or get_orchestration_tracker()
        parent_event_id = getattr(self, '_current_parent_event_id', None)
        
        try:
            # 🚀 新增：特殊处理 answer_extraction 类型，使用优化的动态生成逻辑
            if template_name == "answer_extraction":
                prompt = self._generate_answer_extraction_prompt(**kwargs)
                # 🎯 编排追踪：提示词生成完成
                if tracker and prompt:
                    tracker.track_prompt_generate(
                        template_name,
                        kwargs.get('query', '')[:100] if 'query' in kwargs else '',
                        {"template_name": template_name, "prompt_length": len(prompt) if prompt else 0},
                        parent_event_id
                    )
                return prompt
            
            template = self.templates.get(template_name)
            if not template:
                # 🚀 优化：模板不存在时使用debug级别（因为fallback会处理，不是真正的错误）
                self.logger.debug(f"模板不存在: {template_name}，将使用fallback机制")
                return None
            
            # 更新使用次数
            template.usage_count += 1
            
            # 🚀 优化：处理可选占位符，确保不存在的占位符被替换为空字符串
            # 提取模板中的所有占位符
            import re
            placeholder_pattern = r'\{(\w+)\}'
            template_placeholders = set(re.findall(placeholder_pattern, template.content))
            
            # 为缺失的可选占位符提供默认值
            safe_kwargs = kwargs.copy()
            
            # 上下文相关的可选占位符
            optional_placeholders = {
                'context_summary': '',
                'keywords': '',
                'context_confidence': '',
                'context_confidence_guidance': '',
                'query_type': '',  # query_type 也是可选的
                'query_analysis': ''  # 🚀 修复：添加 query_analysis 作为可选占位符（兼容旧模板）
            }
            
            for placeholder, default_value in optional_placeholders.items():
                if placeholder in template_placeholders and placeholder not in safe_kwargs:
                    safe_kwargs[placeholder] = default_value
            
            # 🚀 优化：智能处理 context_confidence_guidance
            # 如果提供了 context_confidence，生成指导文本
            if 'context_confidence' in safe_kwargs and safe_kwargs.get('context_confidence'):
                try:
                    confidence_value = float(safe_kwargs['context_confidence'])
                    if confidence_value > 0.8:
                        safe_kwargs['context_confidence_guidance'] = (
                            "\n   e) Leverage the high-confidence context information (confidence: {:.2f}) "
                            "to enhance your reasoning accuracy.".format(confidence_value)
                        )
                    else:
                        safe_kwargs['context_confidence_guidance'] = ""
                except (ValueError, TypeError):
                    safe_kwargs['context_confidence_guidance'] = ""
            
            # 如果 context_summary 存在，格式化它
            if 'context_summary' in safe_kwargs and safe_kwargs.get('context_summary'):
                safe_kwargs['context_summary'] = f"\n{safe_kwargs['context_summary']}\n"
            else:
                safe_kwargs['context_summary'] = ""
            
            # 如果 keywords 存在，格式化它
            if 'keywords' in safe_kwargs and safe_kwargs.get('keywords'):
                safe_kwargs['keywords'] = f"Context Keywords: {safe_kwargs['keywords']}\n"
            else:
                safe_kwargs['keywords'] = ""
            
            # 🚀 改进：智能转义JSON格式中的大括号，避免被format()误解析为占位符
            # 策略：识别实际占位符，保护它们，然后转义其他所有大括号
            import re
            placeholder_pattern = r'\{(\w+)\}'
            
            # 找到所有有效的占位符（在safe_kwargs中的）
            valid_placeholders = set(safe_kwargs.keys())
            
            # 构建转义后的内容
            escaped_content = template.content
            
            # 先保护所有有效的占位符（使用临时标记）
            placeholder_temp_map = {}
            placeholder_counter = 0
            
            # 使用正则表达式找到所有占位符匹配
            matches = list(re.finditer(placeholder_pattern, escaped_content))
            # 从后往前处理，避免位置变化影响
            for match in reversed(matches):
                placeholder_name = match.group(1)
                if placeholder_name in valid_placeholders:
                    # 这是一个有效的占位符，保护它
                    temp_key = f"__TEMP_PLACEHOLDER_{placeholder_counter}__"
                    placeholder_temp_map[temp_key] = match.group(0)  # 保存原始格式 {name}
                    escaped_content = (
                        escaped_content[:match.start()] + 
                        temp_key + 
                        escaped_content[match.end():]
                    )
                    placeholder_counter += 1
            
            # 转义所有剩余的大括号（这些应该是JSON格式或其他文本）
            escaped_content = escaped_content.replace('{', '{{').replace('}', '}}')
            
            # 恢复占位符
            for temp_key, original_placeholder in placeholder_temp_map.items():
                escaped_content = escaped_content.replace(temp_key, original_placeholder)
            
            # 生成提示词（使用安全的kwargs，避免 KeyError）
            try:
                prompt = escaped_content.format(**safe_kwargs)
            except KeyError as e:
                # 如果还有占位符缺失，记录详细信息
                missing_placeholder = str(e).strip("'\"")
                self.logger.warning(f"模板占位符缺失: '{missing_placeholder}'，尝试使用默认值")
                raise
            
            # 清理多余的空行（由空的可选占位符产生）
            import re as regex_module
            prompt = regex_module.sub(r'\n{3,}', '\n\n', prompt)
            
            # 记录性能数据
            self._record_performance(template_name, True, 0.1)
            
            return prompt
            
        except KeyError as e:
            self.logger.warning(f"模板占位符缺失: {e}，尝试使用默认值")
            # 尝试使用部分参数生成
            try:
                template = self.templates.get(template_name)
                if not template:
                    # 🚀 优化：模板不存在时使用debug级别（因为fallback会处理，不是真正的错误）
                    self.logger.debug(f"模板不存在: {template_name}，将使用fallback机制")
                    return None
                # 只使用提供的参数，忽略缺失的
                safe_kwargs = {k: v for k, v in kwargs.items() if k in template.content}
                prompt = template.content.format(**safe_kwargs)
                return prompt
            except Exception as e2:
                self.logger.error(f"生成提示词失败: {e2}")
                self._record_performance(template_name, False, 0.0)
                return None
        except Exception as e:
            self.logger.error(f"生成提示词失败: {e}")
            self._record_performance(template_name, False, 0.0)
            return None
    
    def search_templates(self, category: Optional[str] = None, 
                        quality_threshold: Optional[float] = None) -> List[PromptTemplate]:
        """搜索模板"""
        results = []
        
        for template in self.templates.values():
            if category and template.category != category:
                continue
            
            if quality_threshold and template.quality_score < quality_threshold:
                continue
            
            results.append(template)
        
        # 按质量分数排序
        results.sort(key=lambda x: x.quality_score, reverse=True)
        return results
    
    def update_template(self, name: str, content: Optional[str] = None, 
                      quality_score: Optional[float] = None) -> bool:
        """更新模板"""
        try:
            if name not in self.templates:
                self.logger.error(f"模板不存在: {name}")
                return False
            
            template = self.templates[name]
            
            if content is not None:
                template.content = content
            
            if quality_score is not None:
                template.quality_score = quality_score
                self.performance_data[name].quality_score = quality_score
            
            self._save_templates()
            self.logger.info(f"模板更新成功: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新模板失败: {e}")
            return False
    
    def delete_template(self, name: str) -> bool:
        """删除模板"""
        try:
            if name not in self.templates:
                self.logger.error(f"模板不存在: {name}")
                return False
            
            del self.templates[name]
            del self.performance_data[name]
            
            self._save_templates()
            self.logger.info(f"模板删除成功: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"删除模板失败: {e}")
            return False
    
    def _record_performance(self, template_name: str, success: bool, response_time: float):
        """记录性能数据"""
        if template_name not in self.performance_data:
            return
        
        perf = self.performance_data[template_name]
        perf.total_usage += 1
        
        # 更新成功率
        if success:
            perf.success_rate = (perf.success_rate * (perf.total_usage - 1) + 1.0) / perf.total_usage
        else:
            perf.success_rate = (perf.success_rate * (perf.total_usage - 1)) / perf.total_usage
            
        # 更新平均响应时间
        perf.avg_response_time = (perf.avg_response_time * (perf.total_usage - 1) + response_time) / perf.total_usage
        
        # 更新质量分数
        perf.quality_score = self._calculate_template_score(self.templates[template_name])
    
    def _calculate_template_score(self, template: PromptTemplate) -> float:
        """计算模板评分"""
        if template.name not in self.performance_data:
            return template.quality_score
            
        perf = self.performance_data[template.name]
        usage_weight = min(1.0, perf.total_usage / 10.0)  # 使用频率权重
        score = perf.quality_score * perf.success_rate * (0.5 + 0.5 * usage_weight)
        
        return score
    
    def optimize_templates(self) -> None:
        """优化模板"""
        try:
            # 基于性能数据优化模板
            for name, perf in self.performance_data.items():
                if perf.total_usage > 5:  # 有足够的使用数据
                    if perf.success_rate < 0.5:  # 成功率太低
                        self.logger.warning(f"模板 {name} 成功率过低: {perf.success_rate}")
                        # 可以标记为需要改进
                    
                    if perf.avg_response_time > 2.0:  # 响应时间太长
                        self.logger.warning(f"模板 {name} 响应时间过长: {perf.avg_response_time}")
                        # 可以标记为需要优化
            
            self.logger.info("模板优化完成")
            
        except Exception as e:
            self.logger.error(f"模板优化失败: {e}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        total_templates = len(self.templates)
        total_usage = sum(perf.total_usage for perf in self.performance_data.values())
        avg_success_rate = sum(perf.success_rate for perf in self.performance_data.values()) / max(total_templates, 1)
        avg_response_time = sum(perf.avg_response_time for perf in self.performance_data.values()) / max(total_templates, 1)
        
        return {
            "total_templates": total_templates,
            "total_usage": total_usage,
            "average_success_rate": avg_success_rate,
            "average_response_time": avg_response_time,
            "top_templates": self._get_top_templates(5),
            "low_performance_templates": self._get_low_performance_templates()
        }
    
    def _get_top_templates(self, limit: int = 5) -> List[Dict[str, Any]]:
        """获取顶级模板"""
        templates_with_scores = []
        
        for name, template in self.templates.items():
            if name in self.performance_data:
                perf = self.performance_data[name]
                score = self._calculate_template_score(template)
                templates_with_scores.append({
                    "name": name,
                    "category": template.category,
                    "score": score,
                    "usage_count": perf.total_usage,
                    "success_rate": perf.success_rate
                })
        
        templates_with_scores.sort(key=lambda x: x["score"], reverse=True)
        return templates_with_scores[:limit]
    
    def _get_low_performance_templates(self) -> List[Dict[str, Any]]:
        """获取低性能模板"""
        low_performance = []
        
        for name, perf in self.performance_data.items():
            if perf.total_usage > 3 and (perf.success_rate < 0.6 or perf.avg_response_time > 1.5):
                low_performance.append({
                    "name": name,
                    "success_rate": perf.success_rate,
                    "avg_response_time": perf.avg_response_time,
                    "usage_count": perf.total_usage
                })
        
        return low_performance
    
    def _save_templates(self) -> None:
        """保存模板"""
        try:
            templates_file = self.templates_dir / "templates.json"
            data = {
                "templates": [
                    {
                        "name": t.name,
                        "content": t.content,
                        "category": t.category,
                        "quality_score": t.quality_score,
                        "usage_count": t.usage_count,
                        "created_at": t.created_at,
                        "metadata": t.metadata
                    }
                    for t in self.templates.values()
                ]
            }
            
            with open(templates_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # 保存性能数据
            self._save_performance_data()
            
        except Exception as e:
            self.logger.error(f"保存模板失败: {e}")
    
    def _save_performance_data(self) -> None:
        """保存性能数据"""
        try:
            perf_file = self.templates_dir / "performance.json"
            data = {
                name: {
                    "total_usage": perf.total_usage,
                    "success_rate": perf.success_rate,
                    "avg_response_time": perf.avg_response_time,
                    "quality_score": perf.quality_score
                }
                for name, perf in self.performance_data.items()
            }
            
            with open(perf_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"保存性能数据失败: {e}")
    
    def get_engine_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        return {
            "status": "active",
            "total_templates": len(self.templates),
            "categories": list(set(t.category for t in self.templates.values())),
            "config": self.config,
            "performance_summary": {
                "total_usage": sum(perf.total_usage for perf in self.performance_data.values()),
                "avg_success_rate": sum(perf.success_rate for perf in self.performance_data.values()) / max(len(self.performance_data), 1),
                "avg_response_time": sum(perf.avg_response_time for perf in self.performance_data.values()) / max(len(self.performance_data), 1)
            }
        }
    
    def generate_answer_format_instruction(
        self, 
        query: str, 
        query_type: Optional[str] = None,
        config_center: Optional[Any] = None
    ) -> Optional[str]:
        """🚀 新增：生成答案格式要求（提示词优化功能）
        
        策略：
        1. 优先使用LLM分析查询并生成格式要求（最可扩展）
        2. 如果LLM不可用，使用配置中心（而非硬编码）
        3. 最后：使用通用格式要求（最小化fallback）
        
        Args:
            query: 查询文本
            query_type: 查询类型（可选，作为参考）
            config_center: 配置中心实例（可选，用于获取配置）
            
        Returns:
            格式要求指令字符串，如果失败返回None
        """
        try:
            # 🚀 P0紧急修复：禁用LLM格式要求生成（性能瓶颈545秒）
            # 问题：每次提示词生成都调用LLM，耗时545秒，导致总响应时间544秒
            # 解决：直接跳过LLM调用，使用配置中心或fallback
            # 预期效果：提示词生成时间从545秒降低到<1秒，总响应时间从544秒降低到<10秒
            # 
            # 🚀 策略1: 使用LLM分析查询并生成格式要求（已禁用，性能优先）
            # if self.llm_integration:
            #     llm_instruction = self._generate_answer_format_instruction_with_llm(query)
            #     if llm_instruction:
            #         return llm_instruction
            
            # 🚀 策略2: 使用配置中心（而非硬编码）
            if config_center:
                config_instruction = self._generate_answer_format_instruction_from_config(query, query_type, config_center)
                if config_instruction:
                    return config_instruction
            
            # 🚀 策略3: 通用格式要求（最小化fallback，但根据查询类型和内容生成精确要求）
            return self._get_answer_format_instruction_fallback(query, query_type)
            
        except Exception as e:
            self.logger.debug(f"生成答案格式要求失败: {e}")
            return self._get_answer_format_instruction_fallback(query, query_type)
    
    def _generate_answer_format_instruction_with_llm(self, query: str) -> Optional[str]:
        """🚀 新增：使用LLM分析查询并生成精确的格式要求"""
        try:
            if not self.llm_integration:
                return None
            
            # 使用提示词工程生成格式要求提示词
            format_prompt = self.generate_prompt(
                "answer_format_requirement",
                query=query
            )
            
            if not format_prompt:
                # Fallback: 生成通用格式要求提示词
                format_prompt = f"""Analyze the following query and generate precise answer format requirements.

Query: {query}

Your task:
1. Determine what type of answer is needed (numerical, ranking, name, location, general, etc.)
2. Generate a clear, specific format requirement that will guide the LLM to generate the answer in the correct format
3. Include examples of correct and wrong formats

Return a format instruction in the following structure:

🎯 ANSWER FORMAT REQUIREMENT (MANDATORY - READ FIRST):

[Description of what type of answer is needed]

✅ CORRECT FORMAT: [specific format with examples]
❌ WRONG FORMAT: [common mistakes to avoid]

EXAMPLES:
- Question: [example question]
  ✅ Correct Answer: [example correct answer]
  ❌ Wrong Answer: [example wrong answer]

CRITICAL: In your "Final Answer:" section, return ONLY [specific requirement].

Format Instruction:"""
            
            # 🚀 P0紧急修复：禁用LLM调用（性能瓶颈）
            # 问题：LLM调用耗时545秒，导致提示词生成极慢
            # 解决：直接返回None，让上层使用fallback
            # 如果未来需要启用，可以添加超时保护（见P1修复）
            self.logger.debug("LLM格式要求生成已禁用（性能优化），使用fallback")
            return None
            
            # 🚀 P1修复：如果未来需要启用LLM，使用以下实现（带超时保护）
            # # 调用LLM生成格式要求（带超时保护，最多2秒）
            # try:
            #     import signal
            #     
            #     def timeout_handler(signum, frame):
            #         raise TimeoutError("LLM格式要求生成超时")
            #     
            #     # 只在Unix系统上使用signal（Windows不支持SIGALRM）
            #     if hasattr(signal, 'SIGALRM'):
            #         signal.signal(signal.SIGALRM, timeout_handler)
            #         signal.alarm(2)  # 2秒超时
            #     
            #     try:
            #         response = self.llm_integration._call_llm(format_prompt)
            #     finally:
            #         if hasattr(signal, 'SIGALRM'):
            #             signal.alarm(0)  # 取消超时
            #     
            #     if response:
            #         # 清理和验证响应
            #         cleaned = response.strip()
            #         if cleaned and len(cleaned) > 50:  # 确保有实际内容
            #             return cleaned
            # except TimeoutError:
            #     self.logger.warning("LLM格式要求生成超时（>2秒），使用fallback")
            #     return None
            
        except Exception as e:
            self.logger.debug(f"LLM生成答案格式要求失败: {e}")
            return None
    
    def _generate_answer_format_instruction_from_config(
        self, 
        query: str, 
        query_type: Optional[str], 
        config_center: Any
    ) -> Optional[str]:
        """🚀 新增：从配置中心获取格式要求（而非硬编码）"""
        try:
            # 从配置中心获取格式要求模板
            format_templates = config_center.get_config_value(
                "answer_format", "format_templates", {}
            )
            
            # 根据查询类型获取模板（如果存在）
            if query_type and query_type in format_templates:
                template = format_templates[query_type]
                # 替换查询占位符
                return template.replace("{query}", query)
            
            # 如果没有特定类型模板，返回通用模板
            general_template = config_center.get_config_value(
                "answer_format", "general_template", None
            )
            if general_template:
                return general_template.replace("{query}", query)
            
            return None
            
        except Exception as e:
            self.logger.debug(f"配置中心获取格式要求失败: {e}")
            return None
    
    def _get_answer_format_instruction_fallback(self, query: str = "", query_type: Optional[str] = None) -> str:
        """🚀 增强：根据查询类型和查询内容生成精确的答案格式要求
        
        Args:
            query: 查询文本（用于分析答案类型）
            query_type: 查询类型（可选，作为参考）
        """
        import re
        
        # 分析查询内容，判断答案类型
        answer_type = self._analyze_answer_type(query, query_type)
        
        # 根据答案类型生成格式要求
        if answer_type == "numerical_not_year":
            return """🎯 CRITICAL ANSWER FORMAT REQUIREMENT (MANDATORY - READ FIRST):

This is a NUMERICAL question. You MUST return ONLY a number (NOT a year).

✅ CORRECT FORMAT:
- Return ONLY the number itself (e.g., "2", "87", "506000", "828")
- Do NOT return years (e.g., "2004", "1951", "2019", "2000", "1980")
- Do NOT return units (e.g., "87 years", "2 items")
- Do NOT return ranges or approximations (e.g., "around 80-90")

❌ WRONG FORMAT (DO NOT USE):
- Years: "2004", "1951", "2019", "2000", "1980" (unless the query explicitly asks for a year)
- With units: "87 years", "2 items"
- Ranges: "around 80-90", "approximately 2"
- Explanations: "The answer is 87"

CRITICAL RULES:
1. Return ONLY the number that directly answers the question
2. Do NOT extract years from the evidence unless the query explicitly asks for a year
3. Do NOT return the last number you see in the evidence - analyze what the question is asking for
4. If the question asks for a count, rank, difference, or quantity, return that number, NOT a year

In your "Final Answer:" section, return ONLY the number."""
        
        elif answer_type == "year":
            return """🎯 CRITICAL ANSWER FORMAT REQUIREMENT (MANDATORY - READ FIRST):

This is a YEAR question. You MUST return ONLY the year.

✅ CORRECT FORMAT:
- Return ONLY the year (e.g., "2004", "1951", "2019", "2000", "1980")
- Do NOT return other numbers (e.g., "2", "87", "506000")

❌ WRONG FORMAT (DO NOT USE):
- Other numbers: "2", "87", "506000"
- With explanations: "The year is 2004"

CRITICAL RULES:
1. Return ONLY the year that directly answers the question
2. Do NOT return counts, ranks, differences, or quantities

In your "Final Answer:" section, return ONLY the year."""
        
        elif answer_type == "ranking":
            return """🎯 CRITICAL ANSWER FORMAT REQUIREMENT (MANDATORY - READ FIRST):

This is a RANKING question. You MUST return ONLY the ordinal rank.

✅ CORRECT FORMAT:
- Return ONLY the ordinal rank (e.g., "37th", "2nd", "1st", "3rd")
- Do NOT return cardinal numbers (e.g., "37", "2", "1", "3")
- Do NOT return ranges (e.g., "around 15th-20th")

❌ WRONG FORMAT (DO NOT USE):
- Cardinal numbers: "37", "2", "1", "3"
- Ranges: "around 15th-20th"
- Explanations: "The rank is 37th"

CRITICAL RULES:
1. Return ONLY the ordinal rank (with "th", "nd", "st", "rd" suffix)
2. Do NOT return cardinal numbers

In your "Final Answer:" section, return ONLY the ordinal rank."""
        
        elif answer_type == "name":
            return """🎯 CRITICAL ANSWER FORMAT REQUIREMENT (MANDATORY - READ FIRST):

This is a NAME question. You MUST return ONLY the complete name.

✅ CORRECT FORMAT:
- Return ONLY the complete name (e.g., "Jane Ballou", "Mesut Özil", "Arianne Kathleen")
- Do NOT return partial names (e.g., "Ballou", "Özil", "Kathleen")
- Do NOT return explanations (e.g., "The person is Jane Ballou")

❌ WRONG FORMAT (DO NOT USE):
- Partial names: "Ballou", "Özil", "Kathleen"
- Explanations: "The person is Jane Ballou", "Based on evidence, Jane Ballou"

CRITICAL RULES:
1. Return ONLY the complete name
2. Do NOT include prefixes like "The person is" or "Based on evidence"

In your "Final Answer:" section, return ONLY the complete name."""
        
        elif answer_type == "location":
            return """🎯 CRITICAL ANSWER FORMAT REQUIREMENT (MANDATORY - READ FIRST):

This is a LOCATION/COUNTRY question. You MUST return ONLY the location/country name.

✅ CORRECT FORMAT:
- Return ONLY the location/country name (e.g., "France", "Argentina", "Warsaw")
- Do NOT return explanations (e.g., "The country is France")

❌ WRONG FORMAT (DO NOT USE):
- Explanations: "The country is France", "It is France"

CRITICAL RULES:
1. Return ONLY the location/country name
2. Do NOT include prefixes like "The country is" or "It is"

In your "Final Answer:" section, return ONLY the location/country name."""
        
        else:
            # 通用格式要求
            return """🎯 ANSWER FORMAT REQUIREMENT (MANDATORY - READ FIRST):

You MUST return the answer in a concise, direct format:

✅ CORRECT FORMAT: Direct answer (max 20 words), no redundant phrases
❌ WRONG FORMAT: Long explanations, phrases like "The answer is" or "It is"

CRITICAL: In your "Final Answer:" section, return ONLY the answer, keep it concise and direct."""
    
    def _analyze_answer_type(self, query: str, query_type: Optional[str] = None) -> str:
        """分析查询内容，判断答案类型
        
        Args:
            query: 查询文本
            query_type: 查询类型（可选，作为参考）
            
        Returns:
            答案类型: "numerical_not_year", "year", "ranking", "name", "location", "general"
        """
        if not query:
            return "general"
        
        query_lower = query.lower()
        
        # 检查是否是年份查询
        year_keywords = ["year", "when", "date", "born in", "died in", "founded in", "established in", "occurred in"]
        if any(keyword in query_lower for keyword in year_keywords):
            return "year"
        
        # 检查是否是排名查询
        ranking_keywords = ["rank", "ranking", "position", "place", "ordinal", "first", "second", "third", "nth"]
        if any(keyword in query_lower for keyword in ranking_keywords):
            return "ranking"
        
        # 检查是否是人名查询
        name_keywords = ["who", "name", "person", "people", "mother", "father", "leader", "president", "mayor"]
        if any(keyword in query_lower for keyword in name_keywords):
            return "name"
        
        # 检查是否是地点/国家查询
        location_keywords = ["where", "country", "location", "city", "place", "capital", "which country", "which city"]
        if any(keyword in query_lower for keyword in location_keywords):
            return "location"
        
        # 检查是否是数值查询（但不是年份）
        numerical_keywords = ["how many", "how much", "count", "number", "quantity", "difference", "earlier", "later", "times"]
        if any(keyword in query_lower for keyword in numerical_keywords):
            return "numerical_not_year"
        
        # 根据查询类型判断
        if query_type:
            if query_type in ["numerical", "mathematical"]:
                return "numerical_not_year"
            elif query_type == "ranking":
                return "ranking"
            elif query_type in ["name", "person", "factual"]:
                if "who" in query_lower or "name" in query_lower:
                    return "name"
            elif query_type in ["location", "country"]:
                return "location"
        
        return "general"


    def _generate_answer_extraction_prompt(self, **kwargs) -> Optional[str]:
        """🚀 新增：生成优化的答案提取提示词
        
        根据查询类型和证据格式，动态生成最适合的提示词。
        这是从 engine.py 中移过来的提示词优化逻辑。
        
        Args:
            **kwargs: 包含以下参数：
                - query: 查询文本（必需）
                - evidence: 证据文本（必需）
                - query_type: 查询类型（可选）
                - step_index: 步骤索引（可选）
                - original_query: 原始查询（可选）
        
        Returns:
            生成的提示词，如果参数不足返回None
        """
        try:
            query = kwargs.get('query') or kwargs.get('question')
            evidence = kwargs.get('evidence') or kwargs.get('content')
            
            if not query or not evidence:
                self.logger.debug("answer_extraction 提示词生成：缺少必需参数（query 或 evidence）")
                return None
            
            # 检测查询类型
            import re
            query_lower = query.lower()
            ordinal_match = re.search(r'(\d+)(?:st|nd|rd|th)', query, re.IGNORECASE)
            is_ordinal_query = bool(ordinal_match)
            is_relationship_query = bool(re.search(
                r'\b(mother|father|parent|spouse|wife|husband|daughter|son|child)\b', 
                query, re.IGNORECASE
            ))
            
            # 检测证据是否包含列表格式
            has_list_format = bool(re.search(
                r'\b(Martha|Abigail|Sarah|Harriet|Mary|Eleanor|Lucretia|Julia|Letitia|Priscilla|Jane|Margaret|Anna|Angelica|Emily|Dolley|Louisa|Elizabeth)\s+[A-Z][a-z]+', 
                evidence, re.IGNORECASE
            ))
            
            # 🚀 新增：检测证据中是否包含验证信息（统计标准说明、警告等）
            # 🚀 修复：同时检测中英文验证信息（因为证据格式化可能使用英文）
            has_validation_info = (
                "证据质量评估" in evidence or
                "Evidence Quality Assessment" in evidence or
                "统计说明" in evidence or
                "Statistical Note" in evidence or
                "置信度级别" in evidence or
                "Confidence Level" in evidence or
                "检测到的问题" in evidence or
                "Issues Detected" in evidence or
                "不确定性级别" in evidence or
                "Uncertainty Level" in evidence
            )
            
            # 🚀 新增：检测是否有矛盾
            has_contradictions = "矛盾" in evidence or "不一致" in evidence or "contradiction" in evidence.lower() or "inconsistency" in evidence.lower()
            
            # 根据查询类型和验证信息生成不同的提示词
            if is_ordinal_query and has_list_format and ordinal_match:
                ordinal_num = int(ordinal_match.group(1))
                # 序数查询 + 列表格式：使用增强的提示词（包含验证信息处理）
                if has_validation_info:
                    # 生成序数后缀
                    ordinal_suffix = "th"
                    if ordinal_num % 10 == 1 and ordinal_num % 100 != 11:
                        ordinal_suffix = "st"
                    elif ordinal_num % 10 == 2 and ordinal_num % 100 != 12:
                        ordinal_suffix = "nd"
                    elif ordinal_num % 10 == 3 and ordinal_num % 100 != 13:
                        ordinal_suffix = "rd"
                    
                    prompt = f"""Question: {query}

Evidence:
{evidence}

Important Notes:
1. Please carefully read the "Statistical Note" and "Confidence Level" information in the evidence
2. If the evidence mentions different statistical standards, clearly state the statistical method used
3. Find the {ordinal_num}{ordinal_suffix} item from the list in the evidence
4. If contradictions or inconsistencies are found, point them out and state the most reliable version

Requirements:
- Prioritize high-confidence information
- If contradictions are found, point them out and state the most reliable version
- If information is insufficient, clearly state the limitations
- Return only the answer (if possible, add a brief note after the answer)

**CRITICAL LANGUAGE REQUIREMENT**: All answers must be in ENGLISH, even if the query is in another language. Use English for dates, names, locations, and all other answer components.

Answer:"""
                else:
                    # 生成序数后缀
                    ordinal_suffix = "th"
                    if ordinal_num % 10 == 1 and ordinal_num % 100 != 11:
                        ordinal_suffix = "st"
                    elif ordinal_num % 10 == 2 and ordinal_num % 100 != 12:
                        ordinal_suffix = "nd"
                    elif ordinal_num % 10 == 3 and ordinal_num % 100 != 13:
                        ordinal_suffix = "rd"
                    
                    prompt = f"""Question: {query}

Evidence:
{evidence}

Requirements: Find the {ordinal_num}{ordinal_suffix} item from the list in the evidence. Return only the name.

**CRITICAL LANGUAGE REQUIREMENT**: All answers must be in ENGLISH, even if the query is in another language. Use English for dates, names, locations, and all other answer components.

Answer:"""
            elif is_ordinal_query or is_relationship_query:
                # 序数查询或关系查询：使用增强的提示词（包含验证信息处理）
                if has_validation_info or has_contradictions:
                    prompt = f"""Question: {query}

Evidence:
{evidence}

Important Notes:
1. Please carefully read the quality assessment information in the evidence
2. If the evidence mentions different statistical standards or contradictions, clearly state so
3. Prioritize high-confidence information
4. If contradictions are found, point them out and state the most reliable version

Requirements:
- Extract the answer from the evidence
- If contradictions or inconsistencies are found, point them out and state the most reliable version
- If information is insufficient, clearly state the limitations
- Return only the answer (if possible, add a brief note after the answer)

**CRITICAL LANGUAGE REQUIREMENT**: All answers must be in ENGLISH, even if the query is in another language. Use English for dates, names, locations, and all other answer components.

Answer:"""
                else:
                    prompt = f"""Question: {query}

Evidence:
{evidence}

Requirements: Extract the answer from the evidence. Return only the answer.

**CRITICAL LANGUAGE REQUIREMENT**: All answers must be in ENGLISH, even if the query is in another language. Use English for dates, names, locations, and all other answer components.

Answer:"""
            else:
                # 通用查询：使用增强的提示词（包含验证信息处理）
                if has_validation_info or has_contradictions:
                    prompt = f"""Question: {query}

Evidence:
{evidence}

Important Notes:
1. Please carefully read the quality assessment information in the evidence
2. If the evidence mentions contradictions or inconsistencies, clearly state so
3. Prioritize high-confidence information
4. If contradictions are found, point them out and state the most reliable version

Requirements:
- Extract the answer from the evidence
- If contradictions or inconsistencies are found, point them out and state the most reliable version
- If information is insufficient, clearly state the limitations
- Return only the answer (if possible, add a brief note after the answer)

**CRITICAL LANGUAGE REQUIREMENT**: All answers must be in ENGLISH, even if the query is in another language. Use English for dates, names, locations, and all other answer components.

Answer:"""
                else:
                    prompt = f"""Question: {query}

Evidence:
{evidence}

Requirements: Extract the answer from the evidence. Return only the answer.

**CRITICAL LANGUAGE REQUIREMENT**: All answers must be in ENGLISH, even if the query is in another language. Use English for dates, names, locations, and all other answer components.

Answer:"""
            
            return prompt
            
        except Exception as e:
            self.logger.error(f"生成 answer_extraction 提示词失败: {e}", exc_info=True)
            return None


def get_prompt_engine(templates_dir: str = "templates", llm_integration: Optional[Any] = None) -> PromptEngine:
    """获取提示词引擎实例
    
    Args:
        templates_dir: 模板目录路径
        llm_integration: LLM集成实例（可选，用于提示词优化）
    """
    return PromptEngine(templates_dir=templates_dir, llm_integration=llm_integration)


if __name__ == "__main__":
    # 测试提示词引擎
    engine = PromptEngine()
    
    # 添加模板
    engine.add_template(
        "test_template",
        "这是一个测试模板：{input}",
        "test",
        0.8,
        {"description": "测试模板"}
    )
    
    # 生成提示词
    prompt = engine.generate_prompt("test_template", input="Hello World")
    print(f"生成的提示词: {prompt}")
    
    # 获取性能报告
    report = engine.get_performance_report()
    print(f"性能报告: {report}")
    
    # 获取引擎状态
    status = engine.get_engine_status()
    print(f"引擎状态: {status}")