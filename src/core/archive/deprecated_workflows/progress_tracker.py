"""
显式进度跟踪器 - Progress Tracker
===================================

Agent 长时运行的"心智锚点"，用于防止 Agent 在长上下文中迷失宏观目标。

功能：
1. 宏观目标跟踪 - 记录当前任务的总体目标
2. 进度节点 - 记录已完成的关键步骤
3. 下一步计划 - 记录待执行的关键节点
4. 决策日志 - 记录重要的决策点和理由
5. 跨会话恢复 - Agent 重启后能快速恢复状态

原理：
- 当 Agent 被唤醒时，除了加载 LangGraph 状态，首先读取这个轻量级文件
- 它作为 Agent 的"心智锚点"，帮助 Agent 快速定位到当前任务的关键节点
"""

import os
import json
import time
import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class ProgressStatus(Enum):
    """进度状态"""
    PENDING = "pending"      # 待开始
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    BLOCKED = "blocked"      # 被阻塞
    FAILED = "failed"       # 失败


class DecisionType(Enum):
    """决策类型"""
    APPROACH = "approach"        # 方法选择
    PRIORITY = "priority"        # 优先级调整
    DIRECTION = "direction"      # 方向变更
    FALLBACK = "fallback"        # 回退策略
    CONFIRMATION = "confirmation"  # 确认决策


@dataclass
class ProgressNode:
    """进度节点 - 代表一个关键步骤"""
    node_id: str
    title: str
    description: str = ""
    status: ProgressStatus = ProgressStatus.PENDING
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    evidence: List[str] = field(default_factory=list)  # 证据/输出
    blockers: List[str] = field(default_factory=list)  # 阻塞原因


@dataclass
class DecisionLog:
    """决策日志"""
    decision_id: str
    decision_type: DecisionType
    context: str           # 决策背景
    options: List[str]      # 可选方案
    chosen: str            # 最终选择
    reason: str            # 选择理由
    timestamp: float = field(default_factory=time.time)
    reverted: bool = False   # 是否被回退


