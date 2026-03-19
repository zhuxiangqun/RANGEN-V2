"""
能力发现服务 - 基盘核心能力
============================

基于用户需求自动发现和匹配最佳能力组合。

功能：
1. 能力注册 - 自动扫描并注册所有可用能力
2. 需求分析 - 分析用户需求，确定所需能力类型
3. 能力匹配 - 基于语义匹配找到最合适的能力
4. 执行计划 - 生成能力编排执行计划
5. 自动执行 - 编排并执行能力链

这是基盘的核心能力，所有应用层都应该通过它来发现和使用能力。
"""

import os
import re
import time
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading

try:
    from src.core.capability_service import CapabilityService, CapabilityInfo
    from src.core.capability_orchestration_engine import (
        CapabilityOrchestrationEngine,
        OrchestrationPlan,
        OrchestrationMode,
        CapabilityNode
    )
    from src.core.llm_integration import LLMIntegration
except ImportError as e:
    logger.warning(f"Failed to import core modules: {e}")
    CapabilityService = None
    CapabilityOrchestrationEngine = None
    LLMIntegration = None

logger = logging.getLogger(__name__)


class CapabilityType(Enum):
    """能力类型"""
    QUERY = "query"           # 查询处理
    DIAGNOSIS = "diagnosis"   # 运维诊断
    REASONING = "reasoning"   # 推理分析
    CREATION = "creation"     # 创建实体
    EXECUTION = "execution"   # 执行操作
    FETCH = "fetch"           # 内容获取
    LEARNING = "learning"     # 学习优化
    VALIDATION = "validation" # 验证


@dataclass
class CapabilitySpec:
    """能力规格"""
    name: str
    type: CapabilityType
    handler: str  # 处理函数名
    module: str    # 模块路径
    description: str = ""
    keywords: List[str] = field(default_factory=list)
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class MatchResult:
    """匹配结果"""
    capability: CapabilitySpec
    score: float  # 0-1 匹配度
    reason: str
    execution_order: int = 0


@dataclass
class ExecutionPlan:
    """执行计划"""
    plan_id: str
    query: str
    matched_capabilities: List[MatchResult]
    execution_order: List[str]  # 能力执行顺序
    estimated_time: float = 0.0
    requires_confirmation: bool = False


# 预定义能力注册表
DEFAULT_CAPABILITIES = [
    CapabilitySpec(
        name="ProductionWorkflow",
        type=CapabilityType.QUERY,
        handler="execute",
        module="src.core.production_workflow",
        description="通用查询处理，支持RAG、复杂推理和知识问答",
        keywords=["查询", "问题", "什么", "如何", "为什么", "告诉", "分析", "理解", "回答"]
    ),
    CapabilitySpec(
        name="OpsDiagnosisAgent",
        type=CapabilityType.DIAGNOSIS,
        handler="execute",
        module="src.agents.ops_diagnosis_agent",
        description="运维诊断和健康检查，检测系统问题",
        keywords=["检查", "诊断", "修复", "health", "check", "状态", "问题", "404", "错误", "故障", "离线"]
    ),
    CapabilitySpec(
        name="WebCrawler",
        type=CapabilityType.FETCH,
        handler="crawl",
        module="src.kms.web_crawler",
        description="网页内容抓取，获取URL对应的网页内容",
        keywords=["url", "http", "网页", "文章", "链接", "访问"]
    ),
    CapabilitySpec(
        name="SmartCreator",
        type=CapabilityType.CREATION,
        handler="create",
        module="src.services.unified_creator",
        description="创建Agent、Skill、Tool等实体",
        keywords=["创建", "新建", "添加", "做一个", "开发", "生成"]
    ),
    CapabilitySpec(
        name="SkillTriggerLearner",
        type=CapabilityType.LEARNING,
        handler="learn_from_feedback",
        module="src.services.intent_understanding_service",
        description="从反馈中学习，优化意图识别",
        keywords=["学习", "反馈", "纠正", "纠正我"]
    ),
    CapabilitySpec(
        name="ExecutionCoordinator",
        type=CapabilityType.REASONING,
        handler="run_task",
        module="src.core.execution_coordinator",
        description="复杂任务执行，协调多阶段工作流",
        keywords=["执行", "运行", "完成", "处理", "复杂", "多步"]
    ),
]


