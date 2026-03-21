#!/usr/bin/env python3
"""
TDD Enforcer - 强制执行测试驱动开发 (TDD)

借鉴 Superpowers TDD Skill 的铁律:
"NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST"

实现 RED-GREEN-REFACTOR 循环:
- RED: 写一个失败的测试
- GREEN: 写最少量代码让测试通过
- REFACTOR: 重构代码 (在测试通过后)
"""

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# 状态文件路径
TDD_STATE_FILE = ".tdd_state.json"


@dataclass
class TestRecord:
    """测试记录"""
    test_path: str
    production_path: str
    status: str  # pending, failing, passing, refactoring
    created_at: str
    updated_at: str
    human_approved: bool = False
    approval_reason: str = ""


@dataclass
class TDDViolation:
    """TDD 违规记录"""
    production_path: str
    reason: str
    timestamp: str
    human_override: bool = False


class TDDEnforcer:
    """
    TDD 强制执行器
    
    铁律: "NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST"
    
    使用方法:
    1. 先调用 check_can_write_production(path) 检查是否可以写生产代码
    2. 如果返回 False，需要先写测试
    3. 写完测试后调用 register_test() 注册
    4. 测试通过后调用 mark_test_passing()
    """
    
    def __init__(self, state_file: str = TDD_STATE_FILE):
        self.state_file = state_file
        self._state: Dict = self._load_state()
        self._violations: List[TDDViolation] = []
        
        logger.info(f"TDDEnforcer 初始化，状态文件: {state_file}")
    
    def _load_state(self) -> Dict:
        """加载状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"加载TDD状态失败: {e}")
                return self._create_default_state()
        return self._create_default_state()
    
    def _create_default_state(self) -> Dict:
        """创建默认状态"""
        return {
            "tests": {},
            "violations": [],
            "config": {
                "allow_override_with_approval": True,
                "max_violations": 100
            }
        }
    
    def _save_state(self):
        """保存状态"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self._state, f, indent=2)
        except IOError as e:
            logger.error(f"保存TDD状态失败: {e}")
    
    def _get_production_path(self, test_path: str) -> str:
        """从测试路径推断生产代码路径"""
        # test_foo.py -> foo.py 或 tests/test_foo.py -> src/foo.py
        test_name = Path(test_path).stem
        
        if test_name.startswith("test_"):
            prod_name = test_name[5:]  # 移除 test_ 前缀
        else:
            prod_name = test_name
        
        # 尝试多种映射
        candidates = [
            prod_name + ".py",
            f"src/{prod_name}.py",
            prod_name.replace("test_", "") + ".py",
        ]
        
        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
        
        return prod_name + ".py"
    
    def _get_test_path(self, production_path: str) -> str:
        """从生产代码路径推断测试路径"""
        prod_name = Path(production_path).stem
        
        # 尝试多种映射
        candidates = [
            f"test_{prod_name}.py",
            f"tests/test_{prod_name}.py",
            f"tests/unit/test_{prod_name}.py",
        ]
        
        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
        
        return f"test_{prod_name}.py"
    
    def check_can_write_production(
        self, 
        path: str, 
        human_approved: bool = False,
        approval_reason: str = ""
    ) -> Tuple[bool, str]:
        """
        检查是否可以写生产代码
        
        规则:
        1. 如果已有测试且状态为 failing -> 可以写
        2. 如果已有测试且状态为 passing -> 不能写，需要先修改测试
        3. 如果没有测试 -> 不能写（除非 human_approved=True）
        
        Args:
            path: 生产代码路径
            human_approved: 人类是否批准绕过（紧急修复等）
            approval_reason: 批准原因
            
        Returns:
            (can_write, reason)
        """
        tests = self._state.get("tests", {})
        
        # 检查是否有对应的测试
        test_path = self._get_test_path(path)
        
        if test_path in tests:
            test_record = tests[test_path]
            status = test_record.get("status", "pending")
            
            if status == "failing":
                logger.info(f"允许写生产代码 {path}: 有失败的测试")
                return True, "允许: 存在失败的测试"
            
            elif status == "passing":
                logger.warning(f"禁止写生产代码 {path}: 测试已通过，需要先修改测试")
                return False, "禁止: 测试已通过，需要先修改测试使其失败"
            
            elif status == "refactoring":
                logger.info(f"允许写生产代码 {path}: 处于重构阶段")
                return True, "允许: 处于重构阶段"
            
            else:  # pending
                # 检查测试是否真的失败
                if self._is_test_failing(test_path):
                    test_record["status"] = "failing"
                    self._save_state()
                    logger.info(f"测试 {test_path} 现在是失败的")
                    return True, "允许: 测试已确认失败"
                
                logger.warning(f"禁止写生产代码 {path}: 没有失败的测试")
                return False, "禁止: 需要先写一个失败的测试 (RED 阶段)"
        
        # 没有测试
        if human_approved:
            # 记录批准
            violation = TDDViolation(
                production_path=path,
                reason="人类批准绕过TDD",
                timestamp=datetime.now().isoformat(),
                human_override=True
            )
            self._violations.append(violation)
            self._state["violations"].append(asdict(violation))
            self._save_state()
            
            logger.info(f"人类批准绕过TDD: {path} - {approval_reason}")
            return True, f"允许 (人类批准): {approval_reason}"
        
        logger.warning(f"禁止写生产代码 {path}: 没有对应的测试")
        return False, "禁止: 需要先写一个失败的测试"
    
    def _is_test_failing(self, test_path: str) -> bool:
        """检查测试是否失败（通过运行测试）"""
        try:
            import subprocess
            result = subprocess.run(
                ["python", "-m", "pytest", test_path, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=30
            )
            # pytest 返回码: 0=全部通过, 1=有失败, 2=测试被中断
            return result.returncode == 1
        except Exception as e:
            logger.warning(f"无法运行测试 {test_path}: {e}")
            return False
    
    def register_test(
        self, 
        test_path: str, 
        test_code: str = "",
        production_path: str = ""
    ) -> bool:
        """
        注册新测试
        
        Args:
            test_path: 测试文件路径
            test_code: 测试代码（如果需要创建文件）
            production_path: 对应的生产代码路径
            
        Returns:
            是否成功
        """
        if not production_path:
            production_path = self._get_production_path(test_path)
        
        tests = self._state.setdefault("tests", {})
        
        now = datetime.now().isoformat()
        tests[test_path] = {
            "test_path": test_path,
            "production_path": production_path,
            "status": "pending",
            "created_at": now,
            "updated_at": now,
            "human_approved": False,
            "approval_reason": ""
        }
        
        self._save_state()
        logger.info(f"注册测试: {test_path} -> {production_path}")
        
        return True
    
    def mark_test_failing(self, test_path: str) -> bool:
        """标记测试为失败状态 (RED 阶段完成)"""
        tests = self._state.get("tests", {})
        
        if test_path in tests:
            tests[test_path]["status"] = "failing"
            tests[test_path]["updated_at"] = datetime.now().isoformat()
            self._save_state()
            logger.info(f"测试进入 RED 阶段: {test_path}")
            return True
        
        logger.warning(f"测试未注册: {test_path}")
        return False
    
    def mark_test_passing(self, test_path: str) -> bool:
        """标记测试为通过状态 (GREEN 阶段完成)"""
        tests = self._state.get("tests", {})
        
        if test_path in tests:
            tests[test_path]["status"] = "passing"
            tests[test_path]["updated_at"] = datetime.now().isoformat()
            self._save_state()
            logger.info(f"测试进入 GREEN 阶段: {test_path}")
            return True
        
        logger.warning(f"测试未注册: {test_path}")
        return False
    
    def start_refactoring(self, test_path: str) -> bool:
        """开始重构阶段 (REFACTOR)"""
        tests = self._state.get("tests", {})
        
        if test_path in tests:
            tests[test_path]["status"] = "refactoring"
            tests[test_path]["updated_at"] = datetime.now().isoformat()
            self._save_state()
            logger.info(f"测试进入 REFACTOR 阶段: {test_path}")
            return True
        
        logger.warning(f"测试未注册: {test_path}")
        return False
    
    def get_violations(self) -> List[Dict]:
        """获取 TDD 违规记录"""
        return self._state.get("violations", [])
    
    def is_in_red_phase(self, test_path: str) -> bool:
        """检查测试是否处于 RED 阶段（失败状态）"""
        tests = self._state.get("tests", {})
        
        if test_path in tests:
            return tests[test_path].get("status") == "failing"
        
        return False
    
    def get_test_status(self, test_path: str) -> Optional[str]:
        """获取测试状态"""
        tests = self._state.get("tests", {})
        
        if test_path in tests:
            return tests[test_path].get("status")
        
        return None
    
    def list_tests(self) -> List[Dict]:
        """列出所有注册的测试"""
        return list(self._state.get("tests", {}).values())
    
    def get_red_green_refactor_status(self) -> Dict[str, int]:
        """获取 RED-GREEN-REFACTOR 统计"""
        tests = self._state.get("tests", {})
        
        stats = {
            "red": 0,      # 有失败的测试
            "green": 0,    # 测试通过的
            "refactoring": 0,
            "pending": 0,
            "total": len(tests)
        }
        
        for test in tests.values():
            status = test.get("status", "pending")
            if status == "failing":
                stats["red"] += 1
            elif status == "passing":
                stats["green"] += 1
            elif status == "refactoring":
                stats["refactoring"] += 1
            else:
                stats["pending"] += 1
        
        return stats
    
    def reset(self):
        """重置 TDD 状态"""
        self._state = self._create_default_state()
        self._violations = []
        self._save_state()
        logger.info("TDD 状态已重置")


# 全局单例
_enforcer: Optional[TDDEnforcer] = None


def get_enforcer() -> TDDEnforcer:
    """获取全局 TDD Enforcer 实例"""
    global _enforcer
    if _enforcer is None:
        _enforcer = TDDEnforcer()
    return _enforcer
