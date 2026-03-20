#!/usr/bin/env python3
"""
HARD-GATE 机制 - 强制设计先行

借鉴 Superpowers 的 HARD-GATE 机制:

<HARD-GATE>
Do NOT invoke any implementation skill... 
until you have presented a design and the user has approved it.
</HARD-GATE>

核心铁律: 设计未批准，禁止写任何生产代码。

使用方式:
    from src.agents.hard_gate import HARD_GATE, HardGateError
    
    # 在任何写代码之前检查
    HARD_GATE.check_design_approved()  # 抛出异常如果没有批准
    
    # 设计讨论开始时
    HARD_GATE.start_design_phase("用户管理系统")
    
    # 设计批准后
    HARD_GATE.approve_design()
    
    # 可以开始实现了
    HARD_GATE.check_implementation_allowed()  # 通过后才能写代码
"""

import json
import logging
import os
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

# 状态文件路径
HARD_GATE_STATE_FILE = ".hard_gate_state.json"


class GatePhase(Enum):
    """门控阶段"""
    IDLE = "idle"                          # 空闲，未开始
    BRAINSTORMING = "brainstorming"        # 需求讨论中
    DESIGN_REVIEW = "design_review"        # 设计审查中
    DESIGN_APPROVED = "design_approved"    # 设计已批准
    IMPLEMENTING = "implementing"           # 实现中
    COMPLETED = "completed"                 # 完成


class HardGateError(Exception):
    """HARD-GATE 违规异常"""
    def __init__(self, message: str, phase: GatePhase, suggestion: str = ""):
        self.message = message
        self.phase = phase
        self.suggestion = suggestion
        super().__init__(self.format_message())
    
    def format_message(self) -> str:
        msg = f"\n🔒 HARD-GATE 阻止: {self.message}\n"
        msg += f"   当前阶段: {self.phase.value}\n"
        if self.suggestion:
            msg += f"   建议: {self.suggestion}\n"
        msg += "\n   必须完成设计阶段才能继续。\n"
        return msg


@dataclass
class DesignSpec:
    """设计规范文档"""
    title: str
    description: str
    components: List[str] = field(default_factory=list)
    file_changes: List[str] = field(default_factory=list)  # 涉及的文件
    approved: bool = False
    approved_by: str = ""
    approved_at: str = ""
    spec_file_path: str = ""
    questions: List[Dict[str, Any]] = field(default_factory=list)  # 已回答的问题
    approaches: List[Dict[str, Any]] = field(default_factory=list)  # 考虑的方案
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class HardGateState:
    """HARD-GATE 状态"""
    phase: GatePhase = GatePhase.IDLE
    current_design: Optional[DesignSpec] = None
    design_history: List[Dict] = field(default_factory=list)
    violations: List[Dict] = field(default_factory=list)
    config: Dict = field(default_factory=lambda: {
        "allow_human_override": True,
        "require_design_document": True,
        "strict_mode": False,  # True时不允许任何绕过
    })
    
    def to_dict(self) -> Dict:
        result = {
            "phase": self.phase.value,
            "current_design": self.current_design.to_dict() if self.current_design else None,
            "design_history": self.design_history,
            "violations": self.violations,
            "config": self.config,
        }
        return result


