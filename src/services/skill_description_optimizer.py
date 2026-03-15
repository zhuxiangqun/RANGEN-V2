#!/usr/bin/env python3
"""
技能描述优化引擎
借鉴Anthropic skill-creator的最新改进，自动优化技能描述质量
确保描述包含明确的功能说明和触发条件
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import uuid

logger = logging.getLogger(__name__)


@dataclass
class OptimizationRequirements:
    """优化要求"""
    include_function_purpose: bool = True  # 包含功能用途
    include_trigger_conditions: bool = True  # 包含触发条件
    include_examples: bool = True  # 包含使用示例
    include_input_output: bool = True  # 包含输入输出格式
    include_constraints: bool = True  # 包含限制条件
    max_length: int = 500  # 最大长度
    min_length: int = 50   # 最小长度
    language: str = "zh"   # 语言


@dataclass
class OptimizedDescription:
    """优化后的描述"""
    original: str
    optimized: str
    quality_score: float  # 优化质量评分 (0-1)
    improvements: List[str]  # 具体改进项
    requirements_met: Dict[str, bool]  # 要求满足情况
    optimization_timestamp: datetime = field(default_factory=datetime.now)
    optimizer_version: str = "v1.0"


@dataclass
class ValidationResult:
    """验证结果"""
    passed: bool
    score: float  # 验证评分 (0-1)
    issues: List[Dict[str, Any]]  # 发现问题
    suggestions: List[str]  # 改进建议
    validation_timestamp: datetime = field(default_factory=datetime.now)


class SkillDescriptionOptimizer:
    """技能描述优化引擎"""
    
    def __init__(self, llm_service=None):
        """
        初始化优化引擎
        
        Args:
            llm_service: 可选的LLM服务（如果可用）
        """
        self.llm_service = llm_service
        self.logger = logging.getLogger(f"{__name__}.SkillDescriptionOptimizer")
        
        # 关键短语模板
        self.key_phrases = {
            "function_purpose": [
                "用于", "功能是", "作用是", "可以", "能够",
                "used for", "function is", "can", "able to"
            ],
            "trigger_conditions": [
                "当", "如果", "在...时", "当用户", "触发条件", "适用场景",
                "when", "if", "triggered when", "scenario"
            ],
            "input_format": [
                "输入", "参数", "接收", "需要",
                "input", "parameter", "receives", "requires"
            ],
            "output_format": [
                "输出", "返回", "结果", "生成",
                "output", "returns", "result", "generates"
            ],
            "constraints": [
                "限制", "要求", "前提", "注意", "不能", "必须",
                "limitation", "requirement", "constraint", "note"
            ]
        }
    
    async def optimize_description(self, 
                                 original_description: str,
                                 skill_name: str,
                                 skill_category: str,
                                 requirements: Optional[OptimizationRequirements] = None) -> OptimizedDescription:
        """优化技能描述"""
        if requirements is None:
            requirements = OptimizationRequirements()
        
        optimization_id = f"opt_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        
        self.logger.info(f"🔄 开始优化技能描述: {skill_name}")
        self.logger.info(f"  优化ID: {optimization_id}")
        self.logger.info(f"  原始描述长度: {len(original_description)}字符")
        
        try:
            # 1. 分析原始描述
            analysis_result = await self._analyze_description(original_description, requirements)
            
            # 2. 生成优化建议
            suggestions = await self._generate_suggestions(analysis_result, requirements)
            
            # 3. 应用优化
            if self.llm_service and self._should_use_llm(original_description, analysis_result):
                optimized = await self._optimize_with_llm(
                    original_description, skill_name, skill_category, suggestions, requirements
                )
            else:
                optimized = await self._optimize_with_rules(
                    original_description, suggestions, requirements
                )
            
            # 4. 验证优化结果
            validation_result = await self._validate_optimized_description(
                optimized, original_description, requirements
            )
            
            # 5. 计算质量评分
            quality_score = self._calculate_quality_score(analysis_result, validation_result)
            
            # 6. 检查要求满足情况
            requirements_met = await self._check_requirements_met(optimized, requirements)
            
            result = OptimizedDescription(
                original=original_description,
                optimized=optimized,
                quality_score=quality_score,
                improvements=suggestions,
                requirements_met=requirements_met
            )
            
            self.logger.info(f"✅ 技能描述优化完成: {skill_name}")
            self.logger.info(f"  优化质量评分: {quality_score:.2f}")
            self.logger.info(f"  优化后长度: {len(optimized)}字符")
            self.logger.info(f"  改进项: {len(suggestions)}个")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 技能描述优化失败 {skill_name}: {e}", exc_info=True)
            # 返回原始描述作为兜底
            return OptimizedDescription(
                original=original_description,
                optimized=original_description,
                quality_score=0.3,
                improvements=[f"优化过程出错: {e}"],
                requirements_met={key: False for key in requirements.__dict__.keys()}
            )
    
    async def _analyze_description(self, description: str, 
                                 requirements: OptimizationRequirements) -> Dict[str, Any]:
        """分析描述质量"""
        analysis = {
            "length": len(description),
            "has_function_purpose": False,
            "has_trigger_conditions": False,
            "has_examples": False,
            "has_input_output": False,
            "has_constraints": False,
            "readability_score": 0.0,
            "keyword_coverage": {}
        }
        
        # 检查长度
        if analysis["length"] >= requirements.min_length:
            analysis["readability_score"] += 0.2
        if analysis["length"] <= requirements.max_length:
            analysis["readability_score"] += 0.1
        
        # 检查关键短语
        for key, phrases in self.key_phrases.items():
            phrase_count = 0
            for phrase in phrases:
                if phrase in description.lower():
                    phrase_count += 1
            
            coverage = min(phrase_count / max(len(phrases), 1), 1.0)
            analysis["keyword_coverage"][key] = coverage
            
            # 设置对应标志
            if coverage > 0.3:  # 至少30%的关键词被覆盖
                if key == "function_purpose":
                    analysis["has_function_purpose"] = True
                elif key == "trigger_conditions":
                    analysis["has_trigger_conditions"] = True
                elif key == "input_format" or key == "output_format":
                    analysis["has_input_output"] = True
                elif key == "constraints":
                    analysis["has_constraints"] = True
        
        # 检查示例（简单启发式）
        example_patterns = ["例如", "例子", "示例", "比如", "example", "e.g.", "for example"]
        if any(pattern in description for pattern in example_patterns):
            analysis["has_examples"] = True
        
        # 计算可读性评分
        sentence_count = len(re.split(r'[.!?。！？]', description))
        if sentence_count > 0:
            avg_sentence_length = analysis["length"] / sentence_count
            if 15 <= avg_sentence_length <= 30:
                analysis["readability_score"] += 0.3
            elif avg_sentence_length < 50:
                analysis["readability_score"] += 0.1
        
        return analysis
    
    async def _generate_suggestions(self, analysis: Dict[str, Any],
                                  requirements: OptimizationRequirements) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        # 基于要求的建议
        if requirements.include_function_purpose and not analysis["has_function_purpose"]:
            suggestions.append("添加明确的功能用途说明")
        
        if requirements.include_trigger_conditions and not analysis["has_trigger_conditions"]:
            suggestions.append("添加触发条件说明（何时使用该技能）")
        
        if requirements.include_examples and not analysis["has_examples"]:
            suggestions.append("添加使用示例")
        
        if requirements.include_input_output and not analysis["has_input_output"]:
            suggestions.append("明确输入输出格式")
        
        if requirements.include_constraints and not analysis["has_constraints"]:
            suggestions.append("添加限制条件和注意事项")
        
        # 基于分析的建议
        if analysis["length"] < requirements.min_length:
            suggestions.append(f"描述过短（{analysis['length']}字符），建议扩展到至少{requirements.min_length}字符")
        
        if analysis["length"] > requirements.max_length:
            suggestions.append(f"描述过长（{analysis['length']}字符），建议精简到最多{requirements.max_length}字符")
        
        if analysis["readability_score"] < 0.5:
            suggestions.append("提高描述可读性，使用更清晰的句子结构")
        
        # 关键词覆盖建议
        for key, coverage in analysis["keyword_coverage"].items():
            if coverage < 0.3:
                key_name = {
                    "function_purpose": "功能用途",
                    "trigger_conditions": "触发条件",
                    "input_format": "输入格式",
                    "output_format": "输出格式",
                    "constraints": "限制条件"
                }.get(key, key)
                suggestions.append(f"增加关于'{key_name}'的描述")
        
        return list(set(suggestions))  # 去重
    
    def _should_use_llm(self, description: str, analysis: Dict[str, Any]) -> bool:
        """判断是否使用LLM进行优化"""
        if not self.llm_service:
            return False
        
        # 如果描述质量很差，使用LLM
        if analysis["readability_score"] < 0.3:
            return True
        
        # 如果缺少多个关键要素，使用LLM
        missing_count = sum([
            1 for key in ["has_function_purpose", "has_trigger_conditions", 
                         "has_examples", "has_input_output", "has_constraints"]
            if not analysis.get(key, False)
        ])
        
        return missing_count >= 3
    
    async def _optimize_with_llm(self, original: str, skill_name: str, skill_category: str,
                               suggestions: List[str], requirements: OptimizationRequirements) -> str:
        """使用LLM优化描述"""
        self.logger.info("使用LLM优化技能描述")
        
        # 安全检查
        if not self.llm_service:
            self.logger.warning("LLM服务不可用，回退到规则优化")
            return await self._optimize_with_rules(original, suggestions, requirements)
        
        prompt = self._build_llm_prompt(original, skill_name, skill_category, suggestions, requirements)
        
        try:
            # 添加超时保护，避免无限等待
            optimized = await asyncio.wait_for(
                self.llm_service.generate_text(prompt),
                timeout=30.0  # 30秒超时
            )
            
            # 清理LLM输出
            optimized = self._clean_llm_output(optimized)
            
            return optimized
            
        except asyncio.TimeoutError:
            self.logger.warning("LLM优化超时，回退到规则优化")
            return await self._optimize_with_rules(original, suggestions, requirements)
        except Exception as e:
            self.logger.warning(f"LLM优化失败，回退到规则优化: {e}")
            return await self._optimize_with_rules(original, suggestions, requirements)
    
    def _build_llm_prompt(self, original: str, skill_name: str, skill_category: str,
                         suggestions: List[str], requirements: OptimizationRequirements) -> str:
        """构建LLM提示"""
        language_instructions = {
            "zh": "请使用中文回答",
            "en": "Please respond in English"
        }.get(requirements.language, "请使用中文回答")
        
        prompt = f"""{language_instructions}

