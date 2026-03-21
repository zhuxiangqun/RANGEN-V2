"""
任务契约系统 (Task Contract System)

基于文章《如何成为世界一流的智能体工程师》的核心原则：
- 明确的任务完成标准
- 测试驱动验证
- 截图/行为验证
- Stop-hook: 阻止任务终止直到契约完成

设计原则：
- 少即是多：简洁的契约格式
- 上下文精确：只加载需要的验证规则
- 迭代优化：支持规则动态更新
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import os

from src.services.logging_service import get_logger

logger = get_logger(__name__)


class ContractStatus(Enum):
    """契约状态"""
    PENDING = "pending"           # 待执行
    IN_PROGRESS = "in_progress"   # 执行中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"            # 失败
    BLOCKED = "blocked"          # 被阻塞


class VerificationType(Enum):
    """验证类型"""
    TEST = "test"                # 测试验证
    SCREENSHOT = "screenshot"    # 截图验证
    MANUAL = "manual"            # 人工验证
    ASSERTION = "assertion"     # 断言验证
    FILE_EXISTS = "file_exists"  # 文件存在验证


@dataclass
class VerificationItem:
    """单个验证项"""
    id: str
    type: VerificationType
    description: str
    criteria: str                # 验证标准描述
    weight: float = 1.0           # 权重
    required: bool = True        # 是否必须
    passed: Optional[bool] = None
    evidence: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "description": self.description,
            "criteria": self.criteria,
            "weight": self.weight,
            "required": self.required,
            "passed": self.passed,
            "evidence": self.evidence
        }


@dataclass
class TaskContract:
    """
    任务契约定义
    
    使用方式:
        contract = TaskContract(
            task_id="feature_auth",
            description="实现JWT认证系统",
            verifications=[
                VerificationItem(
                    id="test_auth",
                    type=VerificationType.TEST,
                    description="认证测试通过",
                    criteria="tests/test_auth.py 全部通过"
                ),
                VerificationItem(
                    id="doc_exists",
                    type=VerificationType.FILE_EXISTS,
                    description="文档存在",
                    criteria="docs/auth.md 存在"
                )
            ]
        )
    """
    task_id: str
    description: str
    created_at: datetime = field(default_factory=datetime.now)
    status: ContractStatus = ContractStatus.PENDING
    verifications: List[VerificationItem] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_verification(self, verification: VerificationItem):
        """添加验证项"""
        self.verifications.append(verification)
    
    def get_pending_verifications(self) -> List[VerificationItem]:
        """获取待验证项"""
        return [v for v in self.verifications if v.passed is None]
    
    def get_required_verifications(self) -> List[VerificationItem]:
        """获取必需的验证项"""
        return [v for v in self.verifications if v.required and v.passed is not True]
    
    def is_completed(self) -> bool:
        """检查是否所有必需验证项都通过"""
        return all(
            v.passed for v in self.verifications 
            if v.required
        ) and len(self.get_required_verifications()) == 0
    
    def get_score(self) -> float:
        """计算完成度分数"""
        if not self.verifications:
            return 0.0
        
        total_weight = sum(v.weight for v in self.verifications)
        passed_weight = sum(
            v.weight for v in self.verifications 
            if v.passed is True
        )
        
        return passed_weight / total_weight if total_weight > 0 else 0.0
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "score": self.get_score(),
            "is_completed": self.is_completed(),
            "verifications": [v.to_dict() for v in self.verifications],
            "context": self.context,
            "metadata": self.metadata
        }
    
    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        md = f"""# 任务契约: {self.task_id}

**描述**: {self.description}
**状态**: {self.status.value}
**完成度**: {self.get_score():.1%}
**创建时间**: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}

## 验证项

