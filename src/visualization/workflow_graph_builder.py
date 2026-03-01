"""
工作流图构建器 - 生成可展开/折叠的分层 Mermaid 图表
"""
import logging
from typing import Dict, List, Any, Optional, Set

logger = logging.getLogger(__name__)


class WorkflowGraphBuilder:
    """工作流图构建器 - 生成分层的 Mermaid 图表"""
    
    # 🚀 新增：边的说明映射（用于边的标签显示）
    EDGE_DESCRIPTIONS = {
        # 路由边
        ("route_query", "query_analysis"): "分析查询",
        ("query_analysis", "scheduling_optimization"): "调度优化",
        ("scheduling_optimization", "chief_agent"): "路由到核心大脑",
        ("scheduling_optimization", "simple_query"): "路由到简单查询",
        ("scheduling_optimization", "complex_query"): "路由到复杂查询",
        ("route_query", "chief_agent"): "路由到核心大脑",
        ("route_query", "simple_query"): "路由到简单查询",
        ("route_query", "complex_query"): "路由到复杂查询",
        
        # 简单/复杂查询到核心大脑
        ("simple_query", "chief_agent"): "协调处理",
        ("complex_query", "chief_agent"): "协调处理",
        
        # 多智能体序列
        ("chief_agent", "memory_agent"): "记忆管理",
        ("memory_agent", "knowledge_retrieval_agent"): "知识检索",
        ("knowledge_retrieval_agent", "reasoning_agent"): "推理分析",
        ("reasoning_agent", "answer_generation_agent"): "答案生成",
        ("answer_generation_agent", "citation_agent"): "引用生成",
        ("citation_agent", "synthesize"): "结果合成",
        
        # 详细处理流程（备选路径）
        ("simple_query", "knowledge_retrieval_detailed"): "详细检索",
        ("complex_query", "knowledge_retrieval_detailed"): "详细检索",
        ("knowledge_retrieval_detailed", "reasoning_analysis_detailed"): "详细推理",
        ("reasoning_analysis_detailed", "answer_generation_detailed"): "详细生成",
        ("answer_generation_detailed", "citation_generation_detailed"): "详细引用",
        ("citation_generation_detailed", "synthesize"): "结果合成",
        
        # 学习流程
        ("synthesize", "feedback_collection"): "收集反馈",
        ("feedback_collection", "learning_aggregation"): "聚合学习",
        ("learning_aggregation", "knowledge_distribution"): "知识分布",
        ("knowledge_distribution", "continuous_learning_monitor"): "持续监控",
        ("continuous_learning_monitor", "standardized_interface_adapter"): "接口适配",
        ("standardized_interface_adapter", "format"): "格式化输出",
        
        # 主流程
        ("synthesize", "format"): "格式化输出",
        ("format", "END"): "完成",
        ("format", "__end__"): "完成",
        
        # 向后兼容（旧版本节点）
        ("multi_agent_coordinate", "memory_agent"): "协调处理",
        ("multi_agent_coordinate", "chief_agent"): "协调处理",
        ("multi_agent_coordinate", "synthesize"): "结果合成",
    }
    
    # 🚀 新增：节点功能说明映射（用于 tooltip 显示）
    NODE_DESCRIPTIONS = {
        "route_query": "路由查询节点：分析查询复杂度并决定路由路径（simple/complex/reasoning/multi_agent）",
        "simple_query": "简单查询节点：快速检索知识库并生成简单答案，适用于复杂度较低的查询",
        "complex_query": "复杂查询节点：使用多步骤推理处理复杂查询，适用于需要深度分析的查询",
        "generate_steps": "生成推理步骤节点：将复杂查询分解为多个推理步骤，用于推理链处理",
        "execute_step": "执行步骤节点：执行单个推理步骤，收集相关证据",
        "gather_evidence": "收集证据节点：为当前推理步骤收集相关证据和知识",
        "extract_step_answer": "提取步骤答案节点：从证据中提取当前步骤的答案",
        "synthesize_reasoning_answer": "合成推理答案节点：将所有推理步骤的答案合成为最终答案",
        "chief_agent": "核心大脑节点：系统的核心协调组件，统一协调所有查询路径，选择最佳执行策略",
        "memory_agent": "记忆智能体节点：管理上下文和记忆，为后续智能体提供上下文信息",
        "knowledge_retrieval_agent": "知识检索智能体节点：从知识库中检索相关知识，提供证据和引用",
        "reasoning_agent": "推理智能体节点：进行深度推理分析，处理复杂逻辑关系。包含推理链能力（generate_steps, execute_step等），会根据needs_reasoning_chain标志自动选择推理模式",
        "answer_generation_agent": "答案生成智能体节点：基于检索的知识和推理结果生成最终答案",
        "citation_agent": "引用生成智能体节点：为答案生成准确的引用和来源标注",
        "synthesize": "结果合成节点：综合所有路径的结果，生成最终答案",
        "format": "格式化节点：格式化最终结果，准备输出",
        "query_analysis": "查询分析节点：分析查询类型、意图和特征",
        "scheduling_optimization": "调度优化节点：优化任务调度和执行顺序",
        "feedback_collection": "反馈收集节点：收集执行反馈和性能数据",
        "learning_aggregation": "学习聚合节点：聚合学习数据，优化系统性能",
        "knowledge_distribution": "知识分布节点：将学习到的知识分布到各个组件",
        "continuous_learning_monitor": "持续学习监控节点：监控系统学习效果和性能改进",
        "node_learning_monitor": "节点学习监控节点：多智能体协调路径中的轻量级监控节点，插入在各个智能体节点之间（如 memory_agent → node_learning_monitor → knowledge_retrieval_agent）。通过读取状态中的 node_execution_times 和 node_learning_data，实时监控最近执行的节点，如果节点成功率低则调整后续节点的超时或重试策略，并应用学习到的路由优化",
        "standardized_interface_adapter": "标准化接口适配器节点：提供统一的接口适配，支持不同能力组件",
        "capability_knowledge_retrieval": "知识检索能力节点：通过能力插件框架执行知识检索，从知识库中检索相关信息",
        "capability_reasoning": "推理能力节点：通过能力插件框架执行推理分析，基于证据进行逻辑推理",
        "capability_answer_generation": "答案生成能力节点：通过能力插件框架执行答案生成，基于上下文生成自然语言答案",
        "knowledge_retrieval_detailed": "详细知识检索节点：备选路径中的知识检索节点，仅在多智能体协调节点不可用时使用，从知识库中检索详细的相关信息",
        "reasoning_analysis_detailed": "详细推理分析节点：备选路径中的推理分析节点，仅在多智能体协调节点不可用时使用，进行详细的推理分析",
        "answer_generation_detailed": "详细答案生成节点：备选路径中的答案生成节点，仅在多智能体协调节点不可用时使用，基于检索的知识和推理结果生成详细答案",
        "citation_generation_detailed": "详细引用生成节点：备选路径中的引用生成节点，仅在多智能体协调节点不可用时使用，为答案生成详细的引用和来源标注",
        "multi_agent_subgraph": "多智能体协调子图：封装了完整的多智能体协调流程，包括核心大脑（ChiefAgent）和专家智能体序列（memory_agent → knowledge_retrieval_agent → reasoning_agent → answer_generation_agent → citation_agent）",
        "reasoning_path_subgraph": "推理路径子图：封装了推理链处理流程，包括生成推理步骤、执行步骤、收集证据、提取答案和合成推理答案",
    }
    
    # 定义节点分组（大的节点组）
    # 注意：multi_agent、detailed_processing 是互斥的路径（通过条件路由选择）
    # 它们不会同时执行，而是根据查询类型和复杂度选择其中一个路径
    # 🚀 修复：推理链是 reasoning_agent 的内部能力，不是独立的并行路径
    # 推理链节点（generate_steps, execute_step等）在 reasoning_agent 内部执行，不在主流程图中显示
    NODE_GROUPS = {
        # 注意：context_engineering、rag_retrieval、prompt_engineering 不再作为预处理节点
        # 它们在实际执行路径中由专家智能体内部使用，因此不在这里显示
        # "preprocessing": {
        #     "name": "预处理阶段",
        #     "nodes": ["context_engineering", "rag_retrieval", "prompt_engineering"],
        #     "collapsed": True,  # 默认折叠
        #     "description": "所有路径共享的预处理步骤"
        # },
        "analysis": {
            "name": "查询分析阶段",
            "nodes": ["query_analysis", "scheduling_optimization"],
            "collapsed": True,
            "description": "所有路径共享的分析步骤"
        },
        "multi_agent": {
            "name": "多智能体协调路径",
            "nodes": ["chief_agent", "memory_agent", "knowledge_retrieval_agent", "reasoning_agent", 
                     "answer_generation_agent", "citation_agent"],
            "collapsed": True,
            "description": "所有路径的基础机制：核心大脑（ChiefAgent）协调 → 专家智能体序列处理（顺序执行）。推理链能力集成在 reasoning_agent 内部，会根据 needs_reasoning_chain 标志自动选择推理模式"
        },
        # 🚀 移除：推理链不再是独立的并行路径
        # 推理链是 reasoning_agent 的内部能力，当 reasoning_agent 执行时，如果需要推理链，
        # 会在内部调用推理链能力（generate_steps, execute_step等），这些节点不在主流程图中显示
        # "reasoning": {
        #     "name": "推理链处理路径",
        #     "nodes": ["generate_steps", "execute_step", "gather_evidence", 
        #              "extract_step_answer", "synthesize_reasoning_answer"],
        #     "collapsed": True,
        #     "description": "推理路径：用于需要推理链的复杂查询（互斥路径）"
        # },
        # 🚀 为了完整显示系统架构，包含详细处理流程节点组（备选路径）
        # 这些节点在工作流图中可见，但可能不会被执行（取决于实际路由）
        # 执行时会根据实际情况高亮显示执行的节点
        "detailed_processing": {
            "name": "详细处理流程（备选）",
            "nodes": ["knowledge_retrieval_detailed", "reasoning_analysis_detailed",
                     "answer_generation_detailed", "citation_generation_detailed"],
            "collapsed": True,
            "description": "备选路径：仅在多智能体协调节点不可用时使用"
        },
        "synthesis": {
            "name": "结果合成",
            "nodes": ["synthesize", "format"],
            "collapsed": False,  # 默认展开
            "description": "所有路径最终汇聚到结果合成"
        },
        "learning": {
            "name": "学习流程",
            "nodes": ["feedback_collection", "learning_aggregation", "knowledge_distribution", 
                     "continuous_learning_monitor", "standardized_interface_adapter"],
            "collapsed": False,  # 🚀 修复：默认展开学习流程节点组，确保用户能看到学习流程节点
            "description": "学习流程：从 synthesize 开始，通过反馈收集、学习聚合、知识分布等步骤，最终连接到 format。这是主流程的增强路径，用于持续学习和优化。注意：node_learning_monitor 不属于学习流程，它是多智能体协调路径中的轻量级监控节点"
        }
    }
    
    # 独立节点（不属于任何组）
    # 🚀 为了完整显示系统架构，包含所有可能的节点
    # 执行时会根据实际情况高亮显示执行的节点
    # 注意：simple_query 和 complex_query 是路由节点，不是处理节点组，所以保持为独立节点
    STANDALONE_NODES = ["route_query", "simple_query", "complex_query"]
    
    def __init__(self):
        self.expanded_groups: Set[str] = set()  # 已展开的组
    
    def build_hierarchical_mermaid(self, nodes: List[str], edges: List[Any], 
                                   expanded_groups: Optional[Set[str]] = None) -> str:
        """构建分层的 Mermaid 图表
        
        Args:
            nodes: 节点列表
            edges: 边列表
            expanded_groups: 已展开的组（如果为 None，使用默认折叠状态）
        
        Returns:
            Mermaid 图表字符串
        """
        if expanded_groups is not None:
            self.expanded_groups = expanded_groups
        
        # 🚀 增强：如果节点列表为空或很少，尝试使用预定义的节点组来显示所有可能的节点
        # 这样可以确保即使某些节点不可达，也能显示完整的系统架构
        # 将节点列表转换为集合，以便快速查找（必须在所有使用之前定义）
        node_set = set(nodes)
        
        # 🚀 修复：先补充所有可能的节点，然后再推断边
        # 从节点组中提取所有可能的节点
        all_possible_nodes = set()
        for group_info in self.NODE_GROUPS.values():
            all_possible_nodes.update(group_info["nodes"])
        all_possible_nodes.update(self.STANDALONE_NODES)
        
        # 🚀 新增：定义推理链节点（这些节点是 reasoning_agent 的内部能力，不在主流程图中显示）
        reasoning_chain_nodes = {"generate_steps", "execute_step", "gather_evidence", 
                                 "extract_step_answer", "synthesize_reasoning_answer"}
        
        # 合并到节点列表（去重），但排除推理链节点
        original_count = len(nodes)
        for node in all_possible_nodes:
            if node not in node_set and node not in reasoning_chain_nodes:
                nodes.append(node)
                node_set.add(node)  # 同时更新 node_set
                logger.info(f"✅ [工作流图构建] 补充节点到显示列表: {node}")
        
        # 🚀 修复：确保学习流程节点被正确补充
        # 注意：node_learning_monitor 不属于学习流程，它是多智能体协调路径中的轻量级监控节点
        learning_nodes = ["feedback_collection", "learning_aggregation", "knowledge_distribution", 
                         "continuous_learning_monitor", "standardized_interface_adapter"]
        for node in learning_nodes:
            if node not in node_set:
                nodes.append(node)
                node_set.add(node)
                logger.info(f"✅ [工作流图构建] 强制补充学习流程节点: {node}")
        
        # 🚀 修复：确保 node_learning_monitor 被补充（它不属于学习流程，但需要显示）
        if "node_learning_monitor" not in node_set:
            nodes.append("node_learning_monitor")
            node_set.add("node_learning_monitor")
            logger.info(f"✅ [工作流图构建] 强制补充节点学习监控节点: node_learning_monitor")
        
        # 🚀 新增：如果节点列表中有推理链节点，记录但不显示（它们是 reasoning_agent 的内部能力）
        reasoning_nodes_in_list = [node for node in nodes if node in reasoning_chain_nodes]
        if reasoning_nodes_in_list:
            logger.info(f"📋 [工作流图构建] 检测到推理链节点（reasoning_agent内部能力，不在主流程图中显示）: {reasoning_nodes_in_list}")
            # 从节点列表中移除推理链节点，因为它们不在主流程图中显示
            nodes = [node for node in nodes if node not in reasoning_chain_nodes]
            node_set = set(nodes)  # 更新 node_set
        
        if len(nodes) > original_count:
            logger.info(f"📊 [工作流图构建] 节点总数: {len(nodes)} (原始: {original_count}, 补充: {len(nodes) - original_count})")
        
        # 🚀 修复：在构建节点映射之前，先收集所有属于节点组的节点
        # 这样可以在后续处理中避免将它们作为独立节点显示
        grouped_nodes = set()
        for group_id, group_info in self.NODE_GROUPS.items():
            grouped_nodes.update(group_info["nodes"])
        
        # 构建节点映射（节点名 -> 所属组）
        node_to_group: Dict[str, Optional[str]] = {}
        for group_id, group_info in self.NODE_GROUPS.items():
            for node in group_info["nodes"]:
                node_to_group[node] = group_id
        
        # 标记独立节点（确保独立节点不会被分配到任何组）
        for node in self.STANDALONE_NODES:
            node_to_group[node] = None
        
        # 🚀 修复：确保 node_set 在节点补充后是最新的（用于边的推断）
        # 重新构建 node_set，确保包含所有补充的节点
        node_set = set(nodes)
        
        # 构建 Mermaid 图表
        # 🚀 修复：使用 graph TD 并明确指定不自动推断边
        lines = ["graph TD"]
        
        # 添加独立节点（始终显示）
        # 🚀 增强：即使节点不在节点列表中，也显示独立节点（用于完整显示系统架构）
        # 🚀 修复：只显示真正的独立节点，不显示属于节点组的节点
        for node in self.STANDALONE_NODES:
            # 确保独立节点不在任何节点组中
            if node not in grouped_nodes:
                display_name = self._format_node_name(node)
                # 如果节点不在实际节点集合中，标记为不可达节点（灰色）
                if node in node_set:
                    lines.append(f"    {node}[{display_name}]")
                else:
                    lines.append(f"    {node}[{display_name}]:::unreachable")
                    logger.info(f"✅ [工作流图构建] 独立节点 '{node}' 不在节点列表中，但会显示（不可达）")
        
        # 添加节点组（根据展开状态）
        
        for group_id, group_info in self.NODE_GROUPS.items():
            # 🚀 增强：为了完整显示系统架构，即使节点不在节点集合中，也显示节点组
            # 查找属于该组的节点（在节点集合中存在）
            group_nodes = [n for n in group_info["nodes"] if n in node_set]
            # 如果节点组中的节点都不在节点集合中，但节点组定义了节点，也显示节点组（使用预定义的节点）
            if not group_nodes and group_info["nodes"]:
                # 使用预定义的节点（即使它们不在实际节点列表中）
                group_nodes = group_info["nodes"]
                logger.info(f"✅ [工作流图构建] 节点组 '{group_id}' 中的节点不在节点列表中，使用预定义节点: {group_nodes}")
            
            # 🚀 修复：确保学习流程节点组一定会显示
            if group_id == "learning" and not group_nodes and group_info["nodes"]:
                group_nodes = group_info["nodes"]
                logger.info(f"✅ [工作流图构建] 强制显示学习流程节点组，节点: {group_nodes}")
            
            if not group_nodes:
                logger.warning(f"⚠️ [工作流图构建] 节点组 '{group_id}' 没有节点，跳过显示")
                continue
            
            logger.info(f"✅ [工作流图构建] 处理节点组 '{group_id}'，包含 {len(group_nodes)} 个节点: {group_nodes}")
            
            is_expanded = group_id in self.expanded_groups
            
            if is_expanded:
                # 展开状态：显示子图内的所有节点
                lines.append(f"    subgraph {group_id}[\"{group_info['name']}\"]")
                for node in group_nodes:
                    display_name = self._format_node_name(node)
                    # 🚀 增强：如果节点不在实际节点集合中，标记为不可达节点（灰色）
                    node_style = ""
                    if node not in node_set:
                        node_style = ":::unreachable"
                    lines.append(f"        {node}[{display_name}]{node_style}")
                lines.append("    end")
            else:
                # 折叠状态：显示一个汇总节点
                group_node_id = f"{group_id}_group"
                # 🚀 修复：移除描述信息，描述只作为 tooltip 显示，不显示在节点标签上
                # 添加描述信息（如果是互斥路径）
                description = group_info.get('description', '')
                # 🚀 增强：使用预定义的节点数量（即使它们不在实际节点列表中）
                predefined_node_count = len(group_info["nodes"])
                actual_node_count = len([n for n in group_info["nodes"] if n in node_set])
                node_label = f"{group_info['name']} ({predefined_node_count}个节点)"
                if actual_node_count < predefined_node_count:
                    node_label += f" (实际: {actual_node_count})"
                # 🚀 修复：移除描述文字，描述只作为 tooltip 显示
                # if description:
                #     # Mermaid 支持换行，使用 <br/> 或 \n
                #     node_label += f"\\n({description})"
                # 🚀 修复：使用正确的 Mermaid 语法，节点组应该显示为一个节点
                # 注意：Mermaid 不支持自定义类名用于折叠，我们通过前端 JavaScript 处理点击事件
                lines.append(f"    {group_node_id}[\"{node_label}\"]")
                
                # 🚀 修复：确保节点组中的节点不会作为独立节点显示
                # 从 node_set 中移除这些节点，避免它们被后续逻辑作为独立节点添加
                for node in group_nodes:
                    if node in node_set:
                        node_set.discard(node)
                        logger.debug(f"✅ [工作流图构建] 节点 '{node}' 属于节点组 '{group_id}'，已从独立节点列表中移除")
        
        # 添加边（需要处理节点组的情况）
        # LangGraph 的边可能是多种格式，需要灵活处理
        processed_edges = set()  # 用于去重
        
        # 🚀 增强：总是尝试从节点关系推断边（补充 LangGraph 返回的边）
        # 这样可以确保即使 LangGraph 没有返回完整的边信息，也能显示基本的连接关系
        # 🚀 修复：边的推断必须在节点补充之后执行，这样 node_set 才包含所有节点
        # 🚀 修复：在推断边之前，需要恢复完整的节点集合（因为节点组折叠时节点被从 node_set 中移除了）
        # 创建一个完整的节点集合用于边的推断（包括所有补充的节点）
        full_node_set = set(nodes)  # 使用完整的 nodes 列表，而不是被修改过的 node_set
        original_edge_count = len(edges) if edges else 0
        logger.info(f"📊 [工作流图构建] 原始边数量: {original_edge_count}, 完整节点集合大小: {len(full_node_set)}")
        
        # 推断基本连接关系（基于节点名称和逻辑顺序）
        # 🚀 修复：使用 full_node_set 而不是 node_set，因为 node_set 在节点组折叠时被修改了
        inferred_edges = []
        
        # route_query → query_analysis → scheduling_optimization
        if "route_query" in full_node_set and "query_analysis" in full_node_set:
            inferred_edges.append(("route_query", "query_analysis"))
        if "query_analysis" in full_node_set and "scheduling_optimization" in full_node_set:
            inferred_edges.append(("query_analysis", "scheduling_optimization"))
        
        # 路由节点到各个路径的连接（条件路由）- 这些是分支边，使用虚线
        routing_node = "scheduling_optimization" if "scheduling_optimization" in full_node_set else "route_query"
        
        # scheduling_optimization/route_query → chief_agent (如果存在) - 分支边
        if routing_node in full_node_set and "chief_agent" in full_node_set:
            inferred_edges.append((routing_node, "chief_agent", True))  # True 表示虚线
        
        # 路由节点 → simple_query 和 complex_query（备选路径）- 分支边
        if routing_node in full_node_set and "simple_query" in full_node_set:
            inferred_edges.append((routing_node, "simple_query", True))  # True 表示虚线
        if routing_node in full_node_set and "complex_query" in full_node_set:
            inferred_edges.append((routing_node, "complex_query", True))  # True 表示虚线
        
        # 🚀 移除：推理链不是独立的并行路径
        # 推理链是 reasoning_agent 的内部能力，不需要从路由节点直接连接到推理链节点
        # 推理链节点（generate_steps, execute_step等）在 reasoning_agent 内部执行
        # if routing_node in full_node_set and "generate_steps" in full_node_set:
        #     inferred_edges.append((routing_node, "generate_steps", True))  # True 表示虚线
        
        # chief_agent → memory_agent
        if "chief_agent" in full_node_set and "memory_agent" in full_node_set:
            inferred_edges.append(("chief_agent", "memory_agent"))
        
        # 专家智能体序列
        if "memory_agent" in full_node_set and "knowledge_retrieval_agent" in full_node_set:
            inferred_edges.append(("memory_agent", "knowledge_retrieval_agent"))
        if "knowledge_retrieval_agent" in full_node_set and "reasoning_agent" in full_node_set:
            inferred_edges.append(("knowledge_retrieval_agent", "reasoning_agent"))
        if "reasoning_agent" in full_node_set and "answer_generation_agent" in full_node_set:
            inferred_edges.append(("reasoning_agent", "answer_generation_agent"))
        if "answer_generation_agent" in full_node_set and "citation_agent" in full_node_set:
            inferred_edges.append(("answer_generation_agent", "citation_agent"))
        if "citation_agent" in full_node_set and "synthesize" in full_node_set:
            inferred_edges.append(("citation_agent", "synthesize"))
        
        # 🚀 修复：如果 multi_agent_coordinate 存在（旧版本），将其连接到专家智能体序列
        # 注意：multi_agent_coordinate 节点在新版本中已被移除，但如果图中存在，应该正确连接
        # multi_agent_coordinate 实际上是 chief_agent 的别名/旧名称，应该与 chief_agent 有相同的连接关系
        if "multi_agent_coordinate" in full_node_set:
            # 确定路由节点（从哪里连接进来）
            routing_node_for_coordinate = "scheduling_optimization" if "scheduling_optimization" in full_node_set else "route_query"
            
            # 🚀 修复：总是为 multi_agent_coordinate 添加入边（从路由节点）
            # 即使 chief_agent 存在，multi_agent_coordinate 也应该被连接（可能是旧版本遗留）
            if routing_node_for_coordinate in full_node_set:
                inferred_edges.append((routing_node_for_coordinate, "multi_agent_coordinate"))
                logger.info(f"✅ [工作流图构建] 添加边: {routing_node_for_coordinate} → multi_agent_coordinate")
            
            # multi_agent_coordinate 连接到 memory_agent（专家智能体序列入口）
            if "memory_agent" in full_node_set:
                inferred_edges.append(("multi_agent_coordinate", "memory_agent"))
                logger.info(f"✅ [工作流图构建] 添加边: multi_agent_coordinate → memory_agent")
            elif "chief_agent" in full_node_set:
                # 如果 memory_agent 不存在但 chief_agent 存在，连接到 chief_agent
                inferred_edges.append(("multi_agent_coordinate", "chief_agent"))
                logger.info(f"✅ [工作流图构建] 添加边: multi_agent_coordinate → chief_agent")
            elif "synthesize" in full_node_set:
                # 如果没有智能体节点，直接连接到 synthesize
                inferred_edges.append(("multi_agent_coordinate", "synthesize"))
                logger.info(f"✅ [工作流图构建] 添加边: multi_agent_coordinate → synthesize")
            
            logger.info(f"✅ [工作流图构建] 为 multi_agent_coordinate 节点添加连接边完成")
        
        # 🚀 移除：推理链节点不在主流程图中显示
        # 推理链节点（generate_steps, execute_step, gather_evidence等）是 reasoning_agent 的内部能力
        # 当 reasoning_agent 执行时，如果需要推理链，会在内部调用这些节点
        # 这些节点不在主流程图中显示，因为它们不是独立的并行路径
        # 推理路径（已移除）
        # if "generate_steps" in full_node_set and "execute_step" in full_node_set:
        #     inferred_edges.append(("generate_steps", "execute_step"))
        # if "execute_step" in full_node_set and "gather_evidence" in full_node_set:
        #     inferred_edges.append(("execute_step", "gather_evidence"))
        # if "gather_evidence" in full_node_set and "extract_step_answer" in full_node_set:
        #     inferred_edges.append(("gather_evidence", "extract_step_answer"))
        # if "extract_step_answer" in full_node_set and "synthesize_reasoning_answer" in full_node_set:
        #     inferred_edges.append(("extract_step_answer", "synthesize_reasoning_answer"))
        # if "synthesize_reasoning_answer" in full_node_set and "synthesize" in full_node_set:
        #     inferred_edges.append(("synthesize_reasoning_answer", "synthesize"))
        
        # 详细处理流程（备选路径）- 这些是分支路径，使用虚线
        if "simple_query" in full_node_set and "knowledge_retrieval_detailed" in full_node_set:
            inferred_edges.append(("simple_query", "knowledge_retrieval_detailed", True))  # True 表示虚线
        if "complex_query" in full_node_set and "knowledge_retrieval_detailed" in full_node_set:
            inferred_edges.append(("complex_query", "knowledge_retrieval_detailed", True))  # True 表示虚线
        if "knowledge_retrieval_detailed" in full_node_set and "reasoning_analysis_detailed" in full_node_set:
            inferred_edges.append(("knowledge_retrieval_detailed", "reasoning_analysis_detailed", True))  # True 表示虚线
        if "reasoning_analysis_detailed" in full_node_set and "answer_generation_detailed" in full_node_set:
            inferred_edges.append(("reasoning_analysis_detailed", "answer_generation_detailed", True))  # True 表示虚线
        if "answer_generation_detailed" in full_node_set and "citation_generation_detailed" in full_node_set:
            inferred_edges.append(("answer_generation_detailed", "citation_generation_detailed", True))  # True 表示虚线
        if "citation_generation_detailed" in full_node_set and "synthesize" in full_node_set:
            inferred_edges.append(("citation_generation_detailed", "synthesize", True))  # True 表示虚线
        
        # 🚀 新增：学习流程的连接
        # synthesize → feedback_collection（学习流程入口）
        if "synthesize" in full_node_set and "feedback_collection" in full_node_set:
            inferred_edges.append(("synthesize", "feedback_collection", True))  # True 表示虚线（学习流程）
        # feedback_collection → learning_aggregation
        if "feedback_collection" in full_node_set and "learning_aggregation" in full_node_set:
            inferred_edges.append(("feedback_collection", "learning_aggregation", True))  # True 表示虚线
        # learning_aggregation → knowledge_distribution
        if "learning_aggregation" in full_node_set and "knowledge_distribution" in full_node_set:
            inferred_edges.append(("learning_aggregation", "knowledge_distribution", True))  # True 表示虚线
        # knowledge_distribution → continuous_learning_monitor
        if "knowledge_distribution" in full_node_set and "continuous_learning_monitor" in full_node_set:
            inferred_edges.append(("knowledge_distribution", "continuous_learning_monitor", True))  # True 表示虚线
        # continuous_learning_monitor → standardized_interface_adapter
        if "continuous_learning_monitor" in full_node_set and "standardized_interface_adapter" in full_node_set:
            inferred_edges.append(("continuous_learning_monitor", "standardized_interface_adapter", True))  # True 表示虚线
        # standardized_interface_adapter → format（学习流程最终连接到format）
        if "standardized_interface_adapter" in full_node_set and "format" in full_node_set:
            inferred_edges.append(("standardized_interface_adapter", "format", True))  # True 表示虚线
        
        # synthesize → format（主流程直接路径）
        if "synthesize" in full_node_set and "format" in full_node_set:
            inferred_edges.append(("synthesize", "format"))
        
        # format → END（工作流结束）
        # 🚀 修复：确保 END 节点在最后一步
        if "format" in full_node_set:
            # END 是 LangGraph 的特殊节点，在 Mermaid 中通常显示为 __end__ 或 END
            # 检查节点列表中是否有 END 或 __end__ 节点
            end_node = None
            for node in nodes:
                node_str = str(node).lower()
                if node_str in ["end", "__end__", "__end"]:
                    end_node = node
                    break
            
            # 如果没有找到 END 节点，添加一个（Mermaid 会自动处理）
            if end_node:
                inferred_edges.append(("format", end_node))
            else:
                # 🚀 修复：即使节点列表中没有 END，也添加 format → END 的边
                # Mermaid 会自动创建 END 节点
                inferred_edges.append(("format", "END"))
        
        # 合并推断的边到 edges 列表（去重）
        edges = list(edges) if edges else []
        existing_edges_set = set()
        
        # 🚀 修复：在处理原始边时也排除不应该存在的边
        filtered_edges = []
        for edge in edges:
            source = None
            target = None
            
            # 提取边的源和目标
            if isinstance(edge, (tuple, list)) and len(edge) >= 2:
                source = str(edge[0])
                target = str(edge[1])
            elif isinstance(edge, dict):
                source = str(edge.get('source') or edge.get('from') or edge.get('start') or '')
                target = str(edge.get('target') or edge.get('to') or edge.get('end') or '')
            
            if not source or not target:
                continue
            
            # 🚀 修复：排除 simple_query 和 complex_query 之间的边（更彻底的检查）
            source_lower = source.lower()
            target_lower = target.lower()
            if (source_lower == "simple_query" and target_lower == "complex_query") or \
               (source_lower == "complex_query" and target_lower == "simple_query"):
                logger.debug(f"⏭️ [工作流图构建] 排除互斥路径之间的边（原始边）: {source} <-> {target}")
                continue
            
            # 🚀 修复：保留 synthesize → feedback_collection 的边，但标记为虚线（学习流程）
            # feedback_collection 流程是主流程的一部分（从 synthesize 开始，最终连接到 format）
            # 但为了区分主流程和学习流程，使用虚线显示学习流程
            # 注意：synthesize 可以同时连接到 feedback_collection 和 format（并行执行）
            
            # 保留有效的边
            filtered_edges.append(edge)
            existing_edges_set.add((source, target))
        
        edges = filtered_edges
        
        # 🚀 修复：分离 format → END 边，确保它最后处理
        # 🚀 修复：同时过滤掉不应该存在的推断边
        format_to_end_edges = []
        other_inferred_edges = []
        for e in inferred_edges:
            if len(e) < 2:
                continue
            
            source = str(e[0])
            target = str(e[1])
            source_lower = source.lower()
            target_lower = target.lower()
            
            # 🚀 修复：排除 simple_query 和 complex_query 之间的推断边
            if (source_lower == "simple_query" and target_lower == "complex_query") or \
               (source_lower == "complex_query" and target_lower == "simple_query"):
                logger.debug(f"⏭️ [工作流图构建] 排除互斥路径之间的推断边: {source} <-> {target}")
                continue
            
            # 🚀 修复：保留 synthesize → feedback_collection 的推断边，但标记为虚线（学习流程）
            # feedback_collection 流程是主流程的一部分，应该显示，但用虚线区分学习流程
            # 学习链的推断边会在后续处理中标记为虚线，这里不排除
            
            # 分离 format → END 边
            if (target.upper() in ["END", "__END__", "__END"] or 
                source == "format" and target.upper() in ["END", "__END__", "__END"]):
                format_to_end_edges.append(e)
            else:
                other_inferred_edges.append(e)
        
        # 先添加其他边
        new_edges = [e for e in other_inferred_edges if (str(e[0]), str(e[1])) not in existing_edges_set]
        edges.extend(new_edges)
        
        # 更新 existing_edges_set
        for e in new_edges:
            existing_edges_set.add((str(e[0]), str(e[1])))
        
        # 最后添加 format → END 边（确保 END 在最后）
        for e in format_to_end_edges:
            if (str(e[0]), str(e[1])) not in existing_edges_set:
                edges.append(e)
                existing_edges_set.add((str(e[0]), str(e[1])))
        logger.info(f"✅ [工作流图构建] 推断出 {len(new_edges)} 条新边（共 {len(inferred_edges)} 条推断边），总边数: {len(edges)}")
        if new_edges:
            logger.info(f"📋 [工作流图构建] 新推断的边: {new_edges[:10]}...")  # 只显示前10条
        
        # 🚀 调试：记录所有边的信息
        logger.info(f"📊 [工作流图构建] 开始处理 {len(edges)} 条边")
        
        for edge in edges:
            source = None
            target = None
            
            # 尝试多种边格式
            if isinstance(edge, dict):
                source = edge.get('source') or edge.get('from') or edge.get('start')
                target = edge.get('target') or edge.get('to') or edge.get('end')
            elif isinstance(edge, tuple) or isinstance(edge, list):
                if len(edge) >= 2:
                    source = edge[0]
                    target = edge[1]
            elif hasattr(edge, 'source') and hasattr(edge, 'target'):
                source = edge.source
                target = edge.target
            elif hasattr(edge, 'from_node') and hasattr(edge, 'to_node'):
                source = edge.from_node
                target = edge.to_node
            
            if not source or not target:
                continue
            
            # 转换为字符串（如果是对象）
            source = str(source) if source else None
            target = str(target) if target else None
            
            if not source or not target:
                continue
            
            # 处理源节点和目标节点可能属于组的情况
            source_group = node_to_group.get(source)
            target_group = node_to_group.get(target)
            
            # 🚀 修复：如果节点在折叠的组中，使用组节点
            # 但需要确保组节点已经添加到图中
            original_source = source
            original_target = target
            if source_group and source_group not in self.expanded_groups:
                source = f"{source_group}_group"
                logger.debug(f"🔄 [工作流图构建] 源节点 '{original_source}' 属于折叠组 '{source_group}'，映射到 '{source}'")
            if target_group and target_group not in self.expanded_groups:
                target = f"{target_group}_group"
                logger.debug(f"🔄 [工作流图构建] 目标节点 '{original_target}' 属于折叠组 '{target_group}'，映射到 '{target}'")
            
            # 🚀 修复：如果源节点或目标节点是独立节点，但连接到节点组，确保边仍然添加
            # 例如：route_query (独立节点) → analysis_group (节点组)
            
            # 🚀 修复：排除不应该存在的边
            # 1. simple_query 和 complex_query 是互斥的路径，它们之间不应该有边
            # 2. synthesize 应该直接连接到 format，然后 format → END，不应该连接到 feedback_collection
            # 检查原始节点和目标节点（在节点组映射之前）
            if (original_source == "simple_query" and original_target == "complex_query") or \
               (original_source == "complex_query" and original_target == "simple_query"):
                logger.debug(f"⏭️ [工作流图构建] 排除互斥路径之间的边: {original_source} <-> {original_target}")
                continue
            # 🚀 修复：保留 synthesize → feedback_collection 的边（学习流程）
            # 学习流程是主流程的增强路径：synthesize → feedback_collection → learning_aggregation → 
            # knowledge_distribution → continuous_learning_monitor → standardized_interface_adapter → format
            # 学习流程的边会在后续处理中标记为虚线，以区分主流程和学习流程
            # 这里不排除学习流程的边
            
            # 去重：避免重复的边
            edge_key = (source, target)
            if edge_key not in processed_edges:
                processed_edges.add(edge_key)
                
                # 🚀 修复：检查是否是分支边（虚线）
                # 判断是否是分支边：从路由节点出发的边，或者备选路径的边，或者学习流程的边
                is_dashed = False
                routing_nodes = {"route_query", "scheduling_optimization"}
                branch_targets = {"simple_query", "complex_query", "chief_agent", 
                                 "knowledge_retrieval_detailed", "reasoning_analysis_detailed", 
                                 "answer_generation_detailed", "citation_generation_detailed"}
                learning_chain_nodes = {"feedback_collection", "learning_aggregation", 
                                       "knowledge_distribution", "continuous_learning_monitor", 
                                       "standardized_interface_adapter"}
                
                # 检查边是否来自推断的边列表（包含虚线标记）
                # 🚀 修复：使用更新后的 edges 列表（包含 format → END）
                for inferred_edge in edges:
                    if isinstance(inferred_edge, (tuple, list)) and len(inferred_edge) >= 3 and inferred_edge[2] is True:
                        if str(inferred_edge[0]) == original_source and str(inferred_edge[1]) == original_target:
                            is_dashed = True
                            break
                    # 也检查原始的 inferred_edges（向后兼容）
                    elif isinstance(inferred_edge, (tuple, list)) and len(inferred_edge) >= 2:
                        # 检查是否是分支边
                        if str(inferred_edge[0]) == original_source and str(inferred_edge[1]) == original_target:
                            # 检查是否是分支目标节点
                            if original_source in routing_nodes or original_source in branch_targets or original_target in branch_targets:
                                is_dashed = True
                                break
                
                # 或者根据节点类型判断
                if not is_dashed:
                    if original_source in routing_nodes or original_source in branch_targets or original_target in branch_targets:
                        is_dashed = True
                    # 🚀 修复：学习流程是主流程的一部分，使用实线（不是分支）
                    # 虚线只用于表示条件分支或备选路径，学习流程是主流程的连续部分
                
                # 🚀 新增：获取边的说明（用于边的标签）
                # 优先使用原始节点名称查找边的说明（因为EDGE_DESCRIPTIONS使用的是原始节点名称）
                edge_key = (original_source, original_target)
                edge_label = self.EDGE_DESCRIPTIONS.get(edge_key)
                
                # 🚀 调试：如果没找到说明，尝试使用组节点名称查找（用于子图内部的边）
                if not edge_label and source != original_source or target != original_target:
                    # 如果节点被映射到组，尝试查找组内部的边说明
                    # 但通常子图内部的边说明应该在子图展开时处理
                    pass
                
                # 🚀 调试：记录边的说明查找结果
                if edge_label:
                    logger.info(f"✅ [工作流图构建] 找到边的说明: {original_source} → {original_target}: {edge_label}")
                else:
                    logger.debug(f"🔍 [工作流图构建] 未找到边的说明: {original_source} → {original_target}")
                
                # 根据是否是虚线选择不同的 Mermaid 语法，并添加标签（如果有）
                if is_dashed:
                    if edge_label:
                        lines.append(f"    {source} -.->|{edge_label}| {target}")
                        logger.info(f"✅ [工作流图构建] 添加带标签的虚线边: {source} -.->|{edge_label}| {target}")
                    else:
                        lines.append(f"    {source} -.-> {target}")
                        logger.debug(f"✅ [工作流图构建] 添加虚线边: {source} -.-> {target}")
                else:
                    if edge_label:
                        lines.append(f"    {source} -->|{edge_label}| {target}")
                        logger.info(f"✅ [工作流图构建] 添加带标签的实线边: {source} -->|{edge_label}| {target}")
                    else:
                        lines.append(f"    {source} --> {target}")
                        logger.debug(f"✅ [工作流图构建] 添加实线边: {source} --> {target}")
            else:
                logger.debug(f"⏭️ [工作流图构建] 跳过重复边: {source} --> {target}")
        
        # 🚀 修复：确保 format → END 边最后添加（如果还没有添加）
        # 检查是否已经有 format → END 的边
        has_format_to_end = False
        for edge_key in processed_edges:
            if edge_key[0] == "format" and (edge_key[1].upper() in ["END", "__END__", "__END"] or 
                                             "end" in str(edge_key[1]).lower()):
                has_format_to_end = True
                break
        
        # 如果没有 format → END 边，添加它（确保 END 在最后）
        if not has_format_to_end and "format" in node_set:
            lines.append("    format --> END")
            processed_edges.add(("format", "END"))
            logger.info("✅ [工作流图构建] 添加 format → END 边（确保 END 在最后）")
        
        # 🚀 调试：记录最终生成的边数量
        logger.info(f"📊 [工作流图构建] 最终生成 {len(processed_edges)} 条边（去重后）")
        if len(processed_edges) == 0:
            logger.warning("⚠️ [工作流图构建] 没有生成任何边！这可能导致节点显示为孤立状态")
        
        # 添加样式定义
        lines.append("    classDef collapsible fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,cursor:pointer")
        # 🚀 新增：不可达节点样式（灰色，表示节点存在但可能不会被执行）
        lines.append("    classDef unreachable fill:#f5f5f5,stroke:#cccccc,stroke-width:1px,stroke-dasharray: 3 3")
        
        # 🚀 修复：为所有节点组节点添加 collapsible 类（通过前端 JavaScript 处理点击事件）
        for group_id in self.NODE_GROUPS.keys():
            group_node_id = f"{group_id}_group"
            lines.append(f"    class {group_node_id} collapsible")
        
        return "\n".join(lines)
    
    def _format_node_name(self, node_name: str) -> str:
        """格式化节点名称（用于显示）"""
        # 将下划线分隔的名称转换为标题格式
        return node_name.replace('_', ' ').title()
    
    def get_node_group_info(self) -> Dict[str, Dict[str, Any]]:
        """获取节点组信息（用于前端）"""
        return {
            group_id: {
                "name": group_info["name"],
                "nodes": group_info["nodes"],
                "collapsed": group_id not in self.expanded_groups,
                "description": group_info.get("description", "")  # 🚀 新增：包含节点组描述
            }
            for group_id, group_info in self.NODE_GROUPS.items()
        }
    
    def get_node_descriptions(self, workflow=None) -> Dict[str, str]:
        """
        获取节点功能说明映射（用于 tooltip）
        
        🚀 增强：优先从节点函数的docstring动态提取说明，如果没有则使用硬编码的说明
        这样当节点功能发生变化时，说明会自动更新
        
        Args:
            workflow: LangGraph工作流对象（可选），如果提供则尝试动态提取节点说明
        
        Returns:
            节点名称到说明的映射字典
        """
        descriptions = self.NODE_DESCRIPTIONS.copy()
        
        # 🚀 新增：添加节点组说明（节点组不是实际节点函数，无法从工作流提取）
        for group_id, group_info in self.NODE_GROUPS.items():
            if group_id not in descriptions:
                # 使用节点组的description作为说明
                group_desc = group_info.get("description", "")
                if group_desc:
                    descriptions[group_id] = group_desc
                    logger.debug(f"✅ [节点说明] 添加节点组 '{group_id}' 的说明")
        
        # 🚀 新增：如果提供了工作流对象，尝试动态提取节点说明
        if workflow is not None:
            try:
                dynamic_descriptions = self._extract_node_descriptions_from_workflow(workflow)
                # 合并动态说明（优先使用动态说明，但排除默认值）
                for node_name, desc in dynamic_descriptions.items():
                    # 🚀 修复：检查是否是默认值（"Node in a graph." 或 "Node in graph"）
                    desc_lower = desc.lower().strip() if desc else ''
                    is_default_value = (
                        desc_lower in ['node in a graph.', 'node in graph', 'node in graph.', 'node', ''] or
                        'node in graph' in desc_lower or
                        desc_lower == 'node in a graph'
                    )
                    
                    if desc and not is_default_value:
                        # 不是默认值，使用动态说明
                        descriptions[node_name] = desc
                        logger.debug(f"✅ [节点说明] 从docstring动态提取节点 '{node_name}' 的说明: {desc[:50]}")
                    else:
                        # 动态说明是默认值或无效，使用硬编码说明
                        if node_name in self.NODE_DESCRIPTIONS:
                            descriptions[node_name] = self.NODE_DESCRIPTIONS[node_name]
                            logger.warning(f"⚠️ [节点说明] 节点 '{node_name}' 的动态说明是默认值 ('{desc}')，使用硬编码说明")
                        else:
                            # 既没有动态说明，也没有硬编码说明，记录警告
                            logger.warning(f"⚠️ [节点说明] 节点 '{node_name}' 没有说明（动态: {desc}, 硬编码: 无）")
                
                # 🚀 修复：确保所有在NODE_DESCRIPTIONS中的节点都有说明（即使动态提取没有找到）
                # 同时检查并替换任何默认值
                for node_name in self.NODE_DESCRIPTIONS:
                    if node_name not in descriptions:
                        descriptions[node_name] = self.NODE_DESCRIPTIONS[node_name]
                        logger.debug(f"✅ [节点说明] 节点 '{node_name}' 使用硬编码说明（动态提取未找到）")
                    else:
                        # 🚀 修复：即使动态提取找到了说明，也要检查是否是默认值
                        desc_value = descriptions[node_name]
                        desc_lower = desc_value.lower().strip() if desc_value else ''
                        is_default = (
                            desc_lower in ['node in a graph.', 'node in graph', 'node in graph.', 'node', ''] or
                            'node in graph' in desc_lower or
                            desc_lower == 'node in a graph'
                        )
                        if is_default:
                            descriptions[node_name] = self.NODE_DESCRIPTIONS[node_name]
                            logger.warning(f"⚠️ [节点说明] 节点 '{node_name}' 的动态说明是默认值，已替换为硬编码说明")
                
                # 🚀 修复：最后检查，确保没有默认值
                def is_default_description(desc: str) -> bool:
                    """检查是否是默认值说明"""
                    if not desc:
                        return True
                    desc_lower = desc.lower().strip()
                    return (
                        desc_lower in ['node in a graph.', 'node in graph', 'node in graph.', 'node', ''] or
                        'node in graph' in desc_lower or
                        desc_lower == 'node in a graph'
                    )
                
                final_check = {}
                filtered_count = 0
                for node_name, desc in descriptions.items():
                    if desc and not is_default_description(desc):
                        # 不是默认值，保留
                        final_check[node_name] = desc
                    else:
                        # 是默认值或被过滤掉，尝试使用硬编码说明
                        filtered_count += 1
                        if node_name in self.NODE_DESCRIPTIONS:
                            hardcoded_desc = self.NODE_DESCRIPTIONS[node_name]
                            # 确保硬编码说明也不是默认值
                            if hardcoded_desc and not is_default_description(hardcoded_desc):
                                final_check[node_name] = hardcoded_desc
                            else:
                                logger.warning(f"⚠️ [节点说明] 节点 '{node_name}' 的硬编码说明也是默认值，跳过")
                        else:
                            logger.debug(f"⚠️ [节点说明] 节点 '{node_name}' 没有有效的说明（动态: {desc}, 硬编码: 无）")
                
                if filtered_count > 0:
                    logger.warning(f"⚠️ [节点说明] 过滤掉了 {filtered_count} 个默认值说明")
                descriptions = final_check
                
            except Exception as e:
                logger.warning(f"⚠️ [节点说明] 动态提取节点说明失败: {e}，使用硬编码说明")
                import traceback
                logger.debug(f"详细错误:\n{traceback.format_exc()}")
        
        # 🚀 修复：明确过滤掉 LangGraph 内部节点（__start__, __end__）的说明
        # 这些节点不应该有说明，因为它们是 LangGraph 自动生成的内部节点
        # 注意：这个过滤必须在最后执行，无论前面的代码是否成功
        langgraph_internal_nodes = ['__start__', '__end__', '__START__', '__END__', 'START', 'END']
        for internal_node in langgraph_internal_nodes:
            if internal_node in descriptions:
                del descriptions[internal_node]
                logger.debug(f"✅ [节点说明] 已过滤掉 LangGraph 内部节点 '{internal_node}' 的说明")
        
        # 🚀 修复：同时过滤掉包含 LangGraph 默认说明的节点
        # 这些说明通常是 "A node in a Pregel graph" 或类似内容
        langgraph_default_patterns = [
            'a node in a pregel graph',
            'node in a pregel graph',
            'a node in a graph',
            'this won\'t be invoked',
            'won\'t be invoked'
        ]
        nodes_to_remove = []
        for node_name, desc in descriptions.items():
            if desc:
                desc_lower = desc.lower().strip()
                if any(pattern in desc_lower for pattern in langgraph_default_patterns):
                    nodes_to_remove.append(node_name)
                    logger.debug(f"✅ [节点说明] 已过滤掉包含 LangGraph 默认说明的节点 '{node_name}': {desc[:50]}")
        
        for node_name in nodes_to_remove:
            del descriptions[node_name]
        
        return descriptions
    
    def _extract_node_descriptions_from_workflow(self, workflow) -> Dict[str, str]:
        """
        从LangGraph工作流对象中提取节点函数的docstring
        
        Args:
            workflow: LangGraph工作流对象（编译后的workflow）
        
        Returns:
            节点名称到说明的映射字典
        """
        descriptions = {}
        
        # 🚀 修复：明确排除 LangGraph 内部节点（__start__, __end__）
        # 这些节点不应该有说明，因为它们是 LangGraph 自动生成的内部节点
        langgraph_internal_nodes = {'__start__', '__end__', '__START__', '__END__', 'START', 'END'}
        
        # 🚀 新增：首先尝试从原始类方法和函数中提取docstring（最可靠的方法）
        try:
            from src.core.langgraph_unified_workflow import UnifiedResearchWorkflow
            from src.core.langgraph_agent_nodes import AgentNodes
            from src.core.langgraph_reasoning_nodes import ReasoningNodes
            from src.core.langgraph_detailed_processing_nodes import DetailedProcessingNodes
            from src.core.langgraph_core_nodes import CoreNodes
            from src.core.langgraph_config_nodes import feedback_collection_node
            from src.core.langgraph_learning_nodes import (
                learning_aggregation_node,
                continuous_learning_monitor
            )
            from src.core.langgraph_capability_nodes import standardized_interface_adapter
            
            # 节点名称到原始类方法的映射
            node_to_method_map = {
                'route_query': (UnifiedResearchWorkflow, '_route_query_node'),
                'simple_query': (UnifiedResearchWorkflow, '_simple_query_node'),
                'complex_query': (UnifiedResearchWorkflow, '_complex_query_node'),
                'synthesize': (UnifiedResearchWorkflow, '_synthesize_node'),
                'format': (UnifiedResearchWorkflow, '_format_node'),
                'chief_agent': (AgentNodes, 'chief_agent_node'),
                'memory_agent': (AgentNodes, 'memory_agent_node'),
                'knowledge_retrieval_agent': (AgentNodes, 'knowledge_retrieval_agent_node'),
                'reasoning_agent': (AgentNodes, 'reasoning_agent_node'),
                'answer_generation_agent': (AgentNodes, 'answer_generation_agent_node'),
                'citation_agent': (AgentNodes, 'citation_agent_node'),
                'generate_steps': (ReasoningNodes, 'generate_steps_node'),
                'execute_step': (ReasoningNodes, 'execute_step_node'),
                'gather_evidence': (ReasoningNodes, 'gather_evidence_node'),
                'extract_step_answer': (ReasoningNodes, 'extract_step_answer_node'),
                'synthesize_reasoning_answer': (ReasoningNodes, 'synthesize_answer_node'),
                'query_analysis': (DetailedProcessingNodes, 'query_analysis_node'),
                'scheduling_optimization': (DetailedProcessingNodes, 'scheduling_optimization_node'),
                'rag_retrieval': (CoreNodes, 'rag_retrieval_node'),
                'prompt_engineering': (CoreNodes, 'prompt_engineering_node'),
                'context_engineering': (CoreNodes, 'context_engineering_node'),
            }
            
            # 节点名称到原始函数的映射（独立函数，不是类方法）
            node_to_function_map = {
                'feedback_collection': feedback_collection_node,
                'learning_aggregation': learning_aggregation_node,
                'continuous_learning_monitor': continuous_learning_monitor,
                'standardized_interface_adapter': standardized_interface_adapter,
            }
            
            # 从原始类方法中提取docstring
            for node_name, (cls, method_name) in node_to_method_map.items():
                try:
                    if hasattr(cls, method_name):
                        method = getattr(cls, method_name)
                        if hasattr(method, '__doc__') and method.__doc__:
                            doc = method.__doc__.strip()
                            # 检查是否是默认值
                            doc_lower = doc.lower().strip()
                            is_default = (
                                doc_lower in ['node in a graph.', 'node in graph', 'node in graph.', 'node', ''] or
                                'node in graph' in doc_lower or
                                doc_lower == 'node in a graph'
                            )
                            if doc and not is_default:
                                # 格式化docstring
                                formatted_desc = self._format_docstring(doc)
                                if formatted_desc:
                                    descriptions[node_name] = formatted_desc
                                    logger.debug(f"✅ [节点说明] 从原始类方法提取节点 '{node_name}' 的说明: {formatted_desc[:50]}")
                except Exception as e:
                    logger.debug(f"⚠️ [节点说明] 从原始类方法提取节点 '{node_name}' 的说明失败: {e}")
            
            # 从原始函数中提取docstring
            for node_name, func in node_to_function_map.items():
                try:
                    if func and hasattr(func, '__doc__') and func.__doc__:
                        doc = func.__doc__.strip()
                        # 检查是否是默认值
                        doc_lower = doc.lower().strip()
                        is_default = (
                            doc_lower in ['node in a graph.', 'node in graph', 'node in graph.', 'node', ''] or
                            'node in graph' in doc_lower or
                            doc_lower == 'node in a graph'
                        )
                        if doc and not is_default:
                            # 格式化docstring
                            formatted_desc = self._format_docstring(doc)
                            if formatted_desc:
                                descriptions[node_name] = formatted_desc
                                logger.debug(f"✅ [节点说明] 从原始函数提取节点 '{node_name}' 的说明: {formatted_desc[:50]}")
                except Exception as e:
                    logger.debug(f"⚠️ [节点说明] 从原始函数提取节点 '{node_name}' 的说明失败: {e}")
        except Exception as e:
            logger.debug(f"⚠️ [节点说明] 从原始类方法和函数提取说明失败: {e}")
        
        try:
            # 方法1: 尝试从workflow的nodes属性获取节点函数
            if hasattr(workflow, 'nodes'):
                nodes_dict = workflow.nodes
                if isinstance(nodes_dict, dict):
                    for node_name, node_func in nodes_dict.items():
                        # 🚀 修复：优先检查是否是子图节点
                        if self._is_subgraph_node(node_func):
                            # 从子图内部提取节点说明
                            subgraph_descriptions = self._extract_subgraph_descriptions(node_func)
                            descriptions.update(subgraph_descriptions)
                            # 为子图节点本身添加说明
                            if node_name not in descriptions and node_name in self.NODE_DESCRIPTIONS:
                                descriptions[node_name] = self.NODE_DESCRIPTIONS[node_name]
                            elif node_name not in descriptions:
                                # 即使没有硬编码说明，也记录子图节点
                                logger.debug(f"⚠️ [节点说明] 子图节点 '{node_name}' 没有硬编码说明")
                        else:
                            # 普通节点，提取docstring
                            # 🚀 修复：只有在原始类方法中没有找到说明时，才从工作流中提取
                            if node_name not in descriptions:
                                desc = self._extract_docstring(node_func)
                                # 🚀 修复：如果提取的说明是默认值（如"Node in graph"），则忽略，使用硬编码说明
                                if desc and desc.lower().strip() not in ['node in graph', 'node', '']:
                                    if 'node in graph' not in desc.lower():
                                        descriptions[node_name] = desc
                                    elif node_name in self.NODE_DESCRIPTIONS:
                                        descriptions[node_name] = self.NODE_DESCRIPTIONS[node_name]
                                elif node_name in self.NODE_DESCRIPTIONS:
                                    # 没有动态说明，使用硬编码说明
                                    descriptions[node_name] = self.NODE_DESCRIPTIONS[node_name]
            
            # 方法2: 尝试从workflow的graph获取节点
            if hasattr(workflow, 'get_graph'):
                graph = workflow.get_graph()
                if hasattr(graph, 'nodes'):
                    # graph.nodes可能是节点列表或字典
                    if isinstance(graph.nodes, dict):
                        for node_name, node_func in graph.nodes.items():
                            if self._is_subgraph_node(node_func):
                                subgraph_descriptions = self._extract_subgraph_descriptions(node_func)
                                descriptions.update(subgraph_descriptions)
                                if node_name not in descriptions and node_name in self.NODE_DESCRIPTIONS:
                                    descriptions[node_name] = self.NODE_DESCRIPTIONS[node_name]
                            else:
                                # 🚀 修复：只有在原始类方法中没有找到说明时，才从工作流中提取
                                if node_name not in descriptions:
                                    desc = self._extract_docstring(node_func)
                                    if desc and desc.lower().strip() not in ['node in graph', 'node', '']:
                                        if 'node in graph' not in desc.lower():
                                            descriptions[node_name] = desc
                                        elif node_name in self.NODE_DESCRIPTIONS:
                                            descriptions[node_name] = self.NODE_DESCRIPTIONS[node_name]
                                    elif node_name in self.NODE_DESCRIPTIONS:
                                        descriptions[node_name] = self.NODE_DESCRIPTIONS[node_name]
                    elif isinstance(graph.nodes, (list, set)):
                        # 如果是列表，尝试通过节点名称获取函数
                        for node_name in graph.nodes:
                            if hasattr(workflow, 'nodes') and isinstance(workflow.nodes, dict):
                                node_func = workflow.nodes.get(node_name)
                                if node_func:
                                    if self._is_subgraph_node(node_func):
                                        subgraph_descriptions = self._extract_subgraph_descriptions(node_func)
                                        descriptions.update(subgraph_descriptions)
                                        if node_name not in descriptions and node_name in self.NODE_DESCRIPTIONS:
                                            descriptions[node_name] = self.NODE_DESCRIPTIONS[node_name]
                                    else:
                                        desc = self._extract_docstring(node_func)
                                        if desc and desc.lower().strip() not in ['node in graph', 'node', '']:
                                            if 'node in graph' not in desc.lower():
                                                descriptions[node_name] = desc
                                            elif node_name in self.NODE_DESCRIPTIONS:
                                                descriptions[node_name] = self.NODE_DESCRIPTIONS[node_name]
                                        elif node_name in self.NODE_DESCRIPTIONS:
                                            descriptions[node_name] = self.NODE_DESCRIPTIONS[node_name]
            
            # 方法3: 尝试从编译后的workflow的内部结构获取
            # LangGraph的编译后的workflow可能有_builder属性
            if hasattr(workflow, '_builder'):
                builder = workflow._builder
                if hasattr(builder, '_nodes'):
                    nodes_dict = builder._nodes
                    if isinstance(nodes_dict, dict):
                        for node_name, node_func in nodes_dict.items():
                            if self._is_subgraph_node(node_func):
                                subgraph_descriptions = self._extract_subgraph_descriptions(node_func)
                                descriptions.update(subgraph_descriptions)
                                if node_name not in descriptions and node_name in self.NODE_DESCRIPTIONS:
                                    descriptions[node_name] = self.NODE_DESCRIPTIONS[node_name]
                            else:
                                # 🚀 修复：只有在原始类方法中没有找到说明时，才从工作流中提取
                                if node_name not in descriptions:
                                    desc = self._extract_docstring(node_func)
                                    if desc and desc.lower().strip() not in ['node in graph', 'node', '']:
                                        if 'node in graph' not in desc.lower():
                                            descriptions[node_name] = desc
                                        elif node_name in self.NODE_DESCRIPTIONS:
                                            descriptions[node_name] = self.NODE_DESCRIPTIONS[node_name]
                                    elif node_name in self.NODE_DESCRIPTIONS:
                                        descriptions[node_name] = self.NODE_DESCRIPTIONS[node_name]
            
            # 🚀 修复：过滤掉 LangGraph 内部节点（__start__, __end__）和包含默认说明的节点
            filtered_descriptions = {}
            langgraph_default_patterns = [
                'a node in a pregel graph',
                'node in a pregel graph',
                'a node in a graph',
                'this won\'t be invoked',
                'won\'t be invoked'
            ]
            for node_name, desc in descriptions.items():
                # 首先检查是否是内部节点
                if node_name in langgraph_internal_nodes:
                    logger.debug(f"✅ [节点说明] 已过滤掉 LangGraph 内部节点 '{node_name}' 的说明")
                    continue
                
                # 然后检查是否包含 LangGraph 默认说明
                if desc:
                    desc_lower = desc.lower().strip()
                    if any(pattern in desc_lower for pattern in langgraph_default_patterns):
                        logger.debug(f"✅ [节点说明] 已过滤掉包含 LangGraph 默认说明的节点 '{node_name}': {desc[:50]}")
                        continue
                
                # 通过所有检查，保留节点说明
                filtered_descriptions[node_name] = desc
            descriptions = filtered_descriptions
            
            logger.info(f"✅ [节点说明] 从工作流中动态提取了 {len(descriptions)} 个节点的说明")
            # 🚀 调试：输出提取的节点名称和说明
            if descriptions:
                logger.debug(f"📋 [节点说明] 提取的节点（前20个）:")
                for node_name, desc in list(descriptions.items())[:20]:
                    logger.debug(f"   - {node_name}: {desc[:60]}")
            
            # 🚀 调试：检查是否有"Node in graph"
            problematic_nodes = [name for name, desc in descriptions.items() if desc and 'node in graph' in desc.lower()]
            if problematic_nodes:
                logger.warning(f"⚠️ [节点说明] 发现 {len(problematic_nodes)} 个节点的说明是'Node in graph': {problematic_nodes[:10]}")
            
        except Exception as e:
            logger.warning(f"⚠️ [节点说明] 提取节点说明时出错: {e}")
            import traceback
            logger.debug(f"详细错误:\n{traceback.format_exc()}")
        
        return descriptions
    
    def _is_subgraph_node(self, node_func) -> bool:
        """
        判断节点是否是子图节点
        
        Args:
            node_func: 节点函数对象
        
        Returns:
            如果是子图节点返回True，否则返回False
        """
        if node_func is None:
            return False
        
        # 检查是否是编译后的子图（LangGraph的编译后的子图通常有特定的属性）
        # 子图通常是 CompiledGraph 或类似的类型
        if hasattr(node_func, 'get_graph'):
            return True
        
        # 检查是否有_builder属性（LangGraph的内部结构）
        if hasattr(node_func, '_builder'):
            return True
        
        # 检查类型名称
        type_name = type(node_func).__name__
        if 'Graph' in type_name or 'Subgraph' in type_name:
            return True
        
        return False
    
    def _extract_subgraph_descriptions(self, subgraph_node) -> Dict[str, str]:
        """
        从子图节点中提取内部节点的说明
        
        Args:
            subgraph_node: 子图节点对象
        
        Returns:
            子图内部节点名称到说明的映射字典
        """
        descriptions = {}
        
        try:
            # 尝试获取子图的graph对象
            if hasattr(subgraph_node, 'get_graph'):
                graph = subgraph_node.get_graph()
                if hasattr(graph, 'nodes'):
                    if isinstance(graph.nodes, dict):
                        for inner_node_name, inner_node_func in graph.nodes.items():
                            desc = self._extract_docstring(inner_node_func)
                            # 🚀 修复：如果提取的说明是默认值，使用硬编码说明
                            if desc and desc.lower().strip() not in ['node in graph', 'node', '']:
                                if 'node in graph' not in desc.lower():
                                    descriptions[inner_node_name] = desc
                                elif inner_node_name in self.NODE_DESCRIPTIONS:
                                    descriptions[inner_node_name] = self.NODE_DESCRIPTIONS[inner_node_name]
                            # 如果无法提取，尝试使用硬编码说明
                            elif inner_node_name in self.NODE_DESCRIPTIONS:
                                descriptions[inner_node_name] = self.NODE_DESCRIPTIONS[inner_node_name]
                    elif isinstance(graph.nodes, (list, set)):
                        # 如果是列表，尝试从nodes属性获取函数
                        if hasattr(subgraph_node, 'nodes') and isinstance(subgraph_node.nodes, dict):
                            for inner_node_name in graph.nodes:
                                inner_node_func = subgraph_node.nodes.get(inner_node_name)
                                if inner_node_func:
                                    desc = self._extract_docstring(inner_node_func)
                                    if desc and desc.lower().strip() not in ['node in graph', 'node', '']:
                                        if 'node in graph' not in desc.lower():
                                            descriptions[inner_node_name] = desc
                                        elif inner_node_name in self.NODE_DESCRIPTIONS:
                                            descriptions[inner_node_name] = self.NODE_DESCRIPTIONS[inner_node_name]
                                    elif inner_node_name in self.NODE_DESCRIPTIONS:
                                        descriptions[inner_node_name] = self.NODE_DESCRIPTIONS[inner_node_name]
            
            # 尝试从_builder属性获取
            elif hasattr(subgraph_node, '_builder'):
                builder = subgraph_node._builder
                if hasattr(builder, '_nodes'):
                    nodes_dict = builder._nodes
                    if isinstance(nodes_dict, dict):
                        for inner_node_name, inner_node_func in nodes_dict.items():
                            desc = self._extract_docstring(inner_node_func)
                            if desc and desc.lower().strip() not in ['node in graph', 'node', '']:
                                if 'node in graph' not in desc.lower():
                                    descriptions[inner_node_name] = desc
                                elif inner_node_name in self.NODE_DESCRIPTIONS:
                                    descriptions[inner_node_name] = self.NODE_DESCRIPTIONS[inner_node_name]
                            elif inner_node_name in self.NODE_DESCRIPTIONS:
                                descriptions[inner_node_name] = self.NODE_DESCRIPTIONS[inner_node_name]
            
            # 尝试从nodes属性直接获取
            elif hasattr(subgraph_node, 'nodes') and isinstance(subgraph_node.nodes, dict):
                for inner_node_name, inner_node_func in subgraph_node.nodes.items():
                    desc = self._extract_docstring(inner_node_func)
                    if desc and desc.lower().strip() not in ['node in graph', 'node', '']:
                        if 'node in graph' not in desc.lower():
                            descriptions[inner_node_name] = desc
                        elif inner_node_name in self.NODE_DESCRIPTIONS:
                            descriptions[inner_node_name] = self.NODE_DESCRIPTIONS[inner_node_name]
                    elif inner_node_name in self.NODE_DESCRIPTIONS:
                        descriptions[inner_node_name] = self.NODE_DESCRIPTIONS[inner_node_name]
            
            if descriptions:
                logger.debug(f"✅ [节点说明] 从子图中提取了 {len(descriptions)} 个内部节点的说明")
        
        except Exception as e:
            logger.debug(f"⚠️ [节点说明] 提取子图内部节点说明时出错: {e}")
        
        return descriptions
    
    def _extract_docstring(self, node_func) -> Optional[str]:
        """
        从节点函数中提取docstring并格式化为说明文本
        
        Args:
            node_func: 节点函数对象
        
        Returns:
            格式化后的说明文本，如果没有docstring则返回None
        """
        if node_func is None:
            return None
        
        try:
            # 🚀 调试：记录节点函数的类型和属性
            func_type = type(node_func).__name__
            func_name = getattr(node_func, '__name__', 'unknown')
            
            # 获取docstring
            doc = None
            doc_source = None
            
            # 🚀 修复：递归查找docstring，支持多层装饰器包装
            def find_docstring_recursive(func, depth=0, max_depth=10):
                """递归查找docstring，支持多层装饰器包装"""
                if depth > max_depth:
                    return None, None
                
                # 如果是函数对象，直接获取__doc__
                if hasattr(func, '__doc__') and func.__doc__:
                    doc_str = func.__doc__.strip()
                    # 🚀 修复：检查是否是默认值（"Node in a graph." 或 "Node in graph"）
                    doc_lower = doc_str.lower() if doc_str else ''
                    is_default = (
                        doc_lower in ['node in a graph.', 'node in graph', 'node in graph.', 'node', ''] or
                        'node in graph' in doc_lower or
                        doc_lower == 'node in a graph'
                    )
                    if doc_str and not is_default:
                        return doc_str, f'__doc__ (depth={depth})'
                
                # 如果是包装函数（如装饰器包装的），递归查找
                if hasattr(func, '__wrapped__'):
                    wrapped = func.__wrapped__
                    doc_str, source = find_docstring_recursive(wrapped, depth + 1, max_depth)
                    if doc_str:
                        return doc_str, source or f'__wrapped__.__doc__ (depth={depth})'
                
                # 如果是方法对象，尝试获取函数的docstring
                if hasattr(func, '__func__'):
                    func_obj = func.__func__
                    doc_str, source = find_docstring_recursive(func_obj, depth + 1, max_depth)
                    if doc_str:
                        return doc_str, source or f'__func__.__doc__ (depth={depth})'
                
                return None, None
            
            doc, doc_source = find_docstring_recursive(node_func)
            
            # 🚀 兼容：如果递归查找失败，尝试简单查找
            if not doc:
                # 如果是函数对象，直接获取__doc__
                if hasattr(node_func, '__doc__'):
                    doc = node_func.__doc__
                    doc_source = '__doc__'
                
                # 如果是包装函数（如装饰器包装的），尝试获取原始函数
                if not doc and hasattr(node_func, '__wrapped__'):
                    doc = getattr(node_func.__wrapped__, '__doc__', None)
                    doc_source = '__wrapped__.__doc__'
                
                # 如果是方法对象，尝试获取函数的docstring
                if not doc and hasattr(node_func, '__func__'):
                    doc = getattr(node_func.__func__, '__doc__', None)
                    doc_source = '__func__.__doc__'
            
            # 🚀 调试：记录提取结果
            if doc:
                # 检查是否是默认值（"Node in a graph." 或 "Node in graph"）
                doc_stripped = doc.strip().lower()
                is_default_value = (
                    doc_stripped in ['node in a graph.', 'node in graph', 'node in graph.', 'node', ''] or
                    'node in graph' in doc_stripped or
                    doc_stripped == 'node in a graph'
                )
                if is_default_value:
                    # 🚀 修复：对于LangGraph自动生成的节点（如__start__, __end__）或无法提取名称的节点，不产生警告
                    # 这些节点是正常的，没有docstring是预期的行为
                    is_special_node = (
                        func_name in ['unknown', '__start__', '__end__', '__START__', '__END__'] or
                        func_name.startswith('__') and func_name.endswith('__') or
                        func_type == 'Node'  # LangGraph自动生成的节点类型
                    )
                    
                    if not is_special_node:
                        # 只有非特殊节点才产生警告
                        logger.warning(f"⚠️ [节点说明] 节点函数 '{func_name}' ({func_type}) 的docstring是默认值: '{doc[:50]}' (来源: {doc_source})")
                        # 🚀 调试：尝试获取更多信息
                        if hasattr(node_func, '__wrapped__'):
                            wrapped = node_func.__wrapped__
                            logger.debug(f"   → __wrapped__ 类型: {type(wrapped).__name__}, 名称: {getattr(wrapped, '__name__', 'unknown')}")
                        if hasattr(node_func, '__func__'):
                            func = node_func.__func__
                            logger.debug(f"   → __func__ 类型: {type(func).__name__}, 名称: {getattr(func, '__name__', 'unknown')}")
                    else:
                        # 特殊节点，使用debug级别记录
                        logger.debug(f"ℹ️ [节点说明] LangGraph自动生成的节点 '{func_name}' ({func_type}) 使用默认docstring，这是正常行为")
                    return None  # 返回None，让调用者使用硬编码说明
            
            if not doc:
                logger.debug(f"⚠️ [节点说明] 节点函数 '{func_name}' ({func_type}) 没有docstring")
                return None
            
            # 清理docstring：移除多余的空行和空白
            doc_lines = [line.strip() for line in doc.split('\n') if line.strip()]
            if not doc_lines:
                return None
            
            # 提取第一行或前几行作为简要说明
            # 如果第一行很短（<50字符），可能包含多行
            first_line = doc_lines[0]
            if len(first_line) < 50 and len(doc_lines) > 1:
                # 合并前两行
                description = f"{first_line} {doc_lines[1]}"
            else:
                description = first_line
            
            # 移除常见的docstring格式标记
            description = description.replace('"""', '').replace("'''", '').strip()
            
            # 如果说明以节点名称开头，移除重复的节点名称
            # 例如："路由查询节点 - 初始化状态" -> "初始化状态并判断查询复杂度"
            if ' - ' in description:
                parts = description.split(' - ', 1)
                if len(parts) > 1:
                    description = parts[1].strip()
            
            logger.debug(f"✅ [节点说明] 从节点函数 '{func_name}' 提取说明: '{description[:50]}' (来源: {doc_source})")
            return description if description else None
            
        except Exception as e:
            logger.warning(f"⚠️ [节点说明] 提取docstring时出错: {e}")
            import traceback
            logger.debug(f"详细错误:\n{traceback.format_exc()}")
            return None
    
    def _format_docstring(self, doc: str) -> Optional[str]:
        """
        格式化docstring为说明文本
        
        Args:
            doc: 原始docstring
        
        Returns:
            格式化后的说明文本
        """
        if not doc:
            return None
        
        # 清理docstring：移除多余的空行和空白
        doc_lines = [line.strip() for line in doc.split('\n') if line.strip()]
        if not doc_lines:
            return None
        
        # 提取第一行或前几行作为简要说明
        # 如果第一行很短（<50字符），可能包含多行
        first_line = doc_lines[0]
        if len(first_line) < 50 and len(doc_lines) > 1:
            # 合并前两行
            description = f"{first_line} {doc_lines[1]}"
        else:
            description = first_line
        
        # 移除常见的docstring格式标记
        description = description.replace('"""', '').replace("'''", '').strip()
        
        # 如果说明以节点名称开头，移除重复的节点名称
        # 例如："路由查询节点 - 初始化状态" -> "初始化状态并判断查询复杂度"
        if ' - ' in description:
            parts = description.split(' - ', 1)
            if len(parts) > 1:
                description = parts[1].strip()
        
        return description if description else None

