#!/usr/bin/env python3
"""
SOP（标准操作程序）学习系统 - 基于GenericAgent理念

借鉴GenericAgent的种子哲学和SOP学习机制，从任务执行历史中学习并保存为标准操作程序。
系统从成功的任务执行中提取模式，形成可重用的SOP，实现智能体的自我学习和能力扩展。
"""

import json
import time
import hashlib
import logging
from typing import Dict, List, Any, Optional, Union, Tuple, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import pickle
from collections import defaultdict

from src.agents.agent_history_manager import HistoryType
from src.core.verdict import Verdict, VerdictValidator, get_verdict_validator, VerdictLevel


class SOPLevel(str, Enum):
    """SOP层级 - 借鉴GenericAgent的三层内存系统"""
    L0_META = "l0_meta"          # 元SOP：如何管理SOP自身
    L2_GLOBAL = "l2_global"      # 全局事实：环境、凭证、路径
    L3_TASK = "l3_task"          # 任务SOP：具体任务执行流程


class SOPCategory(str, Enum):
    """SOP类别"""
    HAND_EXECUTION = "hand_execution"      # Hand能力执行
    TASK_SEQUENCE = "task_sequence"        # 任务序列
    SYSTEM_OPERATION = "system_operation"  # 系统操作
    API_INTEGRATION = "api_integration"    # API集成
    DATA_PROCESSING = "data_processing"    # 数据处理
    CUSTOM = "custom"                      # 自定义


@dataclass
class SOPStep:
    """SOP执行步骤"""
    step_id: str
    hand_name: str                    # 使用的Hand能力
    parameters: Dict[str, Any]        # 执行参数
    description: str                  # 步骤描述
    expected_output_schema: Optional[Dict[str, Any]] = None  # 预期输出模式
    required_conditions: List[str] = field(default_factory=list)  # 执行条件
    optional_parameters: List[str] = field(default_factory=list)  # 可选参数
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    
    def __post_init__(self):
        if not self.step_id:
            content = f"{self.hand_name}_{hash(str(self.parameters))}"
            self.step_id = hashlib.md5(content.encode()).hexdigest()[:12]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SOPStep":
        """从字典创建"""
        return cls(**data)