请优化以下AI技能的描述：

技能名称：{skill_name}
技能分类：{skill_category}
原始描述：{original}

优化要求：
1. 保持原意不变
2. 语言清晰简洁
3. 长度控制在{requirements.min_length}-{requirements.max_length}字符之间
4. 必须包含以下要素：
"""

        if requirements.include_function_purpose:
            prompt += "   - 明确的功能用途说明（做什么）\n"
        if requirements.include_trigger_conditions:
            prompt += "   - 明确的触发条件（何时使用）\n"
        if requirements.include_examples:
            prompt += "   - 至少一个使用示例\n"
        if requirements.include_input_output:
            prompt += "   - 输入输出格式说明\n"
        if requirements.include_constraints:
            prompt += "   - 限制条件和注意事项\n"
        
        if suggestions:
            prompt += f"\n具体改进建议：\n" + "\n".join([f"- {s}" for s in suggestions])
        
        prompt += f"\n请直接输出优化后的描述，不要添加任何额外解释。"
        
        return prompt
    
    def _clean_llm_output(self, text: str) -> str:
        """清理LLM输出"""
        # 移除常见的LLM前缀
        prefixes = ["优化后的描述：", "描述：", "```", "```markdown", "```text"]
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):].lstrip()
        
        # 移除代码块标记
        text = text.replace("```", "")
        
        # 移除多余空白
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
        
        return text
    
    async def _optimize_with_rules(self, original: str, 
                                 suggestions: List[str],
                                 requirements: OptimizationRequirements) -> str:
        """使用规则优化描述"""
        self.logger.info("使用规则优化技能描述")
        
        optimized = original
        
        # 应用基于建议的规则优化
        for suggestion in suggestions:
            if "添加明确的功能用途说明" in suggestion and "功能是" not in optimized.lower():
                optimized = self._add_function_purpose(optimized)
            elif "添加触发条件说明" in suggestion and "当" not in optimized and "if" not in optimized.lower():
                optimized = self._add_trigger_conditions(optimized)
            elif "添加使用示例" in suggestion and "例如" not in optimized and "example" not in optimized.lower():
                optimized = self._add_example(optimized)
            elif "明确输入输出格式" in suggestion:
                optimized = self._add_input_output(optimized)
            elif "添加限制条件和注意事项" in suggestion:
                optimized = self._add_constraints(optimized)
        
        # 长度调整
        if len(optimized) < requirements.min_length:
            optimized = self._expand_description(optimized, requirements.min_length)
        elif len(optimized) > requirements.max_length:
            optimized = self._shorten_description(optimized, requirements.max_length)
        
        return optimized
    
    def _add_function_purpose(self, description: str) -> str:
        """添加功能用途说明"""
        if len(description) > 0:
            return f"{description}。该技能用于..."
        return "该技能用于..."
    
    def _add_trigger_conditions(self, description: str) -> str:
        """添加触发条件说明"""
        if len(description) > 0:
            return f"{description}。当用户需要...时，可以触发此技能。"
        return "当用户需要...时，可以触发此技能。"
    
    def _add_example(self, description: str) -> str:
        """添加使用示例"""
        if len(description) > 0:
            return f"{description}。例如：..."
        return "例如：..."
    
    def _add_input_output(self, description: str) -> str:
        """添加输入输出格式"""
        if len(description) > 0:
            return f"{description}。输入格式：...，输出格式：..."
        return "输入格式：...，输出格式：..."
    
    def _add_constraints(self, description: str) -> str:
        """添加限制条件"""
        if len(description) > 0:
            return f"{description}。注意：..."
        return "注意：..."
    
    def _expand_description(self, description: str, min_length: int) -> str:
        """扩展描述"""
        if len(description) >= min_length:
            return description
        
        # 添加通用补充
        additions = [
            "该技能设计用于提高工作效率。",
            "使用时请确保输入数据格式正确。",
            "输出结果可能需要进一步验证。",
            "如有问题请参考相关文档。"
        ]
        
        expanded = description
        for addition in additions:
            if len(expanded) < min_length:
                expanded += " " + addition
        
        return expanded
    
    def _shorten_description(self, description: str, max_length: int) -> str:
        """缩短描述"""
        if len(description) <= max_length:
            return description
        
        # 简单截断并添加省略号
        shortened = description[:max_length-3] + "..."
        
        # 确保截断在句子边界
        last_period = shortened.rfind('.')
        last_exclamation = shortened.rfind('!')
        last_question = shortened.rfind('?')
        
        cutoff = max(last_period, last_exclamation, last_question)
        if cutoff > max_length * 0.7:  # 确保保留大部分内容
            shortened = shortened[:cutoff+1]
        
        return shortened
    
    async def _validate_optimized_description(self, optimized: str, 
                                            original: str,
                                            requirements: OptimizationRequirements) -> ValidationResult:
        """验证优化后的描述"""
        issues = []
        suggestions = []
        score = 0.7  # 基础分
        
        # 检查长度
        if len(optimized) < requirements.min_length:
            issues.append({
                "type": "too_short",
                "severity": "medium",
                "description": f"描述过短 ({len(optimized)}字符，要求至少{requirements.min_length}字符)"
            })
            score -= 0.2
        
        if len(optimized) > requirements.max_length:
            issues.append({
                "type": "too_long",
                "severity": "low",
                "description": f"描述过长 ({len(optimized)}字符，要求最多{requirements.max_length}字符)"
            })
            score -= 0.1
        
        # 检查内容保留
        original_keywords = set(re.findall(r'\b\w{4,}\b', original.lower()))
        optimized_keywords = set(re.findall(r'\b\w{4,}\b', optimized.lower()))
        
        if original_keywords:
            retention_rate = len(original_keywords.intersection(optimized_keywords)) / len(original_keywords)
            if retention_rate < 0.7:
                issues.append({
                    "type": "low_retention",
                    "severity": "medium",
                    "description": f"关键词保留率较低 ({retention_rate:.1%})"
                })
                score -= 0.1
                suggestions.append("保留更多原始描述中的关键词")
        
        # 检查可读性
        sentence_count = len(re.split(r'[.!?。！？]', optimized))
        if sentence_count > 0:
            avg_length = len(optimized) / sentence_count
            if avg_length > 50:
                issues.append({
                    "type": "long_sentences",
                    "severity": "low",
                    "description": f"句子平均长度过长 ({avg_length:.1f}字符)"
                })
                suggestions.append("使用更短的句子提高可读性")
        
        # 最终评分调整
        score = max(0.0, min(1.0, score))
        
        return ValidationResult(
            passed=score >= 0.6,
            score=score,
            issues=issues,
            suggestions=suggestions
        )
    
    def _calculate_quality_score(self, analysis: Dict[str, Any],
                               validation_result: ValidationResult) -> float:
        """计算优化质量评分"""
        # 基础分来自验证结果
        base_score = validation_result.score
        
        # 分析结果加成
        analysis_bonus = 0.0
        
        if analysis.get("has_function_purpose", False):
            analysis_bonus += 0.1
        if analysis.get("has_trigger_conditions", False):
            analysis_bonus += 0.15  # 触发条件很重要
        if analysis.get("has_examples", False):
            analysis_bonus += 0.1
        if analysis.get("has_input_output", False):
            analysis_bonus += 0.1
        if analysis.get("has_constraints", False):
            analysis_bonus += 0.05
        
        # 可读性加成
        readability = analysis.get("readability_score", 0.0)
        analysis_bonus += readability * 0.1
        
        final_score = base_score + analysis_bonus
        return min(final_score, 1.0)
    
    async def _check_requirements_met(self, optimized: str,
                                    requirements: OptimizationRequirements) -> Dict[str, bool]:
        """检查要求满足情况"""
        met = {}
        
        # 重新分析优化后的描述
        analysis = await self._analyze_description(optimized, requirements)
        
        met["include_function_purpose"] = analysis["has_function_purpose"]
        met["include_trigger_conditions"] = analysis["has_trigger_conditions"]
        met["include_examples"] = analysis["has_examples"]
        met["include_input_output"] = analysis["has_input_output"]
        met["include_constraints"] = analysis["has_constraints"]
        met["length_within_range"] = (
            requirements.min_length <= len(optimized) <= requirements.max_length
        )
        
        return met
    
    async def optimize_multiple_descriptions(self,
                                           descriptions: List[Tuple[str, str, str]],
                                           requirements: Optional[OptimizationRequirements] = None
                                           ) -> Dict[str, OptimizedDescription]:
        """批量优化多个技能描述"""
        results = {}
        
        self.logger.info(f"开始批量优化 {len(descriptions)} 个技能描述")
        
        for original, skill_name, skill_category in descriptions:
            try:
                result = await self.optimize_description(
                    original, skill_name, skill_category, requirements
                )
                results[skill_name] = result
            except Exception as e:
                self.logger.error(f"批量优化失败 {skill_name}: {e}")
                # 添加错误结果
                results[skill_name] = OptimizedDescription(
                    original=original,
                    optimized=original,
                    quality_score=0.0,
                    improvements=[f"优化失败: {e}"],
                    requirements_met={}
                )
        
        self.logger.info(f"批量优化完成: {len(results)}/{len(descriptions)} 个技能成功")
        
        return results


# 模拟LLM服务（用于测试）
class MockLLMService:
    """模拟LLM服务"""
    
    async def generate_text(self, prompt: str) -> str:
        """生成文本"""
        # 简单模拟，实际应该调用真正的LLM
        await asyncio.sleep(0.1)
        
        # 提取技能名称（简单解析）
        import re
        name_match = re.search(r'技能名称：(.+?)\n', prompt)
        skill_name = name_match.group(1) if name_match else "某技能"
        
        return f"""优化后的描述：{skill_name}用于处理各种任务，提高工作效率。当用户需要快速解决问题时，可以触发此技能。