| ID | 类型 | 描述 | 标准 | 状态 |
|----|------|------|------|------|
"""
        for v in self.verifications:
            status_icon = "✅" if v.passed is True else "❌" if v.passed is False else "⏳"
            md += f"| {v.id} | {v.type.value} | {v.description} | {v.criteria} | {status_icon} |\n"
        
        return md


class ContractRegistry:
    """契约注册表 - 管理所有任务契约"""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or ".rangen/contracts"
        self._contracts: Dict[str, TaskContract] = {}
        self._load_from_disk()
    
    def _load_from_disk(self):
        """从磁盘加载"""
        if not os.path.exists(self.storage_path):
            return
        
        try:
            for filename in os.listdir(self.storage_path):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.storage_path, filename)
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        contract = self._dict_to_contract(data)
                        self._contracts[contract.task_id] = contract
        except Exception as e:
            logger.warning(f"Failed to load contracts: {e}")
    
    def _dict_to_contract(self, data: Dict) -> TaskContract:
        """字典转契约"""
        verifications = [
            VerificationItem(
                id=v["id"],
                type=VerificationType(v["type"]),
                description=v["description"],
                criteria=v["criteria"],
                weight=v.get("weight", 1.0),
                required=v.get("required", True),
                passed=v.get("passed"),
                evidence=v.get("evidence")
            )
            for v in data.get("verifications", [])
        ]
        
        return TaskContract(
            task_id=data["task_id"],
            description=data["description"],
            created_at=datetime.fromisoformat(data["created_at"]),
            status=ContractStatus(data["status"]),
            verifications=verifications,
            context=data.get("context", {}),
            metadata=data.get("metadata", {})
        )
    
    def save_to_disk(self, contract: TaskContract):
        """保存到磁盘"""
        os.makedirs(self.storage_path, exist_ok=True)
        filepath = os.path.join(self.storage_path, f"{contract.task_id}.json")
        
        with open(filepath, 'w') as f:
            json.dump(contract.to_dict(), f, indent=2)
    
    def create(self, task_id: str, description: str, 
               verifications: Optional[List[VerificationItem]] = None,
               context: Optional[Dict] = None) -> TaskContract:
        """创建新契约"""
        contract = TaskContract(
            task_id=task_id,
            description=description,
            verifications=verifications or [],
            context=context or {}
        )
        self._contracts[task_id] = contract
        self.save_to_disk(contract)
        logger.info(f"Created contract: {task_id}")
        return contract
    
    def get(self, task_id: str) -> Optional[TaskContract]:
        """获取契约"""
        return self._contracts.get(task_id)
    
    def list_all(self) -> List[TaskContract]:
        """列出所有契约"""
        return list(self._contracts.values())
    
    def list_pending(self) -> List[TaskContract]:
        """列出待完成的契约"""
        return [c for c in self._contracts.values() if not c.is_completed()]
    
    def update_verification(self, task_id: str, verification_id: str, 
                           passed: bool, evidence: Optional[str] = None) -> bool:
        """更新验证项"""
        contract = self._contracts.get(task_id)
        if not contract:
            return False
        
        for v in contract.verifications:
            if v.id == verification_id:
                v.passed = passed
                v.evidence = evidence
                contract.status = ContractStatus.COMPLETED if contract.is_completed() else ContractStatus.IN_PROGRESS
                self.save_to_disk(contract)
                return True
        
        return False
    
    def can_terminate(self, task_id: str) -> bool:
        """
        检查任务是否可以终止 (Stop-hook 核心逻辑)
        
        这就是文章说的"阻止 AI 智能体终止会话，直到契约完成"
        """
        contract = self._contracts.get(task_id)
        if not contract:
            return True  # 没有契约，允许终止
        
        return contract.is_completed()


# 全局单例
_global_registry: Optional[ContractRegistry] = None

def get_contract_registry() -> ContractRegistry:
    """获取全局契约注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ContractRegistry()
    return _global_registry


# ============ 便捷函数 ============

def create_contract(task_id: str, description: str, 
                   verifications: Optional[List[Dict]] = None) -> TaskContract:
    """
    快速创建契约的便捷函数
    
    使用示例:
        contract = create_contract(
            "implement_auth",
            "实现JWT认证",
            [
                {"id": "test", "type": "test", "description": "测试通过", "criteria": "pytest passes"},
                {"id": "doc", "type": "file_exists", "description": "文档存在", "criteria": "docs/auth.md"}
            ]
        )
    """
    registry = get_contract_registry()
    
    items = []
    if verifications:
        for v in verifications:
            items.append(VerificationItem(
                id=v["id"],
                type=VerificationType(v["type"]),
                description=v["description"],
                criteria=v["criteria"],
                weight=v.get("weight", 1.0),
                required=v.get("required", True)
            ))
    
    return registry.create(task_id, description, items)


def check_contract_status(task_id: str) -> Dict:
    """检查契约状态"""
    registry = get_contract_registry()
    contract = registry.get(task_id)
    
    if not contract:
        return {"exists": False}
    
    return {
        "exists": True,
        "task_id": task_id,
        "description": contract.description,
        "status": contract.status.value,
        "score": contract.get_score(),
        "is_completed": contract.is_completed(),
        "can_terminate": contract.is_completed(),
        "pending_count": len(contract.get_pending_verifications()),
        "required_failed": len(contract.get_required_verifications())
    }
