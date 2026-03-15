#!/usr/bin/env python3
"""
GAIA Benchmark Evaluator - GAIA基准测试评估器
用于评估Agent在GAIA风格任务上的表现
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import time


class TaskDifficulty(Enum):
    """任务难度"""
    LEVEL_1 = "level_1"  # 基础任务
    LEVEL_2 = "level_2"  # 中级任务
    LEVEL_3 = "level_3"  # 高级任务


class EvaluationStatus(Enum):
    """评估状态"""
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"
    ERROR = "error"


@dataclass
class GAIATask:
    """GAIA风格任务"""
    id: str
    question: str
    difficulty: TaskDifficulty
    answer: Optional[str] = None
    expected_tools: List[str] = field(default_factory=list)
    required_steps: List[str] = field(default_factory=list)
    ground_truth: Optional[Dict[str, Any]] = None


@dataclass
class EvaluationResult:
    """评估结果"""
    task_id: str
    difficulty: TaskDifficulty
    status: EvaluationStatus
    score: float  # 0-100
    execution_time: float
    tools_used: List[str] = field(default_factory=list)
    steps_completed: List[str] = field(default_factory=list)
    feedback: str = ""
    error: Optional[str] = None


@dataclass
class BenchmarkReport:
    """基准测试报告"""
    total_tasks: int
    passed_tasks: int
    failed_tasks: int
    partial_tasks: int
    average_score: float
    average_execution_time: float
    level_scores: Dict[str, float] = field(default_factory=dict)
    level_counts: Dict[str, int] = field(default_factory=dict)


class GAIABenchmarkEvaluator:
    """
    GAIA基准测试评估器
    
    功能：
    1. 运行GAIA风格任务
    2. 评估Agent表现
    3. 生成详细报告
    4. 对比不同Agent性能
    """
    
    def __init__(self, agent_executor: Callable):
        """
        初始化评估器
        
        Args:
            agent_executor: Agent执行函数，接收任务返回结果
        """
        self.agent_executor = agent_executor
        self.task_history: List[EvaluationResult] = []
        
        # 预设GAIA风格任务
        self.preset_tasks = self._create_preset_tasks()
    
    def _create_preset_tasks(self) -> List[GAIATask]:
        """创建预设GAIA风格任务"""
        return [
            # Level 1 - 基础任务
            GAIATask(
                id="gaia_l1_001",
                question="请搜索最新的AI新闻",
                difficulty=TaskDifficulty.LEVEL_1,
                expected_tools=["search"]
            ),
            GAIATask(
                id="gaia_l1_002",
                question="请计算 123 * 456",
                difficulty=TaskDifficulty.LEVEL_1,
                expected_tools=["calculator"]
            ),
            
            # Level 2 - 中级任务
            GAIATask(
                id="gaia_l2_001",
                question="请搜索AI的最新发展，然后总结3个要点",
                difficulty=TaskDifficulty.LEVEL_2,
                expected_tools=["search", "reasoning"]
            ),
            GAIATask(
                id="gaia_l2_002",
                question="请查找日本制造业的最新市场数据，并分析趋势",
                difficulty=TaskDifficulty.LEVEL_2,
                expected_tools=["search", "knowledge_retrieval", "reasoning"]
            ),
            
            # Level 3 - 高级任务
            GAIATask(
                id="gaia_l3_001",
                question="请搜索最新AI技术发展，分析对制造业的影响，并制定一份报告",
                difficulty=TaskDifficulty.LEVEL_3,
                expected_tools=["search", "knowledge_retrieval", "reasoning", "browser"]
            ),
            GAIATask(
                id="gaia_l3_002",
                question="请访问Google搜索最新的AI新闻，分析3个主要趋势，并生成中文报告",
                difficulty=TaskDifficulty.LEVEL_3,
                expected_tools=["browser", "reasoning"]
            )
        ]
    
    async def evaluate_task(self, task: GAIATask) -> EvaluationResult:
        """
        评估单个任务
        
        Args:
            task: GAIA任务
            
        Returns:
            评估结果
        """
        start_time = time.time()
        
        try:
            # 执行任务
            result = await self.agent_executor(task.question)
            
            execution_time = time.time() - start_time
            
            # 评估结果
            status, score, feedback = self._evaluate_result(
                result, 
                task.expected_tools
            )
            
            evaluation = EvaluationResult(
                task_id=task.id,
                difficulty=task.difficulty,
                status=status,
                score=score,
                execution_time=execution_time,
                tools_used=[],  # 可从执行追踪器获取
                steps_completed=[],
                feedback=feedback
            )
            
        except Exception as e:
            evaluation = EvaluationResult(
                task_id=task.id,
                difficulty=task.difficulty,
                status=EvaluationStatus.ERROR,
                score=0.0,
                execution_time=time.time() - start_time,
                error=str(e)
            )
        
        self.task_history.append(evaluation)
        return evaluation
    
    def _evaluate_result(
        self, 
        result: Any, 
        expected_tools: List[str]
    ) -> tuple:
        """
        评估结果
        
        Returns:
            (status, score, feedback)
        """
        result_str = str(result) if result else ""
        
        # 基础检查：结果不为空
        if not result_str or len(result_str) < 10:
            return (
                EvaluationStatus.FAILED, 
                0.0, 
                "结果为空或过短"
            )
        
        # 计算分数
        score = 50.0  # 基础分数
        
        # 检查是否有实质性内容
        if len(result_str) > 50:
            score += 20.0
        
        # 检查是否使用了正确的工具
        # (这里简化处理，实际应该从执行追踪器获取)
        
        # 检查内容质量
        if any(keyword in result_str.lower() for keyword in ["分析", "总结", "结果", "首先", "但是"]):
            score += 15.0
        
        # 判断状态
        if score >= 80:
            status = EvaluationStatus.PASSED
            feedback = "优秀"
        elif score >= 50:
            status = EvaluationStatus.PARTIAL
            feedback = "基本完成"
        else:
            status = EvaluationStatus.FAILED
            feedback = "未满足要求"
        
        return (status, min(score, 100.0), feedback)
    
    async def run_benchmark(
        self, 
        tasks: Optional[List[GAIATask]] = None,
        difficulty_filter: Optional[TaskDifficulty] = None
    ) -> BenchmarkReport:
        """
        运行完整基准测试
        
        Args:
            tasks: 任务列表（默认使用预设任务）
            difficulty_filter: 难度筛选
            
        Returns:
            基准测试报告
        """
        tasks = tasks or self.preset_tasks
        
        # 筛选任务
        if difficulty_filter:
            tasks = [t for t in tasks if t.difficulty == difficulty_filter]
        
        # 执行所有任务
        results = []
        for task in tasks:
            result = await self.evaluate_task(task)
            results.append(result)
        
        # 生成报告
        return self._generate_report(results)
    
    def _generate_report(self, results: List[EvaluationResult]) -> BenchmarkReport:
        """生成报告"""
        total = len(results)
        passed = sum(1 for r in results if r.status == EvaluationStatus.PASSED)
        failed = sum(1 for r in results if r.status == EvaluationStatus.FAILED)
        partial = sum(1 for r in results if r.status == EvaluationStatus.PARTIAL)
        
        avg_score = sum(r.score for r in results) / total if total > 0 else 0
        avg_time = sum(r.execution_time for r in results) / total if total > 0 else 0
        
        # 按难度分组统计
        level_scores = {}
        level_counts = {}
        
        for difficulty in TaskDifficulty:
            level_results = [r for r in results if r.difficulty == difficulty]
            if level_results:
                level_counts[difficulty.value] = len(level_results)
                level_scores[difficulty.value] = sum(r.score for r in level_results) / len(level_results)
            else:
                level_counts[difficulty.value] = 0
                level_scores[difficulty.value] = 0.0
        
        return BenchmarkReport(
            total_tasks=total,
            passed_tasks=passed,
            failed_tasks=failed,
            partial_tasks=partial,
            average_score=avg_score,
            average_execution_time=avg_time,
            level_scores=level_scores,
            level_counts=level_counts
        )
    
    def print_report(self, report: BenchmarkReport):
        """打印报告"""
        print("\n" + "="*60)
        print("📊 GAIA 基准测试报告")
        print("="*60)
        print(f"总任务数: {report.total_tasks}")
        print(f"通过: {report.passed_tasks} | 失败: {report.failed_tasks} | 部分: {report.partial_tasks}")
        print(f"平均分数: {report.average_score:.1f}%")
        print(f"平均执行时间: {report.average_execution_time:.2f}秒")
        print("\n按难度统计:")
        for level, score in report.level_scores.items():
            count = report.level_counts.get(level, 0)
            print(f"  {level}: {score:.1f}% ({count}个任务)")
        print("="*60)


# 便捷函数
async def quick_benchmark(agent_executor: Callable) -> BenchmarkReport:
    """快速基准测试"""
    evaluator = GAIABenchmarkEvaluator(agent_executor)
    report = await evaluator.run_benchmark()
    evaluator.print_report(report)
    return report
