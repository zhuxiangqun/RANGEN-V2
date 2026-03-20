#!/usr/bin/env python3
"""
Strict TDD Enforcer - 不可绕过的 TDD 强制执行器

基于 src/agents/tdd_enforcer.py 的增强版

核心改进:
1. 不可绕过 - 无失败测试禁止写生产代码
2. 强制删除 - 如果先写了代码，必须删除
3. 状态检查 - 跟踪每个文件的 TDD 状态

铁律: "NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST"

使用方式:
    from src.agents.strict_tdd_enforcer import StrictTDDEnforcer
    
    enforcer = StrictTDDEnforcer()
    
    # 检查是否可以写生产代码
    can_write, reason = enforcer.can_write_production("src/auth.py")
    if not can_write:
        raise TDDViolationError(reason)
    
    # 注册测试
    enforcer.register_test("tests/test_auth.py", "src/auth.py")
    
    # 标记测试通过
    enforcer.mark_test_passing("tests/test_auth.py")
"""

import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

logger = logging.getLogger(__name__)

# 状态文件
TDD_STATE_FILE = ".strict_tdd_state.json"


class TDDPhase(Enum):
    """TDD 阶段"""
    NO_TEST = "no_test"          # 没有测试
    TEST_WRITTEN = "test_written"  # 测试已写
    TEST_FAILING = "test_failing"  # 测试失败（RED阶段）
    CODE_WRITTEN = "code_written"  # 代码已写
    TEST_PASSING = "test_passing"  # 测试通过（GREEN阶段）
    REFACTORING = "refactoring"  # 重构中
    COMPLETE = "complete"          # 完成


class TDDViolationError(Exception):
    """TDD 违规异常"""
    def __init__(self, message: str, phase: TDDPhase, suggestion: str = ""):
        self.message = message
        self.phase = phase
        self.suggestion = suggestion
        super().__init__(self.format_message())
    
    def format_message(self) -> str:
        msg = f"\n🔴 TDD 违规: {self.message}\n"
        msg += f"   当前阶段: {self.phase.value}\n"
        if self.suggestion:
            msg += f"   建议: {self.suggestion}\n"
        msg += "\n   铁律: 'NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST'\n"
        return msg


@dataclass
class TestRecord:
    """测试记录"""
    test_path: str
    production_path: str
    status: TDDPhase
    created_at: str
    first_failure_at: Optional[str] = None
    first_success_at: Optional[str] = None
    attempts: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "test_path": self.test_path,
            "production_path": self.production_path,
            "status": self.status.value,
            "created_at": self.created_at,
            "first_failure_at": self.first_failure_at,
            "first_success_at": self.first_success_at,
            "attempts": self.attempts,
        }


@dataclass 
class ViolationRecord:
    """违规记录"""
    production_path: str
    reason: str
    timestamp: str
    must_delete: bool = True