class CapabilityDiscoveryService:
    """
    能力发现服务 - 基盘核心能力
    
    自动发现和匹配最佳能力组合，支持：
    1. 能力注册和索引
    2. 基于关键词的快速匹配
    3. 基于语义的深度匹配
    4. 执行计划生成
    """
    
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        self._capabilities: Dict[str, CapabilitySpec] = {}
        self._capability_handlers: Dict[str, callable] = {}
        self._type_index: Dict[CapabilityType, List[str]] = {}
        self._keyword_index: Dict[str, Set[str]] = {}
        
        # LLM 用于语义匹配
        self._llm = None
        
        # 注册默认能力
        self._register_default_capabilities()
        
        # 注册执行处理器
        self._register_handlers()
        
        logger.info("CapabilityDiscoveryService initialized")
    
    def _register_default_capabilities(self):
        """注册默认能力"""
        for cap in DEFAULT_CAPABILITIES:
            self.register_capability(cap)
    
    def _register_handlers(self):
        """注册能力处理器"""
        from src.core.production_workflow import ProductionWorkflow
        from src.agents.ops_diagnosis_agent import OpsDiagnosisAgent
        from src.kms.web_crawler import WebCrawler
        from src.services.intent_understanding_service import get_intent_understanding_service
        from src.core.execution_coordinator import ExecutionCoordinator
        
        self._capability_handlers = {
            "ProductionWorkflow": lambda ctx: ProductionWorkflow(),
            "OpsDiagnosisAgent": lambda ctx: OpsDiagnosisAgent(),
            "WebCrawler": lambda ctx: WebCrawler(),
            "SkillTriggerLearner": lambda ctx: get_intent_understanding_service(),
            "ExecutionCoordinator": lambda ctx: ExecutionCoordinator(),
        }
    
    def register_capability(self, capability: CapabilitySpec):
        """注册能力"""
        with self._lock:
            self._capabilities[capability.name] = capability
            
            # 更新类型索引
            if capability.type not in self._type_index:
                self._type_index[capability.type] = []
            self._type_index[capability.type].append(capability.name)
            
            # 更新关键词索引
            for keyword in capability.keywords:
                keyword_lower = keyword.lower()
                if keyword_lower not in self._keyword_index:
                    self._keyword_index[keyword_lower] = set()
                self._keyword_index[keyword_lower].add(capability.name)
            
            logger.info(f"Registered capability: {capability.name} ({capability.type.value})")
    
    def get_capabilities(self) -> List[CapabilitySpec]:
        """获取所有已注册能力"""
        return list(self._capabilities.values())
    
    def get_capability(self, name: str) -> Optional[CapabilitySpec]:
        """获取指定能力"""
        return self._capabilities.get(name)
    
    def get_capabilities_by_type(self, cap_type: CapabilityType) -> List[CapabilitySpec]:
        """获取指定类型的能力"""
        names = self._type_index.get(cap_type, [])
        return [self._capabilities[name] for name in names if name in self._capabilities]
    
    def discover(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionPlan:
        """
        发现匹配的能力并生成执行计划
        
        Args:
            query: 用户查询
            context: 上下文信息
            
        Returns:
            ExecutionPlan: 执行计划
        """
        query_lower = query.lower()
        plan_id = f"plan_{int(time.time() * 1000)}"
        
        # 1. 关键词快速匹配
        keyword_matches = self._match_by_keywords(query_lower)
        
        # 2. URL 检测 - 特殊处理
        urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', query)
        if urls:
            url_cap = self.get_capability("WebCrawler")
            if url_cap:
                keyword_matches.append(MatchResult(
                    capability=url_cap,
                    score=1.0,
                    reason="检测到URL，需要抓取内容"
                ))
        
        # 3. 基于语义的深度匹配 (如果有 LLM)
        semantic_matches = self._match_by_semantics(query, context)
        
        # 4. 合并结果
        all_matches = self._merge_matches(keyword_matches, semantic_matches)
        
        # 5. 排序并生成执行计划
        all_matches.sort(key=lambda x: x.score, reverse=True)
        
        # 6. 确定执行顺序
        execution_order = self._determine_execution_order(all_matches, query_lower)
        
        # 7. 判断是否需要确认
        requires_confirmation = self._check_requires_confirmation(all_matches, query_lower)
        
        return ExecutionPlan(
            plan_id=plan_id,
            query=query,
            matched_capabilities=all_matches,
            execution_order=execution_order,
            estimated_time=len(execution_order) * 2.0,  # 估算
            requires_confirmation=requires_confirmation
        )
    
    def _match_by_keywords(self, query_lower: str) -> List[MatchResult]:
        """基于关键词匹配"""
        matches = []
        matched_caps = set()
        
        # 检查每个关键词
        for keyword, cap_names in self._keyword_index.items():
            if keyword in query_lower:
                for cap_name in cap_names:
                    if cap_name not in matched_caps:
                        cap = self._capabilities[cap_name]
                        matches.append(MatchResult(
                            capability=cap,
                            score=0.8,
                            reason=f"关键词匹配: {keyword}"
                        ))
                        matched_caps.add(cap_name)
        
        return matches
    
    def _match_by_semantics(
        self,
        query: str,
        context: Optional[Dict[str, Any]]
    ) -> List[MatchResult]:
        """基于语义匹配"""
        if self._llm is None:
            try:
                from dotenv import load_dotenv
                load_dotenv(override=False)
                
                if LLMIntegration:
                    self._llm = LLMIntegration({
                        "llm_provider": os.getenv("LLM_PROVIDER", "deepseek"),
                        "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
                        "model": "deepseek-chat"
                    })
            except Exception as e:
                logger.warning(f"Failed to initialize LLM: {e}")
                return []
        
        if self._llm is None:
            return []
        
        try:
            prompt = f"""分析用户需求，选择最合适的能力。

用户需求: {query}

可用能力:
{self._format_capabilities_for_llm()}

请输出JSON格式的选择结果:
{{
    "selected_capabilities": ["能力1", "能力2", ...],
    "reason": "选择理由",
    "execution_order": ["能力1", "能力2"]
}}
"""
            
            response = self._llm._call_llm(
                prompt=prompt,
                system_prompt="你是一个能力选择专家，根据用户需求匹配最合适的能力组合。",
                temperature=0.1
            )
            
            if response:
                return self._parse_llm_response(response)
        except Exception as e:
            logger.warning(f"Semantic matching failed: {e}")
        
        return []
    
    def _format_capabilities_for_llm(self) -> str:
        """格式化能力列表供 LLM 使用"""
        lines = []
        for cap in self._capabilities.values():
            lines.append(f"- {cap.name}: {cap.description}")
            lines.append(f"  关键词: {', '.join(cap.keywords[:5])}")
        return "\n".join(lines)
    
    def _parse_llm_response(self, response: str) -> List[MatchResult]:
        """解析 LLM 返回的匹配结果"""
        try:
            # 提取 JSON
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            
            data = json.loads(json_str)
            selected = data.get("selected_capabilities", [])
            
            matches = []
            for cap_name in selected:
                if cap_name in self._capabilities:
                    cap = self._capabilities[cap_name]
                    matches.append(MatchResult(
                        capability=cap,
                        score=0.95,
                        reason=data.get("reason", "语义匹配")
                    ))
            
            return matches
        except Exception as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            return []
    
    def _merge_matches(
        self,
        keyword_matches: List[MatchResult],
        semantic_matches: List[MatchResult]
    ) -> List[MatchResult]:
        """合并匹配结果"""
        merged = {}
        
        # 添加关键词匹配
        for m in keyword_matches:
            if m.capability.name not in merged:
                merged[m.capability.name] = m
            else:
                # 提高分数
                existing = merged[m.capability.name]
                existing.score = max(existing.score, m.score)
        
        # 添加语义匹配
        for m in semantic_matches:
            if m.capability.name not in merged:
                merged[m.capability.name] = m
            else:
                existing = merged[m.capability.name]
                existing.score = max(existing.score, m.score)
                existing.reason = f"{existing.reason}; {m.reason}"
        
        return list(merged.values())
    
    def _determine_execution_order(
        self,
        matches: List[MatchResult],
        query_lower: str
    ) -> List[str]:
        """确定执行顺序"""
        order = []
        
        # URL 需要优先处理
        if "http" in query_lower:
            for m in matches:
                if m.capability.type == CapabilityType.FETCH:
                    order.append(m.capability.name)
                    break
        
        # 其他能力按类型优先级
        type_priority = {
            CapabilityType.FETCH: 1,
            CapabilityType.DIAGNOSIS: 2,
            CapabilityType.QUERY: 3,
            CapabilityType.REASONING: 4,
            CapabilityType.CREATION: 5,
            CapabilityType.LEARNING: 6,
        }
        
        remaining = [m for m in matches if m.capability.name not in order]
        remaining.sort(key=lambda x: type_priority.get(x.capability.type, 99))
        
        for m in remaining:
            order.append(m.capability.name)
        
        return order
    
    def _check_requires_confirmation(
        self,
        matches: List[MatchResult],
        query_lower: str
    ) -> bool:
        """检查是否需要确认"""
        # 创建类操作需要确认
        creation_keywords = ["创建", "新建", "添加", "做一个"]
        if any(k in query_lower for k in creation_keywords):
            return True
        
        return False
    
    async def execute_plan(
        self,
        plan: ExecutionPlan,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行编排计划
        
        Args:
            plan: 执行计划
            context: 执行上下文
            
        Returns:
            执行结果
        """
        results = {}
        current_input = {"query": plan.query, "context": context or {}}
        
        for cap_name in plan.execution_order:
            try:
                result = await self._execute_capability(cap_name, current_input)
                results[cap_name] = result
                current_input = {
                    "previous_result": result,
                    "query": plan.query,
                    "context": context or {}
                }
            except Exception as e:
                logger.error(f"Failed to execute {cap_name}: {e}")
                results[cap_name] = {"error": str(e)}
        
        # 返回最终结果
        return {
            "plan_id": plan.plan_id,
            "results": results,
            "final_result": self._extract_final_result(results)
        }
    
    async def _execute_capability(
        self,
        cap_name: str,
        input_data: Dict[str, Any]
    ) -> Any:
        """执行单个能力"""
        cap = self._capabilities.get(cap_name)
        if not cap:
            return {"error": f"Capability not found: {cap_name}"}
        
        handler_factory = self._capability_handlers.get(cap_name)
        if not handler_factory:
            return {"error": f"Handler not found: {cap_name}"}
        
        try:
            handler_instance = handler_factory(input_data)
            
            if hasattr(handler_instance, cap.handler):
                method = getattr(handler_instance, cap.handler)
                if asyncio.iscoroutinefunction(method):
                    return await method(input_data)
                else:
                    return method(input_data)
            
            return {"error": f"Method {cap.handler} not found"}
        except Exception as e:
            logger.error(f"Execution error for {cap_name}: {e}")
            return {"error": str(e)}
    
    def _extract_final_result(self, results: Dict[str, Any]) -> Any:
        """提取最终结果"""
        # 优先返回 ProductionWorkflow 的结果
        if "ProductionWorkflow" in results:
            return results["ProductionWorkflow"]
        
        # 返回最后一个成功的结果
        for cap_name in reversed(list(results.keys())):
            result = results[cap_name]
            if isinstance(result, dict) and "error" not in result:
                return result
        
        return results
    
    def get_discovery_stats(self) -> Dict[str, Any]:
        """获取发现统计"""
        return {
            "total_capabilities": len(self._capabilities),
            "capabilities_by_type": {
                cap_type.value: len(caps)
                for cap_type, caps in self._type_index.items()
            },
            "keyword_index_size": len(self._keyword_index)
        }


# 单例访问
_capability_discovery: Optional[CapabilityDiscoveryService] = None

def get_capability_discovery_service() -> CapabilityDiscoveryService:
    """获取能力发现服务单例"""
    global _capability_discovery
    if _capability_discovery is None:
        _capability_discovery = CapabilityDiscoveryService()
    return _capability_discovery
