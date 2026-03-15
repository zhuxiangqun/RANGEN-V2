"""
统一技能服务模块

合并以下服务:
- SkillService (skill_service.py)
- SkillDescriptionOptimizer (skill_description_optimizer.py)
- SkillQualityEvaluator (skill_quality_evaluator.py)
- SkillBenchmarkSystem (skill_benchmark_system.py)

使用示例:
```python
from src.services.skills import SkillsService

skills = SkillsService()
skills.register_skill("search", handler)
skills.trigger("search", context)
```
"""

import time
from typing import Dict, Any, List, Optional, Callable, Awaitable
from enum import Enum
from dataclasses import dataclass, field


# ============== Enums ==============

class SkillCategory(str, Enum):
    """技能类别"""
    RETRIEVAL = "retrieval"
    REASONING = "reasoning"
    CODE = "code"
    CREATIVE = "creative"
    UTILITY = "utility"
    CUSTOM = "custom"


class SkillStatus(str, Enum):
    """技能状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BETA = "beta"
    DEPRECATED = "deprecated"


class TriggerType(str, Enum):
    """触发类型"""
    AUTO = "auto"           # 自动触发
    MANUAL = "manual"      # 手动触发
    CONDITIONAL = "conditional"  # 条件触发


# ============== Data Classes ==============

@dataclass
class Skill:
    """技能定义"""
    name: str
    category: SkillCategory
    description: str
    trigger_type: TriggerType
    handler: Callable
    keywords: List[str]
    metadata: Dict[str, Any]
    status: SkillStatus
    version: str
    created_at: float
    usage_count: int = 0
    success_rate: float = 0.0


@dataclass
class SkillResult:
    """技能执行结果"""
    skill_name: str
    success: bool
    result: Any
    execution_time: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillBenchmark:
    """技能基准测试"""
    skill_name: str
    test_cases: int
    success_rate: float
    avg_latency: float
    score: float
    timestamp: float


@dataclass
class OptimizationResult:
    """优化结果"""
    original_description: str
    optimized_description: str
    improvements: List[str]
    score: float


# ============== Main Class ==============

class SkillsService:
    """
    统一技能服务
    
    提供:
    - 技能注册 (Registration)
    - 技能触发 (Triggering)
    - 技能优化 (Optimization)
    - 质量评估 (Quality Evaluation)
    - 基准测试 (Benchmarking)
    """
    
    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        self._skill_triggers: Dict[str, List[str]] = {}  # keyword -> skill names
        self._benchmarks: Dict[str, SkillBenchmark] = {}
        self._execution_history: List[SkillResult] = []
        self._max_history = 10000
    
    # ============== Registration ==============
    
    def register_skill(
        self,
        name: str,
        handler: Callable,
        category: SkillCategory = SkillCategory.CUSTOM,
        description: str = "",
        keywords: Optional[List[str]] = None,
        trigger_type: TriggerType = TriggerType.MANUAL,
        metadata: Optional[Dict[str, Any]] = None,
        version: str = "1.0.0"
    ) -> Skill:
        """注册技能"""
        skill = Skill(
            name=name,
            category=category,
            description=description,
            trigger_type=trigger_type,
            handler=handler,
            keywords=keywords or [],
            metadata=metadata or {},
            status=SkillStatus.ACTIVE,
            version=version,
            created_at=time.time()
        )
        
        self._skills[name] = skill
        
        # Register triggers
        for keyword in skill.keywords:
            if keyword not in self._skill_triggers:
                self._skill_triggers[keyword] = []
            self._skill_triggers[keyword].append(name)
        
        return skill
    
    def unregister_skill(self, name: str) -> bool:
        """注销技能"""
        if name not in self._skills:
            return False
        
        # Remove triggers
        skill = self._skills[name]
        for keyword in skill.keywords:
            if keyword in self._skill_triggers:
                self._skill_triggers[keyword].remove(name)
        
        del self._skills[name]
        return True
    
    def get_skill(self, name: str) -> Optional[Skill]:
        """获取技能"""
        return self._skills.get(name)
    
    def list_skills(
        self,
        category: Optional[SkillCategory] = None,
        status: Optional[SkillStatus] = None
    ) -> List[Skill]:
        """列出技能"""
        skills = list(self._skills.values())
        
        if category:
            skills = [s for s in skills if s.category == category]
        
        if status:
            skills = [s for s in skills if s.status == status]
        
        return skills
    
    # ============== Triggering ==============
    
    async def trigger(
        self,
        skill_name: str,
        context: Dict[str, Any]
    ) -> SkillResult:
        """触发技能"""
        start_time = time.time()
        
        if skill_name not in self._skills:
            return SkillResult(
                skill_name=skill_name,
                success=False,
                result=None,
                execution_time=time.time() - start_time,
                error=f"Skill not found: {skill_name}"
            )
        
        skill = self._skills[skill_name]
        
        if skill.status != SkillStatus.ACTIVE:
            return SkillResult(
                skill_name=skill_name,
                success=False,
                result=None,
                execution_time=time.time() - start_time,
                error=f"Skill is not active: {skill.status}"
            )
        
        try:
            # Execute handler
            import asyncio
            if asyncio.iscoroutinefunction(skill.handler):
                result = await skill.handler(context)
            else:
                result = skill.handler(context)
            
            # Update stats
            skill.usage_count += 1
            skill.success_rate = (
                (skill.success_rate * (skill.usage_count - 1) + 1.0)
                / skill.usage_count
            )
            
            execution_time = time.time() - start_time
            
            skill_result = SkillResult(
                skill_name=skill_name,
                success=True,
                result=result,
                execution_time=execution_time
            )
            
            self._execution_history.append(skill_result)
            self._trim_history()
            
            return skill_result
            
        except Exception as e:
            # Update stats
            skill.usage_count += 1
            skill.success_rate = (
                (skill.success_rate * (skill.usage_count - 1))
                / skill.usage_count
            )
            
            execution_time = time.time() - start_time
            
            skill_result = SkillResult(
                skill_name=skill_name,
                success=False,
                result=None,
                execution_time=execution_time,
                error=str(e)
            )
            
            self._execution_history.append(skill_result)
            self._trim_history()
            
            return skill_result
    
    def auto_trigger(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> Optional[SkillResult]:
        """自动触发技能"""
        # Find matching skills
        query_lower = query.lower()
        candidates = []
        
        for keyword, skill_names in self._skill_triggers.items():
            if keyword.lower() in query_lower:
                for name in skill_names:
                    skill = self._skills.get(name)
                    if skill and skill.status == SkillStatus.ACTIVE:
                        candidates.append(skill)
        
        if not candidates:
            return None
        
        # Sort by success rate
        candidates.sort(key=lambda s: s.success_rate, reverse=True)
        
        # Trigger best match
        best_skill = candidates[0]
        
        # Run async
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in async context, create task
                asyncio.create_task(self.trigger(best_skill.name, context))
                return None
            else:
                return loop.run_until_complete(self.trigger(best_skill.name, context))
        except:
            return None
    
    def _trim_history(self) -> None:
        """修剪历史"""
        if len(self._execution_history) > self._max_history:
            self._execution_history = self._execution_history[-self._max_history:]
    
    # ============== Optimization ==============
    
    def optimize_description(
        self,
        skill_name: str,
        requirements: str
    ) -> OptimizationResult:
        """优化技能描述"""
        skill = self._skills.get(skill_name)
        
        if not skill:
            return OptimizationResult(
                original_description="",
                optimized_description="",
                improvements=[],
                score=0.0
            )
        
        original = skill.description
        
        # Simple optimization (in production would use LLM)
        improvements = []
        
        # Add requirements if missing
        if requirements and requirements not in original:
            improved = f"{original} {requirements}" if original else requirements
            improvements.append("Added requirements context")
        else:
            improved = original
        
        # Calculate score
        score = 0.5 + (len(improvements) * 0.2)
        
        return OptimizationResult(
            original_description=original,
            optimized_description=improved,
            improvements=improvements,
            score=min(1.0, score)
        )
    
    # ============== Benchmarking ==============
    
    def benchmark(
        self,
        skill_name: str,
        test_cases: List[Dict[str, Any]]
    ) -> SkillBenchmark:
        """基准测试"""
        skill = self._skills.get(skill_name)
        
        if not skill:
            raise ValueError(f"Skill not found: {skill_name}")
        
        successes = 0
        latencies = []
        
        import asyncio
        for case in test_cases:
            start = time.time()
            
            try:
                if asyncio.iscoroutinefunction(skill.handler):
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        continue
                    loop.run_until_complete(skill.handler(case))
                else:
                    skill.handler(case)
                
                successes += 1
            except:
                pass
            
            latencies.append(time.time() - start)
        
        success_rate = successes / len(test_cases) if test_cases else 0
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        # Calculate score
        score = success_rate * 0.7 + (1.0 / (1.0 + avg_latency)) * 0.3
        
        benchmark = SkillBenchmark(
            skill_name=skill_name,
            test_cases=len(test_cases),
            success_rate=success_rate,
            avg_latency=avg_latency,
            score=score,
            timestamp=time.time()
        )
        
        self._benchmarks[skill_name] = benchmark
        
        return benchmark
    
    def compare_skills(
        self,
        skill_names: List[str],
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, SkillBenchmark]:
        """比较技能"""
        results = {}
        
        for name in skill_names:
            try:
                results[name] = self.benchmark(name, test_cases)
            except:
                pass
        
        return results
    
    # ============== Analytics ==============
    
    def get_skill_stats(self) -> Dict[str, Any]:
        """获取技能统计"""
        return {
            "total_skills": len(self._skills),
            "active_skills": len([s for s in self._skills.values() if s.status == SkillStatus.ACTIVE]),
            "by_category": {
                cat.value: len([s for s in self._skills.values() if s.category == cat])
                for cat in SkillCategory
            },
            "most_used": sorted(
                [(s.name, s.usage_count) for s in self._skills.values()],
                key=lambda x: x[1],
                reverse=True
            )[:5],
            "highest_success": sorted(
                [(s.name, s.success_rate) for s in self._skills.values() if s.usage_count > 0],
                key=lambda x: x[1],
                reverse=True
            )[:5],
        }
    
    def get_execution_history(
        self,
        skill_name: Optional[str] = None,
        limit: int = 100
    ) -> List[SkillResult]:
        """获取执行历史"""
        history = self._execution_history
        
        if skill_name:
            history = [r for r in history if r.skill_name == skill_name]
        
        return history[-limit:]


# ============== Factory ==============

def get_skills_service() -> SkillsService:
    """获取技能服务"""
    return SkillsService()