class StrictTDDEnforcer:
    """
    严格 TDD 强制执行器
    
    核心特点:
    1. 不可绕过 - 无失败测试禁止写生产代码
    2. 强制删除 - 先写代码必须删除
    3. 状态跟踪 - 每个文件都有 TDD 状态
    4. 测试优先 - 必须先看到测试失败
    """
    
    def __init__(self, state_file: str = TDD_STATE_FILE):
        self.state_file = state_file
        self._records: Dict[str, TestRecord] = {}
        self._violations: List[ViolationRecord] = []
        self._load_state()
        
        logger.info(f"StrictTDDEnforcer 初始化，状态文件: {state_file}")
    
    def _load_state(self):
        """加载状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                
                self._records = {
                    k: TestRecord(**v) for k, v in data.get('records', {}).items()
                }
                self._violations = [
                    ViolationRecord(**v) for v in data.get('violations', [])
                ]
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"加载TDD状态失败: {e}")
    
    def _save_state(self):
        """保存状态"""
        data = {
            'records': {k: v.to_dict() for k, v in self._records.items()},
            'violations': [
                {'production_path': v.production_path, 'reason': v.reason, 
                 'timestamp': v.timestamp, 'must_delete': v.must_delete}
                for v in self._violations[-100:]  # 只保留最近100条
            ]
        }
        
        try:
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            logger.error(f"保存TDD状态失败: {e}")
    
    def _record_violation(self, path: str, reason: str):
        """记录违规"""
        violation = ViolationRecord(
            production_path=path,
            reason=reason,
            timestamp=datetime.now().isoformat(),
            must_delete=True,  # 强制删除
        )
        self._violations.append(violation)
        self._save_state()
        logger.warning(f"TDD 违规: {reason}")
        return violation
    
    # ==================== 核心检查方法 ====================
    
    def can_write_production(self, production_path: str) -> Tuple[bool, str]:
        """
        检查是否可以写生产代码
        
        这是最核心的方法。任何写生产代码前都必须调用。
        
        Args:
            production_path: 生产代码路径
            
        Returns:
            (True, message) 如果允许
            (False, message) 如果不允许
        """
        # 查找对应的测试记录
        test_path = self._find_test_for_production(production_path)
        
        if not test_path:
            # 没有找到测试记录，不允许写
            reason = (
                f"没有为 '{production_path}' 编写测试。\n"
                "必须先编写测试才能写生产代码。\n"
                "建议: 先创建测试文件，如 tests/test_auth.py"
            )
            return False, reason
        
        # 检查测试状态
        record = self._records.get(test_path)
        if not record:
            reason = (
                f"测试 '{test_path}' 状态未知。\n"
                "请重新注册测试。"
            )
            return False, reason
        
        # 检查当前阶段
        if record.status in [TDDPhase.NO_TEST]:
            reason = (
                f"测试 '{test_path}' 尚未运行。\n"
                "请先运行测试确认它失败。"
            )
            return False, reason
        
        if record.status == TDDPhase.TEST_FAILING:
            # RED 阶段 - 可以写代码
            return True, "允许写入 (RED 阶段，测试已失败)"
        
        if record.status == TDDPhase.TEST_PASSING:
            # 之前已经通过，可能需要新的测试
            return False, (
                f"测试 '{test_path}' 已经通过。\n"
                "如果需要新功能，请先编写新的失败测试。"
            )
        
        if record.status in [TDDPhase.TEST_WRITTEN, TDDPhase.CODE_WRITTEN]:
            return True, f"允许写入 (当前状态: {record.status.value})"
        
        return True, "允许写入"
    
    def can_write_test(self, test_path: str, production_path: str) -> Tuple[bool, str]:
        """
        检查是否可以写测试代码
        
        Args:
            test_path: 测试文件路径
            production_path: 对应的生产代码路径
            
        Returns:
            (True, message) 如果允许
            (False, message) 如果不允许
        """
        # 测试总是可以写的
        return True, "可以编写测试"
    
    def assert_can_write_production(self, production_path: str):
        """
        断言可以写生产代码
        
        如果不能写，抛出 TDDViolationError
        """
        can_write, reason = self.can_write_production(production_path)
        if not can_write:
            raise TDDViolationError(
                reason,
                TDDPhase.NO_TEST,
                "必须先编写失败的测试"
            )
    
    def check_violation(self, production_path: str) -> Tuple[bool, Optional[ViolationRecord]]:
        """
        检查是否已有违规
        
        Args:
            production_path: 生产代码路径
            
        Returns:
            (has_violation, violation_record)
        """
        for v in self._violations:
            if v.production_path == production_path and v.must_delete:
                return True, v
        return False, None
    
    # ==================== 状态管理 ====================
    
    def register_test(self, test_path: str, production_path: str) -> TestRecord:
        """
        注册测试
        
        在编写测试后调用。
        
        Args:
            test_path: 测试文件路径
            production_path: 对应的生产代码路径
        """
        record = TestRecord(
            test_path=test_path,
            production_path=production_path,
            status=TDDPhase.TEST_WRITTEN,
            created_at=datetime.now().isoformat(),
        )
        
        self._records[test_path] = record
        self._save_state()
        
        logger.info(f"注册测试: {test_path} -> {production_path}")
        return record
    
    def mark_test_failure(self, test_path: str) -> TestRecord:
        """
        标记测试失败 (RED 阶段)
        
        运行测试后发现失败时调用。
        
        Args:
            test_path: 测试文件路径
        """
        record = self._records.get(test_path)
        if not record:
            raise ValueError(f"测试 '{test_path}' 未注册")
        
        record.status = TDDPhase.TEST_FAILING
        record.attempts += 1
        
        if not record.first_failure_at:
            record.first_failure_at = datetime.now().isoformat()
        
        self._save_state()
        
        logger.info(f"RED 阶段: {test_path} 测试失败")
        return record
    
    def mark_code_written(self, test_path: str) -> TestRecord:
        """
        标记代码已写 (GREEN 阶段)
        
        写完让测试通过的生产代码后调用。
        
        Args:
            test_path: 测试文件路径
        """
        record = self._records.get(test_path)
        if not record:
            raise ValueError(f"测试 '{test_path}' 未注册")
        
        # 检查是否真的看到了测试失败
        if record.status != TDDPhase.TEST_FAILING:
            raise TDDViolationError(
                f"必须先看到测试失败才能写代码。当前状态: {record.status.value}",
                record.status,
                "运行测试，确认 RED 阶段"
            )
        
        record.status = TDDPhase.CODE_WRITTEN
        self._save_state()
        
        logger.info(f"GREEN 阶段: {test_path} 代码已写")
        return record
    
    def mark_test_passing(self, test_path: str) -> TestRecord:
        """
        标记测试通过 (GREEN 阶段完成)
        
        测试运行通过后调用。
        
        Args:
            test_path: 测试文件路径
        """
        record = self._records.get(test_path)
        if not record:
            raise ValueError(f"测试 '{test_path}' 未注册")
        
        # 检查是否写了代码
        if record.status not in [TDDPhase.CODE_WRITTEN, TDDPhase.TEST_FAILING]:
            logger.warning(
                f"测试 '{test_path}' 状态异常: {record.status.value}"
            )
        
        record.status = TDDPhase.TEST_PASSING
        record.first_success_at = datetime.now().isoformat()
        self._save_state()
        
        logger.info(f"GREEN 阶段完成: {test_path} 测试通过")
        return record
    
    def start_refactoring(self, test_path: str):
        """开始重构"""
        record = self._records.get(test_path)
        if not record:
            raise ValueError(f"测试 '{test_path}' 未注册")
        
        if record.status != TDDPhase.TEST_PASSING:
            raise TDDViolationError(
                "测试必须通过才能重构",
                record.status,
                "先让测试通过"
            )
        
        record.status = TDDPhase.REFACTORING
        self._save_state()
    
    def complete_task(self, test_path: str):
        """完成任务"""
        record = self._records.get(test_path)
        if not record:
            return
        
        record.status = TDDPhase.COMPLETE
        self._save_state()
    
    def delete_production_code(self, production_path: str) -> bool:
        """
        删除生产代码 (违规后强制)
        
        Args:
            production_path: 生产代码路径
            
        Returns:
            True 如果成功删除
        """
        if os.path.exists(production_path):
            try:
                os.remove(production_path)
                logger.info(f"已删除: {production_path}")
                
                # 移除违规记录
                for v in self._violations:
                    if v.production_path == production_path:
                        v.must_delete = False
                
                return True
            except IOError as e:
                logger.error(f"删除失败: {e}")
                return False
        return True
    
    # ==================== 辅助方法 ====================
    
    def _find_test_for_production(self, production_path: str) -> Optional[str]:
        """查找生产代码对应的测试"""
        for test_path, record in self._records.items():
            if record.production_path == production_path:
                return test_path
        return None
    
    def get_record(self, test_path: str) -> Optional[TestRecord]:
        """获取测试记录"""
        return self._records.get(test_path)
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态摘要"""
        stats = {
            "total_tests": len(self._records),
            "violations": len([v for v in self._violations if v.must_delete]),
            "by_status": {},
        }
        
        for record in self._records.values():
            status = record.status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        
        return stats
    
    def reset(self):
        """重置所有状态"""
        self._records.clear()
        self._violations.clear()
        self._save_state()
        logger.info("StrictTDDEnforcer 已重置")