@dataclass
class StandardOperatingProcedure:
    """标准操作程序"""
    sop_id: str
    name: str
    description: str
    category: SOPCategory
    level: SOPLevel
    version: str = "1.0.0"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    # 执行流程
    steps: List[SOPStep] = field(default_factory=list)
    pre_conditions: List[str] = field(default_factory=list)  # 执行前提条件
    post_conditions: List[str] = field(default_factory=list)  # 执行后条件
    success_criteria: Dict[str, Any] = field(default_factory=dict)  # 成功标准
    
    # 学习信息
    source_execution_ids: List[str] = field(default_factory=list)  # 来源执行记录ID
    learning_count: int = 0  # 学习次数
    execution_count: int = 0  # 执行次数
    success_rate: float = 0.0  # 成功率
    
    # 关联信息
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # 依赖的其他SOP
    recommended_contexts: List[str] = field(default_factory=list)  # 推荐使用场景
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_executed: Optional[float] = None
    
    def __post_init__(self):
        if not self.sop_id:
            content = f"{self.name}_{self.category.value}_{time.time()}"
            self.sop_id = hashlib.md5(content.encode()).hexdigest()[:16]
    
    def add_step(self, step: SOPStep) -> None:
        """添加执行步骤"""
        self.steps.append(step)
        self.updated_at = time.time()
    
    def remove_step(self, step_id: str) -> bool:
        """移除执行步骤"""
        for i, step in enumerate(self.steps):
            if step.step_id == step_id:
                self.steps.pop(i)
                self.updated_at = time.time()
                return True
        return False
    
    def validate(self) -> Tuple[bool, List[str]]:
        """验证SOP完整性"""
        errors = []
        
        if not self.name:
            errors.append("SOP名称不能为空")
        
        if not self.description:
            errors.append("SOP描述不能为空")
        
        if not self.steps:
            errors.append("SOP必须包含至少一个执行步骤")
        
        # 检查步骤完整性
        for i, step in enumerate(self.steps):
            if not step.hand_name:
                errors.append(f"步骤 {i+1}: Hand名称不能为空")
            if not step.description:
                errors.append(f"步骤 {i+1}: 步骤描述不能为空")
        
        return len(errors) == 0, errors
    
    def get_summary(self) -> Dict[str, Any]:
        """获取SOP摘要"""
        return {
            "sop_id": self.sop_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "level": self.level.value,
            "version": self.version,
            "step_count": len(self.steps),
            "learning_count": self.learning_count,
            "execution_count": self.execution_count,
            "success_rate": self.success_rate,
            "created_at": datetime.fromtimestamp(self.created_at).isoformat(),
            "updated_at": datetime.fromtimestamp(self.updated_at).isoformat(),
            "tags": self.tags
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 转换步骤列表
        data["steps"] = [step.to_dict() for step in self.steps]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StandardOperatingProcedure":
        """从字典创建"""
        # 处理步骤转换
        steps_data = data.pop("steps", [])
        sop = cls(**data)
        sop.steps = [SOPStep.from_dict(step_data) for step_data in steps_data]
        return sop


class SOPSimilarityMetric:
    """SOP相似度度量"""
    
    @staticmethod
    def calculate_step_similarity(step1: SOPStep, step2: SOPStep) -> float:
        """计算步骤相似度"""
        similarity = 0.0
        
        # Hand名称相似度
        if step1.hand_name == step2.hand_name:
            similarity += 0.3
        else:
            # 检查是否为同类Hand
            similarity += 0.1
        
        # 参数相似度
        param_keys1 = set(step1.parameters.keys())
        param_keys2 = set(step2.parameters.keys())
        
        common_keys = param_keys1.intersection(param_keys2)
        all_keys = param_keys1.union(param_keys2)
        
        if all_keys:
            param_key_similarity = len(common_keys) / len(all_keys)
            similarity += param_key_similarity * 0.4
        
        # 描述语义相似度（简化版）
        if step1.description and step2.description:
            # 简单的词重叠计算
            words1 = set(step1.description.lower().split())
            words2 = set(step2.description.lower().split())
            
            if words1 and words2:
                word_overlap = len(words1.intersection(words2)) / len(words1.union(words2))
                similarity += word_overlap * 0.3
        
        return min(similarity, 1.0)
    
    @staticmethod
    def calculate_sop_similarity(sop1: StandardOperatingProcedure, sop2: StandardOperatingProcedure) -> float:
        """计算SOP相似度"""
        # 类别相似度
        if sop1.category != sop2.category:
            return 0.3  # 不同类别仍有基础相似度
        
        similarity = 0.5  # 类别相同的基础相似度
        
        # 步骤结构相似度
        steps_sim = SOPSimilarityMetric._calculate_sequence_similarity(sop1.steps, sop2.steps)
        similarity += steps_sim * 0.5
        
        return min(similarity, 1.0)
    
    @staticmethod
    def _calculate_sequence_similarity(steps1: List[SOPStep], steps2: List[SOPStep]) -> float:
        """计算步骤序列相似度"""
        if not steps1 or not steps2:
            return 0.0
        
        # 使用动态规划计算序列对齐相似度
        n, m = len(steps1), len(steps2)
        dp = [[0.0] * (m + 1) for _ in range(n + 1)]
        
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                step_sim = SOPSimilarityMetric.calculate_step_similarity(steps1[i-1], steps2[j-1])
                dp[i][j] = max(
                    dp[i-1][j-1] + step_sim,  # 匹配
                    dp[i-1][j],               # 删除steps1[i]
                    dp[i][j-1]                # 删除steps2[j]
                )
        
        # 归一化到0-1
        max_possible = min(n, m) * 1.0
        return dp[n][m] / max_possible if max_possible > 0 else 0.0


class SOPSuggestion:
    """SOP优化建议"""
    
    def __init__(self, sop_id: str, suggestion_type: str, description: str, 
                 priority: str = "medium", confidence: float = 0.5):
        self.sop_id = sop_id
        self.suggestion_type = suggestion_type
        self.description = description
        self.priority = priority  # low, medium, high, critical
        self.confidence = confidence  # 0-1
        self.created_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sop_id": self.sop_id,
            "suggestion_type": self.suggestion_type,
            "description": self.description,
            "priority": self.priority,
            "confidence": self.confidence,
            "created_at": datetime.fromtimestamp(self.created_at).isoformat()
        }


