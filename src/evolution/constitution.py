#!/usr/bin/env python3
"""
宪法检查器
确保所有进化修改都符合宪法原则
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

from .evolution_types import EvolutionPlan, EvolutionImpactLevel


class ConstitutionChecker:
    """宪法符合性检查器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 加载宪法原则
        self.constitution_path = Path(__file__).parent.parent.parent / "constitution"
        self.identity_path = self.constitution_path / "identity.md"
        self.bible_path = self.constitution_path / "BIBLE.md"
        
        self.identity_content = self._load_identity()
        self.principles = self._load_principles()
        
        self.violation_history: List[Dict[str, Any]] = []
        self.max_violation_history = 100
        
        self.logger.info("宪法检查器初始化完成")
    
    def _load_identity(self) -> Dict[str, Any]:
        """加载身份定义"""
        identity = {
            "system_name": "RANGEN自进化创业者伙伴",
            "core_mission": "帮助创业者进入日本市场，并持续优化自身能力",
            "capability_areas": [
                "日本市场分析",
                "商业方案设计", 
                "技术解决方案",
                "客户开拓",
                "创业者决策支持"
            ],
            "evolution_preferences": {
                "learning_style": "从成功案例中提取模式，从失败中学习教训",
                "optimization_focus": "首先优化对创业者最有价值的功能",
                "evolution_pace": "渐进式改进为主，重大修改需多重验证",
                "knowledge_solidification": "将成功经验固化为可复用的能力包"
            }
        }
        
        if self.identity_path.exists():
            try:
                content = self.identity_path.read_text(encoding='utf-8')
                # 可以解析markdown内容，但为了简化，我们使用硬编码版本
                self.logger.info("身份定义文件加载成功")
            except Exception as e:
                self.logger.error(f"加载身份定义文件失败: {e}")
        
        return identity
    
    def _load_principles(self) -> Dict[str, Dict[str, Any]]:
        """加载宪法原则"""
        principles = {
            "principle_0": {
                "name": "创业者主权原则",
                "core": "所有进化和优化必须以提升创业者价值为最高目标",
                "rules": [
                    "进化方向必须对齐创业者的业务目标",
                    "重大功能变更需创业者明确确认",
                    "进化优先级基于对创业者的实际价值",
                    "不得降低对创业者重要功能的性能"
                ],
                "boundaries": {
                    "allowed": ["优化日本市场分析准确性", "提高方案生成速度", "增强创业者决策支持能力"],
                    "prohibited": ["删除创业者常用功能", "降低关键功能的可靠性"]
                }
            },
            "principle_1": {
                "name": "安全第一原则",
                "core": "不得进行危险、非法或不可逆的操作",
                "prohibitions": [
                    "支付操作: 不得进行任何形式的支付或资金转移",
                    "违法操作: 不得违反任何国家或地区的法律法规",
                    "系统破坏: 不得删除或破坏系统核心文件",
                    "数据泄露: 不得泄露创业者敏感信息",
                    "身份篡改: 不得修改核心身份定义(identity.md)"
                ],
                "safeguards": [
                    "所有外部API调用需安全检查",
                    "文件写入操作需多重验证",
                    "敏感操作需人工确认",
                    "定期安全审计和漏洞扫描"
                ]
            },
            "principle_2": {
                "name": "透明进化原则",
                "core": "所有自我修改必须有完整、可追溯的记录",
                "requirements": [
                    "Git提交: 所有代码修改必须通过Git提交",
                    "修改说明: 每次提交必须包含详细的修改说明",
                    "进化日志: 维护完整的进化历史记录",
                    "影响分析: 记录修改对系统性能的影响",
                    "回滚机制: 支持快速回滚到前一个稳定版本"
                ]
            },
            "principle_3": {
                "name": "价值验证原则",
                "core": "进化必须有明确的预期价值，并通过验证",
                "validation_process": [
                    "价值假设: 明确进化的预期价值主张",
                    "多模型审查: 至少两个独立LLM审查进化方案",
                    "创业者确认: 重大修改需创业者明确批准",
                    "A/B测试: 关键功能修改需对比测试",
                    "效果评估: 进化后验证实际效果"
                ]
            },
            "principle_4": {
                "name": "持续学习原则",
                "core": "从每次交互中学习，持续优化知识和方法",
                "learning_boundaries": [
                    "只学习与日本市场相关的知识",
                    "不学习违反原则的内容",
                    "不存储创业者个人隐私信息",
                    "定期清理无用知识"
                ]
            },
            "principle_5": {
                "name": "工作流优先原则",
                "core": "优化深度集成到创业者的日常工作流"
            },
            "principle_6": {
                "name": "可控透明原则",
                "core": "每个关键节点都可观测、可干预、可定制"
            },
            "principle_7": {
                "name": "知识资产化原则",
                "core": "将成功经验固化为可复用、可版本化的能力包"
            },
            "principle_8": {
                "name": "迭代优化原则",
                "core": "通过持续的小步迭代实现系统进化"
            }
        }
        
        if self.bible_path.exists():
            try:
                content = self.bible_path.read_text(encoding='utf-8')
                # 可以解析markdown内容，但为了简化，我们使用硬编码版本
                self.logger.info("宪法原则文件加载成功")
            except Exception as e:
                self.logger.error(f"加载宪法原则文件失败: {e}")
        
        return principles
    
    async def check_evolution_plan(self, plan: EvolutionPlan) -> Dict[str, Any]:
        """检查进化计划是否符合宪法"""
        self.logger.info(f"检查进化计划宪法符合性: {plan.plan_id}")
        
        violations = []
        warnings = []
        
        # Principle 0: 创业者主权原则
        if not await self._check_entrepreneur_sovereignty(plan):
            violations.append({
                "principle": "principle_0",
                "name": "创业者主权原则",
                "description": "进化计划可能未充分对齐创业者价值"
            })
        
        # Principle 1: 安全第一原则
        safety_check = await self._check_safety(plan)
        if not safety_check["passed"]:
            violations.extend(safety_check["violations"])
        
        # Principle 2: 透明进化原则
        if not await self._check_transparency(plan):
            warnings.append({
                "principle": "principle_2",
                "name": "透明进化原则",
                "description": "计划缺少足够的透明性保障"
            })
        
        # Principle 3: 价值验证原则
        if not await self._check_value_validation(plan):
            warnings.append({
                "principle": "principle_3",
                "name": "价值验证原则",
                "description": "计划的价值验证机制不足"
            })
        
        # Principle 4-8: 其他原则检查
        other_checks = await self._check_other_principles(plan)
        warnings.extend(other_checks["warnings"])
        
        # 根据影响级别调整严格度
        strictness = self._get_strictness_level(plan.impact_level)
        
        result = {
            "plan_id": plan.plan_id,
            "timestamp": datetime.now().isoformat(),
            "violations": violations,
            "warnings": warnings,
            "strictness_level": strictness,
            "approved": len(violations) == 0,
            "needs_human_review": len(violations) > 0 or plan.impact_level in [EvolutionImpactLevel.MAJOR, EvolutionImpactLevel.ARCHITECTURAL],
            "review_summary": self._generate_review_summary(violations, warnings, plan)
        }
        
        # 记录违规历史
        if violations:
            self._record_violation(plan, violations)
        
        self.logger.info(f"宪法检查结果: 批准={result['approved']}, 违规数={len(violations)}, 警告数={len(warnings)}")
        
        return result
    
    async def _check_entrepreneur_sovereignty(self, plan: EvolutionPlan) -> bool:
        """检查创业者主权原则"""
        # 检查计划是否对齐创业者价值
        entrepreneur_keywords = ["创业者", "日本市场", "效率", "性能", "准确性", "用户体验"]
        description = plan.description.lower()
        
        # 检查是否包含创业者价值关键词
        has_entrepreneur_value = any(keyword in description for keyword in ["创业者", "效率", "性能", "准确性", "用户体验"])
        
        # 检查是否可能损害创业者价值
        harmful_keywords = ["删除", "移除", "降低", "减少", "限制", "禁用"]
        is_harmful = any(keyword in description for keyword in harmful_keywords)
        
        # 检查目标文件是否包含核心身份文件
        core_identity_files = ["constitution/identity.md", "constitution/BIBLE.md"]
        targets_core_identity = any(file in core_identity_files for file in plan.target_files)
        
        return has_entrepreneur_value and not is_harmful and not targets_core_identity
    
    async def _check_safety(self, plan: EvolutionPlan) -> Dict[str, Any]:
        """检查安全第一原则"""
        violations = []
        
        # 检查是否涉及危险操作
        dangerous_patterns = [
            "支付", "转账", "资金", "银行", "信用卡",
            "删除.*系统", "删除.*核心", "格式化", "清空",
            "执行.*命令", "系统调用", "shell", "终端",
            "修改.*密码", "修改.*密钥", "修改.*证书"
        ]
        
        description = plan.description.lower()
        for pattern in dangerous_patterns:
            if pattern in description:
                violations.append({
                    "principle": "principle_1",
                    "name": "安全第一原则",
                    "description": f"检测到潜在危险操作: {pattern}",
                    "severity": "high"
                })
        
        # 检查目标文件是否敏感
        sensitive_dirs = ["/etc/", "/bin/", "/usr/", "/var/", "C:\\Windows\\", "C:\\Program Files\\"]
        for file_path in plan.target_files:
            for sensitive_dir in sensitive_dirs:
                if file_path.startswith(sensitive_dir):
                    violations.append({
                        "principle": "principle_1",
                        "name": "安全第一原则",
                        "description": f"目标文件位于敏感目录: {file_path}",
                        "severity": "critical"
                    })
                    break
        
        return {
            "passed": len(violations) == 0,
            "violations": violations
        }
    
    async def _check_transparency(self, plan: EvolutionPlan) -> bool:
        """检查透明进化原则"""
        # 检查计划是否包含足够的透明性信息
        required_info = [
            plan.description,  # 必须有描述
            plan.expected_benefits,  # 必须有预期收益
            plan.risks,  # 必须有风险评估
            plan.validation_methods  # 必须有验证方法
        ]
        
        # 所有必需信息都不能为空
        return all(info for info in required_info)
    
    async def _check_value_validation(self, plan: EvolutionPlan) -> bool:
        """检查价值验证原则"""
        # 检查是否有明确的预期收益
        if not plan.expected_benefits:
            return False
        
        # 检查是否有验证方法
        if not plan.validation_methods:
            return False
        
        # 检查预期收益是否具体可衡量
        measurable_keywords = ["提高", "降低", "减少", "增加", "优化", "改进", "加速"]
        benefits_text = " ".join(plan.expected_benefits).lower()
        has_measurable_benefits = any(keyword in benefits_text for keyword in measurable_keywords)
        
        return has_measurable_benefits
    
    async def _check_other_principles(self, plan: EvolutionPlan) -> Dict[str, Any]:
        """检查其他原则"""
        warnings = []
        
        # Principle 4: 持续学习原则
        if "学习" not in plan.description and "优化" not in plan.description:
            warnings.append({
                "principle": "principle_4",
                "name": "持续学习原则",
                "description": "计划未明确体现学习或优化意图",
                "severity": "low"
            })
        
        # Principle 5: 工作流优先原则
        workflow_keywords = ["工作流", "流程", "自动化", "集成", "触发"]
        description = plan.description.lower()
        if not any(keyword in description for keyword in workflow_keywords):
            warnings.append({
                "principle": "principle_5",
                "name": "工作流优先原则",
                "description": "计划未明确涉及工作流优化",
                "severity": "low"
            })
        
        # Principle 7: 知识资产化原则
        if plan.impact_level == EvolutionImpactLevel.MINOR and "知识" not in description:
            warnings.append({
                "principle": "principle_7",
                "name": "知识资产化原则",
                "description": "微优化未考虑知识资产化",
                "severity": "low"
            })
        
        return {"warnings": warnings}
    
    def _get_strictness_level(self, impact_level: EvolutionImpactLevel) -> str:
        """根据影响级别确定严格度"""
        strictness_map = {
            EvolutionImpactLevel.MINOR: "low",
            EvolutionImpactLevel.MODERATE: "medium",
            EvolutionImpactLevel.MAJOR: "high",
            EvolutionImpactLevel.ARCHITECTURAL: "critical"
        }
        return strictness_map.get(impact_level, "medium")
    
    def _generate_review_summary(self, violations: List[Dict], warnings: List[Dict], plan: EvolutionPlan) -> str:
        """生成审查摘要"""
        if not violations and not warnings:
            return f"进化计划 '{plan.plan_id}' 完全符合宪法原则。"
        
        summary_parts = [f"进化计划 '{plan.plan_id}' 审查结果:"]
        
        if violations:
            summary_parts.append("🚨 违规事项:")
            for i, violation in enumerate(violations, 1):
                summary_parts.append(f"  {i}. {violation['name']}: {violation['description']}")
        
        if warnings:
            summary_parts.append("⚠️ 警告事项:")
            for i, warning in enumerate(warnings, 1):
                summary_parts.append(f"  {i}. {warning['name']}: {warning['description']}")
        
        if violations:
            summary_parts.append("❌ 由于存在违规事项，计划未获批准。")
        else:
            summary_parts.append("✅ 计划获得批准，但请注意警告事项。")
        
        return "\n".join(summary_parts)
    
    def _record_violation(self, plan: EvolutionPlan, violations: List[Dict]):
        """记录违规历史"""
        violation_record = {
            "plan_id": plan.plan_id,
            "timestamp": datetime.now().isoformat(),
            "description": plan.description,
            "impact_level": plan.impact_level.value,
            "violations": violations,
            "target_files": plan.target_files
        }
        
        self.violation_history.append(violation_record)
        if len(self.violation_history) > self.max_violation_history:
            self.violation_history.pop(0)
        
        # 保存到文件
        violation_log_path = Path(__file__).parent.parent.parent / "evolution_logs" / "constitution_violations.json"
        violation_log_path.parent.mkdir(exist_ok=True)
        
        try:
            existing_data = []
            if violation_log_path.exists():
                with open(violation_log_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            existing_data.append(violation_record)
            
            with open(violation_log_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"违规记录已保存到: {violation_log_path}")
        except Exception as e:
            self.logger.error(f"保存违规记录失败: {e}")
    
    async def check_code_modification(self, modification: Dict[str, Any]) -> Dict[str, Any]:
        """检查具体的代码修改是否符合宪法"""
        self.logger.info(f"检查代码修改宪法符合性")
        
        violations = []
        
        # 检查修改类型
        change_type = modification.get("change_type", "")
        file_path = modification.get("file_path", "")
        
        # Principle 1: 安全检查
        if change_type == "delete" and "constitution" in file_path:
            violations.append({
                "principle": "principle_1",
                "name": "安全第一原则",
                "description": "尝试修改宪法文件",
                "severity": "critical"
            })
        
        # Principle 0: 创业者价值检查
        if "test" in file_path and change_type == "delete":
            violations.append({
                "principle": "principle_0",
                "name": "创业者主权原则",
                "description": "删除测试文件可能降低系统可靠性",
                "severity": "medium"
            })
        
        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "needs_human_review": len(violations) > 0
        }
    
    async def get_constitution_status(self) -> Dict[str, Any]:
        """获取宪法状态"""
        return {
            "constitution_version": "1.0.0",
            "principles_count": len(self.principles),
            "violation_history_count": len(self.violation_history),
            "recent_violations": self.violation_history[-5:] if self.violation_history else [],
            "identity": {
                "system_name": self.identity_content.get("system_name"),
                "core_mission": self.identity_content.get("core_mission")
            },
            "last_updated": datetime.now().isoformat()
        }