class HARD_GATE:
    """
    HARD-GATE 强制执行器
    
    核心理念: "设计未签字，禁止写代码"
    
    使用流程:
    
    1. 开始设计阶段:
       HARD_GATE.start_design_phase("用户认证功能")
       
    2. 设计讨论中 (brainstorming):
       - 追问需求
       - 记录问题
       - 提出方案
       
    3. 呈现设计 (design_review):
       HARD_GATE.present_design(spec)
       
    4. 获得批准 (design_approved):
       HARD_GATE.approve_design("user")
       
    5. 检查是否可以写代码:
       HARD_GATE.check_can_write("src/auth.py")
       
    6. 开始实现:
       HARD_GATE.enter_implementation_phase()
    """
    
    _instance: Optional['HARD_GATE'] = None
    
    def __new__(cls, state_file: str = HARD_GATE_STATE_FILE):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, state_file: str = HARD_GATE_STATE_FILE):
        if self._initialized:
            return
        self._initialized = True
        
        self.state_file = state_file
        self._state: HardGateState = self._load_state()
        
        logger.info(f"HARD-GATE 初始化，状态文件: {state_file}")
        logger.info(f"当前阶段: {self._state.phase.value}")
    
    def _load_state(self) -> HardGateState:
        """加载状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                
                state = HardGateState()
                state.phase = GatePhase(data.get('phase', 'idle'))
                
                if data.get('current_design'):
                    cd = data['current_design']
                    state.current_design = DesignSpec(
                        title=cd.get('title', ''),
                        description=cd.get('description', ''),
                        components=cd.get('components', []),
                        file_changes=cd.get('file_changes', []),
                        approved=cd.get('approved', False),
                        approved_by=cd.get('approved_by', ''),
                        approved_at=cd.get('approved_at', ''),
                        spec_file_path=cd.get('spec_file_path', ''),
                    )
                
                state.design_history = data.get('design_history', [])
                state.violations = data.get('violations', [])
                state.config = data.get('config', {})
                
                return state
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"加载HARD-GATE状态失败: {e}")
        
        return HardGateState()
    
    def _save_state(self):
        """保存状态"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self._state.to_dict(), f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error(f"保存HARD-GATE状态失败: {e}")
    
    def _record_violation(self, action: str, message: str):
        """记录违规"""
        violation = {
            "action": action,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "phase": self._state.phase.value,
        }
        self._state.violations.append(violation)
        
        # 只保留最近100条违规记录
        if len(self._state.violations) > 100:
            self._state.violations = self._state.violations[-100:]
        
        self._save_state()
        logger.warning(f"HARD-GATE 违规: {message}")
    
    # ==================== 阶段管理 ====================
    
    def start_design_phase(self, title: str, description: str = "") -> DesignSpec:
        """
        开始设计阶段
        
        Args:
            title: 设计标题
            description: 简要描述
            
        Returns:
            DesignSpec 对象
            
        Raises:
            HardGateError: 如果已经在设计或实现阶段
        """
        if self._state.phase in [GatePhase.BRAINSTORMING, GatePhase.DESIGN_REVIEW]:
            raise HardGateError(
                f"设计阶段 '{self._state.current_design.title}' 尚未完成",
                self._state.phase,
                "先完成当前设计或调用 reset() 重置"
            )
        
        if self._state.phase == GatePhase.IMPLEMENTING:
            raise HardGateError(
                "当前正在实现中",
                self._state.phase,
                "先完成当前实现或调用 reset() 重置"
            )
        
        # 创建新设计规范
        spec = DesignSpec(
            title=title,
            description=description,
        )
        
        self._state.current_design = spec
        self._state.phase = GatePhase.BRAINSTORMING
        self._save_state()
        
        logger.info(f"HARD-GATE: 开始设计阶段 '{title}'")
        return spec
    
    def add_design_component(self, component: str, files: List[str]):
        """
        添加设计组件
        
        Args:
            component: 组件名称
            files: 涉及的文件列表
        """
        if not self._state.current_design:
            raise HardGateError(
                "没有活跃的设计阶段",
                self._state.phase,
                "先调用 start_design_phase()"
            )
        
        self._state.current_design.components.append(component)
        self._state.current_design.file_changes.extend(files)
        self._save_state()
    
    def add_design_question(self, question: str, answer: str):
        """添加设计讨论中的问答"""
        if not self._state.current_design:
            return
        
        self._state.current_design.questions.append({
            "question": question,
            "answer": answer,
            "timestamp": datetime.now().isoformat(),
        })
        self._save_state()
    
    def add_design_approach(self, approach: str, pros: List[str], cons: List[str], recommended: bool = False):
        """添加考虑的方案"""
        if not self._state.current_design:
            return
        
        self._state.current_design.approaches.append({
            "approach": approach,
            "pros": pros,
            "cons": cons,
            "recommended": recommended,
        })
        self._save_state()
    
    def present_design(self, spec_file_path: str = "") -> str:
        """
        呈现设计供审查
        
        Args:
            spec_file_path: 设计文档路径
            
        Returns:
            设计状态摘要
        """
        if not self._state.current_design:
            raise HardGateError(
                "没有活跃的设计",
                self._state.phase,
                "先调用 start_design_phase()"
            )
        
        if self._state.phase != GatePhase.BRAINSTORMING:
            raise HardGateError(
                f"当前阶段是 {self._state.phase.value}，不能呈现设计",
                self._state.phase,
                "设计阶段必须从 BRAINSTORMING 开始"
            )
        
        self._state.current_design.spec_file_path = spec_file_path
        self._state.phase = GatePhase.DESIGN_REVIEW
        self._save_state()
        
        # 生成摘要
        summary = self._generate_design_summary()
        logger.info(f"HARD-GATE: 设计呈现给用户审查\n{summary}")
        return summary
    
    def approve_design(self, approved_by: str = "user") -> bool:
        """
        批准设计
        
        Args:
            approved_by: 批准者标识
            
        Returns:
            True 表示批准成功
        """
        if not self._state.current_design:
            raise HardGateError(
                "没有活跃的设计",
                self._state.phase,
                "先调用 start_design_phase()"
            )
        
        if self._state.phase not in [GatePhase.BRAINSTORMING, GatePhase.DESIGN_REVIEW]:
            raise HardGateError(
                f"当前阶段 {self._state.phase.value} 不能批准设计",
                self._state.phase,
                "设计阶段才能批准"
            )
        
        self._state.current_design.approved = True
        self._state.current_design.approved_by = approved_by
        self._state.current_design.approved_at = datetime.now().isoformat()
        self._state.phase = GatePhase.DESIGN_APPROVED
        self._save_state()
        
        logger.info(f"HARD-GATE: 设计 '{self._state.current_design.title}' 已批准 by {approved_by}")
        return True
    
    def reject_design(self, reason: str) -> bool:
        """
        拒绝设计，需要重新设计
        
        Args:
            reason: 拒绝原因
            
        Returns:
            True
        """
        if not self._state.current_design:
            return False
        
        self._state.current_design.approved = False
        self._state.phase = GatePhase.BRAINSTORMING
        
        # 记录拒绝原因
        self._state.current_design.questions.append({
            "type": "rejection",
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
        })
        
        self._save_state()
        logger.warning(f"HARD-GATE: 设计被拒绝 - {reason}")
        return True
    
    def enter_implementation_phase(self):
        """进入实现阶段"""
        if not self._state.current_design:
            raise HardGateError(
                "没有活跃的设计",
                self._state.phase,
                "先开始设计阶段"
            )
        
        if not self._state.current_design.approved:
            raise HardGateError(
                "设计尚未批准",
                self._state.phase,
                "必须先获得批准才能开始实现"
            )
        
        self._state.phase = GatePhase.IMPLEMENTING
        self._save_state()
        logger.info("HARD-GATE: 进入实现阶段")
    
    def complete_implementation(self):
        """完成实现"""
        if self._state.phase != GatePhase.IMPLEMENTING:
            logger.warning(f"当前阶段不是 IMPLEMENTING，是 {self._state.phase.value}")
            return False
        
        # 保存到历史
        if self._state.current_design:
            self._state.design_history.append({
                "title": self._state.current_design.title,
                "approved_at": self._state.current_design.approved_at,
                "completed_at": datetime.now().isoformat(),
            })
        
        self._state.phase = GatePhase.COMPLETED
        self._save_state()
        logger.info("HARD-GATE: 实现完成")
        return True
    
    def reset(self):
        """重置 HARD-GATE 状态"""
        # 保存已完成的设计到历史
        if self._state.current_design and self._state.current_design.approved:
            self._state.design_history.append({
                "title": self._state.current_design.title,
                "approved_at": self._state.current_design.approved_at,
                "reset_at": datetime.now().isoformat(),
            })
        
        self._state = HardGateState()
        self._save_state()
        logger.info("HARD-GATE: 已重置")
    
    # ==================== 核心检查方法 ====================
    
    def check_can_write(self, file_path: str = "") -> Tuple[bool, str]:
        """
        检查是否可以写代码
        
        这是最核心的方法，任何写代码的操作前都必须调用。
        
        Args:
            file_path: 尝试写入的文件路径
            
        Returns:
            (True, message) 如果允许
            (False, message) 如果不允许
        """
        # 阶段检查
        if self._state.phase == GatePhase.IDLE:
            return False, (
                "HARD-GATE: 未开始设计阶段。\n"
                "必须先完成设计流程才能写代码。\n"
                "调用 HARD_GATE.start_design_phase() 开始。"
            )
        
        if self._state.phase == GatePhase.BRAINSTORMING:
            return False, (
                f"HARD-GATE: 正在设计阶段 '{self._state.current_design.title}'\n"
                "必须完成设计讨论并获得批准才能写代码。\n"
                "调用 HARD_GATE.approve_design() 获得批准。"
            )
        
        if self._state.phase == GatePhase.DESIGN_REVIEW:
            return False, (
                f"HARD-GATE: 设计 '{self._state.current_design.title}' 等待审查\n"
                "必须获得用户批准才能开始实现。\n"
                "请等待用户批准或调用 HARD_GATE.approve_design()。"
            )
        
        if self._state.phase == GatePhase.DESIGN_APPROVED:
            return False, (
                f"HARD-GATE: 设计已批准，但尚未进入实现阶段。\n"
                "调用 HARD_GATE.enter_implementation_phase() 开始实现。"
            )
        
        if self._state.phase == GatePhase.COMPLETED:
            return False, (
                "HARD-GATE: 当前任务已完成。\n"
                "如果需要新功能，调用 HARD_GATE.start_design_phase() 开始新的设计流程。"
            )
        
        # 实现阶段 - 检查文件是否在设计范围内
        if self._state.phase == GatePhase.IMPLEMENTING:
            if file_path and self._state.current_design:
                # 检查文件是否在设计范围内
                if self._state.current_design.file_changes:
                    # 如果有指定的文件列表，检查是否包含
                    is_designed = any(
                        file_path.startswith(f) or f in file_path
                        for f in self._state.current_design.file_changes
                    )
                    if not is_designed:
                        self._record_violation(
                            "undesigned_file",
                            f"尝试写入未设计的文件: {file_path}"
                        )
                        return False, (
                            f"HARD-GATE: 文件 '{file_path}' 不在设计范围内。\n"
                            "涉及的文件: " + ", ".join(self._state.current_design.file_changes)
                        )
            
            return True, "HARD-GATE: 允许写入"
        
        return False, f"HARD-GATE: 未知阶段 {self._state.phase.value}"
    
    def check_can_write_production(self, file_path: str) -> Tuple[bool, str]:
        """
        检查是否可以写生产代码 (别名)
        
        与 check_can_write 相同，但语义上强调生产代码
        """
        return self.check_can_write(file_path)
    
    def assert_can_write(self, file_path: str = ""):
        """
        断言可以写代码
        
        如果不能写，抛出 HardGateError
        """
        can_write, message = self.check_can_write(file_path)
        if not can_write:
            raise HardGateError(
                message,
                self._state.phase,
                self._get_suggestion()
            )
    
    def _get_suggestion(self) -> str:
        """获取当前阶段的建议"""
        suggestions = {
            GatePhase.IDLE: "调用 start_design_phase() 开始设计流程",
            GatePhase.BRAINSTORMING: "完成设计讨论，然后调用 approve_design()",
            GatePhase.DESIGN_REVIEW: "等待用户批准设计，或完善设计后重新提交",
            GatePhase.DESIGN_APPROVED: "调用 enter_implementation_phase() 进入实现",
            GatePhase.IMPLEMENTING: "设计已批准，正在实现中",
            GatePhase.COMPLETED: "调用 reset() 开始新任务",
        }
        return suggestions.get(self._state.phase, "")
    
    # ==================== 状态查询 ====================
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        status = {
            "phase": self._state.phase.value,
            "can_write": self.check_can_write()[0],
        }
        
        if self._state.current_design:
            status["design"] = {
                "title": self._state.current_design.title,
                "approved": self._state.current_design.approved,
                "approved_by": self._state.current_design.approved_by,
                "components": self._state.current_design.components,
                "file_changes": self._state.current_design.file_changes,
                "questions_count": len(self._state.current_design.questions),
                "approaches_count": len(self._state.current_design.approaches),
            }
        
        status["violations_count"] = len(self._state.violations)
        status["designs_completed"] = len(self._state.design_history)
        
        return status
    
    def _generate_design_summary(self) -> str:
        """生成设计摘要"""
        if not self._state.current_design:
            return "No active design"
        
        spec = self._state.current_design
        summary = f"""
═══════════════════════════════════════════════════════════════
                    设计规范摘要
═══════════════════════════════════════════════════════════════

标题: {spec.title}
描述: {spec.description or '(无)'}

组件 ({len(spec.components)}):
"""
        for comp in spec.components:
            summary += f"  • {comp}\n"
        
        if spec.file_changes:
            summary += f"\n涉及文件 ({len(spec.file_changes)}):\n"
            for f in spec.file_changes:
                summary += f"  • {f}\n"
        
        if spec.questions:
            summary += f"\n讨论问答 ({len(spec.questions)}):\n"
            for qa in spec.questions[-3:]:  # 只显示最近3条
                if 'question' in qa:
                    summary += f"  Q: {qa['question'][:50]}...\n"
        
        if spec.approaches:
            summary += f"\n考虑的方案 ({len(spec.approaches)}):\n"
            for i, app in enumerate(spec.approaches, 1):
                rec = " ★" if app.get('recommended') else ""
                summary += f"  {i}. {app['approach']}{rec}\n"
        
        summary += """
═══════════════════════════════════════════════════════════════
"""
        return summary
    
    def __repr__(self) -> str:
        status = self.get_status()
        return f"HARD_GATE(phase={status['phase']}, can_write={status['can_write']})"


