"""
组合式能力构建 (Composite Capabilities)

实现能力组合和编排：
- 能力组合DSL
- 组合执行引擎
- 组合优化策略
- 动态组合生成
- 组合验证和测试
"""

import asyncio
import logging
import json
import statistics
from typing import Dict, List, Any, Optional, Set, Callable, Protocol, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import networkx as nx
import copy
import re

logger = logging.getLogger(__name__)


class CompositionOperator(Enum):
    """组合操作符"""
    SEQUENCE = "sequence"      # 顺序执行
    PARALLEL = "parallel"      # 并行执行
    CONDITIONAL = "conditional" # 条件执行
    LOOP = "loop"             # 循环执行
    PIPELINE = "pipeline"     # 管道传递
    MERGE = "merge"           # 结果合并
    SELECT = "select"         # 选择执行
    FALLBACK = "fallback"     # 回退执行


class CompositionStrategy(Enum):
    """组合策略"""
    PERFORMANCE_OPTIMIZED = "performance_optimized"  # 性能优化
    RELIABILITY_FOCUSED = "reliability_focused"     # 可靠性优先
    COST_OPTIMIZED = "cost_optimized"               # 成本优化
    ACCURACY_MAXIMIZED = "accuracy_maximized"      # 准确性最大化
    LATENCY_MINIMIZED = "latency_minimized"        # 延迟最小化


@dataclass
class CapabilityNode:
    """能力节点"""
    node_id: str
    capability_id: str
    config: Dict[str, Any] = field(default_factory=dict)
    input_mapping: Dict[str, str] = field(default_factory=dict)  # 输入参数映射
    output_mapping: Dict[str, str] = field(default_factory=dict)  # 输出参数映射
    conditions: List[Dict[str, Any]] = field(default_factory=list)  # 执行条件
    timeout: Optional[float] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompositionEdge:
    """组合边"""
    source_node: str
    target_node: str
    operator: CompositionOperator
    condition: Optional[Dict[str, Any]] = None  # 条件表达式
    data_flow: Dict[str, Any] = field(default_factory=dict)  # 数据流配置
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompositionGraph:
    """组合图"""
    composition_id: str
    name: str
    description: str
    nodes: Dict[str, CapabilityNode] = field(default_factory=dict)
    edges: List[CompositionEdge] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)  # 入口节点
    exit_points: List[str] = field(default_factory=list)   # 出口节点
    global_config: Dict[str, Any] = field(default_factory=dict)
    strategy: CompositionStrategy = CompositionStrategy.PERFORMANCE_OPTIMIZED
    created_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"

    def validate(self) -> List[str]:
        """验证组合图"""
        errors = []

        # 检查节点存在性
        all_node_ids = set(self.nodes.keys())
        for edge in self.edges:
            if edge.source_node not in all_node_ids:
                errors.append(f"边源节点不存在: {edge.source_node}")
            if edge.target_node not in all_node_ids:
                errors.append(f"边目标节点不存在: {edge.target_node}")

        # 检查入口点
        for entry in self.entry_points:
            if entry not in all_node_ids:
                errors.append(f"入口节点不存在: {entry}")

        # 检查出口点
        for exit_point in self.exit_points:
            if exit_point not in all_node_ids:
                errors.append(f"出口节点不存在: {exit_point}")

        # 检查图的连通性
        if self.nodes and not errors:
            G = nx.DiGraph()
            G.add_nodes_from(self.nodes.keys())
            G.add_edges_from([(e.source_node, e.target_node) for e in self.edges])

            # 检查是否有从入口到出口的路径
            for entry in self.entry_points:
                for exit_point in self.exit_points:
                    if not nx.has_path(G, entry, exit_point):
                        errors.append(f"无从入口 {entry} 到出口 {exit_point} 的路径")

        return errors

    def get_execution_order(self) -> List[List[str]]:
        """获取执行顺序（拓扑排序）"""
        if not self.validate():
            G = nx.DiGraph()
            G.add_nodes_from(self.nodes.keys())
            G.add_edges_from([(e.source_node, e.target_node) for e in self.edges])

            try:
                # 获取拓扑排序
                topo_order = list(nx.topological_sort(G))

                # 分层执行（考虑并行性）
                levels = {}
                for node in topo_order:
                    predecessors = list(G.predecessors(node))
                    if not predecessors:
                        level = 0
                    else:
                        level = max(levels.get(pred, -1) for pred in predecessors) + 1
                    levels[node] = level

                # 按层分组
                max_level = max(levels.values()) if levels else 0
                execution_levels = []
                for level in range(max_level + 1):
                    level_nodes = [node for node, node_level in levels.items() if node_level == level]
                    if level_nodes:
                        execution_levels.append(level_nodes)

                return execution_levels

            except nx.NetworkXError:
                logger.warning(f"组合图 {self.composition_id} 存在循环依赖")
                return []

        return []