# 便捷函数
async def check_evolution_constitution(plan: EvolutionPlan) -> Dict[str, Any]:
    """检查进化计划宪法符合性（便捷函数）"""
    checker = ConstitutionChecker()
    return await checker.check_evolution_plan(plan)


if __name__ == "__main__":
    # 测试宪法检查器
    import asyncio
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        print("🧪 测试宪法检查器")
        print("=" * 60)
        
        checker = ConstitutionChecker()
        
        # 测试1: 正常的进化计划
        from .evolution_types import EvolutionPlan, EvolutionImpactLevel
        good_plan = EvolutionPlan(
            plan_id="test_good_001",
            description="优化日本市场分析准确性，提高响应速度",
            impact_level=EvolutionImpactLevel.MINOR,
            target_files=["src/agents/japan_market/market_researcher.py"],
            expected_benefits=["提高市场分析准确性20%", "减少响应时间30%"],
            risks=["低风险，主要是代码优化"],
            validation_methods=["单元测试", "性能测试"],
            estimated_effort=8
        )
        
        result = await checker.check_evolution_plan(good_plan)
        print(f"正常计划检查结果: 批准={result['approved']}")
        print(f"违规数: {len(result['violations'])}")
        print(f"警告数: {len(result['warnings'])}")
        
        # 测试2: 危险的进化计划
        bad_plan = EvolutionPlan(
            plan_id="test_bad_001",
            description="删除系统核心文件以节省空间",
            impact_level=EvolutionImpactLevel.MAJOR,
            target_files=["constitution/identity.md", "src/core/config.py"],
            expected_benefits=["节省磁盘空间"],
            risks=["系统可能无法启动"],
            validation_methods=["无"],
            estimated_effort=2
        )
        
        result = await checker.check_evolution_plan(bad_plan)
        print(f"\n危险计划检查结果: 批准={result['approved']}")
        print(f"违规数: {len(result['violations'])}")
        if result['violations']:
            print(f"第一个违规: {result['violations'][0]['description']}")
        
        # 获取宪法状态
        status = await checker.get_constitution_status()
        print(f"\n宪法状态: {status['principles_count']}条原则")
        print(f"违规历史记录数: {status['violation_history_count']}")
    
    asyncio.run(test())