@dataclass
class TaskManifest:
    """任务清单 - Agent 的宏观目标跟踪"""
    task_id: str
    task_title: str
    overall_goal: str      # 总体目标（Agent 需要牢记）
    entry_point: str        # 入口查询/指令
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    # 进度节点
    nodes: List[ProgressNode] = field(default_factory=list)
    
    # 决策日志
    decisions: List[DecisionLog] = field(default_factory=list)
    
    # 状态
    status: ProgressStatus = ProgressStatus.IN_PROGRESS
    current_node_id: Optional[str] = None
    completed_count: int = 0
    total_count: int = 0
    
    # 元数据
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)  # 检查点历史
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（处理枚举序列化）"""
        result = asdict(self)
        # 处理枚举序列化
        result["status"] = self.status.value if isinstance(self.status, ProgressStatus) else self.status
        result["nodes"] = [
            {
                **n,
                "status": n.status.value if isinstance(n.status, ProgressStatus) else n.status
            } if isinstance(n, dict) else {
                "node_id": n.node_id,
                "title": n.title,
                "description": n.description,
                "status": n.status.value if isinstance(n.status, ProgressStatus) else n.status,
                "created_at": n.created_at,
                "completed_at": n.completed_at,
                "evidence": n.evidence,
                "blockers": n.blockers
            }
            for n in self.nodes
        ]
        result["decisions"] = [
            {
                **d,
                "decision_type": d.decision_type.value if isinstance(d.decision_type, DecisionType) else d.decision_type
            } if isinstance(d, dict) else {
                "decision_id": d.decision_id,
                "decision_type": d.decision_type.value if isinstance(d.decision_type, DecisionType) else d.decision_type,
                "context": d.context,
                "options": d.options,
                "chosen": d.chosen,
                "reason": d.reason,
                "timestamp": d.timestamp,
                "reverted": d.reverted
            }
            for d in self.decisions
        ]
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskManifest":
        # 转换枚举
        data["status"] = ProgressStatus(data.get("status", "in_progress"))
        data["nodes"] = [
            ProgressNode(**n) if isinstance(n, dict) else n 
            for n in data.get("nodes", [])
        ]
        data["decisions"] = [
            DecisionLog(
                decision_id=d["decision_id"],
                decision_type=DecisionType(d["decision_type"]),
                context=d["context"],
                options=d["options"],
                chosen=d["chosen"],
                reason=d["reason"],
                timestamp=d.get("timestamp", time.time()),
                reverted=d.get("reverted", False)
            ) if isinstance(d, dict) else d
            for d in data.get("decisions", [])
        ]
        return cls(**data)


class ProgressTracker:
    """
    显式进度跟踪器
    
    为 Agent 提供跨会话的宏观目标跟踪能力。
    """
    
    def __init__(self, workspace_dir: str = "./workspace"):
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.workspace_dir / ".agent_progress.json"
        self.current_manifest: Optional[TaskManifest] = None
        self._load_manifest()
    
    def _load_manifest(self):
        """加载当前任务清单"""
        if self.manifest_file.exists():
            try:
                with open(self.manifest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.current_manifest = TaskManifest.from_dict(data)
                logger.info(f"Loaded progress manifest: {self.current_manifest.task_title}")
            except Exception as e:
                logger.warning(f"Failed to load manifest: {e}")
                self.current_manifest = None
    
    def _save_manifest(self):
        """保存任务清单"""
        if self.current_manifest:
            self.current_manifest.updated_at = time.time()
            try:
                with open(self.manifest_file, 'w', encoding='utf-8') as f:
                    json.dump(self.current_manifest.to_dict(), f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"Failed to save manifest: {e}")
    
    def create_task(
        self,
        task_id: str,
        task_title: str,
        overall_goal: str,
        entry_point: str = "",
        agent_id: str = None,
        session_id: str = None
    ) -> TaskManifest:
        """创建新任务"""
        manifest = TaskManifest(
            task_id=task_id,
            task_title=task_title,
            overall_goal=overall_goal,
            entry_point=entry_point,
            agent_id=agent_id,
            session_id=session_id
        )
        self.current_manifest = manifest
        self._save_manifest()
        logger.info(f"Created task manifest: {task_title}")
        return manifest
    
    def add_node(
        self,
        node_id: str,
        title: str,
        description: str = ""
    ) -> ProgressNode:
        """添加进度节点"""
        if not self.current_manifest:
            raise ValueError("No active task manifest")
        
        node = ProgressNode(
            node_id=node_id,
            title=title,
            description=description
        )
        self.current_manifest.nodes.append(node)
        self.current_manifest.total_count += 1
        self._save_manifest()
        logger.info(f"Added node: {title}")
        return node
    
    def complete_node(
        self,
        node_id: str,
        evidence: List[str] = None,
        blockers: List[str] = None
    ) -> bool:
        """标记节点完成"""
        if not self.current_manifest:
            return False
        
        for node in self.current_manifest.nodes:
            if node.node_id == node_id:
                node.status = ProgressStatus.COMPLETED
                node.completed_at = time.time()
                if evidence:
                    node.evidence.extend(evidence)
                if blockers:
                    node.blockers.extend(blockers)
                
                self.current_manifest.completed_count += 1
                self.current_manifest.current_node_id = None
                self._save_manifest()
                logger.info(f"Completed node: {node.title}")
                return True
        
        return False
    
    def set_current_node(self, node_id: str):
        """设置当前节点"""
        if not self.current_manifest:
            return
        
        self.current_manifest.current_node_id = node_id
        for node in self.current_manifest.nodes:
            if node.node_id == node_id and node.status == ProgressStatus.PENDING:
                node.status = ProgressStatus.IN_PROGRESS
        self._save_manifest()
    
    def log_decision(
        self,
        decision_id: str,
        decision_type: DecisionType,
        context: str,
        options: List[str],
        chosen: str,
        reason: str
    ) -> DecisionLog:
        """记录决策"""
        if not self.current_manifest:
            raise ValueError("No active task manifest")
        
        decision = DecisionLog(
            decision_id=decision_id,
            decision_type=decision_type,
            context=context,
            options=options,
            chosen=chosen,
            reason=reason
        )
        self.current_manifest.decisions.append(decision)
        self._save_manifest()
        logger.info(f"Logged decision: {decision_type.value} - {chosen}")
        return decision
    
    def add_checkpoint(self, label: str, data: Dict[str, Any] = None):
        """添加检查点"""
        if not self.current_manifest:
            return
        
        checkpoint = {
            "label": label,
            "timestamp": time.time(),
            "completed_count": self.current_manifest.completed_count,
            "current_node": self.current_manifest.current_node_id,
            "data": data or {}
        }
        self.current_manifest.checkpoints.append(checkpoint)
        self._save_manifest()
        logger.info(f"Added checkpoint: {label}")
    
    def get_status_summary(self) -> Dict[str, Any]:
        """获取状态摘要"""
        if not self.current_manifest:
            return {"has_manifest": False}
        
        m = self.current_manifest
        pending_nodes = [n for n in m.nodes if n.status == ProgressStatus.PENDING]
        in_progress_nodes = [n for n in m.nodes if n.status == ProgressStatus.IN_PROGRESS]
        completed_nodes = [n for n in m.nodes if n.status == ProgressStatus.COMPLETED]
        
        return {
            "has_manifest": True,
            "task_id": m.task_id,
            "task_title": m.task_title,
            "overall_goal": m.overall_goal,
            "progress": f"{m.completed_count}/{m.total_count}" if m.total_count > 0 else "0/0",
            "progress_pct": (m.completed_count / m.total_count * 100) if m.total_count > 0 else 0,
            "current_node": m.current_node_id,
            "in_progress_count": len(in_progress_nodes),
            "pending_count": len(pending_nodes),
            "completed_count": len(completed_nodes),
            "decision_count": len(m.decisions),
            "checkpoint_count": len(m.checkpoints),
            "recent_decisions": [
                {"type": d.decision_type.value, "chosen": d.chosen, "reason": d.reason[:100]}
                for d in m.decisions[-3:] if not d.reverted
            ],
            "pending_nodes": [
                {"id": n.node_id, "title": n.title}
                for n in pending_nodes[:5]
            ]
        }
    
    def get_recovery_briefing(self) -> str:
        """获取恢复简报 - 帮助 Agent 快速恢复状态"""
        if not self.current_manifest:
            return "No active task manifest."
        
        m = self.current_manifest
        summary = self.get_status_summary()
        
        briefing = f"""