例如：输入一个问题描述，技能会分析问题并提供解决方案。

输入格式：文本格式的问题描述
输出格式：包含解决方案的JSON格式响应

注意：该技能适用于一般性问题，对于专业领域问题可能需要进一步验证。"""


async def main():
    """主函数 - 测试技能描述优化引擎"""
    import sys
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建优化器（使用模拟LLM服务）
    llm_service = MockLLMService()
    optimizer = SkillDescriptionOptimizer(llm_service=llm_service)
    
    # 测试技能
    test_skills = [
        (
            "数据分析工具",
            "数据分析工具",
            "data_analysis",
            "分析数据"
        ),
        (
            "代码审查助手",
            "代码审查助手", 
            "code_review",
            "检查代码质量，找出潜在问题"
        ),
        (
            "文档生成器",
            "文档生成器",
            "documentation",
            "根据代码生成文档，支持多种格式"
        )
    ]
    
    print("🚀 开始技能描述优化测试...")
    
    for original, name, category, description in test_skills:
        print(f"\n{'='*60}")
        print(f"优化技能: {name}")
        print(f"{'='*60}")
        
        # 执行优化
        result = await optimizer.optimize_description(
            description, name, category
        )
        
        # 打印结果
        print(f"📝 原始描述: {result.original}")
        print(f"✨ 优化后描述: {result.optimized}")
        print(f"📊 优化质量评分: {result.quality_score:.2f}")
        print(f"📈 改进项: {len(result.improvements)}个")
        
        for i, improvement in enumerate(result.improvements, 1):
            print(f"  {i}. {improvement}")
        
        print(f"✅ 要求满足情况:")
        for req, met in result.requirements_met.items():
            status = "✓" if met else "✗"
            print(f"  {status} {req}")
    
    print(f"\n{'='*60}")
    print("✅ 技能描述优化测试完成")
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))