# ==================== 全局快捷函数 ====================

def check_can_write(file_path: str = "") -> Tuple[bool, str]:
    """快捷函数: 检查是否可以写代码"""
    return HARD_GATE().check_can_write(file_path)


def assert_can_write(file_path: str = ""):
    """快捷函数: 断言可以写代码"""
    HARD_GATE().assert_can_write(file_path)


def get_status() -> Dict[str, Any]:
    """快捷函数: 获取状态"""
    return HARD_GATE().get_status()


def reset():
    """快捷函数: 重置状态"""
    HARD_GATE().reset()


# ==================== 导出 ====================

__all__ = [
    'HARD_GATE',
    'HardGateError', 
    'GatePhase', 
    'DesignSpec',
    'check_can_write',
    'assert_can_write',
    'get_status',
    'reset',
]


if __name__ == '__main__':
    # 演示用法
    print("=== HARD-GATE 演示 ===\n")
    
    # 重置状态
    HARD_GATE().reset()
    
    # 1. 尝试直接写代码 (应该失败)
    print("1. 尝试直接写代码:")
    can_write, msg = HARD_GATE().check_can_write("src/auth.py")
    print(f"   结果: {'允许' if can_write else '阻止'}")
    print(f"   原因: {msg[:100]}...\n")
    
    # 2. 开始设计阶段
    print("2. 开始设计阶段:")
    spec = HARD_GATE().start_design_phase("用户认证", "实现用户登录和注册功能")
    print(f"   设计: {spec.title}\n")
    
    # 3. 添加组件和文件
    HARD_GATE().add_design_component("认证服务", ["src/auth/service.py"])
    HARD_GATE().add_design_component("用户模型", ["src/auth/models.py"])
    
    # 4. 添加问答
    HARD_GATE().add_design_question("需要支持哪些登录方式?", "用户名密码")
    HARD_GATE().add_design_question("是否需要第三方登录?", "暂时不需要")
    
    # 5. 添加方案
    HARD_GATE().add_design_approach(
        "JWT Token", 
        ["无状态", "扩展性好"], 
        ["需要考虑Token刷新"], 
        recommended=True
    )
    
    # 6. 再次尝试写代码 (应该仍然失败)
    print("3. 设计阶段尝试写代码:")
    can_write, msg = HARD_GATE().check_can_write("src/auth.py")
    print(f"   结果: {'允许' if can_write else '阻止'}")
    print(f"   原因: {msg[:100]}...\n")
    
    # 7. 批准设计
    print("4. 批准设计:")
    HARD_GATE().approve_design("user")
    print("   设计已批准!\n")
    
    # 8. 进入实现阶段
    print("5. 进入实现阶段:")
    HARD_GATE().enter_implementation_phase()
    can_write, msg = HARD_GATE().check_can_write("src/auth/service.py")
    print(f"   结果: {'允许' if can_write else '阻止'}")
    print(f"   原因: {msg}\n")
    
    # 9. 尝试写入未设计的文件
    print("6. 尝试写入未设计的文件:")
    can_write, msg = HARD_GATE().check_can_write("src/unrelated.py")
    print(f"   结果: {'允许' if can_write else '阻止'}")
    print(f"   原因: {msg[:100]}...\n")
    
    # 显示状态
    print("7. 当前状态:")
    import json
    print(json.dumps(HARD_GATE().get_status(), indent=2, ensure_ascii=False))
    
    print("\n=== HARD-GATE 演示完成 ===")