class CompositionDSL:
    """组合DSL（领域特定语言）"""

    def __init__(self):
        self.keywords = {
            'SEQUENCE': CompositionOperator.SEQUENCE,
            'PARALLEL': CompositionOperator.PARALLEL,
            'CONDITIONAL': CompositionOperator.CONDITIONAL,
            'PIPELINE': CompositionOperator.PIPELINE,
            'MERGE': CompositionOperator.MERGE,
            'FALLBACK': CompositionOperator.FALLBACK
        }

    def parse_composition_script(self, script: str) -> CompositionGraph:
        """解析组合脚本"""
        lines = [line.strip() for line in script.split('\n') if line.strip() and not line.strip().startswith('#')]

        if not lines:
            raise ValueError("空的组合脚本")

        # 解析头部
        header = lines[0]
        if not header.startswith('COMPOSITION'):
            raise ValueError("组合脚本必须以 COMPOSITION 开头")

        # 解析组合定义
        composition_def = self._parse_header(header)
        graph = CompositionGraph(
            composition_id=composition_def['id'],
            name=composition_def['name'],
            description=composition_def.get('description', ''),
            strategy=composition_def.get('strategy', CompositionStrategy.PERFORMANCE_OPTIMIZED)
        )

        # 解析节点和边
        i = 1
        while i < len(lines):
            line = lines[i]

            if line.startswith('NODE'):
                node_def = self._parse_node_definition(line)
                graph.nodes[node_def['id']] = node_def['node']
                i += 1
            elif line.startswith('EDGE') or self._is_operator(line.upper()):
                edge_def = self._parse_edge_definition(lines, i)
                graph.edges.append(edge_def['edge'])
                i = edge_def['next_index']
            elif line.startswith('ENTRY'):
                graph.entry_points = self._parse_list(line)
                i += 1
            elif line.startswith('EXIT'):
                graph.exit_points = self._parse_list(line)
                i += 1
            elif line.startswith('CONFIG'):
                graph.global_config = self._parse_config(lines, i)
                i += 1
            else:
                i += 1

        return graph

    def _parse_header(self, header: str) -> Dict[str, Any]:
        """解析头部"""
        # COMPOSITION id="example" name="Example Composition" strategy="performance_optimized"
        pattern = r'COMPOSITION\s+id="([^"]+)"\s+name="([^"]+)"(?:\s+strategy="([^"]+)")?(?:\s+description="([^"]+)")?/?'
        match = re.match(pattern, header)

        if not match:
            raise ValueError(f"无效的组合头部: {header}")

        strategy_str = match.group(3)
        strategy = CompositionStrategy(strategy_str) if strategy_str else CompositionStrategy.PERFORMANCE_OPTIMIZED

        return {
            'id': match.group(1),
            'name': match.group(2),
            'strategy': strategy,
            'description': match.group(4) or ''
        }

    def _parse_node_definition(self, line: str) -> Dict[str, Any]:
        """解析节点定义"""
        # NODE id="node1" capability="knowledge_retrieval" config={"timeout": 30}
        pattern = r'NODE\s+id="([^"]+)"\s+capability="([^"]+)"(?:\s+config=({[^}]+}))?'
        match = re.match(pattern, line)

        if not match:
            raise ValueError(f"无效的节点定义: {line}")

        node_id = match.group(1)
        capability_id = match.group(2)
        config_str = match.group(3)

        config = {}
        if config_str:
            try:
                config = json.loads(config_str)
            except (json.JSONDecodeError, TypeError):
                # 如果JSON解析失败，尝试简单的键值对解析
                try:
                    # 移除外层大括号并解析简单键值对
                    cleaned = config_str.strip('{}')
                    if cleaned:
                        pairs = cleaned.split(',')
                        config = {}
                        for pair in pairs:
                            if ':' in pair:
                                key, value = pair.split(':', 1)
                                key = key.strip().strip('"\'')
                                value = value.strip().strip('"\'')
                                # 尝试转换值类型
                                if value.lower() in ('true', 'false'):
                                    config[key] = value.lower() == 'true'
                                elif value.isdigit():
                                    config[key] = int(value)
                                elif value.replace('.', '', 1).isdigit():
                                    config[key] = float(value)
                                else:
                                    config[key] = value
                except Exception:
                    logger.warning(f"无法解析配置字符串: {config_str}")
                    config = {}

        node = CapabilityNode(
            node_id=node_id,
            capability_id=capability_id,
            config=config
        )

        return {
            'id': node_id,
            'node': node
        }

    def _parse_edge_definition(self, lines: List[str], start_index: int) -> Dict[str, Any]:
        """解析边定义"""
        line = lines[start_index]
        next_index = start_index + 1

        # 检查是否是操作符行
        upper_line = line.upper()
        if self._is_operator(upper_line):
            # 操作符行: PARALLEL node1, node2 -> result
            operator = self._parse_operator_line(line)
            return {
                'edge': operator['edge'],
                'next_index': next_index
            }

        # 标准边定义: EDGE source="node1" target="node2" operator="sequence"
        pattern = r'EDGE\s+source="([^"]+)"\s+target="([^"]+)"(?:\s+operator="([^"]+)")?'
        match = re.match(pattern, line)

        if not match:
            raise ValueError(f"无效的边定义: {line}")

        source = match.group(1)
        target = match.group(2)
        operator_str = match.group(3) or 'sequence'

        operator = CompositionOperator(operator_str)

        edge = CompositionEdge(
            source_node=source,
            target_node=target,
            operator=operator
        )

        return {
            'edge': edge,
            'next_index': next_index
        }

    def _parse_operator_line(self, line: str) -> Dict[str, Any]:
        """解析操作符行"""
        # PARALLEL node1, node2 -> result
        parts = line.split()
        if len(parts) < 2:
            raise ValueError(f"无效的操作符行: {line}")

        operator_str = parts[0].upper()
        if operator_str not in self.keywords:
            raise ValueError(f"未知的操作符: {operator_str}")

        operator = self.keywords[operator_str]

        # 解析源节点和目标节点
        remaining = ' '.join(parts[1:])
        if '->' in remaining:
            source_part, target_part = remaining.split('->', 1)
            source_nodes = [s.strip() for s in source_part.split(',')]
            target_node = target_part.strip()

            # 为每个源节点创建边
            edges = []
            for source in source_nodes:
                edge = CompositionEdge(
                    source_node=source,
                    target_node=target_node,
                    operator=operator
                )
                edges.append(edge)

            # 返回第一个边（简化处理）
            return {'edge': edges[0] if edges else None}
        else:
            raise ValueError(f"操作符行缺少目标节点: {line}")

    def _is_operator(self, line: str) -> bool:
        """检查是否是操作符"""
        first_word = line.split()[0] if line.split() else ""
        return first_word in self.keywords

    def _parse_list(self, line: str) -> List[str]:
        """解析列表"""
        # ENTRY node1, node2, node3
        parts = line.split(None, 1)
        if len(parts) < 2:
            return []

        items_str = parts[1]
        return [item.strip() for item in items_str.split(',')]

    def _parse_config(self, lines: List[str], start_index: int) -> Dict[str, Any]:
        """解析配置"""
        # 简化实现
        return {}


