"""
简化业务工作流 - 分层架构重构

核心思路：
1. 精简节点数量：从37个节点减少到15-18个核心节点
2. 统一处理逻辑：用一个智能处理节点替代多个专用节点
3. 简化路由：直接的条件路由替代多层嵌套路由
4. 能力服务化：能力调用从节点内联改为服务调用

架构：
├── 路由层: route_query (1节点)
├── 协作层: smart_collaborator (1节点，合并协作+冲突检测)
├── 处理层: intelligent_processor (1节点，统一处理所有任务类型)
├── 输出层: format_output (1节点)
└── 总计: 4个核心节点 + 一些辅助节点
"""

import logging
import time
from typing import Dict, Any, Literal
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SimplifiedBusinessState:
    """简化业务状态 - 只保留核心字段"""
    # 基础查询信息
    query: str
    context: Dict[str, Any] = field(default_factory=dict)

    # 路由决策
    route_path: str = ""
    complexity_score: float = 0.0

    # 处理结果
    result: Dict[str, Any] = field(default_factory=dict)
    intermediate_steps: list = field(default_factory=list)

    # 状态跟踪
    current_step: str = ""
    errors: list = field(default_factory=list)

    # 元数据
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SimplifiedBusinessWorkflow:
    """简化业务工作流

    核心设计：
    1. 4个核心节点：路由 → 协作 → 处理 → 输出
    2. 能力服务化：通过CapabilityService调用能力
    3. 状态简化：只保留必要的状态字段
    4. 路由直接：条件路由替代嵌套路由
    """

    def __init__(self):
        """初始化简化工作流"""
        from langgraph.graph import StateGraph, END

        # 创建简化状态图
        self.workflow = StateGraph(SimplifiedBusinessState)

        # 初始化能力服务
        self.capability_service = SimplifiedCapabilityService()

        # 添加核心节点
        self.workflow.add_node("route_query", self.route_query_node)
        self.workflow.add_node("smart_collaborator", self.smart_collaborator_node)
        self.workflow.add_node("intelligent_processor", self.intelligent_processor_node)
        self.workflow.add_node("format_output", self.format_output_node)

        # 设置路由
        self.workflow.add_edge("route_query", "smart_collaborator")
        self.workflow.add_edge("smart_collaborator", "intelligent_processor")
        self.workflow.add_edge("intelligent_processor", "format_output")
        self.workflow.add_edge("format_output", END)

        # 设置入口点
        self.workflow.set_entry_point("route_query")

        # 编译工作流
        self.compiled_workflow = self.workflow.compile()
        logger.info("✅ 简化业务工作流初始化完成")

    async def execute(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行简化工作流"""
        start_time = time.time()

        # 初始化状态
        initial_state = SimplifiedBusinessState(
            query=query,
            context=context or {}
        )

        try:
            # 执行工作流
            result = await self.compiled_workflow.ainvoke(initial_state)

            # 计算执行时间
            execution_time = time.time() - start_time

            logger.info(".2f")
            return {
                "query": result.get("query", ""),
                "result": result.get("result", {}),
                "execution_time": execution_time,
                "route_path": result.get("route_path", ""),
                "intermediate_steps": result.get("intermediate_steps", []),
                "errors": result.get("errors", [])
            }

        except Exception as e:
            logger.error(f"❌ 简化工作流执行失败: {e}")
            return {
                "query": query,
                "error": str(e),
                "execution_time": time.time() - start_time
            }

    def route_query_node(self, state: SimplifiedBusinessState) -> SimplifiedBusinessState:
        """简化的路由节点"""
        query = state.query
        context = state.context

        # 简化的复杂度评估
        query_length = len(query)
        has_keywords = any(word in query.lower() for word in ['why', 'how', 'explain', 'compare'])

        if query_length > 100 or has_keywords:
            state.route_path = "complex"
            state.complexity_score = 0.8
        elif query_length > 50:
            state.route_path = "medium"
            state.complexity_score = 0.5
        else:
            state.route_path = "simple"
            state.complexity_score = 0.2

        logger.info(f"🔀 查询路由: {state.route_path} (复杂度: {state.complexity_score:.1f})")
        return state

    def smart_collaborator_node(self, state: SimplifiedBusinessState) -> SimplifiedBusinessState:
        """智能协作节点 - 合并协作和冲突检测功能"""
        # 简化的协作决策
        complexity = state.complexity_score

        if complexity > 0.7:
            # 复杂查询：多能力协作
            collaboration_plan = {
                "mode": "multi_capability",
                "capabilities": ["knowledge_retrieval", "reasoning", "answer_generation"],
                "coordination_strategy": "sequential"
            }
        elif complexity > 0.4:
            # 中等复杂度：双能力协作
            collaboration_plan = {
                "mode": "dual_capability",
                "capabilities": ["knowledge_retrieval", "answer_generation"],
                "coordination_strategy": "parallel"
            }
        else:
            # 简单查询：单能力处理
            collaboration_plan = {
                "mode": "single_capability",
                "capabilities": ["answer_generation"],
                "coordination_strategy": "direct"
            }

        state.result["collaboration_plan"] = collaboration_plan
        state.intermediate_steps.append(f"协作规划: {collaboration_plan['mode']}")

        logger.info(f"🤝 智能协作: {collaboration_plan['mode']} - {len(collaboration_plan['capabilities'])}个能力")
        return state

    async def intelligent_processor_node(self, state: SimplifiedBusinessState) -> SimplifiedBusinessState:
        """智能处理节点 - 统一处理所有任务类型"""
        try:
            collaboration_plan = state.result.get("collaboration_plan", {})
            capabilities = collaboration_plan.get("capabilities", ["answer_generation"])

            # 通过能力服务执行能力
            results = {}
            for capability_name in capabilities:
                try:
                    result = await self.capability_service.execute_capability(
                        capability_name,
                        {
                            "query": state.query,
                            "context": state.context,
                            "route_path": state.route_path
                        }
                    )
                    results[capability_name] = result
                    state.intermediate_steps.append(f"{capability_name}: 完成")

                except Exception as e:
                    logger.warning(f"⚠️ 能力 {capability_name} 执行失败: {e}")
                    results[capability_name] = {"error": str(e)}
                    state.errors.append(f"能力执行失败: {capability_name} - {e}")

            # 整合结果
            final_result = self._integrate_capability_results(results, collaboration_plan)
            state.result.update(final_result)

            logger.info(f"🧠 智能处理完成: {len(capabilities)}个能力，{len(state.errors)}个错误")

        except Exception as e:
            logger.error(f"❌ 智能处理节点错误: {e}")
            state.errors.append(f"处理节点错误: {e}")
            state.result["error"] = str(e)

        return state

    def format_output_node(self, state: SimplifiedBusinessState) -> SimplifiedBusinessState:
        """格式化输出节点"""
        result = state.result

        # 简化的输出格式化
        formatted_output = {
            "query": state.query,
            "answer": result.get("answer", result.get("final_answer", "无法生成答案")),
            "sources": result.get("sources", []),
            "confidence": result.get("confidence", 0.5),
            "processing_steps": state.intermediate_steps,
            "execution_time": state.execution_time
        }

        # 添加错误信息
        if state.errors:
            formatted_output["warnings"] = state.errors

        state.result = formatted_output
        logger.info("📝 输出格式化完成")
        return state

    def _integrate_capability_results(self, results: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
        """整合能力执行结果"""
        integrated = {}

        # 根据协作模式整合结果
        mode = plan.get("mode", "single_capability")

        if mode == "multi_capability":
            # 多能力模式：合并所有结果
            knowledge = results.get("knowledge_retrieval", {})
            reasoning = results.get("reasoning", {})
            answer = results.get("answer_generation", {})

            integrated.update({
                "knowledge_gathered": knowledge.get("evidence", []),
                "reasoning_steps": reasoning.get("steps", []),
                "answer": answer.get("answer", "基于多能力分析的答案"),
                "confidence": min(0.9, (knowledge.get("confidence", 0.5) +
                                       reasoning.get("confidence", 0.5) +
                                       answer.get("confidence", 0.5)) / 3),
                "sources": knowledge.get("sources", []) + answer.get("sources", [])
            })

        elif mode == "dual_capability":
            # 双能力模式：知识检索 + 答案生成
            knowledge = results.get("knowledge_retrieval", {})
            answer = results.get("answer_generation", {})

            integrated.update({
                "evidence": knowledge.get("evidence", []),
                "answer": answer.get("answer", "基于知识的答案"),
                "confidence": (knowledge.get("confidence", 0.5) + answer.get("confidence", 0.5)) / 2,
                "sources": knowledge.get("sources", []) + answer.get("sources", [])
            })

        else:
            # 单能力模式：直接使用答案生成结果
            answer = results.get("answer_generation", {})
            integrated.update(answer)

        return integrated


class SimplifiedCapabilityService:
    """简化能力服务 - 替代复杂的节点化能力"""

    def __init__(self):
        """初始化能力服务"""
        self.capabilities = {
            'knowledge_retrieval': self._mock_knowledge_retrieval,
            'reasoning': self._mock_reasoning,
            'answer_generation': self._mock_answer_generation,
            'citation': self._mock_citation
        }
        logger.info("✅ 简化能力服务初始化完成")

    async def execute_capability(self, capability_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行能力"""
        if capability_name not in self.capabilities:
            raise ValueError(f"未知能力: {capability_name}")

        # 模拟异步执行
        import asyncio
        await asyncio.sleep(0.05)  # 模拟处理时间

        capability_func = self.capabilities[capability_name]
        return await capability_func(context)

    async def _mock_knowledge_retrieval(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """模拟知识检索能力"""
        query = context.get("query", "")
        return {
            "evidence": [f"为查询'{query}'检索到的知识"],
            "sources": ["mock_source_1", "mock_source_2"],
            "confidence": 0.8
        }

    async def _mock_reasoning(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """模拟推理能力"""
        query = context.get("query", "")
        return {
            "steps": ["分析查询", "应用推理规则", "得出结论"],
            "conclusion": f"对'{query}'的推理结论",
            "confidence": 0.7
        }

    async def _mock_answer_generation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """模拟答案生成能力"""
        query = context.get("query", "")
        route_path = context.get("route_path", "simple")

        # 根据路由路径调整答案复杂度
        if route_path == "complex":
            answer = f"这是对复杂查询'{query}'的详细答案，包含多个方面的分析。"
        elif route_path == "medium":
            answer = f"这是对查询'{query}'的中等复杂度答案。"
        else:
            answer = f"这是对简单查询'{query}'的直接答案。"

        return {
            "answer": answer,
            "confidence": 0.85,
            "sources": ["generated"]
        }

    async def _mock_citation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """模拟引用能力"""
        return {
            "citations": [{
                "text": "引用的相关内容",
                "source": "Mock Academic Source",
                "year": 2024
            }],
            "formatted_citations": "[1] Mock Source (2024)"
        }
