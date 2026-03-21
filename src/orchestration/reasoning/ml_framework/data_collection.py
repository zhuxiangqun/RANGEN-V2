"""
数据收集管道 - 自动化收集和标注执行轨迹
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import json
import re
import atexit

logger = logging.getLogger(__name__)


class DataCollectionPipeline:
    """自动化数据收集和标注管道
    
    收集系统执行轨迹，自动标注，并将困难样本推送到人工标注队列。
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """初始化数据收集管道
        
        Args:
            storage_path: 数据存储路径
        """
        self.logger = logging.getLogger(__name__)
        self.storage_path = storage_path or "data/ml_training"
        self.collection_buffer = []
        self.annotation_queue = []
        
        # 🚀 新增：注册退出时保存数据的处理函数
        atexit.register(self.finalize)
    
    def finalize(self):
        """程序退出时保存缓冲区中的数据"""
        if self.collection_buffer:
            self.logger.info(f"💾 程序退出，保存 {len(self.collection_buffer)} 条数据")
            self._save_buffer()
    
    def collect_execution_trace(self, trace: Dict[str, Any]) -> None:
        """收集执行轨迹
        
        Args:
            trace: 执行轨迹字典，包含：
                - query: 查询文本
                - plan: 生成的计划
                - execution: 执行步骤
                - result: 最终结果
                - metrics: 性能指标
        """
        trace_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": trace.get("query", ""),
            "generated_plan": trace.get("plan", {}),
            "execution_steps": trace.get("execution", []),
            "final_result": trace.get("result", {}),
            "performance_metrics": trace.get("metrics", {})
        }
        
        self.collection_buffer.append(trace_entry)
        
        # 自动标注
        auto_labels = self._auto_annotate(trace_entry)
        trace_entry["auto_labels"] = auto_labels
        
        # 困难样本推送到人工标注队列
        if auto_labels.get("confidence", 1.0) < 0.7:
            self.annotation_queue.append(trace_entry)
            self.logger.info(f"📋 困难样本已推送到人工标注队列: {trace['query'][:50]}...")
        
        # 定期保存
        if len(self.collection_buffer) >= 100:
            self._save_buffer()
    
    def _auto_annotate(self, trace: Dict[str, Any]) -> Dict[str, Any]:
        """自动标注执行轨迹
        
        Args:
            trace: 执行轨迹
            
        Returns:
            自动标注结果，包含：
            - plan_quality: 计划质量评分
            - step_correctness: 步骤正确性
            - parallel_opportunities: 错过的并行机会
            - retry_effectiveness: 重试策略有效性
            - confidence: 标注置信度
        """
        labels = {
            "plan_quality": self._evaluate_plan_quality(trace),
            "step_correctness": self._evaluate_step_correctness(trace),
            "parallel_opportunities": self._identify_missed_parallelism(trace),
            "retry_effectiveness": self._evaluate_retry_strategy(trace)
        }
        
        # 计算整体置信度（简单平均，后续可以用ML模型）
        confidence = sum(labels.values()) / len(labels) if labels else 0.0
        labels["confidence"] = confidence
        
        return labels
    
    def _evaluate_plan_quality(self, trace: Dict[str, Any]) -> float:
        """评估计划质量（0-1）
        
        基于以下因素：
        - 步骤数量合理性（太少或太多都不好）
        - 依赖关系合理性
        - 执行结果（成功/失败）
        - 最终答案质量
        """
        score = 0.5  # 基础分数
        
        plan = trace.get("generated_plan", {})
        steps = plan.get("steps", [])
        result = trace.get("final_result", {})
        metrics = trace.get("performance_metrics", {})
        
        # 如果推理失败，质量分数应该很低
        if result.get("error") or not result.get("success", False):
            # 失败的情况，但如果有部分步骤，给少量分数
            if steps:
                return 0.2  # 有步骤但失败
            return 0.1  # 完全失败
        
        # 1. 步骤数量合理性（0-1分，权重0.2）
        num_steps = len(steps)
        if num_steps == 0:
            step_count_score = 0.0
        elif 1 <= num_steps <= 5:
            step_count_score = 1.0  # 理想范围
        elif 6 <= num_steps <= 10:
            step_count_score = 0.8  # 可接受
        elif 11 <= num_steps <= 15:
            step_count_score = 0.6  # 偏多
        else:
            step_count_score = 0.4  # 太多
        
        # 2. 依赖关系合理性（0-1分，权重0.2）
        dependency_score = 1.0
        if steps:
            # 检查是否有循环依赖
            has_cycle = self._check_dependency_cycles(steps)
            if has_cycle:
                dependency_score = 0.3
            
            # 检查依赖关系是否合理（步骤不应该依赖未来的步骤）
            invalid_deps = 0
            for i, step in enumerate(steps):
                depends_on = step.get("depends_on", [])
                for dep in depends_on:
                    # 如果depends_on是字符串（如"步骤1"），尝试解析
                    if isinstance(dep, str):
                        # 简单检查：如果包含数字，提取它
                        nums = re.findall(r'\d+', dep)
                        if nums:
                            dep_idx = int(nums[0]) - 1  # 假设从1开始
                            if dep_idx >= i + 1:  # 依赖未来步骤
                                invalid_deps += 1
                    elif isinstance(dep, int):
                        if dep >= i + 1:  # 依赖未来步骤
                            invalid_deps += 1
            
            if invalid_deps > 0:
                dependency_score = max(0.3, 1.0 - (invalid_deps / len(steps)))
        
        # 3. 执行结果（0-1分，权重0.3）
        execution_score = 0.5
        if result.get("success", False):
            execution_score = 1.0
        else:
            # 即使失败，如果有最终答案，给部分分数
            if result.get("final_answer") and result.get("final_answer", "").strip():
                execution_score = 0.6
        
        # 4. 步骤执行成功率（0-1分，权重0.3）
        step_success_score = 1.0
        execution_steps = trace.get("execution_steps", [])
        if execution_steps:
            failed_steps = sum(1 for step in execution_steps if step.get("step_failed", False))
            total_steps = len(execution_steps)
            if total_steps > 0:
                step_success_score = 1.0 - (failed_steps / total_steps)
        
        # 加权平均
        score = (
            step_count_score * 0.2 +
            dependency_score * 0.2 +
            execution_score * 0.3 +
            step_success_score * 0.3
        )
        
        return max(0.0, min(1.0, score))
    
    def _evaluate_step_correctness(self, trace: Dict[str, Any]) -> float:
        """评估步骤正确性（0-1）
        
        基于：
        - 步骤执行结果
        - 答案是否存在
        - 步骤是否失败
        - 答案恢复情况
        """
        execution_steps = trace.get("execution_steps", [])
        if not execution_steps:
            # 如果没有执行步骤，检查是否有错误
            if trace.get("final_result", {}).get("error"):
                return 0.0
            return 0.5  # 无执行步骤，无法评估
        
        total_steps = len(execution_steps)
        correct_steps = 0
        
        for step in execution_steps:
            step_score = 1.0
            
            # 检查步骤是否失败
            if step.get("step_failed", False):
                step_score = 0.0
            else:
                # 检查是否有答案
                has_answer = bool(step.get("answer") and step.get("answer", "").strip())
                if not has_answer:
                    step_score = 0.3  # 无答案，但未标记为失败
                else:
                    # 检查是否通过恢复策略获得答案
                    if step.get("answer_recovered", False):
                        step_score = 0.7  # 通过恢复获得，质量稍低
                    else:
                        step_score = 1.0  # 正常获得答案
            
            correct_steps += step_score
        
        # 平均分数
        avg_score = correct_steps / total_steps if total_steps > 0 else 0.0
        return max(0.0, min(1.0, avg_score))
    
    def _identify_missed_parallelism(self, trace: Dict[str, Any]) -> float:
        """识别错过的并行机会（0-1，越高表示错过的机会越多）
        
        分析执行步骤，识别可以并行但串行执行的情况。
        """
        plan = trace.get("generated_plan", {})
        steps = plan.get("steps", [])
        
        if len(steps) < 2:
            return 0.0  # 少于2个步骤，无并行机会
        
        # 统计独立步骤（depends_on为空或只依赖已完成步骤）
        independent_steps = []
        for i, step in enumerate(steps):
            depends_on = step.get("depends_on", [])
            if not depends_on or depends_on == []:
                independent_steps.append(i)
        
        # 如果有多个独立步骤，但它们串行执行，则存在并行机会
        missed_opportunities = 0
        if len(independent_steps) >= 2:
            # 检查这些独立步骤是否连续执行（串行）
            # 简单启发式：如果独立步骤的索引连续，可能是串行执行
            consecutive_independent = 0
            for i in range(len(independent_steps) - 1):
                if independent_steps[i+1] == independent_steps[i] + 1:
                    consecutive_independent += 1
            
            if consecutive_independent > 0:
                # 存在连续执行的独立步骤，可能错过并行机会
                missed_opportunities = consecutive_independent / len(independent_steps)
        
        # 检查是否有parallel_group标记
        has_parallel_groups = any(
            step.get("parallel_group") for step in steps
        )
        
        if has_parallel_groups:
            # 如果有并行组标记，减少错过的机会分数
            missed_opportunities *= 0.5
        
        return max(0.0, min(1.0, missed_opportunities))
    
    def _evaluate_retry_strategy(self, trace: Dict[str, Any]) -> float:
        """评估重试策略有效性（0-1）
        
        基于：
        - 是否有重试
        - 重试是否成功
        - 重试次数是否合理
        """
        execution_steps = trace.get("execution_steps", [])
        if not execution_steps:
            # 如果没有执行步骤，检查是否有错误
            if trace.get("final_result", {}).get("error"):
                return 0.0  # 完全失败，重试策略无效
            return 0.5  # 无执行步骤，无法评估
        
        # 统计恢复成功的步骤
        recovered_steps = sum(
            1 for step in execution_steps
            if step.get("answer_recovered", False)
        )
        
        # 统计失败的步骤
        failed_steps = sum(
            1 for step in execution_steps
            if step.get("step_failed", False)
        )
        
        total_steps = len(execution_steps)
        
        if total_steps == 0:
            return 0.5
        
        # 如果所有步骤都成功，重试策略有效（可能不需要重试，或者重试成功）
        if failed_steps == 0:
            return 1.0
        
        # 如果有失败的步骤，但通过恢复策略成功了一些，给部分分数
        if recovered_steps > 0:
            recovery_rate = recovered_steps / failed_steps if failed_steps > 0 else 0.0
            return max(0.3, min(1.0, recovery_rate))
        
        # 如果有失败的步骤，但没有恢复成功，重试策略无效
        return 0.2
    
    def _check_dependency_cycles(self, steps: List[Dict[str, Any]]) -> bool:
        """检查依赖关系是否有循环
        
        Args:
            steps: 步骤列表
            
        Returns:
            True如果存在循环依赖
        """
        # 构建依赖图
        graph = {}
        for i, step in enumerate(steps):
            depends_on = step.get("depends_on", [])
            graph[i] = []
            for dep in depends_on:
                if isinstance(dep, int):
                    if 0 <= dep < len(steps):
                        graph[i].append(dep)
                elif isinstance(dep, str):
                    # 尝试解析字符串依赖（如"步骤1"）
                    nums = re.findall(r'\d+', dep)
                    if nums:
                        dep_idx = int(nums[0]) - 1  # 假设从1开始
                        if 0 <= dep_idx < len(steps):
                            graph[i].append(dep_idx)
        
        # 使用DFS检测循环
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in range(len(steps)):
            if node not in visited:
                if has_cycle(node):
                    return True
        
        return False
    
    def _save_buffer(self) -> None:
        """保存缓冲区数据"""
        if not self.collection_buffer:
            return
        
        try:
            import os
            import json
            from pathlib import Path
            
            # 确保目录存在
            Path(self.storage_path).mkdir(parents=True, exist_ok=True)
            
            # 生成文件名（带时间戳）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"execution_traces_{timestamp}.jsonl"
            filepath = os.path.join(self.storage_path, filename)
            
            # 保存为JSONL格式（每行一个JSON对象）
            with open(filepath, 'w', encoding='utf-8') as f:
                for trace in self.collection_buffer:
                    f.write(json.dumps(trace, ensure_ascii=False) + '\n')
            
            self.logger.info(f"💾 保存 {len(self.collection_buffer)} 条数据到: {filepath}")
            self.collection_buffer.clear()
        except Exception as e:
            self.logger.error(f"❌ 保存数据失败: {e}")
    
    def extract_training_data_for_model(self, model_name: str, max_samples: Optional[int] = None) -> Dict[str, Any]:
        """从收集的执行轨迹中提取特定模型的训练数据
        
        Args:
            model_name: 模型名称（如"parallel_query_classifier", "deep_confidence_estimator"等）
            max_samples: 最大样本数（None表示使用所有数据）
            
        Returns:
            训练数据字典，包含：
                - training_data: 训练数据列表
                - labels: 标签列表（如果是监督学习）
                - metadata: 元数据
        """
        try:
            # 加载所有收集的数据
            all_traces = []
            
            # 从缓冲区加载
            all_traces.extend(self.collection_buffer)
            
            # 从文件加载
            from pathlib import Path
            storage_path = Path(self.storage_path)
            if storage_path.exists():
                for file_path in storage_path.glob("execution_traces_*.jsonl"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                if line.strip():
                                    trace = json.loads(line)
                                    all_traces.append(trace)
                    except Exception as e:
                        self.logger.warning(f"加载文件失败 {file_path}: {e}")
            
            if not all_traces:
                return {
                    "training_data": [],
                    "labels": [],
                    "metadata": {"total_traces": 0, "model_name": model_name}
                }
            
            # 限制样本数
            if max_samples and len(all_traces) > max_samples:
                all_traces = all_traces[-max_samples:]
            
            # 根据模型类型提取训练数据
            if model_name == "parallel_query_classifier":
                return self._extract_parallel_classifier_data(all_traces)
            elif model_name == "deep_confidence_estimator":
                return self._extract_confidence_estimator_data(all_traces)
            elif model_name == "logic_structure_parser":
                return self._extract_logic_parser_data(all_traces)
            elif model_name == "fewshot_pattern_learner":
                return self._extract_fewshot_learner_data(all_traces)
            elif model_name == "transformer_planner":
                return self._extract_transformer_planner_data(all_traces)
            elif model_name == "gnn_plan_optimizer":
                return self._extract_gnn_optimizer_data(all_traces)
            else:
                self.logger.warning(f"未知的模型名称: {model_name}")
                return {
                    "training_data": [],
                    "labels": [],
                    "metadata": {"total_traces": len(all_traces), "model_name": model_name, "error": "unknown_model"}
                }
                
        except Exception as e:
            self.logger.error(f"提取训练数据失败: {e}")
            return {
                "training_data": [],
                "labels": [],
                "metadata": {"error": str(e), "model_name": model_name}
            }
    
    def _extract_parallel_classifier_data(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """提取并行查询分类器的训练数据"""
        training_data = []
        labels = []
        
        for trace in traces:
            query = trace.get("query", "")
            plan = trace.get("generated_plan", {})
            steps = plan.get("steps", [])
            
            # 检查是否有并行组
            parallel_groups = set()
            for step in steps:
                pg = step.get("parallel_group")
                if pg:
                    parallel_groups.add(pg)
            
            # 标签：是否有并行结构
            has_parallel = len(parallel_groups) > 1 or any(
                len([s for s in steps if s.get("parallel_group") == pg]) > 1 
                for pg in parallel_groups
            )
            
            if query:
                training_data.append(query)
                labels.append(has_parallel)
        
        return {
            "training_data": training_data,
            "labels": labels,
            "metadata": {
                "total_samples": len(training_data),
                "positive_samples": sum(labels),
                "negative_samples": len(labels) - sum(labels)
            }
        }
    
    def _extract_confidence_estimator_data(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """提取置信度评估器的训练数据"""
        training_data = []
        labels = []
        
        for trace in traces:
            query = trace.get("query", "")
            result = trace.get("final_result", {})
            execution_steps = trace.get("execution_steps", [])
            
            # 提取特征
            evidence_count = sum(step.get("evidence_count", 0) for step in execution_steps)
            failed_steps = sum(1 for step in execution_steps if step.get("step_failed", False))
            total_steps = len(execution_steps)
            success = result.get("success", False)
            
            # 标签：实际置信度（基于结果）
            confidence = result.get("total_confidence", 0.5) if success else 0.2
            
            if query:
                training_data.append({
                    "query": query,
                    "answer": result.get("final_answer", ""),
                    "evidence": [],  # 简化：不包含完整证据
                    "context": {
                        "evidence_count": evidence_count,
                        "failed_steps": failed_steps,
                        "total_steps": total_steps,
                        "success": success
                    }
                })
                labels.append(confidence)
        
        return {
            "training_data": training_data,
            "labels": labels,
            "metadata": {
                "total_samples": len(training_data),
                "avg_confidence": sum(labels) / len(labels) if labels else 0.0
            }
        }
    
    def _extract_logic_parser_data(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """提取逻辑结构解析器的训练数据"""
        training_data = []
        labels = []
        
        for trace in traces:
            query = trace.get("query", "")
            plan = trace.get("generated_plan", {})
            steps = plan.get("steps", [])
            
            # 检测逻辑结构类型
            query_lower = query.lower()
            structure_type = "simple"
            
            if " and " in query_lower or " or " in query_lower:
                structure_type = "compound"
            elif any(step.get("parallel_group") for step in steps):
                structure_type = "parallel"
            elif len(steps) > 3:
                structure_type = "complex"
            
            if query:
                training_data.append(query)
                labels.append(structure_type)
        
        return {
            "training_data": training_data,
            "labels": labels,
            "metadata": {
                "total_samples": len(training_data),
                "structure_types": {label: labels.count(label) for label in set(labels)}
            }
        }
    
    def _extract_fewshot_learner_data(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """提取少样本学习器的训练数据"""
        training_data = []
        labels = []
        
        for trace in traces:
            query = trace.get("query", "")
            plan = trace.get("generated_plan", {})
            steps = plan.get("steps", [])
            
            # 提取模式（基于查询类型和步骤结构）
            pattern = "general"
            if steps:
                step_types = [step.get("type", "") for step in steps]
                if "answer_synthesis" in step_types:
                    pattern = "synthesis"
                elif len(steps) == 1:
                    pattern = "single_step"
                elif any(step.get("parallel_group") for step in steps):
                    pattern = "parallel"
            
            if query:
                training_data.append(query)
                labels.append(pattern)
        
        return {
            "training_data": training_data,
            "labels": labels,
            "metadata": {
                "total_samples": len(training_data),
                "patterns": {label: labels.count(label) for label in set(labels)}
            }
        }
    
    def _extract_transformer_planner_data(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """提取Transformer计划生成器的训练数据"""
        training_data = []
        labels = []
        
        for trace in traces:
            query = trace.get("query", "")
            plan = trace.get("generated_plan", {})
            steps = plan.get("steps", [])
            
            if query and steps:
                training_data.append(query)
                # 标签：计划步骤（JSON格式）
                labels.append(json.dumps(steps, ensure_ascii=False))
        
        return {
            "training_data": training_data,
            "labels": labels,
            "metadata": {
                "total_samples": len(training_data),
                "avg_steps": sum(len(json.loads(label)) if isinstance(label, str) else 0 for label in labels) / len(labels) if labels else 0
            }
        }
    
    def _extract_gnn_optimizer_data(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """提取GNN计划优化器的训练数据"""
        training_data = []
        labels = []
        
        for trace in traces:
            plan = trace.get("generated_plan", {})
            steps = plan.get("steps", [])
            execution_steps = trace.get("execution_steps", [])
            
            if steps:
                # 检查是否有优化机会（基于执行结果）
                has_optimization = False
                failed_steps = sum(1 for step in execution_steps if step.get("step_failed", False))
                if failed_steps > 0:
                    has_optimization = True
                
                # 检查是否有并行机会
                parallel_groups = set(step.get("parallel_group") for step in steps if step.get("parallel_group"))
                if len(parallel_groups) == 0 and len(steps) > 1:
                    # 检查是否有可以并行的步骤
                    independent_steps = [i for i, step in enumerate(steps) if not step.get("depends_on")]
                    if len(independent_steps) > 1:
                        has_optimization = True
                
                training_data.append({
                    "steps": steps,
                    "query": trace.get("query", "")
                })
                
                # 标签：优化建议（简化：是否有优化机会）
                suggestions = ["parallelize"] if has_optimization else []
                labels.append(suggestions)
        
        return {
            "training_data": training_data,
            "labels": labels,
            "metadata": {
                "total_samples": len(training_data),
                "optimization_opportunities": sum(1 for label in labels if label)
            }
        }
    
    def get_annotation_queue(self) -> List[Dict[str, Any]]:
        """获取人工标注队列"""
        return self.annotation_queue
    
    def mark_as_annotated(self, trace_id: str, manual_labels: Dict[str, Any]) -> None:
        """标记为已人工标注
        
        Args:
            trace_id: 轨迹ID
            manual_labels: 人工标注结果
        """
        try:
            # 🚀 实现：更新标注队列中的轨迹
            for i, trace in enumerate(self.annotation_queue):
                # 使用查询文本作为ID（简化版本）
                if trace.get("query", "") == trace_id or str(i) == trace_id:
                    trace["manual_labels"] = manual_labels
                    trace["auto_labels"]["confidence"] = 1.0  # 人工标注置信度为1.0
                    trace["is_manually_annotated"] = True
                    
                    # 从队列中移除，添加到已标注列表
                    self.annotation_queue.pop(i)
                    
                    # 保存到已标注文件
                    annotated_dir = Path(self.storage_path) / "annotated"
                    annotated_dir.mkdir(parents=True, exist_ok=True)
                    annotated_file = annotated_dir / f"annotated_{trace_id.replace(' ', '_')[:50]}.json"
                    with open(annotated_file, 'w', encoding='utf-8') as f:
                        json.dump(trace, f, ensure_ascii=False, indent=2)
                    
                    self.logger.info(f"✅ 轨迹 {trace_id} 已人工标注并保存")
                    return
            
            self.logger.warning(f"⚠️ 未找到轨迹: {trace_id}")
        except Exception as e:
            self.logger.error(f"❌ 标注更新失败: {e}")