## 任务恢复简报

### 当前任务
- **目标**: {m.overall_goal}
- **进度**: {summary['progress']} ({summary['progress_pct']:.1f}%)

### 当前状态
"""
        if m.current_node_id:
            briefing += f"- **进行中**: {m.current_node_id}\n"
        
        pending = [n for n in m.nodes if n.status == ProgressStatus.PENDING]
        if pending:
            briefing += f"- **待完成** ({len(pending)}项):\n"
            for n in pending[:3]:
                briefing += f"  - {n.title}\n"
        
        recent = m.decisions[-2:] if m.decisions else []
        if recent:
            briefing += "\n### 最近决策\n"
            for d in recent:
                briefing += f"- **{d.decision_type.value}**: {d.chosen} (理由: {d.reason[:50]}...)\n"
        
        return briefing
    
    def finalize_task(self, status: ProgressStatus = ProgressStatus.COMPLETED):
        """完成任务"""
        if self.current_manifest:
            self.current_manifest.status = status
            self.current_manifest.updated_at = time.time()
            self._save_manifest()
            logger.info(f"Finalized task: {status.value}")
            
            # 备份清单
            backup_file = self.workspace_dir / f".agent_progress_{self.current_manifest.task_id}_{int(time.time())}.json"
            try:
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(self.current_manifest.to_dict(), f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.warning(f"Failed to backup manifest: {e}")
    
    def clear(self):
        """清除当前清单"""
        self.current_manifest = None
        if self.manifest_file.exists():
            self.manifest_file.unlink()
        logger.info("Cleared progress manifest")


# 单例
_progress_tracker: Optional[ProgressTracker] = None

def get_progress_tracker(workspace_dir: str = "./workspace") -> ProgressTracker:
    """获取进度跟踪器单例"""
    global _progress_tracker
    if _progress_tracker is None:
        _progress_tracker = ProgressTracker(workspace_dir)
    return _progress_tracker