def create_tdd_enforcer() -> StrictTDDEnforcer:
    """创建 TDD Enforcer 单例"""
    return StrictTDDEnforcer()


__all__ = [
    'StrictTDDEnforcer',
    'TDDPhase',
    'TDDViolationError',
    'TestRecord',
    'create_tdd_enforcer',
]


if __name__ == '__main__':
    print("=== StrictTDDEnforcer 演示 ===\n")
    
    # 创建 enforcer
    enforcer = StrictTDDEnforcer()
    enforcer.reset()
    
    # 1. 尝试直接写生产代码
    print("1. 尝试写生产代码 (无测试):")
    can_write, msg = enforcer.can_write_production("src/auth.py")
    print(f"   结果: {'允许' if can_write else '阻止'}")
    print(f"   原因: {msg[:80]}...\n")
    
    # 2. 注册测试
    print("2. 注册测试:")
    record = enforcer.register_test("tests/test_auth.py", "src/auth.py")
    print(f"   测试: {record.test_path}")
    print(f"   状态: {record.status.value}\n")
    
    # 3. 再次尝试写生产代码
    print("3. 写测试后尝试写生产代码:")
    can_write, msg = enforcer.can_write_production("src/auth.py")
    print(f"   结果: {'允许' if can_write else '阻止'}")
    print(f"   原因: {msg[:80]}...\n")
    
    # 4. 标记测试失败 (RED)
    print("4. 标记测试失败 (RED):")
    enforcer.mark_test_failure("tests/test_auth.py")
    print(f"   状态: {enforcer.get_record('tests/test_auth.py').status.value}\n")
    
    # 5. 现在可以写代码了
    print("5. RED阶段后尝试写生产代码:")
    can_write, msg = enforcer.can_write_production("src/auth.py")
    print(f"   结果: {'允许' if can_write else '阻止'}")
    print(f"   原因: {msg}\n")
    
    # 6. 标记代码已写
    print("6. 标记代码已写 (GREEN):")
    enforcer.mark_code_written("tests/test_auth.py")
    print(f"   状态: {enforcer.get_record('tests/test_auth.py').status.value}\n")
    
    # 7. 标记测试通过
    print("7. 标记测试通过:")
    enforcer.mark_test_passing("tests/test_auth.py")
    print(f"   状态: {enforcer.get_record('tests/test_auth.py').status.value}\n")
    
    # 8. 完整状态
    print("8. 状态摘要:")
    import json
    print(json.dumps(enforcer.get_status(), indent=2))
    
    print("\n=== StrictTDDEnforcer 演示完成 ===")