class SOPLearningSystem:
    """SOP学习系统 - 核心引擎"""
    
    def __init__(self, persistence_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # SOP存储
        self.sops: Dict[str, StandardOperatingProcedure] = {}
        self.sop_index: Dict[str, List[str]] = defaultdict(list)  # 类别 -> SOP IDs
        self.sop_tags: Dict[str, List[str]] = defaultdict(list)   # 标签 -> SOP IDs
        
        # 学习状态
        self.learning_enabled = True
        self.min_confidence_threshold = 0.7
        self.max_similar_sops = 5
        
        # 持久化配置
        self.persistence_path = persistence_path or ".sop_learning_system.pkl"
        self.auto_save_interval = 300  # 5分钟
        self.last_save_time = time.time()
        
        # 加载现有SOP
        self._load_sops()
        
        # 确保有L0元SOP
        self._ensure_meta_sops()
        
        self.logger.info(f"SOP学习系统初始化完成，已加载 {len(self.sops)} 个SOP")
    
    def _ensure_meta_sops(self) -> None:
        """确保存在元SOP（L0级）"""
        meta_sop_id = "sop_memory_management"
        
        if meta_sop_id not in self.sops:
            meta_sop = StandardOperatingProcedure(
                sop_id=meta_sop_id,
                name="SOP内存管理",
                description="管理SOP学习系统自身的内存和存储",
                category=SOPCategory.SYSTEM_OPERATION,
                level=SOPLevel.L0_META,
                version="1.0.0",
                steps=[
                    SOPStep(
                        step_id="meta_step_1",
                        hand_name="system_hand",  # 假设的系统Hand
                        parameters={"operation": "save_sops", "path": self.persistence_path},
                        description="保存SOP到持久化存储"
                    ),
                    SOPStep(
                        step_id="meta_step_2", 
                        hand_name="system_hand",
                        parameters={"operation": "load_sops", "path": self.persistence_path},
                        description="从持久化存储加载SOP"
                    )
                ],
                tags=["meta", "system", "memory_management"],
                metadata={"auto_generated": True}
            )
            
            self.sops[meta_sop_id] = meta_sop
            self._index_sop(meta_sop)
            self.logger.info("已创建元SOP（内存管理）")
    
    def _index_sop(self, sop: StandardOperatingProcedure) -> None:
        """索引SOP"""
        # 类别索引
        self.sop_index[sop.category.value].append(sop.sop_id)
        
        # 标签索引
        for tag in sop.tags:
            self.sop_tags[tag].append(sop.sop_id)
    
    def _load_sops(self) -> None:
        """从持久化存储加载SOP"""
        try:
            with open(self.persistence_path, 'rb') as f:
                data = pickle.load(f)
            
            loaded_count = 0
            for sop_data in data.get("sops", []):
                try:
                    sop = StandardOperatingProcedure.from_dict(sop_data)
                    self.sops[sop.sop_id] = sop
                    self._index_sop(sop)
                    loaded_count += 1
                except Exception as e:
                    self.logger.error(f"加载SOP失败: {e}")
            
            self.logger.info(f"从持久化存储加载了 {loaded_count} 个SOP")
        except FileNotFoundError:
            self.logger.info("未找到持久化文件，将创建新的SOP存储")
        except Exception as e:
            self.logger.error(f"加载SOP存储失败: {e}")
    
    def _save_sops(self) -> None:
        """保存SOP到持久化存储"""
        try:
            data = {
                "sops": [sop.to_dict() for sop in self.sops.values()],
                "save_timestamp": time.time(),
                "version": "1.0.0"
            }
            
            with open(self.persistence_path, 'wb') as f:
                pickle.dump(data, f)
            
            self.last_save_time = time.time()
            self.logger.debug(f"SOP保存完成，共 {len(self.sops)} 个SOP")
        except Exception as e:
            self.logger.error(f"保存SOP失败: {e}")
    
    def auto_save_check(self) -> None:
        """检查是否需要自动保存"""
        current_time = time.time()
        if current_time - self.last_save_time >= self.auto_save_interval:
            self._save_sops()
    
    def learn_from_execution(self, task_name: str, execution_steps: List[Dict[str, Any]], 
                           verdict: Optional[Verdict] = None, execution_id: str = "", 
                           importance: float = 1.0) -> Optional[str]:
        """
        从执行历史学习SOP - 需要 Verdict 证据包
        
        优化3: SOP学习与Verdict绑定
        - 只有包含完整证据的 Verdict 才能触发学习
        - 防止坏模式被固化
        
        Args:
            task_name: 任务名称
            execution_steps: 执行步骤列表，每个步骤包含hand_name和parameters
            verdict: Verdict 证据包（必须包含完整证据才能学习）
            execution_id: 执行记录ID
            importance: 重要性评分
            
        Returns:
            创建的SOP ID，如果未创建则返回None
        """
        if not self.learning_enabled:
            return None
        
        if not execution_steps:
            self.logger.debug("无执行步骤，跳过学习")
            return None
        
        # Verdict 验证
        if verdict is None:
            self.logger.debug("缺少 Verdict 证据包，跳过学习（需要完整的证据才能学习）")
            return None
        
        # 验证 Verdict 完整性
        validator = get_verdict_validator()
        is_valid, errors = validator.validate(verdict)
        
        if not is_valid:
            self.logger.warning(f"Verdict 验证失败: {errors}，跳过学习")
            return None
        
        # 检查质量等级
        if verdict.quality_level not in [VerdictLevel.COMPLETE, VerdictLevel.HIGH_QUALITY]:
            self.logger.debug(f"Verdict 质量等级不足 ({verdict.quality_level.value})，跳过学习")
            return None
        
        success = verdict.confidence_score >= 0.7
        
        # 1. 查找相似SOP
        similar_sop_id = self._find_similar_sop(execution_steps)
        
        if similar_sop_id:
            # 2. 更新现有SOP
            return self._update_existing_sop(similar_sop_id, execution_steps, execution_id, success, verdict)
        else:
            # 3. 创建新SOP
            return self._create_new_sop(task_name, execution_steps, execution_id, verdict)
    
    def _find_similar_sop(self, execution_steps: List[Dict[str, Any]]) -> Optional[str]:
        """查找相似的SOP"""
        if not execution_steps:
            return None
        
        # 将执行步骤转换为SOPStep对象用于比较
        candidate_steps = []
        for step_data in execution_steps:
            step = SOPStep(
                step_id="",
                hand_name=step_data.get("hand_name", ""),
                parameters=step_data.get("parameters", {}),
                description=step_data.get("description", f"执行 {step_data.get('hand_name', 'unknown')}")
            )
            candidate_steps.append(step)
        
        best_match_id = None
        best_similarity = self.min_confidence_threshold
        
        for sop_id, sop in self.sops.items():
            if sop.level != SOPLevel.L3_TASK:
                continue
            
            similarity = SOPSimilarityMetric.calculate_sequence_similarity(
                candidate_steps, sop.steps
            )
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match_id = sop_id
        
        return best_match_id
    
    def _update_existing_sop(self, sop_id: str, execution_steps: List[Dict[str, Any]], 
                           execution_id: str, success: bool, 
                           verdict: Optional[Verdict] = None) -> str:
        """更新现有SOP"""
        sop = self.sops[sop_id]
        
        # 更新学习信息
        sop.learning_count += 1
        sop.execution_count += 1
        
        if success:
            sop.success_rate = ((sop.success_rate * (sop.execution_count - 1)) + 1.0) / sop.execution_count
        else:
            sop.success_rate = (sop.success_rate * (sop.execution_count - 1)) / sop.execution_count
        
        # 添加来源执行记录
        if execution_id not in sop.source_execution_ids:
            sop.source_execution_ids.append(execution_id)
        
        # 更新元数据（包含 Verdict 信息）
        if verdict:
            if "verdict_ids" not in sop.metadata:
                sop.metadata["verdict_ids"] = []
            if verdict.verdict_id not in sop.metadata["verdict_ids"]:
                sop.metadata["verdict_ids"].append(verdict.verdict_id)
            sop.metadata["last_verdict_level"] = verdict.quality_level.value
            sop.metadata["last_verdict_confidence"] = verdict.confidence_score
        
        # 更新时间戳
        sop.updated_at = time.time()
        
        self.logger.info(f"更新SOP: {sop.name} (ID: {sop_id}), 学习次数: {sop.learning_count}")
        
        # 检查是否需要自动保存
        self.auto_save_check()
        
        return sop_id
    
    def _create_new_sop(self, task_name: str, execution_steps: List[Dict[str, Any]], 
                       execution_id: str, verdict: Optional[Verdict] = None) -> str:
        """创建新SOP"""
        # 生成SOP名称
        sop_name = f"{task_name}_sop_{int(time.time())}"
        
        # 创建步骤
        steps = []
        for i, step_data in enumerate(execution_steps):
            step = SOPStep(
                step_id=f"step_{i+1}",
                hand_name=step_data.get("hand_name", ""),
                parameters=step_data.get("parameters", {}),
                description=step_data.get("description", f"步骤 {i+1}: 执行 {step_data.get('hand_name', 'unknown')}"),
                metadata=step_data.get("metadata", {})
            )
            steps.append(step)
        
        # 确定类别
        category = self._infer_category(execution_steps)
        
        # 构建元数据
        metadata = {"learning_source": "execution_history", "auto_generated": True}
        
        # 添加 Verdict 信息
        if verdict:
            metadata["verdict_ids"] = [verdict.verdict_id]
            metadata["verdict_level"] = verdict.quality_level.value
            metadata["verdict_confidence"] = verdict.confidence_score
            metadata["reasoning_steps_count"] = len(verdict.reasoning_steps)
            metadata["validation_results_count"] = len(verdict.validation_results)
        
        # 创建SOP
        sop = StandardOperatingProcedure(
            sop_id="",
            name=sop_name,
            description=f"从任务 '{task_name}' 学习到的标准操作程序",
            category=category,
            level=SOPLevel.L3_TASK,
            version="1.0.0",
            steps=steps,
            source_execution_ids=[execution_id] if execution_id else [],
            learning_count=1,
            execution_count=1,
            success_rate=1.0,
            tags=["learned", category.value, "verdict_validated"],
            metadata=metadata
        )
        
        # 验证SOP
        is_valid, errors = sop.validate()
        if not is_valid:
            self.logger.warning(f"创建的SOP验证失败: {errors}")
            # 仍保存，但标记为需要优化
            sop.metadata["validation_errors"] = errors
        
        # 保存SOP
        self.sops[sop.sop_id] = sop
        self._index_sop(sop)
        
        self.logger.info(f"创建新SOP: {sop.name} (ID: {sop.sop_id}), 步骤数: {len(steps)}")
        
        # 创建 A/B 实验验证学习效果
        self._create_ab_experiment_for_sop(sop)
        
        # 自动保存
        self.auto_save_check()
        
        return sop.sop_id
    
    def _infer_category(self, execution_steps: List[Dict[str, Any]]) -> SOPCategory:
        """推断执行步骤的类别"""
        if not execution_steps:
            return SOPCategory.CUSTOM
        
        # 分析步骤类型
        hand_names = [step.get("hand_name", "").lower() for step in execution_steps]
        
        # 检查是否为API相关
        api_indicators = ["api", "http", "rest", "request", "call"]
        if any(any(indicator in hand_name for indicator in api_indicators) for hand_name in hand_names):
            return SOPCategory.API_INTEGRATION
        
        # 检查是否为数据处理
        data_indicators = ["data", "process", "transform", "filter", "analyze"]
        if any(any(indicator in hand_name for indicator in data_indicators) for hand_name in hand_names):
            return SOPCategory.DATA_PROCESSING
        
        # 检查是否为系统操作
        system_indicators = ["system", "file", "process", "command", "shell"]
        if any(any(indicator in hand_name for indicator in system_indicators) for hand_name in hand_names):
            return SOPCategory.SYSTEM_OPERATION
        
        # 默认类别
        return SOPCategory.HAND_EXECUTION
    
    def recall_sop(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        回忆相关的SOP
        
        Args:
            task_description: 任务描述
            context: 上下文信息
            
        Returns:
            相关SOP列表，按相关性排序
        """
        relevant_sops = []
        
        # 简单关键词匹配
        task_keywords = set(task_description.lower().split())
        
        for sop_id, sop in self.sops.items():
            if sop.level != SOPLevel.L3_TASK:
                continue
            
            # 计算相关性分数
            relevance = self._calculate_relevance(sop, task_keywords, context)
            
            if relevance > 0:
                relevant_sops.append({
                    "sop": sop,
                    "relevance": relevance,
                    "summary": sop.get_summary()
                })
        
        # 按相关性排序
        relevant_sops.sort(key=lambda x: x["relevance"], reverse=True)
        
        # 返回前N个
        return relevant_sops[:self.max_similar_sops]
    
    def _calculate_relevance(self, sop: StandardOperatingProcedure, 
                           task_keywords: Set[str], context: Optional[Dict[str, Any]]) -> float:
        """计算SOP与任务的相关性"""
        relevance = 0.0
        
        # 名称匹配
        name_keywords = set(sop.name.lower().split())
        name_overlap = len(name_keywords.intersection(task_keywords))
        if name_keywords:
            relevance += name_overlap / len(name_keywords) * 0.3
        
        # 描述匹配
        desc_keywords = set(sop.description.lower().split())
        desc_overlap = len(desc_keywords.intersection(task_keywords))
        if desc_keywords:
            relevance += desc_overlap / len(desc_keywords) * 0.4
        
        # 标签匹配
        tag_matches = sum(1 for tag in sop.tags if any(keyword in tag.lower() for keyword in task_keywords))
        if sop.tags:
            relevance += tag_matches / len(sop.tags) * 0.2
        
        # 上下文匹配（如果有）
        if context:
            # 检查SOP的推荐使用场景
            recommended_matches = sum(1 for ctx in sop.recommended_contexts 
                                    if any(keyword in ctx.lower() for keyword in task_keywords))
            if sop.recommended_contexts:
                relevance += recommended_matches / len(sop.recommended_contexts) * 0.1
        
        # 考虑成功率
        relevance *= (0.7 + 0.3 * sop.success_rate)  # 成功率影响权重
        
        return min(relevance, 1.0)
    
    def get_sop(self, sop_id: str) -> Optional[StandardOperatingProcedure]:
        """获取指定ID的SOP"""
        return self.sops.get(sop_id)
    
    def get_all_sops(self, level: Optional[SOPLevel] = None, 
                    category: Optional[SOPCategory] = None) -> List[Dict[str, Any]]:
        """获取所有SOP"""
        result = []
        
        for sop_id, sop in self.sops.items():
            if level and sop.level != level:
                continue
            if category and sop.category != category:
                continue
            
            result.append({
                "sop": sop,
                "summary": sop.get_summary()
            })
        
        return result
    
    def delete_sop(self, sop_id: str) -> bool:
        """删除SOP"""
        if sop_id in self.sops:
            sop = self.sops.pop(sop_id)
            
            # 从索引中移除
            self._remove_from_index(sop)
            
            self.logger.info(f"删除SOP: {sop.name} (ID: {sop_id})")
            self.auto_save_check()
            return True
        
        return False
    
    def _remove_from_index(self, sop: StandardOperatingProcedure) -> None:
        """从索引中移除SOP"""
        # 从类别索引移除
        if sop.sop_id in self.sop_index[sop.category.value]:
            self.sop_index[sop.category.value].remove(sop.sop_id)
        
        # 从标签索引移除
        for tag in sop.tags:
            if sop.sop_id in self.sop_tags[tag]:
                self.sop_tags[tag].remove(sop.sop_id)
    
    def analyze_sop_quality(self, sop_id: str) -> Dict[str, Any]:
        """分析SOP质量"""
        sop = self.get_sop(sop_id)
        if not sop:
            return {"error": f"SOP {sop_id} 不存在"}
        
        # 基础质量指标
        quality_score = 0.0
        
        # 1. 步骤完整性
        step_completeness = 0.0
        for step in sop.steps:
            if step.hand_name and step.description:
                step_completeness += 1.0
        if sop.steps:
            step_completeness /= len(sop.steps)
        
        quality_score += step_completeness * 0.3
        
        # 2. 学习次数影响
        learning_impact = min(sop.learning_count / 10.0, 1.0)  # 10次学习达到最大
        quality_score += learning_impact * 0.2
        
        # 3. 成功率影响
        quality_score += sop.success_rate * 0.3
        
        # 4. 验证状态
        is_valid, errors = sop.validate()
        if is_valid:
            quality_score += 0.2
        
        # 限制在0-1范围
        quality_score = min(quality_score, 1.0)
        
        return {
            "sop_id": sop_id,
            "sop_name": sop.name,
            "quality_score": quality_score,
            "step_completeness": step_completeness,
            "learning_count": sop.learning_count,
            "execution_count": sop.execution_count,
            "success_rate": sop.success_rate,
            "is_valid": is_valid,
            "validation_errors": errors if not is_valid else [],
            "last_updated": datetime.fromtimestamp(sop.updated_at).isoformat(),
            "age_days": (time.time() - sop.created_at) / 86400,
            "suggestions": self._generate_sop_suggestions(sop, quality_score)
        }
    
    def _generate_sop_suggestions(self, sop: StandardOperatingProcedure, quality_score: float) -> List[Dict[str, Any]]:
        """生成SOP优化建议"""
        suggestions = []
        
        # 基于质量分数的建议
        if quality_score < 0.5:
            suggestions.append({
                "type": "general_improvement",
                "description": "SOP质量较低，建议增加学习次数或优化步骤",
                "priority": "high"
            })
        
        # 学习次数不足
        if sop.learning_count < 3:
            suggestions.append({
                "type": "insufficient_learning",
                "description": f"学习次数不足 ({sop.learning_count}次)，建议从更多成功执行中学习",
                "priority": "medium"
            })
        
        # 步骤描述不完整
        incomplete_steps = [i+1 for i, step in enumerate(sop.steps) if not step.description]
        if incomplete_steps:
            suggestions.append({
                "type": "step_description",
                "description": f"步骤 {incomplete_steps} 缺少描述，建议补充",
                "priority": "medium"
            })
        
        # 成功率较低
        if sop.execution_count > 5 and sop.success_rate < 0.7:
            suggestions.append({
                "type": "low_success_rate",
                "description": f"成功率较低 ({sop.success_rate*100:.1f}%)，建议检查执行条件",
                "priority": "high"
            })
        
        return suggestions
    
    def export_sops(self, format: str = "json", sop_ids: Optional[List[str]] = None) -> Union[str, bytes]:
        """导出SOP"""
        sops_to_export = []
        
        if sop_ids:
            for sop_id in sop_ids:
                if sop_id in self.sops:
                    sops_to_export.append(self.sops[sop_id])
        else:
            sops_to_export = list(self.sops.values())
        
        export_data = {
            "export_timestamp": time.time(),
            "total_sops": len(sops_to_export),
            "sops": [sop.to_dict() for sop in sops_to_export],
            "system_info": {
                "learning_enabled": self.learning_enabled,
                "min_confidence_threshold": self.min_confidence_threshold,
                "max_similar_sops": self.max_similar_sops
            }
        }
        
        if format == "json":
            return json.dumps(export_data, indent=2, default=str, ensure_ascii=False)
        elif format == "pickle":
            return pickle.dumps(export_data)
        else:
            raise ValueError(f"不支持的导出格式: {format}")
    
    def import_sops(self, data: Union[str, bytes], format: str = "json") -> Dict[str, Any]:
        """导入SOP"""
        try:
            if format == "json":
                import_data = json.loads(data)
            elif format == "pickle":
                import_data = pickle.loads(data)
            else:
                return {"success": False, "error": f"不支持的导入格式: {format}"}
            
            imported_count = 0
            skipped_count = 0
            failed_count = 0
            
            for sop_data in import_data.get("sops", []):
                try:
                    sop = StandardOperatingProcedure.from_dict(sop_data)
                    
                    # 检查是否已存在
                    if sop.sop_id in self.sops:
                        # 合并现有SOP
                        existing_sop = self.sops[sop.sop_id]
                        existing_sop.learning_count += sop.learning_count
                        existing_sop.execution_count += sop.execution_count
                        # 合并成功率
                        if existing_sop.execution_count > 0:
                            total_success = (existing_sop.success_rate * (existing_sop.execution_count - sop.execution_count) +
                                           sop.success_rate * sop.execution_count)
                            existing_sop.success_rate = total_success / existing_sop.execution_count
                        
                        # 合并标签
                        for tag in sop.tags:
                            if tag not in existing_sop.tags:
                                existing_sop.tags.append(tag)
                        
                        # 合并来源执行记录
                        for exec_id in sop.source_execution_ids:
                            if exec_id not in existing_sop.source_execution_ids:
                                existing_sop.source_execution_ids.append(exec_id)
                        
                        existing_sop.updated_at = time.time()
                        skipped_count += 1
                    else:
                        # 添加新SOP
                        self.sops[sop.sop_id] = sop
                        self._index_sop(sop)
                        imported_count += 1
                    
                except Exception as e:
                    self.logger.error(f"导入SOP失败: {e}")
                    failed_count += 1
            
            # 保存更新
            self._save_sops()
            
            return {
                "success": True,
                "imported_count": imported_count,
                "skipped_count": skipped_count,
                "failed_count": failed_count,
                "total_sops": len(self.sops)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        total_sops = len(self.sops)
        
        # 按类别统计
        by_category = defaultdict(int)
        by_level = defaultdict(int)
        
        for sop in self.sops.values():
            by_category[sop.category.value] += 1
            by_level[sop.level.value] += 1
        
        # 计算平均质量
        quality_scores = []
        for sop_id in self.sops.keys():
            quality_analysis = self.analyze_sop_quality(sop_id)
            if "quality_score" in quality_analysis:
                quality_scores.append(quality_analysis["quality_score"])
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        return {
            "total_sops": total_sops,
            "by_category": dict(by_category),
            "by_level": dict(by_level),
            "average_quality_score": avg_quality,
            "learning_enabled": self.learning_enabled,
            "persistence_enabled": bool(self.persistence_path),
            "last_save_time": datetime.fromtimestamp(self.last_save_time).isoformat(),
            "auto_save_interval_seconds": self.auto_save_interval
        }
    
    def _create_ab_experiment_for_sop(self, sop: StandardOperatingProcedure) -> Optional[str]:
        """为新学习的 SOP 创建 A/B 实验
        
        Args:
            sop: 新创建的 SOP
            
        Returns:
            实验 ID，如果创建失败返回 None
        """
        try:
            from src.core.ab_testing.ab_framework import get_ab_testing_framework
            
            framework = get_ab_testing_framework()
            if not framework:
                self.logger.warning("A/B Testing Framework 不可用，跳过实验创建")
                return None
            
            # 创建实验：对比使用 SOP vs 不使用 SOP
            experiment = framework.create_experiment(
                name=f"sop_validation_{sop.sop_id}",
                description=f"验证 SOP {sop.name} 的效果",
                control_name="without_sop",
                treatment_name="with_sop",
                traffic_split=50.0
            )
            
            # 启动实验
            framework.start_experiment(experiment.experiment_id)
            
            # 在 SOP 元数据中记录实验 ID
            if "ab_experiments" not in sop.metadata:
                sop.metadata["ab_experiments"] = []
            sop.metadata["ab_experiments"].append(experiment.experiment_id)
            
            self.logger.info(f"✅ 为 SOP {sop.sop_id} 创建 A/B 实验: {experiment.experiment_id}")
            return experiment.experiment_id
            
        except Exception as e:
            self.logger.warning(f"创建 A/B 实验失败: {e}")
            return None
    
    def record_sop_usage(self, sop_id: str, success: bool, confidence: float = 0.0) -> None:
        """记录 SOP 使用结果（用于 A/B 测试数据收集）
        
        Args:
            sop_id: SOP ID
            success: 是否成功
            confidence: 置信度
        """
        sop = self.sops.get(sop_id)
        if not sop:
            return
        
        # 检查是否有活跃的 A/B 实验
        ab_experiments = sop.metadata.get("ab_experiments", [])
        if not ab_experiments:
            return
        
        try:
            from src.core.ab_testing.ab_framework import get_ab_testing_framework
            
            framework = get_ab_testing_framework()
            if not framework:
                return
            
            # 记录到最新的实验
            for exp_id in ab_experiments:
                # 假设 SOP 被使用，所以记录到 treatment 组
                user_id = f"sop_user_{sop_id}_{time.time()}"
                framework.record_metric(exp_id, user_id, "success", 1.0 if success else 0.0)
                framework.record_metric(exp_id, user_id, "confidence", confidence)
                
        except Exception as e:
            self.logger.debug(f"记录 SOP 使用失败: {e}")


# 全局SOP学习系统实例
_sop_learning_system_instance: Optional[SOPLearningSystem] = None


def get_sop_learning_system(persistence_path: Optional[str] = None) -> SOPLearningSystem:
    """获取SOP学习系统实例（单例模式）"""
    global _sop_learning_system_instance
    
    if _sop_learning_system_instance is None:
        _sop_learning_system_instance = SOPLearningSystem(persistence_path)
    
    return _sop_learning_system_instance