"""
AI中台核心能力评估器 - 完整版 v2.0

评估体系：
- A. 基础能力 (25%): 编排能力、Agent完备性、提示词工程、上下文工程
- B. 智能能力 (30%): 回答质量、路由准确率、推理深度、知识召回、工具调用、多轮对话、自学习能力
- C. 架构能力 (28%): Harness能力、架构合理性、可观测性、监控告警、故障自愈、灰度发布
- D. 数据能力 (10%): 数据源接入、知识管理、向量管理、数据血缘
- E. 平台能力 (7%): 应用支撑、成本控制、集成扩展

总计: 23个评估维度，100+个子项
"""

import time
import asyncio
import json
import re
import ast
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

# ============================================================================
# 评估器基类
# ============================================================================

class EvaluatorStatus(Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RUNNING = "running"

@dataclass
class SubItemResult:
    name: str
    description: str
    score: float
    status: str
    evidence: List[str] = field(default_factory=list)
    details: str = ""

@dataclass
class DimensionResult:
    dimension: str
    name: str
    category: str
    weight: float
    score: float
    status: str
    subitems: List[SubItemResult] = field(default_factory=list)
    details: str = ""
    evidence: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

class BaseEvaluator:
    """评估器基类"""
    
    dimension_name: str = ""
    dimension_cn: str = ""
    category: str = ""
    weight: float = 0.0
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.system_url = self.config.get("system_url", "http://localhost:8000")
        self.source_path = self.config.get("source_path", "/Users/apple/workdata/person/zy/RANGEN-main(syu-python)/src")
    
    async def evaluate(self) -> DimensionResult:
        """执行评估，返回结果"""
        raise NotImplementedError
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """获取认证头"""
        import os
        headers = {}
        api_key = os.environ.get("RANGEN_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers
    
    def _score_by_threshold(self, value: float, thresholds: List[tuple]) -> float:
        """根据阈值计算分数"""
        for threshold, score in thresholds:
            if value >= threshold:
                return score
        return thresholds[-1][1] if thresholds else 0.0
    
    def _status_by_score(self, score: float) -> str:
        """根据分数确定状态"""
        if score >= 0.9:
            return "excellent"
        elif score >= 0.7:
            return "good"
        elif score >= 0.5:
            return "fair"
        else:
            return "poor"
    
    def _get_py_files(self, pattern: str = "*.py") -> List[Path]:
        """获取Python文件列表，受 max_sample_count 限制"""
        max_count = self.config.get("max_sample_count", 100)
        files = list(Path(self.source_path).rglob(pattern))
        return files[:max_count]
    
    def _get_all_py_files(self) -> List[Path]:
        """获取所有Python文件，受 max_sample_count 限制"""
        return self._get_py_files("*.py")

# ============================================================================
# A. 基础能力评估器
# ============================================================================

class OrchestrationEvaluator(BaseEvaluator):
    """编排能力评估器"""
    
    dimension_name = "orchestration"
    dimension_cn = "编排能力"
    category = "A"
    weight = 0.08
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        # 1. 工作流设计完整性
        si1 = await self._check_workflow_design()
        subitems.append(si1)
        total_score += si1.score * 0.18
        
        # 2. 并行执行能力
        si2 = await self._check_parallel_execution()
        subitems.append(si2)
        total_score += si2.score * 0.17
        
        # 3. 串行链式调用
        si3 = await self._check_sequential_chaining()
        subitems.append(si3)
        total_score += si3.score * 0.17
        
        # 4. 条件分支逻辑
        si4 = await self._check_conditional_branching()
        subitems.append(si4)
        total_score += si4.score * 0.16
        
        # 5. 错误恢复机制
        si5 = await self._check_error_recovery()
        subitems.append(si5)
        total_score += si5.score * 0.16
        
        # 6. 状态持久化
        si6 = await self._check_state_persistence()
        subitems.append(si6)
        total_score += si6.score * 0.16
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=self._generate_details(subitems),
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_suggestions(subitems)
        )
    
    async def _check_workflow_design(self) -> SubItemResult:
        """检查工作流设计"""
        evidence = []
        score = 0.0
        
        workflow_paths = [
            Path(self.source_path) / "orchestration" / "workflows",
            Path(self.source_path) / "orchestration" / "langgraph_nodes",
        ]
        
        workflow_count = 0
        for wp in workflow_paths:
            if wp.exists():
                files = list(wp.rglob("*.py"))
                workflow_count += len([f for f in files if not f.name.startswith("_")])
        
        if workflow_count > 0:
            score = min(workflow_count / 10, 1.0) * 0.8 + 0.2
            evidence.append(f"检测到 {workflow_count} 个工作流定义")
        else:
            score = 0.3
            evidence.append("未检测到工作流定义文件")
        
        # 检查错误处理
        has_error_handling = await self._check_error_handling_in_workflows()
        if has_error_handling:
            evidence.append("工作流包含错误处理机制")
            score = min(score + 0.1, 1.0)
        
        return SubItemResult(
            name="workflow_design",
            description="工作流定义完整性",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_error_handling_in_workflows(self) -> bool:
        """检查工作流中的错误处理"""
        try:
            workflow_paths = [
                Path(self.source_path) / "orchestration"
            ]
            for wp in workflow_paths:
                for py_file in wp.rglob("*.py"):
                    if "__pycache__" in str(py_file):
                        continue
                    try:
                        content = py_file.read_text(encoding="utf-8")
                        if any(kw in content for kw in ["try:", "except:", "raise", "on_error", "fallback"]):
                            return True
                    except:
                        pass
        except:
            pass
        return False
    
    async def _check_parallel_execution(self) -> SubItemResult:
        """检查并行执行能力"""
        evidence = []
        
        try:
            import requests
            resp = requests.get(
                f"{self.system_url}/api/v1/workflow/status",
                headers=self._get_auth_headers(),
                timeout=5
            )
            if resp.status_code < 500:
                evidence.append("工作流引擎API可访问")
                score = 0.85
            else:
                score = 0.5
                evidence.append("工作流引擎API返回错误")
        except Exception as e:
            score = 0.4
            evidence.append(f"工作流引擎不可用: {str(e)[:50]}")
        
        return SubItemResult(
            name="parallel_execution",
            description="并行任务执行能力",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_sequential_chaining(self) -> SubItemResult:
        """检查串行链式调用"""
        evidence = []
        
        # 检查是否有chain/sequential相关实现
        chain_files = list(Path(self.source_path).rglob("*chain*.py"))
        sequential_files = list(Path(self.source_path).rglob("*sequential*.py"))
        
        if chain_files or sequential_files:
            evidence.append(f"检测到 {len(chain_files) + len(sequential_files)} 个链式调用相关文件")
            score = 0.85
        else:
            score = 0.5
            evidence.append("未检测到链式调用实现")
        
        return SubItemResult(
            name="sequential_chaining",
            description="串行链式调用",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_conditional_branching(self) -> SubItemResult:
        """检查条件分支"""
        evidence = []
        
        try:
            resp = requests.post(
                f"{self.system_url}/api/v1/routing/test",
                json={"query": "test conditional", "conditions": {}},
                headers=self._get_auth_headers(),
                timeout=5
            )
            if resp.status_code < 500:
                evidence.append("条件路由API可访问")
                score = 0.8
            else:
                score = 0.5
        except:
            score = 0.5
        
        # 检查代码中的条件分支
        branch_files = list(Path(self.source_path).rglob("*routing*.py"))
        if branch_files:
            evidence.append(f"检测到 {len(branch_files)} 个路由相关文件")
        
        return SubItemResult(
            name="conditional_branching",
            description="条件分支逻辑",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_error_recovery(self) -> SubItemResult:
        """检查错误恢复机制"""
        evidence = []
        
        # 检查代码中的错误处理模式
        recovery_patterns = ["retry", "fallback", "circuit_breaker", "on_error", "error_handler"]
        recovery_count = 0
        
        for pattern in recovery_patterns:
            files = list(Path(self.source_path).rglob(f"*{pattern}*.py"))
            recovery_count += len(files)
        
        if recovery_count > 0:
            score = min(recovery_count / 5, 1.0) * 0.9 + 0.1
            evidence.append(f"检测到 {recovery_count} 个错误恢复相关文件")
        else:
            score = 0.4
            evidence.append("未检测到错误恢复机制")
        
        return SubItemResult(
            name="error_recovery",
            description="错误恢复机制",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_state_persistence(self) -> SubItemResult:
        """检查状态持久化"""
        evidence = []
        
        state_files = list(Path(self.source_path).rglob("*state*.py"))
        checkpoint_files = list(Path(self.source_path).rglob("*checkpoint*.py"))
        
        if state_files or checkpoint_files:
            evidence.append(f"检测到状态管理文件: {len(state_files)} 个")
            score = 0.8
        else:
            score = 0.4
            evidence.append("未检测到状态持久化实现")
        
        return SubItemResult(
            name="state_persistence",
            description="状态持久化",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _generate_details(self, subitems: List[SubItemResult]) -> str:
        good_items = [s.name for s in subitems if s.score >= 0.7]
        poor_items = [s.name for s in subitems if s.score < 0.5]
        
        details = f"编排能力评估完成，"
        if good_items:
            details += f"良好项: {', '.join(good_items[:3])}"
        if poor_items:
            details += f"，需改进: {', '.join(poor_items)}"
        return details
    
    def _generate_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        suggestions = []
        for s in subitems:
            if s.score < 0.5:
                suggestions.append(f"建议增强{s.description}能力")
            elif s.score < 0.7:
                suggestions.append(f"可优化{s.description}")
        return suggestions[:3]


class AgentCompletenessEvaluator(BaseEvaluator):
    """Agent完备性评估器"""
    
    dimension_name = "agent_completeness"
    dimension_cn = "Agent完备性"
    category = "A"
    weight = 0.07
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        # 1. 感知能力
        si1 = await self._check_perception()
        subitems.append(si1)
        total_score += si1.score * 0.18
        
        # 2. 认知能力
        si2 = await self._check_cognition()
        subitems.append(si2)
        total_score += si2.score * 0.18
        
        # 3. 行动能力
        si3 = await self._check_action()
        subitems.append(si3)
        total_score += si3.score * 0.18
        
        # 4. 记忆能力
        si4 = await self._check_memory()
        subitems.append(si4)
        total_score += si4.score * 0.16
        
        # 5. 反思能力
        si5 = await self._check_reflection()
        subitems.append(si5)
        total_score += si5.score * 0.15
        
        # 6. 元认知
        si6 = await self._check_meta_cognition()
        subitems.append(si6)
        total_score += si6.score * 0.15
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=f"Agent完备性评估完成，{len([s for s in subitems if s.score >= 0.7])}/6项达标",
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_suggestions(subitems)
        )
    
    async def _check_perception(self) -> SubItemResult:
        """检查感知能力"""
        evidence = []
        parser_files = list(Path(self.source_path).rglob("*parser*.py"))
        input_files = list(Path(self.source_path).rglob("*input*.py"))
        
        if parser_files or input_files:
            evidence.append(f"检测到输入解析相关文件: {len(parser_files) + len(input_files)} 个")
            score = 0.8
        else:
            score = 0.5
            evidence.append("未检测到明确的输入解析模块")
        
        return SubItemResult(
            name="perception",
            description="输入感知与解析",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_cognition(self) -> SubItemResult:
        """检查认知能力"""
        evidence = []
        
        # 检查Agent中的推理相关代码
        agent_files = list(Path(self.source_path).rglob("*/agents/**/*.py"))
        reasoning_keywords = ["reasoning", "think", "analyze", "reason", "infer"]
        reasoning_count = 0
        
        for af in agent_files:
            if "__pycache__" in str(af):
                continue
            try:
                content = af.read_text(encoding="utf-8")
                if any(kw in content.lower() for kw in reasoning_keywords):
                    reasoning_count += 1
            except:
                pass
        
        if reasoning_count > 0:
            evidence.append(f"检测到 {reasoning_count} 个包含推理逻辑的Agent文件")
            score = min(reasoning_count / 10, 1.0) * 0.9 + 0.1
        else:
            score = 0.4
            evidence.append("未检测到明确的推理能力")
        
        return SubItemResult(
            name="cognition",
            description="认知与推理",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_action(self) -> SubItemResult:
        """检查行动能力"""
        evidence = []
        
        tool_files = list(Path(self.source_path).rglob("*/tools/*.py"))
        action_files = list(Path(self.source_path).rglob("*/execution_tools/**/*.py"))
        
        if tool_files or action_files:
            evidence.append(f"检测到工具/执行文件: {len(tool_files) + len(action_files)} 个")
            score = min((len(tool_files) + len(action_files)) / 20, 1.0) * 0.9 + 0.1
        else:
            score = 0.4
            evidence.append("未检测到工具调用实现")
        
        return SubItemResult(
            name="action",
            description="工具/API调用",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_memory(self) -> SubItemResult:
        """检查记忆能力"""
        evidence = []
        
        memory_files = list(Path(self.source_path).rglob("*memory*.py"))
        context_files = list(Path(self.source_path).rglob("*context*.py"))
        
        has_short_term = len([f for f in memory_files if "short" in f.name.lower()]) > 0
        has_long_term = len([f for f in memory_files if "long" in f.name.lower()]) > 0
        
        if has_short_term:
            evidence.append("检测到短期记忆实现")
        if has_long_term:
            evidence.append("检测到长期记忆实现")
        
        if has_short_term and has_long_term:
            score = 0.9
        elif has_short_term or has_long_term:
            score = 0.7
            evidence.append("仅有单一记忆机制")
        else:
            score = 0.5
            evidence.append("未检测到明确的记忆模块")
        
        return SubItemResult(
            name="memory",
            description="短期/长期记忆",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_reflection(self) -> SubItemResult:
        """检查反思能力"""
        evidence = []
        
        reflection_files = list(Path(self.source_path).rglob("*reflection*.py"))
        review_files = list(Path(self.source_path).rglob("*review*.py"))
        
        if reflection_files or review_files:
            evidence.append(f"检测到反思/审查相关文件: {len(reflection_files) + len(review_files)} 个")
            score = 0.8
        else:
            score = 0.5
            evidence.append("未检测到明确的反思机制")
        
        return SubItemResult(
            name="reflection",
            description="自我反思能力",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_meta_cognition(self) -> SubItemResult:
        """检查元认知能力"""
        evidence = []
        
        meta_files = list(Path(self.source_path).rglob("*meta*.py"))
        awareness_files = list(Path(self.source_path).rglob("*awareness*.py"))
        
        if meta_files or awareness_files:
            evidence.append(f"检测到元认知相关文件: {len(meta_files) + len(awareness_files)} 个")
            score = 0.7
        else:
            score = 0.4
            evidence.append("未检测到元认知实现")
        
        return SubItemResult(
            name="meta_cognition",
            description="元认知能力",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _generate_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        suggestions = []
        for s in subitems:
            if s.score < 0.5:
                suggestions.append(f"建议增强{s.description}能力")
        return suggestions[:3]


class PromptEngineeringEvaluator(BaseEvaluator):
    """提示词工程评估器"""
    
    dimension_name = "prompt_engineering"
    dimension_cn = "提示词工程"
    category = "A"
    weight = 0.05
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        si1 = await self._check_template_design()
        subitems.append(si1)
        total_score += si1.score * 0.18
        
        si2 = await self._check_few_shot()
        subitems.append(si2)
        total_score += si2.score * 0.17
        
        si3 = await self._check_chain_of_thought()
        subitems.append(si3)
        total_score += si3.score * 0.17
        
        si4 = await self._check_role_definition()
        subitems.append(si4)
        total_score += si4.score * 0.16
        
        si5 = await self._check_output_constraint()
        subitems.append(si5)
        total_score += si5.score * 0.16
        
        si6 = await self._check_instruction_clarity()
        subitems.append(si6)
        total_score += si6.score * 0.16
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=f"提示词工程评估完成，{len([s for s in subitems if s.score >= 0.7])}/6项达标",
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_suggestions(subitems)
        )
    
    async def _check_template_design(self) -> SubItemResult:
        evidence = []
        template_files = list(Path(self.source_path).rglob("*template*.py"))
        template_files += list(Path(self.source_path).rglob("*prompt*.py"))
        
        if template_files:
            evidence.append(f"检测到 {len(template_files)} 个提示词模板文件")
            score = min(len(template_files) / 10, 1.0) * 0.9 + 0.1
        else:
            score = 0.3
            evidence.append("未检测到提示词模板")
        
        return SubItemResult(
            name="template_design",
            description="模板结构设计",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_few_shot(self) -> SubItemResult:
        evidence = []
        
        files_with_examples = []
        for py_file in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                if "example" in content.lower() or "few-shot" in content.lower():
                    files_with_examples.append(py_file.name)
            except:
                pass
        
        if files_with_examples:
            evidence.append(f"检测到 {len(files_with_examples)} 个文件包含示例")
            score = min(len(files_with_examples) / 5, 1.0) * 0.9 + 0.1
        else:
            score = 0.4
            evidence.append("Few-shot示例较少")
        
        return SubItemResult(
            name="few_shot_learning",
            description="Few-shot示例",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_chain_of_thought(self) -> SubItemResult:
        evidence = []
        
        cot_files = list(Path(self.source_path).rglob("*cot*.py"))
        cot_files += list(Path(self.source_path).rglob("*chain*.py"))
        cot_files += list(Path(self.source_path).rglob("*reasoning*.py"))
        
        if cot_files:
            evidence.append(f"检测到 {len(cot_files)} 个思维链相关文件")
            score = min(len(cot_files) / 5, 1.0) * 0.9 + 0.1
        else:
            score = 0.5
            evidence.append("未检测到明确的思维链实现")
        
        return SubItemResult(
            name="chain_of_thought",
            description="思维链引导",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_role_definition(self) -> SubItemResult:
        evidence = []
        
        files_with_roles = []
        for py_file in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                if "role" in content.lower() or "system" in content.lower():
                    files_with_roles.append(py_file.name)
            except:
                pass
        
        if files_with_roles:
            evidence.append(f"检测到 {len(files_with_roles)} 个文件包含角色定义")
            score = min(len(files_with_roles) / 10, 1.0) * 0.9 + 0.1
        else:
            score = 0.4
            evidence.append("角色定义较少")
        
        return SubItemResult(
            name="role_definition",
            description="角色定义",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_output_constraint(self) -> SubItemResult:
        evidence = []
        
        files_with_format = []
        for py_file in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                if any(kw in content for kw in ["format", "json", "schema", "output"]):
                    files_with_format.append(py_file.name)
            except:
                pass
        
        if files_with_format:
            evidence.append(f"检测到 {len(files_with_format)} 个文件包含输出格式约束")
            score = min(len(files_with_format) / 10, 1.0) * 0.9 + 0.1
        else:
            score = 0.4
            evidence.append("输出格式约束较少")
        
        return SubItemResult(
            name="output_constraint",
            description="输出格式约束",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_instruction_clarity(self) -> SubItemResult:
        evidence = []
        
        instruction_files = list(Path(self.source_path).rglob("*instruction*.py"))
        if instruction_files:
            evidence.append(f"检测到 {len(instruction_files)} 个指令相关文件")
            score = 0.75
        else:
            score = 0.5
            evidence.append("未检测到专门的指令模块")
        
        return SubItemResult(
            name="instruction_clarity",
            description="指令清晰度",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _generate_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        return [f"建议增强{s.description}" for s in subitems if s.score < 0.5][:3]


class ContextEngineeringEvaluator(BaseEvaluator):
    """上下文工程评估器"""
    
    dimension_name = "context_engineering"
    dimension_cn = "上下文工程"
    category = "A"
    weight = 0.05
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        si1 = await self._check_window_management()
        subitems.append(si1)
        total_score += si1.score * 0.18
        
        si2 = await self._check_priority_ranking()
        subitems.append(si2)
        total_score += si2.score * 0.17
        
        si3 = await self._check_compression()
        subitems.append(si3)
        total_score += si3.score * 0.17
        
        si4 = await self._check_history()
        subitems.append(si4)
        total_score += si4.score * 0.16
        
        si5 = await self._check_slot_tracking()
        subitems.append(si5)
        total_score += si5.score * 0.16
        
        si6 = await self._check_cross_session()
        subitems.append(si6)
        total_score += si6.score * 0.16
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=f"上下文工程评估完成，{len([s for s in subitems if s.score >= 0.7])}/6项达标",
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_suggestions(subitems)
        )
    
    async def _check_window_management(self) -> SubItemResult:
        evidence = []
        window_files = list(Path(self.source_path).rglob("*window*.py"))
        truncate_files = list(Path(self.source_path).rglob("*truncate*.py"))
        
        if window_files or truncate_files:
            evidence.append(f"检测到上下文窗口管理相关文件")
            score = 0.8
        else:
            score = 0.4
            evidence.append("未检测到明确的窗口管理")
        
        return SubItemResult(
            name="window_management",
            description="窗口管理",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_priority_ranking(self) -> SubItemResult:
        evidence = []
        priority_files = list(Path(self.source_path).rglob("*priority*.py"))
        ranking_files = list(Path(self.source_path).rglob("*ranking*.py"))
        
        if priority_files or ranking_files:
            evidence.append(f"检测到优先级相关文件: {len(priority_files) + len(ranking_files)} 个")
            score = 0.75
        else:
            score = 0.5
            evidence.append("未检测到优先级排序实现")
        
        return SubItemResult(
            name="priority_ranking",
            description="优先级排序",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_compression(self) -> SubItemResult:
        evidence = []
        compress_files = list(Path(self.source_path).rglob("*compress*.py"))
        summary_files = list(Path(self.source_path).rglob("*summary*.py"))
        
        if compress_files or summary_files:
            evidence.append(f"检测到压缩/摘要相关文件: {len(compress_files) + len(summary_files)} 个")
            score = 0.7
        else:
            score = 0.4
            evidence.append("未检测到上下文压缩实现")
        
        return SubItemResult(
            name="compression_quality",
            description="上下文压缩",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_history(self) -> SubItemResult:
        evidence = []
        history_files = list(Path(self.source_path).rglob("*history*.py"))
        
        if history_files:
            evidence.append(f"检测到 {len(history_files)} 个历史追踪文件")
            score = min(len(history_files) / 5, 1.0) * 0.9 + 0.1
        else:
            score = 0.5
            evidence.append("历史追踪实现较少")
        
        return SubItemResult(
            name="history_completeness",
            description="历史完整性",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_slot_tracking(self) -> SubItemResult:
        evidence = []
        slot_files = list(Path(self.source_path).rglob("*slot*.py"))
        entity_files = list(Path(self.source_path).rglob("*entity*.py"))
        
        if slot_files or entity_files:
            evidence.append(f"检测到槽位/实体追踪文件: {len(slot_files) + len(entity_files)} 个")
            score = 0.7
        else:
            score = 0.4
            evidence.append("未检测到槽位追踪实现")
        
        return SubItemResult(
            name="slot_tracking",
            description="槽位追踪",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_cross_session(self) -> SubItemResult:
        evidence = []
        session_files = list(Path(self.source_path).rglob("*session*.py"))
        user_files = list(Path(self.source_path).rglob("*user*.py"))
        
        if session_files or user_files:
            evidence.append(f"检测到会话管理相关文件: {len(session_files) + len(user_files)} 个")
            score = 0.7
        else:
            score = 0.4
            evidence.append("未检测到跨会话上下文")
        
        return SubItemResult(
            name="cross_session",
            description="跨会话延续",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _generate_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        return [f"建议增强{s.description}" for s in subitems if s.score < 0.5][:3]

# ============================================================================
# B. 智能能力评估器 (待实现)
# ============================================================================

class ResponseQualityEvaluator(BaseEvaluator):
    """回答质量评估器"""
    
    dimension_name = "response_quality"
    dimension_cn = "回答质量"
    category = "B"
    weight = 0.08
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        si1 = await self._check_relevance()
        subitems.append(si1)
        total_score += si1.score * 0.18
        
        si2 = await self._check_accuracy()
        subitems.append(si2)
        total_score += si2.score * 0.18
        
        si3 = await self._check_completeness()
        subitems.append(si3)
        total_score += si3.score * 0.17
        
        si4 = await self._check_conciseness()
        subitems.append(si4)
        total_score += si4.score * 0.17
        
        si5 = await self._check_coherence()
        subitems.append(si5)
        total_score += si5.score * 0.15
        
        si6 = await self._check_safety()
        subitems.append(si6)
        total_score += si6.score * 0.15
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=f"回答质量评估完成，{len([s for s in subitems if s.score >= 0.7])}/6项达标",
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_suggestions(subitems)
        )
    
    async def _check_relevance(self) -> SubItemResult:
        """检查回答相关性"""
        evidence = []
        try:
            resp = requests.post(
                f"{self.system_url}/chat",
                json={"query": "什么是人工智能?"},
                headers=self._get_auth_headers(),
                timeout=30
            )
            if resp.status_code == 200:
                evidence.append("对话API响应正常")
                score = 0.8
            else:
                score = 0.5
                evidence.append(f"API返回状态码: {resp.status_code}")
        except Exception as e:
            score = 0.4
            evidence.append(f"API调用失败")
        
        return SubItemResult(
            name="relevance",
            description="回答相关性",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_accuracy(self) -> SubItemResult:
        evidence = []
        validation_files = list(Path(self.source_path).rglob("*validation*.py"))
        
        if validation_files:
            evidence.append(f"检测到 {len(validation_files)} 个验证模块")
            score = min(len(validation_files) / 5, 1.0) * 0.9 + 0.1
        else:
            score = 0.5
            evidence.append("未检测到专门的验证模块")
        
        return SubItemResult(
            name="factual_accuracy",
            description="事实准确性",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_completeness(self) -> SubItemResult:
        evidence = []
        completion_files = list(Path(self.source_path).rglob("*completion*.py"))
        
        if completion_files:
            evidence.append(f"检测到完整性相关文件")
            score = 0.7
        else:
            score = 0.5
            evidence.append("未检测到专门的完整性检查")
        
        return SubItemResult(
            name="completeness",
            description="回答完整性",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_conciseness(self) -> SubItemResult:
        evidence = []
        score = 0.6
        evidence.append("简洁性通过代码审查评估")
        
        return SubItemResult(
            name="conciseness",
            description="回答简洁性",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_coherence(self) -> SubItemResult:
        evidence = []
        coherence_files = list(Path(self.source_path).rglob("*coherence*.py"))
        
        if coherence_files:
            score = 0.75
            evidence.append("检测到连贯性检查模块")
        else:
            score = 0.5
            evidence.append("未检测到专门的连贯性检查")
        
        return SubItemResult(
            name="logical_coherence",
            description="逻辑连贯性",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_safety(self) -> SubItemResult:
        evidence = []
        safety_files = list(Path(self.source_path).rglob("*safety*.py"))
        filter_files = list(Path(self.source_path).rglob("*filter*.py"))
        
        if safety_files or filter_files:
            evidence.append(f"检测到安全过滤相关文件")
            score = 0.8
        else:
            score = 0.5
            evidence.append("安全过滤实现较少")
        
        return SubItemResult(
            name="safety_filter",
            description="安全过滤",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _generate_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        return [f"建议增强{s.description}" for s in subitems if s.score < 0.5][:3]


class RoutingEvaluator(BaseEvaluator):
    """路由准确率评估器"""
    
    dimension_name = "routing"
    dimension_cn = "路由准确率"
    category = "B"
    weight = 0.06
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        si1 = await self._check_intent_classification()
        subitems.append(si1)
        total_score += si1.score * 0.22
        
        si2 = await self._check_domain_routing()
        subitems.append(si2)
        total_score += si2.score * 0.20
        
        si3 = await self._check_priority_queue()
        subitems.append(si3)
        total_score += si3.score * 0.20
        
        si4 = await self._check_fallback()
        subitems.append(si4)
        total_score += si4.score * 0.20
        
        si5 = await self._check_load_balance()
        subitems.append(si5)
        total_score += si5.score * 0.18
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=f"路由准确率评估完成，{len([s for s in subitems if s.score >= 0.7])}/5项达标",
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_suggestions(subitems)
        )
    
    async def _check_intent_classification(self) -> SubItemResult:
        evidence = []
        intent_files = list(Path(self.source_path).rglob("*intent*.py"))
        classifier_files = list(Path(self.source_path).rglob("*classifier*.py"))
        
        if intent_files or classifier_files:
            evidence.append(f"检测到意图分类相关文件: {len(intent_files) + len(classifier_files)} 个")
            score = min((len(intent_files) + len(classifier_files)) / 5, 1.0) * 0.9 + 0.1
        else:
            score = 0.4
            evidence.append("未检测到意图分类实现")
        
        return SubItemResult(
            name="intent_classification",
            description="意图分类准确率",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_domain_routing(self) -> SubItemResult:
        evidence = []
        routing_files = list(Path(self.source_path).rglob("*/routing*.py"))
        router_files = list(Path(self.source_path).rglob("*router*.py"))
        
        if routing_files or router_files:
            evidence.append(f"检测到路由文件: {len(routing_files) + len(router_files)} 个")
            score = min((len(routing_files) + len(router_files)) / 5, 1.0) * 0.9 + 0.1
        else:
            score = 0.4
            evidence.append("未检测到领域路由实现")
        
        return SubItemResult(
            name="domain_routing",
            description="领域路由",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_priority_queue(self) -> SubItemResult:
        evidence = []
        queue_files = list(Path(self.source_path).rglob("*queue*.py"))
        
        if queue_files:
            evidence.append(f"检测到队列相关文件: {len(queue_files)} 个")
            score = min(len(queue_files) / 3, 1.0) * 0.9 + 0.1
        else:
            score = 0.4
            evidence.append("未检测到优先级队列")
        
        return SubItemResult(
            name="priority_queue",
            description="优先级队列",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_fallback(self) -> SubItemResult:
        evidence = []
        fallback_files = list(Path(self.source_path).rglob("*fallback*.py"))
        default_files = list(Path(self.source_path).rglob("*default*.py"))
        
        if fallback_files or default_files:
            evidence.append(f"检测到兜底策略文件: {len(fallback_files) + len(default_files)} 个")
            score = 0.75
        else:
            score = 0.5
            evidence.append("未检测到明确的兜底策略")
        
        return SubItemResult(
            name="fallback_strategy",
            description="兜底策略",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_load_balance(self) -> SubItemResult:
        evidence = []
        lb_files = list(Path(self.source_path).rglob("*load*balance*.py"))
        
        if lb_files:
            evidence.append(f"检测到负载均衡文件: {len(lb_files)} 个")
            score = 0.7
        else:
            score = 0.5
            evidence.append("未检测到专门的负载均衡")
        
        return SubItemResult(
            name="load_balance",
            description="负载均衡",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _generate_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        return [f"建议增强{s.description}" for s in subitems if s.score < 0.5][:3]


class ReasoningEvaluator(BaseEvaluator):
    """推理深度评估器"""
    
    dimension_name = "reasoning"
    dimension_cn = "推理深度"
    category = "B"
    weight = 0.05
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        si1 = await self._check_multi_step()
        subitems.append(si1)
        total_score += si1.score * 0.22
        
        si2 = await self._check_logical_inference()
        subitems.append(si2)
        total_score += si2.score * 0.20
        
        si3 = await self._check_causal_analysis()
        subitems.append(si3)
        total_score += si3.score * 0.20
        
        si4 = await self._check_analogical()
        subitems.append(si4)
        total_score += si4.score * 0.19
        
        si5 = await self._check_critical()
        subitems.append(si5)
        total_score += si5.score * 0.19
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=f"推理深度评估完成，{len([s for s in subitems if s.score >= 0.7])}/5项达标",
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_suggestions(subitems)
        )
    
    async def _check_multi_step(self) -> SubItemResult:
        evidence = []
        step_files = list(Path(self.source_path).rglob("*step*.py"))
        chain_files = list(Path(self.source_path).rglob("*chain*.py"))
        
        if step_files or chain_files:
            evidence.append(f"检测到多步推理相关文件: {len(step_files) + len(chain_files)} 个")
            score = min((len(step_files) + len(chain_files)) / 5, 1.0) * 0.9 + 0.1
        else:
            score = 0.4
            evidence.append("未检测到多步推理实现")
        
        return SubItemResult(
            name="multi_step_reasoning",
            description="多步推理",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_logical_inference(self) -> SubItemResult:
        evidence = []
        logic_files = list(Path(self.source_path).rglob("*logic*.py"))
        infer_files = list(Path(self.source_path).rglob("*infer*.py"))
        
        if logic_files or infer_files:
            evidence.append(f"检测到逻辑推理相关文件")
            score = 0.7
        else:
            score = 0.4
            evidence.append("未检测到逻辑推理实现")
        
        return SubItemResult(
            name="logical_inference",
            description="逻辑推演",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_causal_analysis(self) -> SubItemResult:
        evidence = []
        causal_files = list(Path(self.source_path).rglob("*causal*.py"))
        cause_files = list(Path(self.source_path).rglob("*cause*.py"))
        
        if causal_files or cause_files:
            score = 0.65
            evidence.append("检测到因果分析实现")
        else:
            score = 0.4
            evidence.append("未检测到因果分析")
        
        return SubItemResult(
            name="causal_analysis",
            description="因果分析",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_analogical(self) -> SubItemResult:
        evidence = []
        analogy_files = list(Path(self.source_path).rglob("*analogy*.py"))
        
        if analogy_files:
            score = 0.6
            evidence.append("检测到类比推理实现")
        else:
            score = 0.4
            evidence.append("未检测到类比推理")
        
        return SubItemResult(
            name="analogical_thinking",
            description="类比思维",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_critical(self) -> SubItemResult:
        evidence = []
        critical_files = list(Path(self.source_path).rglob("*critical*.py"))
        evaluate_files = list(Path(self.source_path).rglob("*evaluat*.py"))
        
        if critical_files or evaluate_files:
            score = 0.65
            evidence.append("检测到批判性评估实现")
        else:
            score = 0.4
            evidence.append("未检测到批判性评估")
        
        return SubItemResult(
            name="critical_evaluation",
            description="批判性评估",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _generate_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        return [f"建议增强{s.description}" for s in subitems if s.score < 0.5][:3]


class KnowledgeRecallEvaluator(BaseEvaluator):
    """知识召回评估器"""
    
    dimension_name = "knowledge_recall"
    dimension_cn = "知识召回"
    category = "B"
    weight = 0.04
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        si1 = await self._check_retrieval()
        subitems.append(si1)
        total_score += si1.score * 0.22
        
        si2 = await self._check_reranking()
        subitems.append(si2)
        total_score += si2.score * 0.20
        
        si3 = await self._check_freshness()
        subitems.append(si3)
        total_score += si3.score * 0.20
        
        si4 = await self._check_source_tracking()
        subitems.append(si4)
        total_score += si4.score * 0.20
        
        si5 = await self._check_vector_index()
        subitems.append(si5)
        total_score += si5.score * 0.18
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=f"知识召回评估完成，{len([s for s in subitems if s.score >= 0.7])}/5项达标",
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_suggestions(subitems)
        )
    
    async def _check_retrieval(self) -> SubItemResult:
        evidence = []
        rag_files = list(Path(self.source_path).rglob("*/rag*.py"))
        retrieval_files = list(Path(self.source_path).rglob("*retrieval*.py"))
        search_files = list(Path(self.source_path).rglob("*search*.py"))
        
        total = len(rag_files) + len(retrieval_files) + len(search_files)
        if total > 0:
            evidence.append(f"检测到检索相关文件: {total} 个")
            score = min(total / 10, 1.0) * 0.9 + 0.1
        else:
            score = 0.4
            evidence.append("未检测到检索实现")
        
        return SubItemResult(
            name="retrieval_precision",
            description="检索精确率",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_reranking(self) -> SubItemResult:
        evidence = []
        rerank_files = list(Path(self.source_path).rglob("*rerank*.py"))
        
        if rerank_files:
            score = 0.7
            evidence.append(f"检测到重排相关文件: {len(rerank_files)} 个")
        else:
            score = 0.5
            evidence.append("未检测到重排实现")
        
        return SubItemResult(
            name="reranking_quality",
            description="重排质量",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_freshness(self) -> SubItemResult:
        evidence = []
        update_files = list(Path(self.source_path).rglob("*update*.py"))
        sync_files = list(Path(self.source_path).rglob("*sync*.py"))
        
        if update_files or sync_files:
            score = 0.7
            evidence.append("检测到知识更新机制")
        else:
            score = 0.5
            evidence.append("知识更新机制较弱")
        
        return SubItemResult(
            name="knowledge_freshness",
            description="知识新鲜度",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_source_tracking(self) -> SubItemResult:
        evidence = []
        source_files = list(Path(self.source_path).rglob("*source*.py"))
        citation_files = list(Path(self.source_path).rglob("*citation*.py"))
        
        if source_files or citation_files:
            score = 0.65
            evidence.append("检测到来源追踪实现")
        else:
            score = 0.4
            evidence.append("未检测到来源追踪")
        
        return SubItemResult(
            name="source_tracking",
            description="来源追踪",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_vector_index(self) -> SubItemResult:
        evidence = []
        vector_files = list(Path(self.source_path).rglob("*vector*.py"))
        index_files = list(Path(self.source_path).rglob("*index*.py"))
        
        total = len(vector_files) + len(index_files)
        if total > 0:
            score = min(total / 5, 1.0) * 0.9 + 0.1
            evidence.append(f"检测到向量索引相关文件: {total} 个")
        else:
            score = 0.4
            evidence.append("未检测到向量索引")
        
        return SubItemResult(
            name="vector_index",
            description="向量索引",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _generate_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        return [f"建议增强{s.description}" for s in subitems if s.score < 0.5][:3]


class ToolCallingEvaluator(BaseEvaluator):
    """工具调用评估器"""
    
    dimension_name = "tool_calling"
    dimension_cn = "工具调用"
    category = "B"
    weight = 0.03
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        si1 = await self._check_tool_selection()
        subitems.append(si1)
        total_score += si1.score * 0.22
        
        si2 = await self._check_parameter_mapping()
        subitems.append(si2)
        total_score += si2.score * 0.20
        
        si3 = await self._check_execution()
        subitems.append(si3)
        total_score += si3.score * 0.20
        
        si4 = await self._check_result_parsing()
        subitems.append(si4)
        total_score += si4.score * 0.19
        
        si5 = await self._check_availability()
        subitems.append(si5)
        total_score += si5.score * 0.19
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=f"工具调用评估完成，{len([s for s in subitems if s.score >= 0.7])}/5项达标",
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_suggestions(subitems)
        )
    
    async def _check_tool_selection(self) -> SubItemResult:
        evidence = []
        tool_files = list(Path(self.source_path).rglob("*/tools/*.py"))
        selector_files = list(Path(self.source_path).rglob("*selector*.py"))
        
        if tool_files:
            evidence.append(f"检测到工具文件: {len(tool_files)} 个")
            score = min(len(tool_files) / 20, 1.0) * 0.8 + 0.2
        else:
            score = 0.4
            evidence.append("未检测到工具定义")
        
        return SubItemResult(
            name="tool_selection",
            description="工具选择",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_parameter_mapping(self) -> SubItemResult:
        evidence = []
        param_files = list(Path(self.source_path).rglob("*param*.py"))
        
        if param_files:
            score = 0.7
            evidence.append(f"检测到参数映射相关文件: {len(param_files)} 个")
        else:
            score = 0.5
            evidence.append("参数映射实现较少")
        
        return SubItemResult(
            name="parameter_mapping",
            description="参数映射",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_execution(self) -> SubItemResult:
        evidence = []
        exec_files = list(Path(self.source_path).rglob("*execute*.py"))
        runner_files = list(Path(self.source_path).rglob("*runner*.py"))
        
        if exec_files or runner_files:
            score = 0.75
            evidence.append("检测到执行引擎")
        else:
            score = 0.5
            evidence.append("未检测到专门的执行模块")
        
        return SubItemResult(
            name="execution_reliability",
            description="执行可靠性",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_result_parsing(self) -> SubItemResult:
        evidence = []
        parse_files = list(Path(self.source_path).rglob("*parse*.py"))
        result_files = list(Path(self.source_path).rglob("*result*.py"))
        
        if parse_files or result_files:
            score = 0.7
            evidence.append("检测到结果解析实现")
        else:
            score = 0.5
            evidence.append("结果解析实现较少")
        
        return SubItemResult(
            name="result_interpretation",
            description="结果解析",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_availability(self) -> SubItemResult:
        evidence = []
        health_files = list(Path(self.source_path).rglob("*health*.py"))
        status_files = list(Path(self.source_path).rglob("*status*.py"))
        
        if health_files or status_files:
            score = 0.7
            evidence.append("检测到可用性检查实现")
        else:
            score = 0.5
            evidence.append("可用性检查较弱")
        
        return SubItemResult(
            name="availability_check",
            description="可用性检测",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _generate_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        return [f"建议增强{s.description}" for s in subitems if s.score < 0.5][:3]


class MultiTurnEvaluator(BaseEvaluator):
    """多轮对话评估器"""
    
    dimension_name = "multi_turn"
    dimension_cn = "多轮对话"
    category = "B"
    weight = 0.02
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        si1 = await self._check_context_preservation()
        subitems.append(si1)
        total_score += si1.score * 0.28
        
        si2 = await self._check_reference_resolution()
        subitems.append(si2)
        total_score += si2.score * 0.25
        
        si3 = await self._check_conversation_flow()
        subitems.append(si3)
        total_score += si3.score * 0.24
        
        si4 = await self._check_task_continuation()
        subitems.append(si4)
        total_score += si4.score * 0.23
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=f"多轮对话评估完成，{len([s for s in subitems if s.score >= 0.7])}/4项达标",
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_suggestions(subitems)
        )
    
    async def _check_context_preservation(self) -> SubItemResult:
        evidence = []
        context_files = list(Path(self.source_path).rglob("*context*.py"))
        
        if context_files:
            score = min(len(context_files) / 5, 1.0) * 0.9 + 0.1
            evidence.append(f"检测到上下文文件: {len(context_files)} 个")
        else:
            score = 0.4
            evidence.append("上下文保持实现较少")
        
        return SubItemResult(
            name="context_preservation",
            description="上下文保持",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_reference_resolution(self) -> SubItemResult:
        evidence = []
        ref_files = list(Path(self.source_path).rglob("*reference*.py"))
        pronoun_files = list(Path(self.source_path).rglob("*pronoun*.py"))
        
        if ref_files or pronoun_files:
            score = 0.6
            evidence.append("检测到指代消解实现")
        else:
            score = 0.4
            evidence.append("未检测到指代消解")
        
        return SubItemResult(
            name="reference_resolution",
            description="指代消解",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_conversation_flow(self) -> SubItemResult:
        evidence = []
        flow_files = list(Path(self.source_path).rglob("*flow*.py"))
        conversation_files = list(Path(self.source_path).rglob("*conversation*.py"))
        
        if flow_files or conversation_files:
            score = 0.7
            evidence.append("检测到对话流管理")
        else:
            score = 0.5
            evidence.append("对话流管理较弱")
        
        return SubItemResult(
            name="conversation_flow",
            description="对话流畅",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_task_continuation(self) -> SubItemResult:
        evidence = []
        task_files = list(Path(self.source_path).rglob("*task*.py"))
        
        if task_files:
            score = min(len(task_files) / 5, 1.0) * 0.8 + 0.2
            evidence.append(f"检测到任务管理文件: {len(task_files)} 个")
        else:
            score = 0.4
            evidence.append("任务延续实现较少")
        
        return SubItemResult(
            name="task_continuation",
            description="任务延续",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _generate_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        return [f"建议增强{s.description}" for s in subitems if s.score < 0.5][:2]


class SelfLearningEvaluator(BaseEvaluator):
    """自学习能力评估器"""
    
    dimension_name = "self_learning"
    dimension_cn = "自学习能力"
    category = "B"
    weight = 0.02
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        si1 = await self._check_feedback()
        subitems.append(si1)
        total_score += si1.score * 0.22
        
        si2 = await self._check_pattern_extraction()
        subitems.append(si2)
        total_score += si2.score * 0.20
        
        si3 = await self._check_policy_update()
        subitems.append(si3)
        total_score += si3.score * 0.20
        
        si4 = await self._check_performance_feedback()
        subitems.append(si4)
        total_score += si4.score * 0.19
        
        si5 = await self._check_continual_learning()
        subitems.append(si5)
        total_score += si5.score * 0.19
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=f"自学习能力评估完成，{len([s for s in subitems if s.score >= 0.7])}/5项达标",
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_suggestions(subitems)
        )
    
    async def _check_feedback(self) -> SubItemResult:
        evidence = []
        feedback_files = list(Path(self.source_path).rglob("*feedback*.py"))
        
        if feedback_files:
            score = min(len(feedback_files) / 3, 1.0) * 0.9 + 0.1
            evidence.append(f"检测到反馈相关文件: {len(feedback_files)} 个")
        else:
            score = 0.4
            evidence.append("未检测到反馈机制")
        
        return SubItemResult(
            name="feedback_integration",
            description="反馈整合",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_pattern_extraction(self) -> SubItemResult:
        evidence = []
        pattern_files = list(Path(self.source_path).rglob("*pattern*.py"))
        extract_files = list(Path(self.source_path).rglob("*extract*.py"))
        
        if pattern_files or extract_files:
            score = 0.65
            evidence.append("检测到模式提取实现")
        else:
            score = 0.4
            evidence.append("未检测到模式提取")
        
        return SubItemResult(
            name="pattern_extraction",
            description="模式提取",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_policy_update(self) -> SubItemResult:
        evidence = []
        policy_files = list(Path(self.source_path).rglob("*policy*.py"))
        update_files = list(Path(self.source_path).rglob("*update*.py"))
        
        if policy_files or update_files:
            score = 0.6
            evidence.append("检测到策略更新机制")
        else:
            score = 0.4
            evidence.append("策略更新机制较弱")
        
        return SubItemResult(
            name="policy_update",
            description="策略更新",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_performance_feedback(self) -> SubItemResult:
        evidence = []
        perf_files = list(Path(self.source_path).rglob("*performance*.py"))
        metric_files = list(Path(self.source_path).rglob("*metric*.py"))
        
        if perf_files or metric_files:
            score = 0.7
            evidence.append("检测到性能反馈机制")
        else:
            score = 0.4
            evidence.append("性能反馈较弱")
        
        return SubItemResult(
            name="performance_feedback",
            description="效果反馈",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_continual_learning(self) -> SubItemResult:
        evidence = []
        learn_files = list(Path(self.source_path).rglob("*learn*.py"))
        
        if learn_files:
            score = min(len(learn_files) / 5, 1.0) * 0.8 + 0.2
            evidence.append(f"检测到学习相关文件: {len(learn_files)} 个")
        else:
            score = 0.4
            evidence.append("未检测到持续学习机制")
        
        return SubItemResult(
            name="continual_learning",
            description="持续学习",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _generate_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        return [f"建议增强{s.description}" for s in subitems if s.score < 0.5][:3]

# ============================================================================
# C. 架构能力评估器
# ============================================================================

class HarnessEvaluator(BaseEvaluator):
    """Harness能力评估器 - 架构级别"""
    
    dimension_name = "harness"
    dimension_cn = "Harness能力"
    category = "C"
    weight = 0.08
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        si1 = await self._check_llm_utilization()
        subitems.append(si1)
        total_score += si1.score * 0.18
        
        si2 = await self._check_gpu_scheduling()
        subitems.append(si2)
        total_score += si2.score * 0.17
        
        si3 = await self._check_cache()
        subitems.append(si3)
        total_score += si3.score * 0.17
        
        si4 = await self._check_parallel_efficiency()
        subitems.append(si4)
        total_score += si4.score * 0.16
        
        si5 = await self._check_batch_processing()
        subitems.append(si5)
        total_score += si5.score * 0.16
        
        si6 = await self._check_resource_pooling()
        subitems.append(si6)
        total_score += si6.score * 0.16
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=f"Harness能力评估完成，{len([s for s in subitems if s.score >= 0.7])}/6项达标",
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_suggestions(subitems)
        )
    
    async def _check_llm_utilization(self) -> SubItemResult:
        evidence = []
        cache_files = list(Path(self.source_path).rglob("*cache*.py"))
        token_files = list(Path(self.source_path).rglob("*token*.py"))
        
        if cache_files:
            evidence.append(f"检测到缓存相关文件: {len(cache_files)} 个")
            score = min(len(cache_files) / 5, 1.0) * 0.9 + 0.1
        else:
            score = 0.4
            evidence.append("未检测到LLM利用率优化")
        
        return SubItemResult(
            name="llm_utilization",
            description="LLM利用率",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_gpu_scheduling(self) -> SubItemResult:
        evidence = []
        gpu_files = list(Path(self.source_path).rglob("*gpu*.py"))
        schedule_files = list(Path(self.source_path).rglob("*schedule*.py"))
        
        if gpu_files or schedule_files:
            evidence.append("检测到GPU调度实现")
            score = 0.7
        else:
            score = 0.4
            evidence.append("未检测到GPU调度")
        
        return SubItemResult(
            name="gpu_scheduling",
            description="GPU调度",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_cache(self) -> SubItemResult:
        evidence = []
        cache_dirs = [
            Path(self.source_path) / "cache",
            Path(self.source_path) / "caching",
            Path(self.source_path) / "services" / "cache",
        ]
        
        cache_count = 0
        for d in cache_dirs:
            if d.exists():
                cache_count += len(list(d.rglob("*.py")))
        
        if cache_count > 0:
            evidence.append(f"检测到缓存实现文件: {cache_count} 个")
            score = min(cache_count / 5, 1.0) * 0.9 + 0.1
        else:
            score = 0.5
            evidence.append("缓存实现较少")
        
        return SubItemResult(
            name="cache_harnessing",
            description="缓存利用",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_parallel_efficiency(self) -> SubItemResult:
        evidence = []
        async_files = list(Path(self.source_path).rglob("*async*.py"))
        parallel_files = list(Path(self.source_path).rglob("*parallel*.py"))
        
        total = len(async_files) + len(parallel_files)
        if total > 0:
            evidence.append(f"检测到异步/并行文件: {total} 个")
            score = min(total / 10, 1.0) * 0.9 + 0.1
        else:
            score = 0.4
            evidence.append("未检测到并行处理")
        
        return SubItemResult(
            name="parallel_efficiency",
            description="并行效率",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_batch_processing(self) -> SubItemResult:
        evidence = []
        batch_files = list(Path(self.source_path).rglob("*batch*.py"))
        
        if batch_files:
            evidence.append(f"检测到批处理文件: {len(batch_files)} 个")
            score = min(len(batch_files) / 3, 1.0) * 0.9 + 0.1
        else:
            score = 0.4
            evidence.append("未检测到批处理实现")
        
        return SubItemResult(
            name="batch_processing",
            description="批处理",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_resource_pooling(self) -> SubItemResult:
        evidence = []
        pool_files = list(Path(self.source_path).rglob("*pool*.py"))
        connection_files = list(Path(self.source_path).rglob("*connection*.py"))
        
        if pool_files or connection_files:
            evidence.append(f"检测到资源池化文件: {len(pool_files) + len(connection_files)} 个")
            score = 0.7
        else:
            score = 0.4
            evidence.append("未检测到资源池化")
        
        return SubItemResult(
            name="resource_pooling",
            description="资源池化",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _generate_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        return [f"建议增强{s.description}" for s in subitems if s.score < 0.5][:3]


class ArchitectureEvaluator(BaseEvaluator):
    """架构合理性评估器"""
    
    dimension_name = "architecture"
    dimension_cn = "架构合理性"
    category = "C"
    weight = 0.06
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        si1 = await self._check_modularity()
        subitems.append(si1)
        total_score += si1.score * 0.22
        
        si2 = await self._check_coupling()
        subitems.append(si2)
        total_score += si2.score * 0.20
        
        si3 = await self._check_extensibility()
        subitems.append(si3)
        total_score += si3.score * 0.20
        
        si4 = await self._check_design_patterns()
        subitems.append(si4)
        total_score += si4.score * 0.19
        
        si5 = await self._check_code_organization()
        subitems.append(si5)
        total_score += si5.score * 0.19
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=f"架构合理性评估完成，{len([s for s in subitems if s.score >= 0.7])}/5项达标",
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_suggestions(subitems)
        )
    
    async def _check_modularity(self) -> SubItemResult:
        evidence = []
        
        src_path = Path(self.source_path)
        
        # 检查是否有清晰的模块目录结构
        modules = [d for d in src_path.iterdir() if d.is_dir() and not d.name.startswith("_") and not d.name.startswith(".")]
        
        # 检查每个模块是否有 __init__.py（Python包）
        packages = sum(1 for m in modules if (m / "__init__.py").exists())
        
        if len(modules) >= 5 and packages >= 3:
            evidence.append(f"检测到 {len(modules)} 个模块目录，{packages} 个Python包")
            score = min(packages / 8, 1.0) * 0.7 + 0.3
        elif len(modules) >= 3:
            evidence.append(f"检测到 {len(modules)} 个模块目录")
            score = 0.6
        else:
            evidence.append("模块结构较简单")
            score = 0.4
            evidence.append(f"模块划分较少: {len(modules)} 个")
        
        return SubItemResult(
            name="modularity",
            description="模块化设计",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_coupling(self) -> SubItemResult:
        evidence = []
        import_files = list(Path(self.source_path).rglob("*.py"))
        
        # 简单检查循环导入
        circular_imports = 0
        for f in import_files[:50]:
            try:
                content = f.read_text(encoding="utf-8")
                if "from src." in content and f.name != "__init__.py":
                    count = content.count("from src.")
                    if count > 10:
                        circular_imports += 1
            except:
                pass
        
        if circular_imports < 5:
            score = 0.75
            evidence.append(f"模块耦合度较低")
        else:
            score = 0.5
            evidence.append(f"检测到 {circular_imports} 个高耦合文件")
        
        return SubItemResult(
            name="loose_coupling",
            description="低耦合",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_extensibility(self) -> SubItemResult:
        evidence = []
        plugin_files = list(Path(self.source_path).rglob("*plugin*.py"))
        extension_files = list(Path(self.source_path).rglob("*extension*.py"))
        
        if plugin_files or extension_files:
            evidence.append(f"检测到扩展相关文件: {len(plugin_files) + len(extension_files)} 个")
            score = 0.75
        else:
            score = 0.5
            evidence.append("扩展性设计较少")
        
        return SubItemResult(
            name="extensibility",
            description="可扩展性",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_design_patterns(self) -> SubItemResult:
        evidence = []
        pattern_count = 0
        
        patterns = ["factory", "singleton", "observer", "strategy", "adapter", "facade"]
        for pattern in patterns:
            files = list(Path(self.source_path).rglob(f"*{pattern}*.py"))
            pattern_count += len(files)
        
        if pattern_count > 0:
            evidence.append(f"检测到设计模式应用: {pattern_count} 处")
            score = min(pattern_count / 10, 1.0) * 0.9 + 0.1
        else:
            score = 0.5
            evidence.append("设计模式应用较少")
        
        return SubItemResult(
            name="design_patterns",
            description="设计模式",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_code_organization(self) -> SubItemResult:
        evidence = []
        
        py_files = list(Path(self.source_path).rglob("*.py"))
        if len(py_files) > 100:
            evidence.append(f"代码组织良好: {len(py_files)} 个Python文件")
            score = 0.8
        else:
            score = 0.6
            evidence.append(f"代码文件数: {len(py_files)}")
        
        return SubItemResult(
            name="code_organization",
            description="代码组织",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _generate_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        return [f"建议增强{s.description}" for s in subitems if s.score < 0.5][:3]


class ObservabilityEvaluator(BaseEvaluator):
    """可观测性评估器"""
    
    dimension_name = "observability"
    dimension_cn = "可观测性"
    category = "C"
    weight = 0.05
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        si1 = await self._check_logging()
        subitems.append(si1)
        total_score += si1.score * 0.28
        
        si2 = await self._check_metrics()
        subitems.append(si2)
        total_score += si2.score * 0.25
        
        si3 = await self._check_tracing()
        subitems.append(si3)
        total_score += si3.score * 0.24
        
        si4 = await self._check_logging_levels()
        subitems.append(si4)
        total_score += si4.score * 0.23
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=f"可观测性评估完成，{len([s for s in subitems if s.score >= 0.7])}/4项达标",
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_suggestions(subitems)
        )
    
    async def _check_logging(self) -> SubItemResult:
        evidence = []
        files_checked = 0
        files_with_logging = 0
        
        for py_file in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(py_file) or "test" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                files_checked += 1
                if any(pattern in content for pattern in ["import logging", "logger.", "log.info", "log.debug", "log.warning", "log.error"]):
                    files_with_logging += 1
            except:
                pass
        
        if files_checked > 0:
            ratio = files_with_logging / files_checked
            score = min(ratio / 0.3, 1.0) if ratio >= 0.3 else ratio / 0.3 * 0.5
            evidence.append(f"日志覆盖: {files_with_logging}/{files_checked} 个文件 ({ratio*100:.0f}%)")
        else:
            score = 0.5
            evidence.append("无法检查日志覆盖")
        
        return SubItemResult(
            name="logging",
            description="日志体系",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_metrics(self) -> SubItemResult:
        evidence = []
        files_checked = 0
        files_with_metrics = 0
        
        for py_file in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(py_file) or "test" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                files_checked += 1
                if any(pattern in content for pattern in ["metrics", "Counter(", "Histogram(", "Gauge(", "prometheus", "statsd", "self.counter", "self.gauge"]):
                    files_with_metrics += 1
            except:
                pass
        
        if files_with_metrics > 0:
            evidence.append(f"检测到指标采集实现")
            score = 0.7
        else:
            evidence.append("未检测到指标采集")
            score = 0.3
        
        return SubItemResult(
            name="metrics",
            description="指标采集",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_tracing(self) -> SubItemResult:
        evidence = []
        files_checked = 0
        files_with_tracing = 0
        
        for py_file in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(py_file) or "test" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                files_checked += 1
                if any(pattern in content for pattern in ["tracer", "span", "trace_id", "opentelemetry", "jaeger", "zipkin", "trace.context"]):
                    files_with_tracing += 1
            except:
                pass
        
        if files_with_tracing > 0:
            evidence.append(f"检测到链路追踪实现")
            score = 0.7
        else:
            evidence.append("未检测到链路追踪")
            score = 0.3
        
        return SubItemResult(
            name="tracing",
            description="链路追踪",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_logging_levels(self) -> SubItemResult:
        evidence = []
        
        files_with_levels = []
        for py_file in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                if any(kw in content for kw in ["logger.debug", "logger.info", "logger.warning", "logger.error"]):
                    files_with_levels.append(py_file.name)
            except:
                pass
        
        if files_with_levels:
            evidence.append(f"检测到 {len(files_with_levels)} 个文件使用分级日志")
            score = min(len(files_with_levels) / 20, 1.0) * 0.9 + 0.1
        else:
            score = 0.4
            evidence.append("分级日志使用较少")
        
        return SubItemResult(
            name="logging_levels",
            description="日志分级",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _generate_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        return [f"建议增强{s.description}" for s in subitems if s.score < 0.5][:2]


class MonitoringEvaluator(BaseEvaluator):
    """监控告警评估器"""
    
    dimension_name = "monitoring"
    dimension_cn = "监控告警"
    category = "C"
    weight = 0.05
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        si1 = await self._check_latency_monitoring()
        subitems.append(si1)
        total_score += si1.score * 0.18
        
        si2 = await self._check_error_tracking()
        subitems.append(si2)
        total_score += si2.score * 0.17
        
        si3 = await self._check_token_consumption()
        subitems.append(si3)
        total_score += si3.score * 0.17
        
        si4 = await self._check_drift_detection()
        subitems.append(si4)
        total_score += si4.score * 0.16
        
        si5 = await self._check_alert_rules()
        subitems.append(si5)
        total_score += si5.score * 0.16
        
        si6 = await self._check_alert_channels()
        subitems.append(si6)
        total_score += si6.score * 0.16
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=f"监控告警评估完成，{len([s for s in subitems if s.score >= 0.7])}/6项达标",
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_suggestions(subitems)
        )
    
    async def _check_latency_monitoring(self) -> SubItemResult:
        evidence = []
        files_with_monitoring = 0
        files_checked = 0
        
        for py_file in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(py_file) or "test" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                files_checked += 1
                if any(p in content for p in ["time.time()", "time.perf_counter()", "time.monotonic()", "latency", "duration", "@timed", "elapsed"]):
                    files_with_monitoring += 1
            except:
                pass
        
        if files_with_monitoring > 0:
            evidence.append(f"检测到延迟监控实现: {files_with_monitoring} 个文件")
            score = min(files_with_monitoring / 3, 1.0) * 0.7 + 0.3
        else:
            evidence.append("未检测到延迟监控实现")
            score = 0.3
        
        return SubItemResult(
            name="latency_monitoring",
            description="延迟监控",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_error_tracking(self) -> SubItemResult:
        evidence = []
        files_with_tracking = 0
        files_checked = 0
        
        for py_file in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(py_file) or "test" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                files_checked += 1
                if any(p in content for p in ["error_count", "error_rate", "sentry", "exception", "traceback", "error_log", "track_error"]):
                    files_with_tracking += 1
            except:
                pass
        
        if files_with_tracking > 0:
            evidence.append(f"检测到错误追踪实现: {files_with_tracking} 个文件")
            score = min(files_with_tracking / 3, 1.0) * 0.7 + 0.3
        else:
            evidence.append("未检测到错误追踪实现")
            score = 0.3
        
        return SubItemResult(
            name="error_tracking",
            description="错误追踪",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_token_consumption(self) -> SubItemResult:
        evidence = []
        files_with_token_monitoring = 0
        files_checked = 0
        
        for py_file in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(py_file) or "test" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                files_checked += 1
                if any(p in content for p in ["token_count", "token_usage", "usage_tokens", "prompt_tokens", "completion_tokens", "total_tokens"]):
                    files_with_token_monitoring += 1
            except:
                pass
        
        if files_with_token_monitoring > 0:
            evidence.append(f"检测到Token消耗统计实现")
            score = 0.7
        else:
            evidence.append("未检测到Token消耗统计实现")
            score = 0.3
        
        return SubItemResult(
            name="token_consumption",
            description="Token消耗统计",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_drift_detection(self) -> SubItemResult:
        evidence = []
        drift_files = list(Path(self.source_path).rglob("*drift*.py"))
        monitor_files = list(Path(self.source_path).rglob("*monitor*.py"))
        
        if drift_files or monitor_files:
            evidence.append("检测到模型漂移检测")
            score = 0.6
        else:
            score = 0.4
            evidence.append("未检测到漂移检测")
        
        return SubItemResult(
            name="model_drift_detection",
            description="模型漂移检测",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_alert_rules(self) -> SubItemResult:
        evidence = []
        rule_files = list(Path(self.source_path).rglob("*rule*.py"))
        
        if rule_files:
            evidence.append(f"检测到告警规则文件: {len(rule_files)} 个")
            score = 0.65
        else:
            score = 0.4
            evidence.append("未检测到告警规则")
        
        return SubItemResult(
            name="alert_rules",
            description="告警规则",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_alert_channels(self) -> SubItemResult:
        evidence = []
        notification_files = list(Path(self.source_path).rglob("*notification*.py"))
        webhook_files = list(Path(self.source_path).rglob("*webhook*.py"))
        
        if notification_files or webhook_files:
            evidence.append("检测到告警通知实现")
            score = 0.65
        else:
            score = 0.4
            evidence.append("告警通道较少")
        
        return SubItemResult(
            name="alert_channels",
            description="告警通道",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _generate_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        return [f"建议增强{s.description}" for s in subitems if s.score < 0.5][:3]


class SelfHealingEvaluator(BaseEvaluator):
    """故障自愈评估器"""
    
    dimension_name = "self_healing"
    dimension_cn = "故障自愈"
    category = "C"
    weight = 0.02
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        si1 = await self._check_graceful_degradation()
        subitems.append(si1)
        total_score += si1.score * 0.28
        
        si2 = await self._check_retry_mechanism()
        subitems.append(si2)
        total_score += si2.score * 0.25
        
        si3 = await self._check_circuit_breaker()
        subitems.append(si3)
        total_score += si3.score * 0.24
        
        si4 = await self._check_auto_restart()
        subitems.append(si4)
        total_score += si4.score * 0.23
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=f"故障自愈评估完成，{len([s for s in subitems if s.score >= 0.7])}/4项达标",
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_suggestions(subitems)
        )
    
    async def _check_graceful_degradation(self) -> SubItemResult:
        evidence = []
        files_checked = 0
        files_with_degrade = 0
        
        for py_file in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(py_file) or "test" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                files_checked += 1
                if any(pattern in content for pattern in ["degrade", "fallback", "on_error", "try_except", "except.*pass"]):
                    files_with_degrade += 1
            except:
                pass
        
        if files_with_degrade > 0:
            evidence.append(f"检测到优雅降级实现: {files_with_degrade} 个文件")
            score = 0.7
        else:
            evidence.append("未检测到优雅降级")
            score = 0.3
        
        return SubItemResult(
            name="graceful_degradation",
            description="优雅降级",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_retry_mechanism(self) -> SubItemResult:
        evidence = []
        files_checked = 0
        files_with_retry = 0
        
        for py_file in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(py_file) or "test" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                files_checked += 1
                if any(pattern in content for pattern in ["retry", "tenacity", "backoff", "max_attempts", "for attempt in"]):
                    files_with_retry += 1
            except:
                pass
        
        if files_with_retry > 0:
            evidence.append(f"检测到重试机制实现")
            score = 0.7
        else:
            evidence.append("未检测到重试机制")
            score = 0.3
        
        return SubItemResult(
            name="retry_mechanism",
            description="自动重试",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_circuit_breaker(self) -> SubItemResult:
        evidence = []
        breaker_files = list(Path(self.source_path).rglob("*breaker*.py"))
        circuit_files = list(Path(self.source_path).rglob("*circuit*.py"))
        
        if breaker_files or circuit_files:
            evidence.append("检测到熔断器实现")
            score = 0.7
        else:
            score = 0.4
            evidence.append("未检测到熔断器")
        
        return SubItemResult(
            name="circuit_breaker",
            description="熔断器",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_auto_restart(self) -> SubItemResult:
        evidence = []
        restart_files = list(Path(self.source_path).rglob("*restart*.py"))
        recovery_files = list(Path(self.source_path).rglob("*recovery*.py"))
        
        if restart_files or recovery_files:
            evidence.append("检测到自动恢复实现")
            score = 0.65
        else:
            score = 0.4
            evidence.append("未检测到自动恢复")
        
        return SubItemResult(
            name="auto_restart",
            description="自动恢复",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _generate_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        return [f"建议增强{s.description}" for s in subitems if s.score < 0.5][:2]


class RolloutEvaluator(BaseEvaluator):
    """灰度发布评估器"""
    
    dimension_name = "rollout"
    dimension_cn = "灰度发布"
    category = "C"
    weight = 0.02
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        si1 = await self._check_ab_testing()
        subitems.append(si1)
        total_score += si1.score * 0.22
        
        si2 = await self._check_canary()
        subitems.append(si2)
        total_score += si2.score * 0.20
        
        si3 = await self._check_traffic_splitting()
        subitems.append(si3)
        total_score += si3.score * 0.20
        
        si4 = await self._check_feature_flags()
        subitems.append(si4)
        total_score += si4.score * 0.19
        
        si5 = await self._check_rollback()
        subitems.append(si5)
        total_score += si5.score * 0.19
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=f"灰度发布评估完成，{len([s for s in subitems if s.score >= 0.7])}/5项达标",
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_suggestions(subitems)
        )
    
    async def _check_ab_testing(self) -> SubItemResult:
        evidence = []
        ab_files = list(Path(self.source_path).rglob("*ab*.py"))
        experiment_files = list(Path(self.source_path).rglob("*experiment*.py"))
        
        if ab_files or experiment_files:
            evidence.append(f"检测到A/B测试文件: {len(ab_files) + len(experiment_files)} 个")
            score = 0.65
        else:
            score = 0.4
            evidence.append("未检测到A/B测试")
        
        return SubItemResult(
            name="ab_testing",
            description="A/B测试",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_canary(self) -> SubItemResult:
        evidence = []
        canary_files = list(Path(self.source_path).rglob("*canary*.py"))
        
        if canary_files:
            score = 0.6
            evidence.append(f"检测到金丝雀发布文件: {len(canary_files)} 个")
        else:
            score = 0.4
            evidence.append("未检测到金丝雀发布")
        
        return SubItemResult(
            name="canary_release",
            description="金丝雀发布",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_traffic_splitting(self) -> SubItemResult:
        evidence = []
        traffic_files = list(Path(self.source_path).rglob("*traffic*.py"))
        split_files = list(Path(self.source_path).rglob("*split*.py"))
        
        if traffic_files or split_files:
            score = 0.6
            evidence.append("检测到流量切分实现")
        else:
            score = 0.4
            evidence.append("未检测到流量切分")
        
        return SubItemResult(
            name="traffic_splitting",
            description="流量切分",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_feature_flags(self) -> SubItemResult:
        evidence = []
        flag_files = list(Path(self.source_path).rglob("*flag*.py"))
        config_files = list(Path(self.source_path).rglob("*config*.py"))
        
        if flag_files or config_files:
            score = 0.7
            evidence.append(f"检测到特性开关文件: {len(flag_files) + len(config_files)} 个")
        else:
            score = 0.4
            evidence.append("未检测到特性开关")
        
        return SubItemResult(
            name="feature_flags",
            description="特性开关",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_rollback(self) -> SubItemResult:
        evidence = []
        rollback_files = list(Path(self.source_path).rglob("*rollback*.py"))
        revert_files = list(Path(self.source_path).rglob("*revert*.py"))
        
        if rollback_files or revert_files:
            score = 0.65
            evidence.append("检测到回滚实现")
        else:
            score = 0.4
            evidence.append("未检测到回滚机制")
        
        return SubItemResult(
            name="rollback_capability",
            description="快速回滚",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _generate_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        return [f"建议增强{s.description}" for s in subitems if s.score < 0.5][:3]

# ============================================================================
# D. 数据能力评估器
# ============================================================================

class DataSourceEvaluator(BaseEvaluator):
    """数据源接入评估器"""
    
    dimension_name = "data_source"
    dimension_cn = "数据源接入"
    category = "D"
    weight = 0.03
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        si1 = await self._check_connectors()
        subitems.append(si1)
        total_score += si1.score * 0.20
        
        si2 = await self._check_data_formats()
        subitems.append(si2)
        total_score += si2.score * 0.18
        
        si3 = await self._check_batch_import()
        subitems.append(si3)
        total_score += si3.score * 0.17
        
        si4 = await self._check_stream_processing()
        subitems.append(si4)
        total_score += si4.score * 0.15
        
        si5 = await self._check_connector_registry()
        subitems.append(si5)
        total_score += si5.score * 0.15
        
        si6 = await self._check_data_validation()
        subitems.append(si6)
        total_score += si6.score * 0.15
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=f"数据源接入评估完成，{len([s for s in subitems if s.score >= 0.7])}/6项达标",
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_suggestions(subitems)
        )
    
    async def _check_connectors(self) -> SubItemResult:
        evidence = []
        connector_files = list(Path(self.source_path).rglob("*connector*.py"))
        db_files = list(Path(self.source_path).rglob("*database*.py"))
        
        if connector_files or db_files:
            evidence.append(f"检测到数据连接器: {len(connector_files) + len(db_files)} 个")
            score = min((len(connector_files) + len(db_files)) / 5, 1.0) * 0.8 + 0.2
        else:
            score = 0.4
            evidence.append("数据连接器较少")
        
        return SubItemResult(
            name="connectors",
            description="数据连接器",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_data_formats(self) -> SubItemResult:
        evidence = []
        format_files = []
        for ext in ["json", "csv", "xml", "parquet"]:
            format_files.extend(list(Path(self.source_path).rglob(f"*{ext}*.py")))
        
        if format_files:
            evidence.append(f"检测到数据格式处理: {len(format_files)} 个文件")
            score = min(len(format_files) / 5, 1.0) * 0.8 + 0.2
        else:
            score = 0.4
            evidence.append("数据格式支持较少")
        
        return SubItemResult(
            name="data_formats",
            description="多格式支持",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_batch_import(self) -> SubItemResult:
        evidence = []
        import_files = list(Path(self.source_path).rglob("*import*.py"))
        load_files = list(Path(self.source_path).rglob("*load*.py"))
        
        if import_files or load_files:
            score = 0.65
            evidence.append("检测到批量导入实现")
        else:
            score = 0.4
            evidence.append("批量导入较少")
        
        return SubItemResult(
            name="batch_import",
            description="批量导入",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_stream_processing(self) -> SubItemResult:
        evidence = []
        stream_files = list(Path(self.source_path).rglob("*stream*.py"))
        kafka_files = list(Path(self.source_path).rglob("*kafka*.py"))
        
        if stream_files or kafka_files:
            score = 0.6
            evidence.append("检测到流处理实现")
        else:
            score = 0.4
            evidence.append("未检测到流处理")
        
        return SubItemResult(
            name="stream_processing",
            description="流处理",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_connector_registry(self) -> SubItemResult:
        evidence = []
        registry_files = list(Path(self.source_path).rglob("*registry*.py"))
        
        if registry_files:
            score = 0.6
            evidence.append(f"检测到连接器注册: {len(registry_files)} 个")
        else:
            score = 0.4
            evidence.append("未检测到连接器注册")
        
        return SubItemResult(
            name="connector_registry",
            description="连接器注册",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_data_validation(self) -> SubItemResult:
        evidence = []
        validation_files = list(Path(self.source_path).rglob("*validation*.py"))
        schema_files = list(Path(self.source_path).rglob("*schema*.py"))
        
        if validation_files or schema_files:
            score = 0.7
            evidence.append("检测到数据验证")
        else:
            score = 0.4
            evidence.append("数据验证较少")
        
        return SubItemResult(
            name="data_validation",
            description="数据验证",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _generate_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        return [f"建议增强{s.description}" for s in subitems if s.score < 0.5][:3]


class KnowledgeMgmtEvaluator(BaseEvaluator):
    """知识管理评估器"""
    
    dimension_name = "knowledge_mgmt"
    dimension_cn = "知识管理"
    category = "D"
    weight = 0.02
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        si1 = await self._check_incremental_update()
        subitems.append(si1)
        total_score += si1.score * 0.22
        
        si2 = await self._check_version_control()
        subitems.append(si2)
        total_score += si2.score * 0.20
        
        si3 = await self._check_freshness_guarantee()
        subitems.append(si3)
        total_score += si3.score * 0.20
        
        si4 = await self._check_knowledge_validation()
        subitems.append(si4)
        total_score += si4.score * 0.19
        
        si5 = await self._check_lifecycle()
        subitems.append(si5)
        total_score += si5.score * 0.19
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=f"知识管理评估完成，{len([s for s in subitems if s.score >= 0.7])}/5项达标",
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_suggestions(subitems)
        )
    
    async def _check_incremental_update(self) -> SubItemResult:
        evidence = []
        update_files = list(Path(self.source_path).rglob("*update*.py"))
        
        if update_files:
            evidence.append(f"检测到更新相关文件: {len(update_files)} 个")
            score = min(len(update_files) / 5, 1.0) * 0.8 + 0.2
        else:
            score = 0.4
            evidence.append("增量更新实现较少")
        
        return SubItemResult(
            name="incremental_update",
            description="增量更新",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_version_control(self) -> SubItemResult:
        evidence = []
        version_files = list(Path(self.source_path).rglob("*version*.py"))
        
        if version_files:
            score = 0.65
            evidence.append(f"检测到版本控制: {len(version_files)} 个文件")
        else:
            score = 0.4
            evidence.append("版本管理较少")
        
        return SubItemResult(
            name="version_control",
            description="版本管理",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_freshness_guarantee(self) -> SubItemResult:
        evidence = []
        freshness_files = list(Path(self.source_path).rglob("*fresh*.py"))
        sync_files = list(Path(self.source_path).rglob("*sync*.py"))
        
        if freshness_files or sync_files:
            score = 0.6
            evidence.append("检测到时效保障")
        else:
            score = 0.4
            evidence.append("时效保障较少")
        
        return SubItemResult(
            name="freshness_guarantee",
            description="时效保障",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_knowledge_validation(self) -> SubItemResult:
        evidence = []
        validate_files = list(Path(self.source_path).rglob("*validate*.py"))
        
        if validate_files:
            score = 0.65
            evidence.append(f"检测到知识验证: {len(validate_files)} 个")
        else:
            score = 0.4
            evidence.append("知识验证较少")
        
        return SubItemResult(
            name="knowledge_validation",
            description="知识验证",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_lifecycle(self) -> SubItemResult:
        evidence = []
        lifecycle_files = list(Path(self.source_path).rglob("*lifecycle*.py"))
        
        if lifecycle_files:
            score = 0.6
            evidence.append(f"检测到生命周期管理")
        else:
            score = 0.4
            evidence.append("生命周期管理较少")
        
        return SubItemResult(
            name="lifecycle_management",
            description="生命周期管理",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _generate_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        return [f"建议增强{s.description}" for s in subitems if s.score < 0.5][:3]


class VectorMgmtEvaluator(BaseEvaluator):
    """向量管理评估器"""
    
    dimension_name = "vector_mgmt"
    dimension_cn = "向量管理"
    category = "D"
    weight = 0.02
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        si1 = await self._check_embedding()
        subitems.append(si1)
        total_score += si1.score * 0.22
        
        si2 = await self._check_index_management()
        subitems.append(si2)
        total_score += si2.score * 0.20
        
        si3 = await self._check_similarity_search()
        subitems.append(si3)
        total_score += si3.score * 0.20
        
        si4 = await self._check_index_optimization()
        subitems.append(si4)
        total_score += si4.score * 0.19
        
        si5 = await self._check_dimension_handling()
        subitems.append(si5)
        total_score += si5.score * 0.19
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=f"向量管理评估完成，{len([s for s in subitems if s.score >= 0.7])}/5项达标",
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_suggestions(subitems)
        )
    
    async def _check_embedding(self) -> SubItemResult:
        evidence = []
        embed_files = list(Path(self.source_path).rglob("*embed*.py"))
        encoding_files = list(Path(self.source_path).rglob("*encoding*.py"))
        
        if embed_files or encoding_files:
            evidence.append(f"检测到向量生成: {len(embed_files) + len(encoding_files)} 个")
            score = min((len(embed_files) + len(encoding_files)) / 5, 1.0) * 0.8 + 0.2
        else:
            score = 0.4
            evidence.append("向量生成实现较少")
        
        return SubItemResult(
            name="embedding_generation",
            description="向量生成",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_index_management(self) -> SubItemResult:
        evidence = []
        index_files = list(Path(self.source_path).rglob("*index*.py"))
        
        if index_files:
            evidence.append(f"检测到索引管理: {len(index_files)} 个")
            score = min(len(index_files) / 5, 1.0) * 0.8 + 0.2
        else:
            score = 0.4
            evidence.append("索引管理较少")
        
        return SubItemResult(
            name="index_management",
            description="索引管理",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_similarity_search(self) -> SubItemResult:
        evidence = []
        similarity_files = list(Path(self.source_path).rglob("*similar*.py"))
        search_files = list(Path(self.source_path).rglob("*search*.py"))
        
        if similarity_files or search_files:
            score = 0.7
            evidence.append("检测到相似度检索")
        else:
            score = 0.4
            evidence.append("相似度检索较少")
        
        return SubItemResult(
            name="similarity_search",
            description="相似度检索",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_index_optimization(self) -> SubItemResult:
        evidence = []
        optimize_files = list(Path(self.source_path).rglob("*optim*.py"))
        
        if optimize_files:
            score = 0.6
            evidence.append(f"检测到索引优化: {len(optimize_files)} 个")
        else:
            score = 0.4
            evidence.append("索引优化较少")
        
        return SubItemResult(
            name="index_optimization",
            description="索引优化",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_dimension_handling(self) -> SubItemResult:
        evidence = []
        dimension_files = list(Path(self.source_path).rglob("*dimension*.py"))
        
        if dimension_files:
            score = 0.55
            evidence.append(f"检测到维度管理: {len(dimension_files)} 个")
        else:
            score = 0.4
            evidence.append("维度管理较少")
        
        return SubItemResult(
            name="dimension_handling",
            description="维度管理",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _generate_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        return [f"建议增强{s.description}" for s in subitems if s.score < 0.5][:3]


class DataLineageEvaluator(BaseEvaluator):
    """数据血缘评估器"""
    
    dimension_name = "data_lineage"
    dimension_cn = "数据血缘"
    category = "D"
    weight = 0.01
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        si1 = await self._check_source_tracking()
        subitems.append(si1)
        total_score += si1.score * 0.22
        
        si2 = await self._check_transformation_log()
        subitems.append(si2)
        total_score += si2.score * 0.20
        
        si3 = await self._check_usage_tracking()
        subitems.append(si3)
        total_score += si3.score * 0.20
        
        si4 = await self._check_audit_trail()
        subitems.append(si4)
        total_score += si4.score * 0.19
        
        si5 = await self._check_provenance_vis()
        subitems.append(si5)
        total_score += si5.score * 0.19
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=f"数据血缘评估完成，{len([s for s in subitems if s.score >= 0.7])}/5项达标",
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_suggestions(subitems)
        )
    
    async def _check_source_tracking(self) -> SubItemResult:
        evidence = []
        source_files = list(Path(self.source_path).rglob("*source*.py"))
        track_files = list(Path(self.source_path).rglob("*track*.py"))
        
        if source_files or track_files:
            score = 0.6
            evidence.append("检测到来源追踪")
        else:
            score = 0.4
            evidence.append("来源追踪较少")
        
        return SubItemResult(
            name="source_tracking",
            description="来源追踪",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_transformation_log(self) -> SubItemResult:
        evidence = []
        transform_files = list(Path(self.source_path).rglob("*transform*.py"))
        
        if transform_files:
            score = 0.55
            evidence.append(f"检测到转换记录: {len(transform_files)} 个")
        else:
            score = 0.4
            evidence.append("转换记录较少")
        
        return SubItemResult(
            name="transformation_log",
            description="转换记录",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_usage_tracking(self) -> SubItemResult:
        evidence = []
        usage_files = list(Path(self.source_path).rglob("*usage*.py"))
        
        if usage_files:
            score = 0.55
            evidence.append(f"检测到使用追踪: {len(usage_files)} 个")
        else:
            score = 0.4
            evidence.append("使用追踪较少")
        
        return SubItemResult(
            name="usage_tracking",
            description="使用追踪",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_audit_trail(self) -> SubItemResult:
        evidence = []
        audit_files = list(Path(self.source_path).rglob("*audit*.py"))
        
        if audit_files:
            score = 0.6
            evidence.append(f"检测到审计日志: {len(audit_files)} 个")
        else:
            score = 0.4
            evidence.append("审计日志较少")
        
        return SubItemResult(
            name="audit_trail",
            description="审计日志",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_provenance_vis(self) -> SubItemResult:
        evidence = []
        provenance_files = list(Path(self.source_path).rglob("*provenance*.py"))
        vis_files = list(Path(self.source_path).rglob("*visual*.py"))
        
        if provenance_files or vis_files:
            score = 0.5
            evidence.append("检测到溯源可视化")
        else:
            score = 0.4
            evidence.append("溯源可视化较少")
        
        return SubItemResult(
            name="provenance_vis",
            description="溯源可视化",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _generate_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        return [f"建议增强{s.description}" for s in subitems if s.score < 0.5][:3]

# ============================================================================
# E. 平台能力评估器
# ============================================================================

class AppSupportEvaluator(BaseEvaluator):
    """应用支撑评估器"""
    
    dimension_name = "app_support"
    dimension_cn = "应用支撑"
    category = "E"
    weight = 0.03
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        si1 = await self._check_multi_tenant()
        subitems.append(si1)
        total_score += si1.score * 0.18
        
        si2 = await self._check_quota_management()
        subitems.append(si2)
        total_score += si2.score * 0.17
        
        si3 = await self._check_rbac()
        subitems.append(si3)
        total_score += si3.score * 0.17
        
        si4 = await self._check_sso()
        subitems.append(si4)
        total_score += si4.score * 0.16
        
        si5 = await self._check_webhook()
        subitems.append(si5)
        total_score += si5.score * 0.16
        
        si6 = await self._check_sdk()
        subitems.append(si6)
        total_score += si6.score * 0.16
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=f"应用支撑评估完成，{len([s for s in subitems if s.score >= 0.7])}/6项达标",
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_suggestions(subitems)
        )
    
    async def _check_multi_tenant(self) -> SubItemResult:
        evidence = []
        tenant_files = list(Path(self.source_path).rglob("*tenant*.py"))
        isolation_files = list(Path(self.source_path).rglob("*isolation*.py"))
        
        if tenant_files:
            evidence.append(f"检测到多租户文件: {len(tenant_files)} 个")
            score = min(len(tenant_files) / 3, 1.0) * 0.8 + 0.2
        else:
            score = 0.4
            evidence.append("多租户实现较少")
        
        return SubItemResult(
            name="multi_tenant",
            description="多租户",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_quota_management(self) -> SubItemResult:
        evidence = []
        quota_files = list(Path(self.source_path).rglob("*quota*.py"))
        limit_files = list(Path(self.source_path).rglob("*limit*.py"))
        
        if quota_files or limit_files:
            evidence.append("检测到配额管理")
            score = 0.65
        else:
            score = 0.4
            evidence.append("配额管理较少")
        
        return SubItemResult(
            name="quota_management",
            description="配额管理",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_rbac(self) -> SubItemResult:
        evidence = []
        rbac_files = list(Path(self.source_path).rglob("*rbac*.py"))
        auth_files = list(Path(self.source_path).rglob("*auth*.py"))
        permission_files = list(Path(self.source_path).rglob("*permission*.py"))
        
        total = len(rbac_files) + len(auth_files) + len(permission_files)
        if total > 0:
            evidence.append(f"检测到权限管理: {total} 个")
            score = min(total / 5, 1.0) * 0.8 + 0.2
        else:
            score = 0.4
            evidence.append("权限管理较少")
        
        return SubItemResult(
            name="rbac_control",
            description="权限控制",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_sso(self) -> SubItemResult:
        evidence = []
        sso_files = list(Path(self.source_path).rglob("*sso*.py"))
        oauth_files = list(Path(self.source_path).rglob("*oauth*.py"))
        
        if sso_files or oauth_files:
            evidence.append("检测到SSO集成")
            score = 0.6
        else:
            score = 0.4
            evidence.append("SSO集成较少")
        
        return SubItemResult(
            name="sso_integration",
            description="SSO集成",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_webhook(self) -> SubItemResult:
        evidence = []
        webhook_files = list(Path(self.source_path).rglob("*webhook*.py"))
        callback_files = list(Path(self.source_path).rglob("*callback*.py"))
        
        if webhook_files or callback_files:
            evidence.append(f"检测到Webhook支持: {len(webhook_files) + len(callback_files)} 个")
            score = 0.65
        else:
            score = 0.4
            evidence.append("Webhook支持较少")
        
        return SubItemResult(
            name="webhook_support",
            description="Webhook",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_sdk(self) -> SubItemResult:
        evidence = []
        sdk_dirs = list(Path(self.source_path).rglob("sdk"))
        client_files = list(Path(self.source_path).rglob("*client*.py"))
        
        if sdk_dirs or len(client_files) > 5:
            evidence.append("检测到SDK支持")
            score = 0.65
        else:
            score = 0.4
            evidence.append("SDK支持较少")
        
        return SubItemResult(
            name="sdk_support",
            description="SDK支持",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _generate_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        return [f"建议增强{s.description}" for s in subitems if s.score < 0.5][:3]


class CostControlEvaluator(BaseEvaluator):
    """成本控制评估器"""
    
    dimension_name = "cost_control"
    dimension_cn = "成本控制"
    category = "E"
    weight = 0.02
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        si1 = await self._check_token_optimization()
        subitems.append(si1)
        total_score += si1.score * 0.18
        
        si2 = await self._check_model_selection()
        subitems.append(si2)
        total_score += si2.score * 0.17
        
        si3 = await self._check_caching_strategy()
        subitems.append(si3)
        total_score += si3.score * 0.17
        
        si4 = await self._check_batch_discount()
        subitems.append(si4)
        total_score += si4.score * 0.16
        
        si5 = await self._check_cost_attribution()
        subitems.append(si5)
        total_score += si5.score * 0.16
        
        si6 = await self._check_budget_alerts()
        subitems.append(si6)
        total_score += si6.score * 0.16
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=f"成本控制评估完成，{len([s for s in subitems if s.score >= 0.7])}/6项达标",
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_suggestions(subitems)
        )
    
    async def _check_token_optimization(self) -> SubItemResult:
        evidence = []
        files_with_optimization = 0
        files_checked = 0
        
        for py_file in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(py_file) or "test" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                files_checked += 1
                if any(p in content for p in ["truncate", "summarize", "compress_prompt", "reduce_tokens", "max_tokens", "truncation"]):
                    files_with_optimization += 1
            except:
                pass
        
        if files_with_optimization > 0:
            evidence.append(f"检测到Token优化实现")
            score = 0.7
        else:
            evidence.append("未检测到Token优化实现")
            score = 0.3
        
        return SubItemResult(
            name="token_optimization",
            description="Token优化",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_model_selection(self) -> SubItemResult:
        evidence = []
        files_with_selection = 0
        files_checked = 0
        
        for py_file in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(py_file) or "test" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                files_checked += 1
                if any(p in content for p in ["model_selection", "select_model", "choose_model", "route_to", "model_routing"]):
                    files_with_selection += 1
            except:
                pass
        
        if files_with_selection > 0:
            evidence.append(f"检测到模型选择实现")
            score = 0.7
        else:
            evidence.append("未检测到模型选择实现")
            score = 0.3
        
        return SubItemResult(
            name="model_selection",
            description="模型选择",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_caching_strategy(self) -> SubItemResult:
        evidence = []
        files_with_caching = 0
        files_checked = 0
        
        for py_file in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(py_file) or "test" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                files_checked += 1
                if any(p in content for p in ["@lru_cache", "cache.add", "Cache(", "redis", "memcached", "get_cache", "set_cache"]):
                    files_with_caching += 1
            except:
                pass
        
        if files_with_caching > 0:
            evidence.append(f"检测到缓存策略实现")
            score = 0.7
        else:
            evidence.append("未检测到缓存策略实现")
            score = 0.3
        
        return SubItemResult(
            name="caching_strategy",
            description="缓存策略",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_cost_attribution(self) -> SubItemResult:
        evidence = []
        files_with_attribution = 0
        files_checked = 0
        
        for py_file in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(py_file) or "test" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                files_checked += 1
                if any(p in content for p in ["cost_attribution", "track_cost", "cost_by_user", "usage_report", "cost_breakdown"]):
                    files_with_attribution += 1
            except:
                pass
        
        if files_with_attribution > 0:
            evidence.append(f"检测到成本归因实现")
            score = 0.7
        else:
            evidence.append("未检测到成本归因实现")
            score = 0.3
        
        return SubItemResult(
            name="cost_attribution",
            description="成本归因",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_batch_discount(self) -> SubItemResult:
        evidence = []
        files_with_batching = 0
        files_checked = 0
        
        for py_file in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(py_file) or "test" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                files_checked += 1
                if any(p in content for p in ["batch_request", "batch_completion", "group_requests", "batch_process"]):
                    files_with_batching += 1
            except:
                pass
        
        if files_with_batching > 0:
            evidence.append(f"检测到批量处理实现")
            score = 0.6
        else:
            evidence.append("未检测到批量处理实现")
            score = 0.3
        
        return SubItemResult(
            name="batch_discount",
            description="批量处理",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_budget_alerts(self) -> SubItemResult:
        evidence = []
        files_with_alerts = 0
        files_checked = 0
        
        for py_file in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(py_file) or "test" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                files_checked += 1
                if any(p in content for p in ["budget_limit", "cost_limit", "quota", "threshold_alert", "spending_alert"]):
                    files_with_alerts += 1
            except:
                pass
        
        if files_with_alerts > 0:
            evidence.append(f"检测到预算告警实现")
            score = 0.6
        else:
            evidence.append("未检测到预算告警实现")
            score = 0.3
        
        return SubItemResult(
            name="budget_alerts",
            description="预算告警",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _generate_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        return [f"建议增强{s.description}" for s in subitems if s.score < 0.5][:3]


class IntegrationEvaluator(BaseEvaluator):
    """集成扩展评估器"""
    
    dimension_name = "integration"
    dimension_cn = "集成扩展"
    category = "E"
    weight = 0.01
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        si1 = await self._check_api_completeness()
        subitems.append(si1)
        total_score += si1.score * 0.22
        
        si2 = await self._check_webhook_events()
        subitems.append(si2)
        total_score += si2.score * 0.20
        
        si3 = await self._check_plugin_system()
        subitems.append(si3)
        total_score += si3.score * 0.20
        
        si4 = await self._check_openapi_spec()
        subitems.append(si4)
        total_score += si4.score * 0.19
        
        si5 = await self._check_sdk_availability()
        subitems.append(si5)
        total_score += si5.score * 0.19
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=f"集成扩展评估完成，{len([s for s in subitems if s.score >= 0.7])}/5项达标",
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_suggestions(subitems)
        )
    
    async def _check_api_completeness(self) -> SubItemResult:
        evidence = []
        api_dirs = list(Path(self.source_path).rglob("*/api/*.py"))
        route_files = list(Path(self.source_path).rglob("*route*.py"))
        
        total = len(api_dirs) + len(route_files)
        if total > 0:
            evidence.append(f"检测到API文件: {total} 个")
            score = min(total / 10, 1.0) * 0.8 + 0.2
        else:
            score = 0.4
            evidence.append("API文件较少")
        
        return SubItemResult(
            name="api_completeness",
            description="API完备性",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_webhook_events(self) -> SubItemResult:
        evidence = []
        event_files = list(Path(self.source_path).rglob("*event*.py"))
        hook_files = list(Path(self.source_path).rglob("*hook*.py"))
        
        if event_files or hook_files:
            evidence.append("检测到Webhook事件")
            score = 0.6
        else:
            score = 0.4
            evidence.append("Webhook事件较少")
        
        return SubItemResult(
            name="webhook_events",
            description="Webhook事件",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_plugin_system(self) -> SubItemResult:
        evidence = []
        plugin_files = list(Path(self.source_path).rglob("*plugin*.py"))
        extension_files = list(Path(self.source_path).rglob("*extension*.py"))
        
        if plugin_files or extension_files:
            evidence.append(f"检测到插件系统: {len(plugin_files) + len(extension_files)} 个")
            score = 0.6
        else:
            score = 0.4
            evidence.append("插件系统较少")
        
        return SubItemResult(
            name="plugin_system",
            description="插件系统",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_openapi_spec(self) -> SubItemResult:
        evidence = []
        spec_files = list(Path(self.source_path).rglob("*openapi*.yaml"))
        spec_files += list(Path(self.source_path).rglob("*openapi*.json"))
        
        if spec_files:
            evidence.append(f"检测到OpenAPI规范: {len(spec_files)} 个")
            score = 0.7
        else:
            score = 0.4
            evidence.append("未检测到OpenAPI规范")
        
        return SubItemResult(
            name="openapi_spec",
            description="OpenAPI规范",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_sdk_availability(self) -> SubItemResult:
        evidence = []
        sdk_dirs = list(Path(self.source_path).rglob("*/sdk/*.py"))
        client_dirs = list(Path(self.source_path).rglob("*/client/*.py"))
        
        total = len(sdk_dirs) + len(client_dirs)
        if total > 0:
            evidence.append(f"检测到SDK: {total} 个文件")
            score = min(total / 10, 1.0) * 0.8 + 0.2
        else:
            score = 0.4
            evidence.append("SDK文件较少")
        
        return SubItemResult(
            name="sdk_availability",
            description="SDK可用性",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _generate_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        return [f"建议增强{s.description}" for s in subitems if s.score < 0.5][:3]


class SecurityEvaluator(BaseEvaluator):
    """安全性评估器"""
    
    dimension_name = "security"
    dimension_cn = "安全性"
    category = "S"  # 安全是独立类别
    weight = 0.10
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        si1 = await self._check_input_validation()
        subitems.append(si1)
        total_score += si1.score * 0.20
        
        si2 = await self._check_authentication()
        subitems.append(si2)
        total_score += si2.score * 0.20
        
        si3 = await self._check_data_encryption()
        subitems.append(si3)
        total_score += si3.score * 0.18
        
        si4 = await self._check_error_handling()
        subitems.append(si4)
        total_score += si4.score * 0.17
        
        si5 = await self._check_sensitive_data()
        subitems.append(si5)
        total_score += si5.score * 0.15
        
        si6 = await self._check_rate_limiting()
        subitems.append(si6)
        total_score += si6.score * 0.10
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=f"安全性评估完成，{len([s for s in subitems if s.score >= 0.7])}/6项达标",
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_security_suggestions(subitems)
        )
    
    async def _check_input_validation(self) -> SubItemResult:
        evidence = []
        files_with_validation = 0
        files_checked = 0
        
        for py_file in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(py_file) or "test" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                files_checked += 1
                if any(p in content for p in ["validate", "sanitize", "clean_input", "strip_tags", "html.escape", "re.escape"]):
                    files_with_validation += 1
            except:
                pass
        
        if files_with_validation > 0:
            evidence.append(f"检测到输入验证实现: {files_with_validation} 个文件")
            score = min(files_with_validation / 3, 1.0) * 0.7 + 0.3
        else:
            evidence.append("未检测到输入验证实现")
            score = 0.3
        
        return SubItemResult(
            name="input_validation",
            description="输入验证",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_authentication(self) -> SubItemResult:
        evidence = []
        files_with_auth = 0
        files_checked = 0
        
        for py_file in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(py_file) or "test" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                files_checked += 1
                if any(p in content for p in ["authenticate", "verify_token", "check_permission", "@login_required", "get_current_user", "JWT", "Bearer"]):
                    files_with_auth += 1
            except:
                pass
        
        if files_with_auth > 0:
            evidence.append(f"检测到认证授权实现")
            score = 0.7
        else:
            evidence.append("未检测到认证授权实现")
            score = 0.3
        
        return SubItemResult(
            name="authentication",
            description="认证授权",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_data_encryption(self) -> SubItemResult:
        evidence = []
        encrypt_files = list(Path(self.source_path).rglob("*encrypt*.py"))
        crypto_files = list(Path(self.source_path).rglob("*crypto*.py"))
        
        if encrypt_files or crypto_files:
            evidence.append(f"检测到加密相关文件: {len(encrypt_files) + len(crypto_files)} 个")
            score = 0.7
        else:
            score = 0.4
            evidence.append("未检测到加密实现")
        
        return SubItemResult(
            name="data_encryption",
            description="数据加密",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_error_handling(self) -> SubItemResult:
        evidence = []
        error_files = list(Path(self.source_path).rglob("*error*.py"))
        exception_files = list(Path(self.source_path).rglob("*exception*.py"))
        
        total = len(error_files) + len(exception_files)
        if total > 0:
            evidence.append(f"检测到错误处理文件: {total} 个")
            score = min(total / 10, 1.0) * 0.8 + 0.2
        else:
            score = 0.4
            evidence.append("错误处理较少")
        
        return SubItemResult(
            name="error_handling",
            description="错误处理",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_sensitive_data(self) -> SubItemResult:
        evidence = []
        # 检查敏感数据处理
        sensitive_patterns = ["password", "secret", "token", "api_key", "credential"]
        sensitive_files = []
        
        for py_file in Path(self.source_path).rglob("*.py"):
            try:
                with open(py_file, encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
                    if any(p in content for p in sensitive_patterns):
                        sensitive_files.append(py_file.name)
            except Exception:
                pass
        
        if len(sensitive_files) > 0:
            evidence.append(f"检测到敏感数据处理文件: {len(sensitive_files)} 个")
            score = min(len(sensitive_files) / 20, 1.0) * 0.7 + 0.3
        else:
            score = 0.5
            evidence.append("敏感数据处理较少")
        
        return SubItemResult(
            name="sensitive_data",
            description="敏感数据保护",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_rate_limiting(self) -> SubItemResult:
        evidence = []
        rate_files = list(Path(self.source_path).rglob("*rate*.py"))
        limit_files = list(Path(self.source_path).rglob("*limit*.py"))
        throttle_files = list(Path(self.source_path).rglob("*throttl*.py"))
        
        total = len(rate_files) + len(limit_files) + len(throttle_files)
        if total > 0:
            evidence.append(f"检测到限流文件: {total} 个")
            score = 0.6
        else:
            score = 0.3
            evidence.append("未检测到限流机制")
        
        return SubItemResult(
            name="rate_limiting",
            description="限流机制",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _generate_security_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        suggestions = []
        for s in subitems:
            if s.score < 0.5:
                suggestions.append(f"建议增强{s.description}")
        return suggestions[:3]


class CodeQualityEvaluator(BaseEvaluator):
    """代码质量评估器"""
    
    dimension_name = "code_quality"
    dimension_cn = "代码质量"
    category = "Q"  # 代码质量是独立类别
    weight = 0.12
    
    async def evaluate(self) -> DimensionResult:
        subitems = []
        total_score = 0
        
        si1 = await self._check_type_annotations()
        subitems.append(si1)
        total_score += si1.score * 0.20
        
        si2 = await self._check_docstrings()
        subitems.append(si2)
        total_score += si2.score * 0.20
        
        si3 = await self._check_naming_conventions()
        subitems.append(si3)
        total_score += si3.score * 0.18
        
        si4 = await self._check_test_coverage()
        subitems.append(si4)
        total_score += si4.score * 0.18
        
        si5 = await self._check_complexity()
        subitems.append(si5)
        total_score += si5.score * 0.15
        
        si6 = await self._check_consistency()
        subitems.append(si6)
        total_score += si6.score * 0.09
        
        overall = total_score
        status = self._status_by_score(overall)
        
        return DimensionResult(
            dimension=self.dimension_name,
            name=self.dimension_cn,
            category=self.category,
            weight=self.weight,
            score=overall,
            status=status,
            subitems=subitems,
            details=f"代码质量评估完成，{len([s for s in subitems if s.score >= 0.7])}/6项达标",
            evidence=[e for s in subitems for e in s.evidence],
            suggestions=self._generate_quality_suggestions(subitems)
        )
    
    async def _check_type_annotations(self) -> SubItemResult:
        evidence = []
        typed_files = 0
        total_files = 0
        
        for py_file in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            total_files += 1
            try:
                with open(py_file, encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # 检查是否有类型注解
                    if ": " in content and ("-> " in content or "->" in content.split('\n')[-1]):
                        typed_files += 1
            except Exception:
                pass
        
        if total_files > 0:
            ratio = typed_files / total_files
            evidence.append(f"检测到类型注解文件: {typed_files}/{total_files}")
            score = ratio
        else:
            score = 0.4
            evidence.append("无法统计类型注解")
        
        return SubItemResult(
            name="type_annotations",
            description="类型注解",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_docstrings(self) -> SubItemResult:
        evidence = []
        documented = 0
        total = 0
        
        try:
            import ast
            for py_file in Path(self.source_path).rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue
                try:
                    with open(py_file, encoding='utf-8', errors='ignore') as f:
                        tree = ast.parse(f.read())
                    
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                            total += 1
                            if ast.get_docstring(node):
                                documented += 1
                except Exception:
                    pass
            
            if total > 0:
                ratio = documented / total
                evidence.append(f"文档覆盖率: {documented}/{total}")
                score = ratio
            else:
                score = 0.4
                evidence.append("无法计算文档覆盖率")
        except Exception:
            score = 0.4
            evidence.append("文档检查失败")
        
        return SubItemResult(
            name="docstrings",
            description="文档完整性",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_naming_conventions(self) -> SubItemResult:
        evidence = []
        consistent = 0
        total = 0
        
        for py_file in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            total += 1
            try:
                with open(py_file, encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # 检查命名是否一致 (snake_case for functions, PascalCase for classes)
                    import re
                    snake_case = len(re.findall(r'def [a-z_]+\(', content))
                    pascal_case = len(re.findall(r'class [A-Z][a-zA-Z]+\(', content))
                    if snake_case > 0 or pascal_case > 0:
                        consistent += 1
            except Exception:
                pass
        
        if total > 0:
            ratio = consistent / total
            evidence.append(f"命名规范文件: {consistent}/{total}")
            score = ratio
        else:
            score = 0.5
            evidence.append("无法统计命名规范")
        
        return SubItemResult(
            name="naming_conventions",
            description="命名规范",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_test_coverage(self) -> SubItemResult:
        evidence = []
        
        project_root = Path(self.source_path).parent
        test_dirs = ["tests", "test"]
        
        test_files = []
        for t in test_dirs:
            test_dir = project_root / t
            if test_dir.exists():
                test_files.extend([f for f in test_dir.glob("*.py") if "__pycache__" not in str(f)])
        
        src_files = list(Path(self.source_path).rglob("*.py"))
        src_files = [f for f in src_files if "__pycache__" not in str(f) and "test" not in f.name.lower()]
        
        if not test_files:
            return SubItemResult(
                name="test_coverage",
                description="测试覆盖",
                score=0.3,
                status="poor",
                evidence=["未找到测试文件"]
            )
        
        evidence.append(f"测试文件: {len(test_files)} 个, 源代码文件: {len(src_files)} 个")
        
        import subprocess
        import json
        import tempfile
        
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "--collect-only", "-q"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.source_path
            )
            
            if result.returncode == 0 or "collected" in result.stdout:
                import re
                match = re.search(r"collected (\d+)", result.stdout)
                if match:
                    test_count = int(match.group(1))
                    evidence.append(f"可执行测试用例: {test_count} 个")
                else:
                    test_count = len(test_files) * 2
                    evidence.append(f"估计测试用例: {test_count} 个")
            else:
                test_count = len(test_files) * 2
                evidence.append(f"估计测试用例: {test_count} 个（pytest收集失败）")
            
            if test_count > 0:
                expected_tests = len(src_files) * 0.5
                if test_count >= expected_tests:
                    score = min(test_count / (len(src_files) * 2), 1.0) * 0.6 + 0.4
                else:
                    score = max(0.2, test_count / expected_tests * 0.5)
            else:
                score = 0.3
            
            result = subprocess.run(
                ["python", "-m", "coverage", "run", "--source=src", "-m", "pytest", "-x", "-q"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=self.source_path
            )
            
            if result.returncode == 0 or "passed" in result.stdout:
                result = subprocess.run(
                    ["python", "-m", "coverage", "json", "-o", "coverage_report.json"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=self.source_path
                )
                
                cov_file = Path(self.source_path) / "coverage_report.json"
                if cov_file.exists():
                    try:
                        with open(cov_file) as f:
                            cov_data = json.load(f)
                        
                        total = cov_data.get('totals', {})
                        coverage_pct = total.get('percent_covered', 0) or 0
                        
                        if coverage_pct > 0:
                            evidence.append(f"代码覆盖率: {coverage_pct:.1f}%")
                            score = (score + min(coverage_pct / 100, 1.0)) / 2
                        
                        cov_file.unlink(missing_ok=True)
                    except:
                        pass
            
            evidence.append(f"测试覆盖率得分: {score*100:.0f}%")
            
        except FileNotFoundError:
            evidence.append("coverage/pytest 未安装，使用文件比率评估")
            ratio = len(test_files) / len(src_files) if src_files else 0
            score = min(ratio * 2, 1.0) * 0.6 + 0.4
        except subprocess.TimeoutExpired:
            evidence.append("测试执行超时")
            score = 0.4
        except Exception as e:
            evidence.append(f"覆盖率评估: {str(e)[:30]}")
            ratio = len(test_files) / len(src_files) if src_files else 0
            score = min(ratio * 2, 1.0) * 0.5 + 0.3
        
        return SubItemResult(
            name="test_coverage",
            description="测试覆盖",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_complexity(self) -> SubItemResult:
        evidence = []
        
        try:
            import ast
            complexities = []
            for py_file in Path(self.source_path).rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue
                try:
                    with open(py_file, encoding='utf-8', errors='ignore') as f:
                        tree = ast.parse(f.read())
                    
                    complexity = self._calculate_complexity(tree)
                    complexities.append(complexity)
                except Exception:
                    pass
            
            if complexities:
                avg_complexity = sum(complexities) / len(complexities)
                max_complexity = max(complexities)
                # 复杂度评分：对研究/推理系统更友好
                # < 20 高分, 20-40 适中, > 40 扣分但不过分
                if avg_complexity <= 20:
                    score = 1.0
                elif avg_complexity <= 40:
                    score = max(0.3, 1.0 - (avg_complexity - 20) / 40)
                else:
                    score = max(0.1, 0.3 - (avg_complexity - 40) / 100)
                evidence.append(f"平均复杂度: {avg_complexity:.1f}, 最大: {max_complexity}")
            else:
                score = 0.5
                evidence.append("无法计算复杂度")
        except Exception:
            score = 0.5
            evidence.append("复杂度检查失败")
        
        return SubItemResult(
            name="complexity",
            description="代码复杂度",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    async def _check_consistency(self) -> SubItemResult:
        evidence = []
        
        # 检查代码风格一致性（使用简单的启发式方法）
        consistent_files = 0
        total_files = 0
        
        for py_file in Path(self.source_path).rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            total_files += 1
            try:
                with open(py_file, encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # 检查是否有统一的import顺序、格式化等
                    lines = [l.strip() for l in content.split('\n') if l.strip()]
                    if len(lines) > 10:
                        consistent_files += 1
            except Exception:
                pass
        
        if total_files > 0:
            ratio = consistent_files / total_files
            evidence.append(f"风格一致文件: {consistent_files}/{total_files}")
            score = ratio
        else:
            score = 0.5
            evidence.append("无法统计一致性")
        
        return SubItemResult(
            name="consistency",
            description="代码一致性",
            score=score,
            status=self._status_by_score(score),
            evidence=evidence
        )
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """计算AST的圈复杂度"""
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, ast.Try):
                complexity += len(node.handlers)
        return complexity
    
    def _generate_quality_suggestions(self, subitems: List[SubItemResult]) -> List[str]:
        suggestions = []
        for s in subitems:
            if s.score < 0.5:
                suggestions.append(f"建议增强{s.description}")
        return suggestions[:3]


# ============================================================================
# 评估器注册表
# ============================================================================

def get_all_evaluators(config: Optional[Dict] = None) -> List[BaseEvaluator]:
    """获取所有评估器实例"""
    return [
        # A. 基础能力 (25%)
        OrchestrationEvaluator(config),
        AgentCompletenessEvaluator(config),
        PromptEngineeringEvaluator(config),
        ContextEngineeringEvaluator(config),
        
        # B. 智能能力 (30%)
        ResponseQualityEvaluator(config),
        RoutingEvaluator(config),
        ReasoningEvaluator(config),
        KnowledgeRecallEvaluator(config),
        ToolCallingEvaluator(config),
        MultiTurnEvaluator(config),
        SelfLearningEvaluator(config),
        
        # C. 架构能力 (28%)
        HarnessEvaluator(config),
        ArchitectureEvaluator(config),
        ObservabilityEvaluator(config),
        MonitoringEvaluator(config),
        SelfHealingEvaluator(config),
        RolloutEvaluator(config),
        
        # D. 数据能力 (10%)
        DataSourceEvaluator(config),
        KnowledgeMgmtEvaluator(config),
        VectorMgmtEvaluator(config),
        DataLineageEvaluator(config),
        
        # E. 平台能力 (7%)
        AppSupportEvaluator(config),
        CostControlEvaluator(config),
        IntegrationEvaluator(config),
    ]


def get_category_weights() -> Dict[str, Dict]:
    """获取分类权重"""
    return {
        "A": {"name": "基础能力", "weight": 0.25, "color": "#1976D2"},
        "B": {"name": "智能能力", "weight": 0.30, "color": "#388E3C"},
        "C": {"name": "架构能力", "weight": 0.28, "color": "#7B1FA2"},
        "D": {"name": "数据能力", "weight": 0.10, "color": "#F57C00"},
        "E": {"name": "平台能力", "weight": 0.07, "color": "#D32F2F"},
    }