class CompositionExecutor:
    """组合执行器"""

    def __init__(self):
        self.execution_contexts: Dict[str, Dict[str, Any]] = {}
        self.capability_manager = None  # 需要注入

    def set_capability_manager(self, manager):
        """设置能力管理器"""
        self.capability_manager = manager

    async def execute_composition(self, graph: CompositionGraph,
                                input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行组合"""
        execution_id = f"exec_{graph.composition_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 初始化执行上下文
        self.execution_contexts[execution_id] = {
            'graph': graph,
            'input_data': input_data,
            'node_results': {},
            'execution_order': graph.get_execution_order(),
            'current_level': 0,
            'status': 'running',
            'start_time': datetime.now()
        }

        try:
            # 按执行顺序执行
            final_result = input_data.copy()

            for level_nodes in graph.get_execution_order():
                # 并行执行同级节点
                level_tasks = []
                for node_id in level_nodes:
                    if node_id in graph.nodes:
                        node = graph.nodes[node_id]
                        task = asyncio.create_task(
                            self._execute_node(execution_id, node, final_result)
                        )
                        level_tasks.append((node_id, task))

                # 等待同级节点完成
                if level_tasks:
                    results = await asyncio.gather(*[task for _, task in level_tasks], return_exceptions=True)

                    for (node_id, _), result in zip(level_tasks, results):
                        if isinstance(result, Exception):
                            logger.error(f"节点 {node_id} 执行失败: {result}")
                            self.execution_contexts[execution_id]['node_results'][node_id] = {
                                'success': False,
                                'error': str(result)
                            }
                        else:
                            self.execution_contexts[execution_id]['node_results'][node_id] = result
                            if isinstance(result, dict):
                                final_result.update(result)

            # 执行完成
            self.execution_contexts[execution_id]['status'] = 'completed'
            self.execution_contexts[execution_id]['end_time'] = datetime.now()

            return {
                'success': True,
                'result': final_result,
                'execution_id': execution_id,
                'node_results': self.execution_contexts[execution_id]['node_results']
            }

        except Exception as e:
            self.execution_contexts[execution_id]['status'] = 'failed'
            self.execution_contexts[execution_id]['error'] = str(e)
            self.execution_contexts[execution_id]['end_time'] = datetime.now()

            return {
                'success': False,
                'error': str(e),
                'execution_id': execution_id
            }

    async def _execute_node(self, execution_id: str, node: CapabilityNode,
                          context_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行节点"""
        try:
            # 准备节点输入
            node_input = self._prepare_node_input(node, context_data)

            # 检查执行条件
            if not self._check_node_conditions(node, context_data):
                return {'skipped': True, 'reason': '条件不满足'}

            # 执行能力
            if not self.capability_manager:
                raise RuntimeError("能力管理器未设置")

            result = await self.capability_manager.execute_capability(
                node.capability_id,
                node_input
            )

            # 处理输出映射
            processed_result = self._process_node_output(node, result)

            return processed_result

        except Exception as e:
            logger.error(f"节点 {node.node_id} 执行失败: {e}")
            raise

    def _prepare_node_input(self, node: CapabilityNode, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """准备节点输入"""
        input_data = {}

        # 应用输入映射
        for target_param, source_expr in node.input_mapping.items():
            try:
                # 安全表达式评估
                value = self._safe_eval_expression(source_expr, {"context": context_data, "node": node})
                input_data[target_param] = value
            except Exception:
                # 如果表达式失败，使用原始上下文数据
                if source_expr in context_data:
                    input_data[target_param] = context_data[source_expr]

        # 如果没有映射，使用默认输入
        if not input_data:
            input_data = context_data.copy()

        # 合并节点配置
        input_data.update(node.config)

        return input_data

    def _check_node_conditions(self, node: CapabilityNode, context_data: Dict[str, Any]) -> bool:
        """检查节点执行条件"""
        for condition in node.conditions:
            try:
                condition_expr = condition.get('expression', '')
                if not condition_expr:
                    continue

                # 安全条件表达式评估
                result = self._safe_eval_expression(condition_expr, {"context": context_data, "node": node})
                if not result:
                    return False
            except Exception:
                # 条件评估失败，跳过该条件
                continue

        return True

    def _process_node_output(self, node: CapabilityNode, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """处理节点输出"""
        processed_result = {}

        # 应用输出映射
        for source_param, target_param in node.output_mapping.items():
            if source_param in raw_result:
                processed_result[target_param] = raw_result[source_param]

        # 如果没有映射，使用原始结果
        if not processed_result:
            processed_result = raw_result.copy()

        return processed_result

    def _safe_eval_expression(self, expr: str, safe_context: Dict[str, Any]) -> Any:
        """安全表达式评估"""
        try:
            # 只支持简单的字段访问和基本操作
            # 移除危险字符
            if any(char in expr for char in ['__', 'import', 'exec', 'eval', 'open', 'file']):
                raise ValueError("表达式包含不安全操作")
            
            # 解析简单表达式: context.key, context["key"], node.prop
            if expr.startswith('context.'):
                key = expr[8:]  # 移除 'context.'
                if '.' in key:
                    # 处理嵌套访问 context.data.value
                    parts = key.split('.')
                    value = safe_context.get('context', {})
                    for part in parts:
                        if isinstance(value, dict) and part in value:
                            value = value[part]
                        else:
                            return None
                    return value
                else:
                    return safe_context.get('context', {}).get(key)
            
            elif expr.startswith('context['):
                # 处理 context["key"] 格式
                if expr.endswith(']'):
                    key = expr[9:-1].strip('"\'')
                    return safe_context.get('context', {}).get(key)
            
            elif expr.startswith('node.'):
                # 处理 node.prop 访问
                key = expr[5:]  # 移除 'node.'
                return getattr(safe_context.get('node'), key, None)
            
            elif expr in safe_context:
                # 直接访问上下文变量
                return safe_context[expr]
            
            else:
                # 简单字面值
                if expr.lower() in ('true', 'false'):
                    return expr.lower() == 'true'
                elif expr.isdigit():
                    return int(expr)
                elif expr.replace('.', '', 1).isdigit():
                    return float(expr)
                elif expr.startswith('"') and expr.endswith('"'):
                    return expr[1:-1]
                elif expr.startswith("'") and expr.endswith("'"):
                    return expr[1:-1]
                else:
                    return None
                    
        except Exception:
            return None


class CompositionOptimizer:
    """组合优化器"""

    def __init__(self):
        self.optimization_strategies = {
            CompositionStrategy.PERFORMANCE_OPTIMIZED: self._optimize_for_performance,
            CompositionStrategy.RELIABILITY_FOCUSED: self._optimize_for_reliability,
            CompositionStrategy.COST_OPTIMIZED: self._optimize_for_cost,
            CompositionStrategy.ACCURACY_MAXIMIZED: self._optimize_for_accuracy,
            CompositionStrategy.LATENCY_MINIMIZED: self._optimize_for_latency
        }

    async def optimize_composition(self, graph: CompositionGraph,
                                 constraints: Optional[Dict[str, Any]] = None) -> CompositionGraph:
        """优化组合"""
        constraints = constraints or {}

        # 选择优化策略
        strategy = graph.strategy
        optimizer = self.optimization_strategies.get(strategy, self._optimize_for_performance)

        # 应用优化
        optimized_graph = await optimizer(graph, constraints)

        # 验证优化后的图
        validation_errors = optimized_graph.validate()
        if validation_errors:
            logger.warning(f"优化后的组合图验证失败: {validation_errors}")
            return graph  # 返回原始图

        return optimized_graph

    async def _optimize_for_performance(self, graph: CompositionGraph,
                                      constraints: Dict[str, Any]) -> CompositionGraph:
        """性能优化"""
        optimized_graph = copy.deepcopy(graph)

        # 识别可以并行化的节点
        parallel_candidates = self._identify_parallel_candidates(optimized_graph)

        # 添加并行边
        for source_nodes, target_node in parallel_candidates:
            for source in source_nodes:
                edge = CompositionEdge(
                    source_node=source,
                    target_node=target_node,
                    operator=CompositionOperator.PARALLEL
                )
                optimized_graph.edges.append(edge)

        return optimized_graph

    async def _optimize_for_reliability(self, graph: CompositionGraph,
                                      constraints: Dict[str, Any]) -> CompositionGraph:
        """可靠性优化"""
        optimized_graph = copy.deepcopy(graph)

        # 为关键节点添加重试和回退
        for node_id, node in optimized_graph.nodes.items():
            if self._is_critical_node(node):
                # 增加重试次数
                node.retry_count = max(node.retry_count, 3)

                # 添加回退节点（简化实现）
                fallback_node = CapabilityNode(
                    node_id=f"{node_id}_fallback",
                    capability_id="basic_fallback",  # 假设存在基本回退能力
                    config={"original_node": node_id}
                )
                optimized_graph.nodes[fallback_node.node_id] = fallback_node

                # 添加回退边
                fallback_edge = CompositionEdge(
                    source_node=node_id,
                    target_node=fallback_node.node_id,
                    operator=CompositionOperator.FALLBACK
                )
                optimized_graph.edges.append(fallback_edge)

        return optimized_graph

    async def _optimize_for_cost(self, graph: CompositionGraph,
                               constraints: Dict[str, Any]) -> CompositionGraph:
        """成本优化"""
        optimized_graph = copy.deepcopy(graph)

        # 优化资源使用
        for node in optimized_graph.nodes.values():
            # 降低资源密集型节点的配置
            if 'model_size' in node.config:
                node.config['model_size'] = min(node.config['model_size'], 'small')
            if 'batch_size' in node.config:
                node.config['batch_size'] = min(node.config['batch_size'], 8)

        return optimized_graph

    async def _optimize_for_accuracy(self, graph: CompositionGraph,
                                   constraints: Dict[str, Any]) -> CompositionGraph:
        """准确性优化"""
        optimized_graph = copy.deepcopy(graph)

        # 为关键节点选择更准确的模型
        for node in optimized_graph.nodes.values():
            if 'model' in node.config:
                # 选择更准确的模型变体
                if 'fast' in node.config['model']:
                    node.config['model'] = node.config['model'].replace('fast', 'accurate')

        return optimized_graph

    async def _optimize_for_latency(self, graph: CompositionGraph,
                                  constraints: Dict[str, Any]) -> CompositionGraph:
        """延迟优化"""
        optimized_graph = copy.deepcopy(graph)

        # 降低超时时间，优先选择快速能力
        for node in optimized_graph.nodes.values():
            if node.timeout:
                node.timeout = min(node.timeout, 30.0)  # 最大30秒

            # 选择快速版本的能力
            if 'model' in node.config and 'large' in node.config['model']:
                node.config['model'] = node.config['model'].replace('large', 'small')

        return optimized_graph

    def _identify_parallel_candidates(self, graph: CompositionGraph) -> List[Tuple[List[str], str]]:
        """识别并行候选"""
        candidates = []

        # 分析图结构，找到可以并行化的节点组
        G = nx.DiGraph()
        G.add_edges_from([(e.source_node, e.target_node) for e in graph.edges])

        # 查找同一层级的节点（可以并行）
        execution_order = graph.get_execution_order()
        for level in execution_order:
            if len(level) > 1:
                # 检查这些节点是否可以并行
                can_parallelize = True
                for i, node1 in enumerate(level):
                    for node2 in level[i+1:]:
                        # 检查是否有直接依赖（不应该有）
                        if G.has_edge(node1, node2) or G.has_edge(node2, node1):
                            can_parallelize = False
                            break
                    if not can_parallelize:
                        break

                if can_parallelize:
                    # 找到共同的后续节点
                    successors = set()
                    for node in level:
                        successors.update(G.successors(node))

                    for successor in successors:
                        candidates.append((level, successor))

        return candidates

    def _is_critical_node(self, node: CapabilityNode) -> bool:
        """判断是否是关键节点"""
        # 基于节点类型和配置判断
        critical_types = ['reasoning', 'decision', 'critical']
        node_type = node.capability_id.lower()

        for critical_type in critical_types:
            if critical_type in node_type:
                return True

        return False


class CompositeCapabilitiesSystem:
    """
    组合式能力构建系统

    提供完整的组合能力构建、优化和执行功能：
    - 组合DSL解析
    - 组合图构建和验证
    - 组合优化
    - 组合执行和监控
    - 组合学习和改进
    """

    def __init__(self):
        self.dsl_parser = CompositionDSL()
        self.executor = CompositionExecutor()
        self.optimizer = CompositionOptimizer()
        self.compositions: Dict[str, CompositionGraph] = {}
        self.execution_history: List[Dict[str, Any]] = []

    async def create_composition_from_script(self, script: str,
                                           optimize: bool = True) -> CompositionGraph:
        """从脚本创建组合"""
        # 解析脚本
        graph = self.dsl_parser.parse_composition_script(script)

        # 验证组合
        validation_errors = graph.validate()
        if validation_errors:
            raise ValueError(f"组合验证失败: {validation_errors}")

        # 优化组合
        if optimize:
            graph = await self.optimizer.optimize_composition(graph)

        # 存储组合
        self.compositions[graph.composition_id] = graph

        logger.info(f"组合创建成功: {graph.composition_id}")
        return graph

    async def execute_composition(self, composition_id: str,
                                input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行组合"""
        if composition_id not in self.compositions:
            raise ValueError(f"组合不存在: {composition_id}")

        graph = self.compositions[composition_id]

        # 执行组合
        result = await self.executor.execute_composition(graph, input_data)

        # 记录执行历史
        execution_record = {
            'composition_id': composition_id,
            'execution_time': datetime.now(),
            'input_data': input_data,
            'result': result,
            'performance_metrics': self._calculate_execution_metrics(result)
        }
        self.execution_history.append(execution_record)

        return result

    def get_composition_info(self, composition_id: str) -> Optional[Dict[str, Any]]:
        """获取组合信息"""
        if composition_id not in self.compositions:
            return None

        graph = self.compositions[composition_id]
        return {
            'id': graph.composition_id,
            'name': graph.name,
            'description': graph.description,
            'node_count': len(graph.nodes),
            'edge_count': len(graph.edges),
            'entry_points': graph.entry_points,
            'exit_points': graph.exit_points,
            'strategy': graph.strategy.value,
            'version': graph.version,
            'execution_order': graph.get_execution_order()
        }

    def list_compositions(self) -> List[Dict[str, Any]]:
        """列出所有组合"""
        return [info for cid in self.compositions.keys() 
                if (info := self.get_composition_info(cid)) is not None]

    async def optimize_existing_composition(self, composition_id: str,
                                           constraints: Optional[Dict[str, Any]] = None) -> bool:
        """优化现有组合"""
        if composition_id not in self.compositions:
            return False

        graph = self.compositions[composition_id]
        optimized_graph = await self.optimizer.optimize_composition(graph, constraints)

        # 更新组合
        self.compositions[composition_id] = optimized_graph

        logger.info(f"组合优化完成: {composition_id}")
        return True

    def get_execution_statistics(self, composition_id: Optional[str] = None) -> Dict[str, Any]:
        """获取执行统计"""
        if composition_id:
            # 特定组合的统计
            relevant_executions = [
                e for e in self.execution_history
                if e['composition_id'] == composition_id
            ]
        else:
            relevant_executions = self.execution_history

        if not relevant_executions:
            return {'total_executions': 0}

        total_executions = len(relevant_executions)
        successful_executions = len([e for e in relevant_executions if e['result'].get('success', False)])

        # 计算平均性能指标
        avg_metrics = {}
        for execution in relevant_executions:
            metrics = execution.get('performance_metrics', {})
            for key, value in metrics.items():
                if key not in avg_metrics:
                    avg_metrics[key] = []
                avg_metrics[key].append(value)

        for key in avg_metrics:
            avg_metrics[key] = statistics.mean(avg_metrics[key]) if avg_metrics[key] else 0

        return {
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'success_rate': successful_executions / total_executions if total_executions > 0 else 0,
            'average_metrics': avg_metrics
        }

    def _calculate_execution_metrics(self, result: Dict[str, Any]) -> Dict[str, float]:
        """计算执行指标"""
        metrics = {}

        if 'execution_id' in result and result['execution_id'] in self.executor.execution_contexts:
            context = self.executor.execution_contexts[result['execution_id']]

            # 计算总执行时间
            if 'start_time' in context and 'end_time' in context:
                execution_time = (context['end_time'] - context['start_time']).total_seconds()
                metrics['total_execution_time'] = execution_time

            # 计算节点成功率
            node_results = context.get('node_results', {})
            if node_results:
                successful_nodes = sum(1 for r in node_results.values() if not isinstance(r, dict) or not r.get('error'))
                metrics['node_success_rate'] = successful_nodes / len(node_results)

        return metrics

    def export_composition_graph(self, composition_id: str, format: str = 'json') -> Optional[str]:
        """导出组合图"""
        if composition_id not in self.compositions:
            return None

        graph = self.compositions[composition_id]

        if format == 'json':
            # 导出为JSON
            graph_data = {
                'composition_id': graph.composition_id,
                'name': graph.name,
                'description': graph.description,
                'nodes': {nid: {
                    'capability_id': node.capability_id,
                    'config': node.config
                } for nid, node in graph.nodes.items()},
                'edges': [{
                    'source': edge.source_node,
                    'target': edge.target_node,
                    'operator': edge.operator.value
                } for edge in graph.edges],
                'entry_points': graph.entry_points,
                'exit_points': graph.exit_points,
                'strategy': graph.strategy.value
            }

            import json
            return json.dumps(graph_data, indent=2, ensure_ascii=False)

        return None


# 全局实例
_composite_capabilities_instance: Optional[CompositeCapabilitiesSystem] = None

def get_composite_capabilities_system() -> CompositeCapabilitiesSystem:
    """获取组合式能力构建系统实例"""
    global _composite_capabilities_instance
    if _composite_capabilities_instance is None:
        _composite_capabilities_instance = CompositeCapabilitiesSystem()
    return _composite_capabilities_instance
