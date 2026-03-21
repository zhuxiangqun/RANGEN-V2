"""
动态规划器 - 根据执行结果动态调整推理计划

初始版本：基于规则的动态调整
未来版本：基于图优化的动态规划
"""
import logging
import re
from typing import Dict, Any, List, Optional, Set
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class DynamicPlanner:
    """动态规划器
    
    根据上一步的执行结果，动态调整后续步骤：
    - 根据结果决定下一步
    - 支持条件分支的动态执行
    - 支持循环依赖的检测和处理
    - 图优化（未来：基于GNN）
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化动态规划器
        
        Args:
            config: 配置字典
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        
        # 执行历史
        self.execution_history = []
        
        # 依赖图
        self.dependency_graph = defaultdict(set)
        
    def plan_next_steps(
        self,
        current_steps: List[Dict[str, Any]],
        execution_results: Dict[int, Dict[str, Any]],
        original_query: str
    ) -> List[Dict[str, Any]]:
        """根据执行结果规划下一步
        
        Args:
            current_steps: 当前步骤列表
            execution_results: 执行结果字典 {step_index: result}
            original_query: 原始查询
            
        Returns:
            调整后的步骤列表
        """
        try:
            # 1. 构建依赖图
            self._build_dependency_graph(current_steps)
            
            # 2. 检测循环依赖
            if self._has_cycle():
                self.logger.warning("⚠️ 检测到循环依赖，尝试修复")
                current_steps = self._fix_cycle(current_steps)
                self._build_dependency_graph(current_steps)
            
            # 3. 根据执行结果动态调整
            adjusted_steps = self._adjust_steps_dynamically(
                current_steps, execution_results, original_query
            )
            
            # 4. 优化执行顺序
            optimized_steps = self._optimize_execution_order(adjusted_steps)
            
            return optimized_steps
            
        except Exception as e:
            self.logger.error(f"动态规划失败: {e}")
            return current_steps
    
    def _build_dependency_graph(self, steps: List[Dict[str, Any]]):
        """构建依赖图"""
        self.dependency_graph.clear()
        
        for i, step in enumerate(steps):
            depends_on = step.get("depends_on", [])
            if isinstance(depends_on, list):
                for dep in depends_on:
                    # 解析依赖（可能是字符串如"步骤1"或索引）
                    dep_idx = self._parse_dependency(dep, i, len(steps))
                    if dep_idx is not None and 0 <= dep_idx < len(steps):
                        self.dependency_graph[i].add(dep_idx)
    
    def _parse_dependency(self, dep: Any, current_idx: int, total_steps: int) -> Optional[int]:
        """解析依赖关系"""
        if isinstance(dep, int):
            return dep
        elif isinstance(dep, str):
            # 尝试从字符串中提取数字（如"步骤1" -> 1）
            nums = re.findall(r'\d+', dep)
            if nums:
                idx = int(nums[0]) - 1  # 假设从1开始
                if 0 <= idx < total_steps:
                    return idx
        return None
    
    def _has_cycle(self) -> bool:
        """检测依赖图中是否有循环"""
        visited = set()
        rec_stack = set()
        
        def dfs(node: int) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.dependency_graph.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in self.dependency_graph:
            if node not in visited:
                if dfs(node):
                    return True
        
        return False
    
    def _fix_cycle(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """修复循环依赖"""
        # 简单策略：移除导致循环的依赖
        fixed_steps = []
        for i, step in enumerate(steps):
            fixed_step = step.copy()
            depends_on = step.get("depends_on", [])
            
            # 只保留不导致循环的依赖
            valid_deps = []
            for dep in depends_on:
                dep_idx = self._parse_dependency(dep, i, len(steps))
                if dep_idx is not None and dep_idx < i:  # 只保留前面的步骤
                    valid_deps.append(dep)
            
            fixed_step["depends_on"] = valid_deps
            fixed_steps.append(fixed_step)
        
        return fixed_steps
    
    def _adjust_steps_dynamically(
        self,
        steps: List[Dict[str, Any]],
        execution_results: Dict[int, Dict[str, Any]],
        original_query: str
    ) -> List[Dict[str, Any]]:
        """根据执行结果动态调整步骤"""
        adjusted_steps = []
        
        for i, step in enumerate(steps):
            adjusted_step = step.copy()
            
            # 如果步骤已执行，检查结果
            if i in execution_results:
                result = execution_results[i]
                
                # 如果步骤失败，可能需要添加重试步骤
                if result.get("step_failed", False):
                    # 添加重试步骤（如果重试次数未超限）
                    retry_count = step.get("retry_count", 0)
                    if retry_count < 3:  # 最多重试3次
                        retry_step = step.copy()
                        retry_step["retry_count"] = retry_count + 1
                        retry_step["depends_on"] = []  # 重试步骤不依赖其他步骤
                        adjusted_steps.append(retry_step)
                        self.logger.info(f"🔄 [动态规划] 为步骤{i}添加重试步骤")
                
                # 如果步骤成功，检查是否需要条件分支
                elif result.get("answer") and self._needs_conditional_branch(step, result):
                    # 添加条件分支步骤
                    branch_steps = self._create_conditional_branches(step, result, original_query)
                    adjusted_steps.extend(branch_steps)
                    self.logger.info(f"🌿 [动态规划] 为步骤{i}添加条件分支")
            
            adjusted_steps.append(adjusted_step)
        
        return adjusted_steps
    
    def _needs_conditional_branch(self, step: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """判断是否需要条件分支"""
        # 如果答案不明确（置信度低），可能需要分支
        confidence = result.get("confidence", 1.0)
        if confidence < 0.7:
            return True
        
        # 如果答案包含多个候选，可能需要分支
        answer = result.get("answer", "")
        if " or " in answer.lower() or "|" in answer:
            return True
        
        return False
    
    def _create_conditional_branches(
        self,
        step: Dict[str, Any],
        result: Dict[str, Any],
        original_query: str
    ) -> List[Dict[str, Any]]:
        """创建条件分支步骤"""
        branches = []
        answer = result.get("answer", "")
        
        # 如果答案包含"or"，创建分支
        if " or " in answer.lower():
            parts = answer.split(" or ")
            for i, part in enumerate(parts):
                branch_step = {
                    "type": "conditional_query",
                    "description": f"条件分支 {i+1}: 验证 {part.strip()}",
                    "sub_query": f"验证 {part.strip()} 是否正确",
                    "depends_on": step.get("depends_on", []),
                    "branch_index": i,
                    "confidence": 0.5,
                }
                branches.append(branch_step)
        
        return branches
    
    def _optimize_execution_order(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """优化执行顺序（拓扑排序）"""
        # 构建依赖图
        self._build_dependency_graph(steps)
        
        # 拓扑排序
        in_degree = defaultdict(int)
        for i in range(len(steps)):
            in_degree[i] = 0
        
        for i, deps in self.dependency_graph.items():
            for dep in deps:
                in_degree[i] += 1
        
        # 找到所有没有依赖的步骤
        queue = deque([i for i in range(len(steps)) if in_degree[i] == 0])
        ordered_steps = []
        
        while queue:
            node = queue.popleft()
            ordered_steps.append(steps[node])
            
            # 更新依赖节点的入度
            for i, deps in self.dependency_graph.items():
                if node in deps:
                    in_degree[i] -= 1
                    if in_degree[i] == 0:
                        queue.append(i)
        
        # 如果还有未排序的步骤（可能是循环），添加到末尾
        remaining = [steps[i] for i in range(len(steps)) if steps[i] not in ordered_steps]
        ordered_steps.extend(remaining)
        
        return ordered_steps

