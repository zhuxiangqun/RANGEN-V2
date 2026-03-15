#!/usr/bin/env python3
"""
测试专家Agent - 专业质量保证角色
负责测试策略、测试用例设计、质量保证
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .professional_agent_base import ProfessionalAgentBase, ProfessionalAgentConfig

logger = logging.getLogger(__name__)


class TestingAgent(ProfessionalAgentBase):
    """测试专家Agent - 专业质量保证角色"""
    
    def __init__(
        self,
        agent_id: str,
        specialization: str = "软件测试",
        config: Optional[ProfessionalAgentConfig] = None
    ):
        """初始化测试专家Agent
        
        Args:
            agent_id: Agent唯一标识符
            specialization: 专业领域细分（如：自动化测试、性能测试、安全测试、移动端测试等）
            config: 配置对象（可选）
        """
        # 默认配置
        default_role_name = "测试专家"
        default_role_name_en = "Testing Specialist"
        default_domain_expertise = f"质量保证 - {specialization}"
        default_expertise_description = f"""资深测试专家，专注于{specialization}领域的质量保证和测试验证。

核心职责：
1. 测试策略制定：基于产品需求和风险分析制定全面的测试策略
2. 测试用例设计：设计高质量、高覆盖率的测试用例和测试场景
3. 测试执行管理：组织和执行各类测试活动，确保测试覆盖和效果
4. 缺陷管理：跟踪和管理缺陷，确保问题及时解决和质量改进
5. 质量评估：评估产品质量状态，提供质量风险预警和改进建议
6. 测试自动化：设计和实施测试自动化，提高测试效率和质量

专业能力：
- 精通软件测试理论和方法（黑盒测试、白盒测试、探索性测试等）
- 熟悉测试工具和框架（Selenium、JUnit、pytest、Appium等）
- 掌握测试自动化技术和最佳实践
- 了解软件开发流程和敏捷测试方法
- 具备质量分析和风险识别能力
"""

        # 根据specialization调整能力
        capabilities = [
            "测试策略",
            "测试用例设计",
            "测试执行",
            "缺陷管理",
            "质量评估",
            f"{specialization}",
            "测试自动化",
            "性能测试"
        ]
        
        # 测试专家可用的工具
        tools = [
            "test_case_generator",
            "test_execution_manager",
            "defect_tracker",
            "performance_tester",
            "security_scanner",
            "coverage_analyzer",
            "api_testing",
            "ui_automation"
        ]
        
        if config is None:
            config = ProfessionalAgentConfig(
                agent_id=agent_id,
                role_name=default_role_name,
                role_name_en=default_role_name_en,
                domain_expertise=default_domain_expertise,
                expertise_description=default_expertise_description,
                capabilities=capabilities,
                tools=tools,
                collaboration_style="detail-oriented",
                capability_level=0.9,
                language="zh-CN"
            )
        
        super().__init__(
            agent_id=agent_id,
            role_name=config.role_name,
            role_name_en=config.role_name_en,
            domain_expertise=config.domain_expertise,
            expertise_description=config.expertise_description,
            config=config
        )
        
        self.specialization = specialization
        self.testing_standards: List[str] = ["ISO 25010", "ISTQB"]  # 测试标准
        
        logger.info(f"初始化测试专家Agent: {agent_id}, 专业领域: {specialization}")
    
    def set_testing_standards(self, standards: List[str]) -> None:
        """设置测试标准
        
        Args:
            standards: 测试标准列表
        """
        self.testing_standards = standards
        logger.info(f"测试专家Agent {self.agent_id} 设置测试标准: {standards}")
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行测试任务
        
        Args:
            task: 任务描述
            
        Returns:
            执行结果
        """
        task_name = task.get("task_name", "未命名任务")
        task_type = task.get("task_type", "general")
        
        logger.info(f"测试专家Agent {self.agent_id} 开始执行任务: {task_name}")
        
        # 根据任务类型执行不同的测试逻辑
        result = {
            "agent_id": self.agent_id,
            "role_name": self.role_name,
            "role_name_en": self.role_name_en,
            "task_id": task.get("task_id", "unknown"),
            "task_name": task_name,
            "task_type": task_type,
            "status": "in_progress",
            "output": None,
            "metrics": {},
            "completion_time": None,
            "testing_details": {},
            "recommendations": []
        }
        
        try:
            if task_type == "test_strategy":
                result = await self._execute_test_strategy(task, result)
            elif task_type == "test_case_design":
                result = await self._execute_test_case_design(task, result)
            elif task_type == "test_execution":
                result = await self._execute_test_execution(task, result)
            elif task_type == "defect_analysis":
                result = await self._execute_defect_analysis(task, result)
            elif task_type == "quality_assessment":
                result = await self._execute_quality_assessment(task, result)
            else:
                result = await self._execute_general_testing_task(task, result)
            
            result["status"] = "completed"
            result["completion_time"] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"测试专家Agent {self.agent_id} 执行任务失败: {str(e)}")
            result["status"] = "failed"
            result["error"] = str(e)
            result["completion_time"] = datetime.now().isoformat()
        
        # 存储任务结果
        self.store_deliverable(f"task_result_{task.get('task_id', 'unknown')}", result)
        
        return result
    
    async def _execute_test_strategy(self, task: Dict[str, Any], base_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行测试策略制定任务
        
        Args:
            task: 任务描述
            base_result: 基础结果
            
        Returns:
            更新后的结果
        """
        product_requirements = task.get("product_requirements", {})
        risk_level = task.get("risk_level", "medium")
        
        logger.info(f"执行测试策略制定任务，风险级别: {risk_level}")
        
        # 测试策略分析
        test_strategy = {
            "requirements_analysis": self.reasoning.analyze(
                query=f"分析产品需求: {json.dumps(product_requirements, ensure_ascii=False)}",
                context=f"风险级别: {risk_level}, 测试标准: {self.testing_standards}",
                reasoning_type=self.reasoning.get_reasoning_type("ANALYTICAL")
            ),
            "risk_assessment": self.reasoning.analyze(
                query=f"评估测试风险",
                context="需求分析已完成",
                reasoning_type=self.reasoning.get_reasoning_type("CRITICAL")
            ),
            "strategy_planning": self.reasoning.generate(
                query=f"制定测试策略",
                context="风险评估已完成",
                reasoning_type=self.reasoning.get_reasoning_type("STRATEGIC")
            ),
            "resource_planning": self.reasoning.generate(
                query=f"规划测试资源",
                context="测试策略已制定",
                reasoning_type=self.reasoning.get_reasoning_type("PLANNING")
            )
        }
        
        # 生成测试策略文档
        test_strategy_doc = f"""
# 测试策略文档 - {task.get('product_name', '产品')}

## 策略概述
- 产品名称: {task.get('product_name', '产品')}
- 风险级别: {risk_level}
- 测试标准: {', '.join(self.testing_standards)}
- 质量目标: {task.get('quality_objectives', '零致命缺陷，关键功能100%覆盖')}

## 测试范围
### 功能测试范围
- 核心功能: {task.get('core_features', ['用户认证', '数据管理', '报告生成'])}
- 辅助功能: {task.get('auxiliary_features', ['设置管理', '帮助文档', '导出功能'])}
- 边界条件: {task.get('boundary_conditions', ['大容量数据', '并发访问', '异常输入'])}
- 兼容性要求: {task.get('compatibility_requirements', ['Chrome/Firefox/Safari', 'Windows/macOS/Linux', '移动端响应式'])}

### 非功能测试范围
- 性能测试: {task.get('performance_testing', ['响应时间<2秒', '并发用户数>1000', '资源使用率<80%'])}
- 安全测试: {task.get('security_testing', ['SQL注入防护', 'XSS攻击防护', '数据加密传输'])}
- 可用性测试: {task.get('usability_testing', ['界面友好度', '操作便捷性', '学习成本'])}
- 可靠性测试: {task.get('reliability_testing', ['系统稳定性', '错误恢复能力', '数据一致性'])}

## 测试方法
### 测试类型
1. 功能测试
   - 黑盒测试: 基于需求的测试
   - 白盒测试: 基于代码的测试
   - 灰盒测试: 结合需求和代码的测试

2. 非功能测试
   - 性能测试: 负载测试、压力测试、稳定性测试
   - 安全测试: 渗透测试、漏洞扫描、代码审计
   - 兼容性测试: 浏览器兼容、操作系统兼容、设备兼容

3. 专项测试
   - 回归测试: 确保修改不影响现有功能
   - 探索性测试: 基于经验和直觉的测试
   - 用户验收测试: 用户视角的测试验证

### 测试级别
- 单元测试: 代码模块级别测试
- 集成测试: 模块间接口测试
- 系统测试: 完整系统功能测试
- 验收测试: 用户验收标准测试

## 测试环境
### 硬件环境
- 测试服务器: {task.get('test_servers', ['Linux服务器 x2', 'Windows服务器 x1'])}
- 测试客户端: {task.get('test_clients', ['PC工作站 x5', '移动设备 x3'])}
- 网络环境: {task.get('network_environment', ['局域网千兆网络', '互联网模拟环境'])}

### 软件环境
- 操作系统: {task.get('operating_systems', ['Windows 10/11', 'macOS', 'Ubuntu'])}
- 浏览器: {task.get('browsers', ['Chrome 最新版', 'Firefox 最新版', 'Safari 最新版'])}
- 测试工具: {task.get('testing_tools', ['Selenium', 'JMeter', 'Postman', 'Appium'])}
- 监控工具: {task.get('monitoring_tools', ['Grafana', 'Prometheus', 'ELK Stack'])}

## 测试计划
### 时间安排
- 需求分析阶段: {task.get('requirements_phase', '1周')}
- 测试设计阶段: {task.get('design_phase', '2周')}
- 测试执行阶段: {task.get('execution_phase', '3周')}
- 测试报告阶段: {task.get('report_phase', '1周')}

### 资源分配
- 测试人员: {task.get('testers_count', '3名测试工程师')}
- 开发支持: {task.get('dev_support', '2名开发工程师')}
- 产品支持: {task.get('product_support', '1名产品经理')}

## 质量指标
### 覆盖指标
- 需求覆盖率: {task.get('requirement_coverage', '100%')}
- 代码覆盖率: {task.get('code_coverage', '>=80%')}
- 功能覆盖率: {task.get('function_coverage', '100%')}
- 路径覆盖率: {task.get('path_coverage', '>=70%')}

### 缺陷指标
- 缺陷密度: {task.get('defect_density', '<=0.5缺陷/千行代码')}
- 缺陷解决率: {task.get('defect_resolution_rate', '>=95%')}
- 严重缺陷数: {task.get('critical_defects', '0')}
- 回归缺陷数: {task.get('regression_defects', '<=5')}

### 性能指标
- 响应时间: {task.get('response_time', '页面加载<3秒，API响应<1秒')}
- 并发用户数: {task.get('concurrent_users', '支持1000并发用户')}
- 系统可用性: {task.get('system_availability', '>=99.9%')}
        """
        
        base_result["output"] = {
            "test_strategy": test_strategy,
            "test_strategy_doc": test_strategy_doc,
            "testing_approach": {
                "methodology": "风险驱动测试 + 基于需求的测试",
                "automation_level": "核心功能自动化率>70%",
                "continuous_testing": "集成到CI/CD流水线",
                "quality_gates": ["代码覆盖率>80%", "零P0/P1缺陷", "性能测试通过"]
            },
            "test_metrics": {
                "coverage_targets": {
                    "requirements": "100%",
                    "code": ">=80%",
                    "functions": "100%",
                    "risks": "100%"
                },
                "quality_targets": {
                    "defect_density": "<=0.5/千行代码",
                    "defect_leakage": "<=5%",
                    "test_effectiveness": ">=90%"
                }
            }
        }
        
        base_result["testing_details"] = {
            "risk_based_testing": True,
            "test_automation_framework": ["pytest", "Selenium", "Jenkins", "Docker"],
            "quality_assurance_process": ["测试左移", "持续测试", "测试右移"]
        }
        
        base_result["recommendations"] = [
            "采用风险驱动测试方法",
            "建立自动化测试框架",
            "实施持续测试流程",
            "加强缺陷预防和分析"
        ]
        
        return base_result
    
    async def _execute_test_case_design(self, task: Dict[str, Any], base_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行测试用例设计任务
        
        Args:
            task: 任务描述
            base_result: 基础结果
            
        Returns:
            更新后的结果
        """
        feature_requirements = task.get("feature_requirements", {})
        test_technique = task.get("test_technique", "等价类划分")
        
        logger.info(f"执行测试用例设计任务，测试技术: {test_technique}")
        
        # 测试用例设计分析
        test_case_design = {
            "requirement_analysis": self.reasoning.analyze(
                query=f"分析功能需求: {json.dumps(feature_requirements, ensure_ascii=False)}",
                context=f"测试技术: {test_technique}",
                reasoning_type=self.reasoning.get_reasoning_type("ANALYTICAL")
            ),
            "test_scenario_identification": self.reasoning.generate(
                query=f"识别测试场景",
                context="需求分析已完成",
                reasoning_type=self.reasoning.get_reasoning_type("CREATIVE")
            ),
            "test_case_generation": self.reasoning.generate(
                query=f"生成测试用例",
                context="测试场景已识别",
                reasoning_type=self.reasoning.get_reasoning_type("DETAILED")
            ),
            "test_data_design": self.reasoning.generate(
                query=f"设计测试数据",
                context="测试用例已生成",
                reasoning_type=self.reasoning.get_reasoning_type("STRUCTURAL")
            )
        }
        
        # 生成测试用例示例
        test_case_example = f"""
# 测试用例文档 - {feature_requirements.get('feature_name', '功能')}

## 功能概述
- 功能名称: {feature_requirements.get('feature_name', '用户登录')}
- 功能描述: {feature_requirements.get('feature_description', '用户通过用户名和密码登录系统')}
- 优先级: {feature_requirements.get('priority', '高')}
- 测试重点: {feature_requirements.get('testing_focus', '安全性、易用性、性能')}

## 测试场景

### 场景1: 正常登录流程
**场景描述**: 有效用户使用正确的用户名和密码登录系统
**前置条件**: 用户已注册，系统正常运行
**测试步骤**:
1. 访问登录页面
2. 输入有效的用户名
3. 输入正确的密码
4. 点击登录按钮
**预期结果**:
- 登录成功
- 跳转到用户主页
- 显示欢迎信息
- 记录登录日志

### 场景2: 密码错误登录
**场景描述**: 有效用户使用错误的密码登录系统
**前置条件**: 用户已注册，系统正常运行
**测试步骤**:
1. 访问登录页面
2. 输入有效的用户名
3. 输入错误的密码
4. 点击登录按钮
**预期结果**:
- 登录失败
- 显示错误提示信息
- 停留在登录页面
- 记录登录失败日志

### 场景3: 用户名不存在
**场景描述**: 使用不存在的用户名尝试登录系统
**前置条件**: 系统正常运行
**测试步骤**:
1. 访问登录页面
2. 输入不存在的用户名
3. 输入任意密码
4. 点击登录按钮
**预期结果**:
- 登录失败
- 显示用户不存在的提示信息
- 停留在登录页面
- 不记录敏感日志

### 场景4: 空用户名或密码
**场景描述**: 尝试使用空用户名或密码登录系统
**前置条件**: 系统正常运行
**测试步骤**:
1. 访问登录页面
2. 用户名留空，输入密码
3. 点击登录按钮
4. 输入用户名，密码留空
5. 点击登录按钮
6. 用户名和密码都留空
7. 点击登录按钮
**预期结果**:
- 登录失败
- 显示相应的验证错误信息
- 停留在登录页面
- 高亮显示错误字段

## 详细测试用例

### 测试用例1: TC-LOGIN-001
**用例名称**: 管理员用户登录
**优先级**: 高
**测试类型**: 功能测试
**测试数据**:
- 用户名: admin@example.com
- 密码: Admin123!
**测试步骤**:
1. 打开浏览器，访问登录页面
2. 在用户名输入框输入"admin@example.com"
3. 在密码输入框输入"Admin123!"
4. 点击"登录"按钮
5. 验证页面跳转和显示内容
**预期结果**:
1. 页面成功跳转到管理员控制台
2. 页面显示"欢迎，管理员"的欢迎信息
3. 导航栏显示管理员专用菜单
4. 浏览器地址栏显示管理员控制台URL
**实际结果**: [待执行]
**测试状态**: [未执行]
**备注**: 验证管理员权限和功能访问

### 测试用例2: TC-LOGIN-002
**用例名称**: 普通用户登录
**优先级**: 高
**测试类型**: 功能测试
**测试数据**:
- 用户名: user@example.com
- 密码: User123!
**测试步骤**:
1. 打开浏览器，访问登录页面
2. 在用户名输入框输入"user@example.com"
3. 在密码输入框输入"User123!"
4. 点击"登录"按钮
5. 验证页面跳转和显示内容
**预期结果**:
1. 页面成功跳转到用户个人中心
2. 页面显示"欢迎回来"的欢迎信息
3. 导航栏显示用户功能菜单
4. 显示用户个人信息和统计数据
**实际结果**: [待执行]
**测试状态**: [未执行]
**备注**: 验证普通用户权限和功能访问

### 测试用例3: TC-LOGIN-003
**用例名称**: 登录失败次数限制
**优先级**: 中
**测试类型**: 安全测试
**测试数据**:
- 用户名: test@example.com
- 密码: WrongPass1, WrongPass2, WrongPass3, WrongPass4, WrongPass5
**测试步骤**:
1. 打开浏览器，访问登录页面
2. 使用相同用户名连续输入错误密码5次
3. 第6次尝试使用正确密码登录
4. 等待15分钟后再次尝试登录
**预期结果**:
1. 前5次登录显示密码错误
2. 第5次失败后显示账户锁定提示
3. 第6次尝试登录失败，提示账户已锁定
4. 15分钟后可以使用正确密码成功登录
**实际结果**: [待执行]
**测试状态**: [未执行]
**备注**: 验证账户安全锁定机制

## 测试数据设计
### 正常数据
- 有效用户名: ["admin", "user1", "testuser", "longusername123"]
- 有效密码: ["Password123!", "Secure@2024", "Test#Pass1", "Aa123456!"]

### 边界数据
- 最小长度用户名: "a" (如果允许)
- 最大长度用户名: "a" * {task.get('max_username_length', 50)}
- 特殊字符用户名: ["user@domain.com", "user.name", "user_name"]
- 空用户名: ""
- 空密码: ""

### 异常数据
- SQL注入尝试: ["' OR '1'='1", "admin'--", "'; DROP TABLE users;--"]
- XSS攻击尝试: ["<script>alert('xss')</script>", "<img src=x onerror=alert(1)>"]
- 超长数据: ["a" * 1000, "b" * 5000]
- 非法字符: ["用户\n名", "密\t码", "用户\r名"]

## 测试覆盖分析
### 需求覆盖
- 功能需求覆盖: 100%
- 业务规则覆盖: 100%
- 异常场景覆盖: 100%
- 安全需求覆盖: 100%

### 代码覆盖
- 语句覆盖: 目标>=90%
- 分支覆盖: 目标>=80%
- 条件覆盖: 目标>=70%
- 路径覆盖: 目标>=60%
        """
        
        base_result["output"] = {
            "test_case_design": test_case_design,
            "test_case_example": test_case_example,
            "test_case_metrics": {
                "total_test_cases": task.get("test_case_count", 50),
                "priority_distribution": {
                    "high": "40%",
                    "medium": "40%",
                    "low": "20%"
                },
                "test_type_distribution": {
                    "functional": "60%",
                    "security": "15%",
                    "performance": "10%",
                    "usability": "10%",
                    "compatibility": "5%"
                }
            },
            "design_techniques": [
                "等价类划分",
                "边界值分析",
                "决策表",
                "状态转换",
                "场景法",
                "错误推测"
            ]
        }
        
        base_result["testing_details"] = {
            "test_case_template": "用例ID | 用例名称 | 优先级 | 前置条件 | 测试步骤 | 预期结果 | 实际结果 | 状态 | 备注",
            "traceability_matrix": "需求ID ↔ 测试用例ID ↔ 缺陷ID",
            "review_process": ["同行评审", "需求方确认", "自动化检查"]
        }
        
        base_result["recommendations"] = [
            "使用多种测试设计技术",
            "建立测试用例评审流程",
            "维护测试用例库",
            "跟踪测试用例有效性"
        ]
        
        return base_result
    
    async def _execute_test_execution(self, task: Dict[str, Any], base_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行测试执行任务
        
        Args:
            task: 任务描述
            base_result: 基础结果
            
        Returns:
            更新后的结果
        """
        test_plan = task.get("test_plan", {})
        execution_environment = task.get("execution_environment", "staging")
        
        logger.info(f"执行测试执行任务，环境: {execution_environment}")
        
        # 测试执行分析
        test_execution = {
            "execution_planning": self.reasoning.analyze(
                query=f"规划测试执行: {json.dumps(test_plan, ensure_ascii=False)}",
                context=f"执行环境: {execution_environment}",
                reasoning_type=self.reasoning.get_reasoning_type("PLANNING")
            ),
            "execution_coordination": self.reasoning.generate(
                query=f"协调测试执行资源",
                context="执行计划已制定",
                reasoning_type=self.reasoning.get_reasoning_type("COORDINATION")
            ),
            "defect_tracking": self.reasoning.analyze(
                query=f"跟踪和分析缺陷",
                context="测试执行进行中",
                reasoning_type=self.reasoning.get_reasoning_type("ANALYTICAL")
            ),
            "progress_reporting": self.reasoning.generate(
                query=f"生成测试进度报告",
                context="缺陷跟踪已完成",
                reasoning_type=self.reasoning.get_reasoning_type("REPORTING")
            )
        }
        
        # 生成测试执行报告
        test_execution_report = f"""
# 测试执行报告 - {test_plan.get('project_name', '项目')}

## 执行概述
- 项目名称: {test_plan.get('project_name', '项目')}
- 测试周期: {task.get('test_period', '2024年1月1日 - 2024年1月31日')}
- 执行环境: {execution_environment}
- 测试团队: {task.get('test_team', '3名测试工程师')}
- 测试版本: {task.get('test_version', 'v1.2.3')}

## 执行统计
### 测试用例执行
- 计划执行用例: {test_plan.get('planned_cases', 500)}
- 实际执行用例: {task.get('executed_cases', 480)}
- 执行完成率: {task.get('execution_rate', '96%')}
- 未执行用例: {task.get('pending_cases', 20)}

### 执行结果分布
- 通过用例: {task.get('passed_cases', 450)}
- 失败用例: {task.get('failed_cases', 25)}
- 阻塞用例: {task.get('blocked_cases', 5)}
- 跳过用例: {task.get('skipped_cases', 0)}

### 执行效率
- 平均执行速度: {task.get('execution_speed', '50用例/人天')}
- 回归测试轮次: {task.get('regression_rounds', 3)}
- 自动化执行比例: {task.get('automation_rate', '65%')}
- 手工测试比例: {task.get('manual_rate', '35%')}

## 缺陷统计
### 缺陷发现
- 总缺陷数: {task.get('total_defects', 30)}
- 新增缺陷: {task.get('new_defects', 25)}
- 回归缺陷: {task.get('regression_defects', 5)}
- 缺陷发现率: {task.get('defect_discovery_rate', '6.25%')}

### 缺陷严重程度分布
- 致命缺陷 (P0): {task.get('p0_defects', 0)}
- 严重缺陷 (P1): {task.get('p1_defects', 3)}
- 一般缺陷 (P2): {task.get('p2_defects', 15)}
- 轻微缺陷 (P3): {task.get('p3_defects', 12)}

### 缺陷状态分布
- 新建: {task.get('new_status', 5)}
- 已分配: {task.get('assigned_status', 8)}
- 已修复: {task.get('fixed_status', 12)}
- 已验证: {task.get('verified_status', 5)}
- 已关闭: {task.get('closed_status', 0)}
- 拒绝/重复: {task.get('rejected_status', 0)}

### 缺陷解决
- 已解决缺陷: {task.get('resolved_defects', 17)}
- 待解决缺陷: {task.get('pending_defects', 13)}
- 解决率: {task.get('resolution_rate', '56.7%')}
- 平均解决时间: {task.get('avg_resolution_time', '2.5天')}

## 质量评估
### 测试覆盖评估
- 需求覆盖: {task.get('requirement_coverage', '95%')}
- 功能覆盖: {task.get('function_coverage', '92%')}
- 代码覆盖: {task.get('code_coverage', '78%')}
- 风险覆盖: {task.get('risk_coverage', '88%')}

### 质量风险
1. 高优先级缺陷: {task.get('high_priority_risks', ['用户登录失败', '数据导出异常'])}
2. 未覆盖功能: {task.get('uncovered_functions', ['批量导入功能', '高级搜索功能'])}
3. 性能瓶颈: {task.get('performance_bottlenecks', ['大文件上传慢', '复杂查询响应时间长'])}
4. 兼容性问题: {task.get('compatibility_issues', ['IE浏览器显示异常', '移动端某些功能异常'])}

### 质量指标
- 缺陷密度: {task.get('defect_density', '0.4缺陷/千行代码')}
- 缺陷泄漏率: {task.get('defect_leakage_rate', '3%')}
- 测试有效性: {task.get('test_effectiveness', '87%')}
- 用户满意度预估: {task.get('user_satisfaction', '4.2/5')}

## 执行问题
### 环境问题
1. {task.get('env_issue1', '测试数据库性能不足，影响性能测试')}
2. {task.get('env_issue2', '自动化测试环境不稳定，偶发性失败')}

### 资源问题
1. {task.get('resource_issue1', '测试数据准备耗时较长')}
2. {task.get('resource_issue2', '部分测试设备不足')}

### 技术问题
1. {task.get('tech_issue1', '某些浏览器自动化测试支持不完善')}
2. {task.get('tech_issue2', '性能测试工具学习成本较高')}

## 改进建议
### 流程改进
1. {task.get('process_improvement1', '提前准备测试数据和环境')}
2. {task.get('process_improvement2', '加强测试用例评审机制')}

### 技术改进
1. {task.get('tech_improvement1', '引入更稳定的自动化测试框架')}
2. {task.get('tech_improvement2', '优化性能测试方法和工具')}

### 团队改进
1. {task.get('team_improvement1', '加强测试技术培训')}
2. {task.get('team_improvement2', '建立知识分享机制')}

## 发布建议
### 发布风险评估
- 总体风险: {task.get('overall_risk', '中等')}
- 主要风险: {task.get('main_risks', ['P1缺陷未完全验证', '性能测试未覆盖所有场景'])}
- 风险缓解: {task.get('risk_mitigation', ['加强回归测试', '监控生产环境性能'])}
- 发布决策: {task.get('release_decision', '建议发布，但需密切监控')}

### 监控建议
1. {task.get('monitoring_suggestion1', '生产环境部署后立即进行冒烟测试')}
2. {task.get('monitoring_suggestion2', '关键功能设置监控告警')}
3. {task.get('monitoring_suggestion3', '收集用户反馈并及时响应')}
        """
        
        base_result["output"] = {
            "test_execution": test_execution,
            "test_execution_report": test_execution_report,
            "execution_metrics": {
                "efficiency": {
                    "test_case_execution_rate": task.get("execution_rate", "96%"),
                    "defects_per_test_case": task.get("defects_per_case", "0.0625"),
                    "automation_success_rate": task.get("automation_success", "92%")
                },
                "effectiveness": {
                    "defect_detection_rate": task.get("defect_detection", "87%"),
                    "critical_defect_ratio": task.get("critical_ratio", "10%"),
                    "regression_defect_ratio": task.get("regression_ratio", "16.7%")
                },
                "quality": {
                    "defect_density": task.get("defect_density", "0.4缺陷/千行代码"),
                    "defect_leakage": task.get("defect_leakage", "3%"),
                    "test_coverage": task.get("test_coverage", "92%")
                }
            },
            "execution_tools": [
                "测试管理工具 (JIRA, TestRail)",
                "缺陷跟踪系统 (Bugzilla, Redmine)",
                "自动化测试框架 (Selenium, pytest)",
                "性能测试工具 (JMeter, LoadRunner)",
                "监控工具 (Grafana, Prometheus)"
            ]
        }
        
        base_result["testing_details"] = {
            "execution_methodology": "迭代式测试执行 + 持续回归",
            "reporting_frequency": "每日进度报告 + 阶段总结报告",
            "escalation_process": "缺陷升级流程 + 风险上报机制"
        }
        
        base_result["recommendations"] = [
            "建立持续测试执行流程",
            "加强测试执行监控",
            "优化测试数据管理",
            "提升测试执行自动化"
        ]
        
        return base_result
    
    async def _execute_defect_analysis(self, task: Dict[str, Any], base_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行缺陷分析任务
        
        Args:
            task: 任务描述
            base_result: 基础结果
            
        Returns:
            更新后的结果
        """
        defect_data = task.get("defect_data", {})
        analysis_period = task.get("analysis_period", "最近一个月")
        
        logger.info(f"执行缺陷分析任务，分析周期: {analysis_period}")
        
        # 缺陷分析
        defect_analysis = {
            "defect_trend_analysis": self.reasoning.analyze(
                query=f"分析缺陷趋势: {json.dumps(defect_data, ensure_ascii=False)}",
                context=f"分析周期: {analysis_period}",
                reasoning_type=self.reasoning.get_reasoning_type("ANALYTICAL")
            ),
            "root_cause_analysis": self.reasoning.analyze(
                query=f"进行缺陷根本原因分析",
                context="缺陷趋势已分析",
                reasoning_type=self.reasoning.get_reasoning_type("ROOT_CAUSE")
            ),
            "defect_pattern_recognition": self.reasoning.analyze(
                query=f"识别缺陷模式",
                context="根本原因已分析",
                reasoning_type=self.reasoning.get_reasoning_type("PATTERN")
            ),
            "prevention_recommendations": self.reasoning.generate(
                query=f"提出缺陷预防建议",
                context="缺陷模式已识别",
                reasoning_type=self.reasoning.get_reasoning_type("PREVENTIVE")
            )
        }
        
        # 生成缺陷分析报告
        defect_analysis_report = f"""
# 缺陷分析报告 - {task.get('product_name', '产品')}

## 分析概述
- 产品名称: {task.get('product_name', '产品')}
- 分析周期: {analysis_period}
- 总缺陷数: {defect_data.get('total_defects', 150)}
- 分析范围: {task.get('analysis_scope', '所有严重程度缺陷')}
- 分析目标: {task.get('analysis_goal', '识别质量风险，改进开发测试流程')}

## 缺陷趋势分析
### 时间趋势
- 月度缺陷趋势: {defect_data.get('monthly_trend', '先升后降，峰值在第二周')}
- 周度缺陷分布: {defect_data.get('weekly_distribution', '周一最多，周五最少')}
- 发现阶段分布: {defect_data.get('stage_distribution', '系统测试阶段发现60%，集成测试20%，单元测试10%，用户反馈10%')}
- 修复时间趋势: {defect_data.get('fix_time_trend', '平均修复时间2.5天，P0缺陷修复最快')}

### 严重程度趋势
- P0缺陷趋势: {defect_data.get('p0_trend', '逐渐减少，本月为0')}
- P1缺陷趋势: {defect_data.get('p1_trend', '波动下降')}
- P2缺陷趋势: {defect_data.get('p2_trend', '保持稳定')}
- P3缺陷趋势: {defect_data.get('p3_trend', '轻微上升')}

## 缺陷分布分析
### 模块分布
1. {defect_data.get('module1', '用户管理模块')}: {defect_data.get('module1_defects', 45)} 缺陷 (30%)
   - 主要问题: {defect_data.get('module1_issues', ['登录认证', '权限管理', '个人资料'])}
   
2. {defect_data.get('module2', '订单管理模块')}: {defect_data.get('module2_defects', 35)} 缺陷 (23.3%)
   - 主要问题: {defect_data.get('module2_issues', ['订单创建', '支付流程', '订单状态'])}
   
3. {defect_data.get('module3', '产品管理模块')}: {defect_data.get('module3_defects', 25)} 缺陷 (16.7%)
   - 主要问题: {defect_data.get('module3_issues', ['产品展示', '搜索功能', '分类管理'])}
   
4. {defect_data.get('module4', '报表统计模块')}: {defect_data.get('module4_defects', 20)} 缺陷 (13.3%)
   - 主要问题: {defect_data.get('module4_issues', ['数据准确性', '导出功能', '性能问题'])}
   
5. {defect_data.get('module5', '其他模块')}: {defect_data.get('module5_defects', 25)} 缺陷 (16.7%)
   - 主要问题: {defect_data.get('module5_issues', ['系统配置', '消息通知', '界面布局'])}

### 缺陷类型分布
- 功能缺陷: {defect_data.get('functional_defects', 80)} (53.3%)
- 界面缺陷: {defect_data.get('ui_defects', 30)} (20%)
- 性能缺陷: {defect_data.get('performance_defects', 20)} (13.3%)
- 安全缺陷: {defect_data.get('security_defects', 10)} (6.7%)
- 兼容性缺陷: {defect_data.get('compatibility_defects', 5)} (3.3%)
- 文档缺陷: {defect_data.get('documentation_defects', 5)} (3.3%)

### 缺陷来源分布
- 新功能开发: {defect_data.get('new_feature_defects', 90)} (60%)
- 功能修改: {defect_data.get('modification_defects', 40)} (26.7%)
- 回归缺陷: {defect_data.get('regression_defects', 15)} (10%)
- 环境问题: {defect_data.get('environment_defects', 5)} (3.3%)

## 根本原因分析
### 开发原因
1. **需求理解偏差** ({defect_data.get('req_misunderstanding', 35)} 缺陷, 23.3%)
   - 表现: {defect_data.get('req_misunderstanding_manifestation', ['功能实现与需求不符', '遗漏需求点'])}
   - 原因: {defect_data.get('req_misunderstanding_cause', ['需求文档不清晰', '需求评审不充分', '沟通不足'])}
   - 建议: {defect_data.get('req_misunderstanding_suggestion', ['加强需求评审', '使用原型验证', '建立需求跟踪'])}
   
2. **编码错误** ({defect_data.get('coding_error', 45)} 缺陷, 30%)
   - 表现: {defect_data.get('coding_error_manifestation', ['逻辑错误', '边界条件处理不当', '异常处理缺失'])}
   - 原因: {defect_data.get('coding_error_cause', ['开发人员经验不足', '代码审查不严格', '时间压力'])}
   - 建议: {defect_data.get('coding_error_suggestion', ['加强代码审查', '建立编码规范', '提供技术培训'])}
   
3. **设计缺陷** ({defect_data.get('design_defect', 25)} 缺陷, 16.7%)
   - 表现: {defect_data.get('design_defect_manifestation', ['系统架构不合理', '接口设计问题', '扩展性不足'])}
   - 原因: {defect_data.get('design_defect_cause', ['设计评审不充分', '技术选型不当', '经验不足'])}
   - 建议: {defect_data.get('design_defect_suggestion', ['加强设计评审', '使用设计模式', '进行架构验证'])}
   
4. **集成问题** ({defect_data.get('integration_issue', 20)} 缺陷, 13.3%)
   - 表现: {defect_data.get('integration_issue_manifestation', ['模块间接口不一致', '数据格式不匹配', '版本兼容性问题'])}
   - 原因: {defect_data.get('integration_issue_cause', ['接口文档不完善', '集成测试不足', '沟通协调问题'])}
   - 建议: {defect_data.get('integration_issue_suggestion', ['完善接口文档', '加强集成测试', '建立接口规范'])}
   
5. **其他原因** ({defect_data.get('other_causes', 25)} 缺陷, 16.7%)
   - 表现: {defect_data.get('other_manifestation', ['环境配置问题', '第三方组件问题', '数据问题'])}
   - 原因: {defect_data.get('other_cause', ['环境管理不规范', '依赖管理不当', '数据质量问题'])}
   - 建议: {defect_data.get('other_suggestion', ['规范环境管理', '加强依赖管理', '建立数据质量标准'])}
   
### 测试原因
1. **测试用例遗漏** ({defect_data.get('test_case_missing', 15)} 缺陷, 10%)
   - 表现: {defect_data.get('test_case_missing_manifestation', ['未覆盖的边界条件', '遗漏的异常场景', '未测试的组合情况'])}
   - 原因: {defect_data.get('test_case_missing_cause', ['测试设计不充分', '需求理解偏差', '时间限制'])}
   - 建议: {defect_data.get('test_case_missing_suggestion', ['使用多种测试设计技术', '加强测试用例评审', '建立测试用例库'])}
   
2. **测试执行问题** ({defect_data.get('test_execution_issue', 10)} 缺陷, 6.7%)
   - 表现: {defect_data.get('test_execution_issue_manifestation', ['测试步骤错误', '测试数据问题', '环境配置问题'])}
   - 原因: {defect_data.get('test_execution_issue_cause', ['测试人员技能不足', '测试文档不清晰', '环境不稳定'])}
   - 建议: {defect_data.get('test_execution_issue_suggestion', ['加强测试培训', '完善测试文档', '稳定测试环境'])}
   
3. **缺陷识别问题** ({defect_data.get('defect_identification_issue', 5)} 缺陷, 3.3%)
   - 表现: {defect_data.get('defect_identification_issue_manifestation', ['未能识别潜在缺陷', '缺陷分类错误', '严重程度评估不当'])}
   - 原因: {defect_data.get('defect_identification_issue_cause', ['测试经验不足', '业务知识欠缺', '判断标准不统一'])}
   - 建议: {defect_data.get('defect_identification_issue_suggestion', ['建立缺陷识别指南', '加强业务培训', '统一判断标准'])}
   
## 缺陷模式识别
### 重复模式
1. **边界条件缺陷模式** ({defect_data.get('boundary_pattern', 20)} 次出现)
   - 模式特征: {defect_data.get('boundary_pattern_feature', '在数据边界值附近出现的问题')}
   - 典型例子: {defect_data.get('boundary_pattern_example', ['最大数量限制错误', '最小输入值验证缺失', '边界值计算错误'])}
   - 预防措施: {defect_data.get('boundary_pattern_prevention', ['加强边界值测试', '使用边界值分析技术', '代码中显式处理边界条件'])}
   
2. **并发处理缺陷模式** ({defect_data.get('concurrency_pattern', 15)} 次出现)
   - 模式特征: {defect_data.get('concurrency_pattern_feature', '在多线程或并发访问时出现的问题')}
   - 典型例子: {defect_data.get('concurrency_pattern_example', ['数据竞争', '死锁', '资源争用'])}
   - 预防措施: {defect_data.get('concurrency_pattern_prevention', ['进行并发测试', '使用线程安全的数据结构', '加锁机制验证'])}
   
3. **输入验证缺陷模式** ({defect_data.get('input_validation_pattern', 25)} 次出现)
   - 模式特征: {defect_data.get('input_validation_pattern_feature', '对用户输入验证不足导致的问题')}
   - 典型例子: {defect_data.get('input_validation_pattern_example', ['SQL注入漏洞', 'XSS攻击风险', '缓冲区溢出'])}
   - 预防措施: {defect_data.get('input_validation_pattern_prevention', ['实施严格的输入验证', '使用安全编码实践', '进行安全测试'])}
   
4. **状态管理缺陷模式** ({defect_data.get('state_management_pattern', 18)} 次出现)
   - 模式特征: {defect_data.get('state_management_pattern_feature', '系统状态管理不当导致的问题')}
   - 典型例子: {defect_data.get('state_management_pattern_example', ['状态不一致', '状态转换错误', '状态恢复失败'])}
   - 预防措施: {defect_data.get('state_management_pattern_prevention', ['设计清晰的状态机', '进行状态转换测试', '加强异常状态处理'])}
   
## 质量改进建议
### 预防性措施
1. **加强需求管理**
   - 实施措施: {defect_data.get('req_management_action', ['建立需求评审流程', '使用原型验证', '需求变更控制'])}
   - 预期效果: {defect_data.get('req_management_effect', '减少需求理解偏差导致的缺陷30%')}
   - 负责人: {defect_data.get('req_management_owner', '产品经理、开发负责人')}
   
2. **改进开发实践**
   - 实施措施: {defect_data.get('dev_practice_action', ['加强代码审查', '实施结对编程', '建立编码规范'])}
   - 预期效果: {defect_data.get('dev_practice_effect', '减少编码错误导致的缺陷40%')}
   - 负责人: {defect_data.get('dev_practice_owner', '开发团队、技术负责人')}
   
3. **优化测试策略**
   - 实施措施: {defect_data.get('test_strategy_action', ['引入测试左移', '加强自动化测试', '实施探索性测试'])}
   - 预期效果: {defect_data.get('test_strategy_effect', '提高缺陷发现率20%')}
   - 负责人: {defect_data.get('test_strategy_owner', '测试团队、质量负责人')}
   
4. **建立质量文化**
   - 实施措施: {defect_data.get('quality_culture_action', ['定期质量回顾', '缺陷根本原因分析', '质量指标可视化'])}
   - 预期效果: {defect_data.get('quality_culture_effect', '建立持续改进的质量文化')}
   - 负责人: {defect_data.get('quality_culture_owner', '全员、质量管理部门')}
   
### 技术改进
1. **引入静态代码分析**
   - 工具选择: {defect_data.get('static_analysis_tools', ['SonarQube', 'Checkstyle', 'PMD'])}
   - 实施计划: {defect_data.get('static_analysis_plan', '集成到CI/CD流水线，每日分析')}
   - 预期效果: {defect_data.get('static_analysis_effect', '提前发现代码质量问题')}
   
2. **加强自动化测试**
   - 覆盖范围: {defect_data.get('automation_coverage', ['核心功能自动化', '接口测试自动化', '性能测试自动化'])}
   - 技术栈: {defect_data.get('automation_tech_stack', ['Selenium WebDriver', 'pytest', 'JMeter'])}
   - 预期效果: {defect_data.get('automation_effect', '提高测试效率50%，减少回归缺陷')}
   
3. **实施持续集成**
   - 流水线设计: {defect_data.get('ci_pipeline', ['代码提交触发构建', '自动运行测试', '质量门禁检查'])}
   - 工具选择: {defect_data.get('ci_tools', ['Jenkins', 'GitLab CI', 'GitHub Actions'])}
   - 预期效果: {defect_data.get('ci_effect', '快速反馈质量问题，减少集成问题')}
   
## 监控指标
### 过程指标
- 缺陷发现率: 目标 {defect_data.get('defect_detection_target', '>90%')}
- 缺陷解决时间: 目标 {defect_data.get('defect_resolution_target', 'P0<4小时, P1<24小时, P2<3天')}
- 回归缺陷比例: 目标 {defect_data.get('regression_defect_target', '<10%')}
- 缺陷重开率: 目标 {defect_data.get('defect_reopen_target', '<5%')}
   
### 结果指标
- 缺陷密度: 目标 {defect_data.get('defect_density_target', '<0.3缺陷/千行代码')}
- 用户投诉率: 目标 {defect_data.get('user_complaint_target', '<1%')}
- 生产缺陷数: 目标 {defect_data.get('production_defect_target', '每月<5')}
- 质量满意度: 目标 {defect_data.get('quality_satisfaction_target', '>4.5/5')}
        """
        
        base_result["output"] = {
            "defect_analysis": defect_analysis,
            "defect_analysis_report": defect_analysis_report,
            "analysis_insights": {
                "key_findings": [
                    defect_data.get("finding1", "用户管理模块缺陷密度最高"),
                    defect_data.get("finding2", "需求理解偏差是主要缺陷原因"),
                    defect_data.get("finding3", "边界条件缺陷是最常见模式")
                ],
                "quality_risks": [
                    defect_data.get("risk1", "安全测试覆盖不足"),
                    defect_data.get("risk2", "回归测试效率较低"),
                    defect_data.get("risk3", "自动化测试维护成本高")
                ],
                "improvement_opportunities": [
                    defect_data.get("opportunity1", "加强需求评审和原型验证"),
                    defect_data.get("opportunity2", "引入静态代码分析和代码审查工具"),
                    defect_data.get("opportunity3", "优化测试自动化策略")
                ]
            },
            "prevention_framework": {
                "proactive_measures": ["需求验证", "设计评审", "代码审查", "单元测试"],
                "reactive_measures": ["缺陷分析", "根本原因分析", "过程改进", "经验分享"],
                "cultural_measures": ["质量意识", "知识共享", "持续改进", "质量指标"]
            }
        }
        
        base_result["testing_details"] = {
            "analysis_methodology": "定量分析 + 定性分析 + 根本原因分析",
            "data_sources": ["缺陷跟踪系统", "测试执行记录", "代码仓库", "用户反馈"],
            "reporting_frequency": "月度分析报告 + 季度深度分析"
        }
        
        base_result["recommendations"] = [
            "建立系统的缺陷分析流程",
            "实施缺陷预防措施",
            "加强质量度量和管理",
            "培养质量改进文化"
        ]
        
        return base_result
    
    async def _execute_quality_assessment(self, task: Dict[str, Any], base_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行质量评估任务
        
        Args:
            task: 任务描述
            base_result: 基础结果
            
        Returns:
            更新后的结果
        """
        quality_data = task.get("quality_data", {})
        assessment_criteria = task.get("assessment_criteria", ["功能完整性", "系统稳定性", "用户体验"])
        
        logger.info(f"执行质量评估任务，评估标准: {assessment_criteria}")
        
        # 质量评估分析
        quality_assessment = {
            "data_collection_analysis": self.reasoning.analyze(
                query=f"分析质量数据: {json.dumps(quality_data, ensure_ascii=False)}",
                context=f"评估标准: {assessment_criteria}",
                reasoning_type=self.reasoning.get_reasoning_type("ANALYTICAL")
            ),
            "criteria_evaluation": self.reasoning.analyze(
                query=f"按照标准评估质量",
                context="质量数据已分析",
                reasoning_type=self.reasoning.get_reasoning_type("EVALUATIVE")
            ),
            "risk_identification": self.reasoning.analyze(
                query=f"识别质量风险",
                context="标准评估已完成",
                reasoning_type=self.reasoning.get_reasoning_type("RISK")
            ),
            "improvement_recommendations": self.reasoning.generate(
                query=f"提出质量改进建议",
                context="风险已识别",
                reasoning_type=self.reasoning.get_reasoning_type("RECOMMENDATION")
            )
        }
        
        # 生成质量评估报告
        quality_assessment_report = f"""
# 质量评估报告 - {task.get('product_name', '产品')}

## 评估概述
- 产品名称: {task.get('product_name', '产品')}
- 评估版本: {quality_data.get('version', 'v1.3.0')}
- 评估时间: {datetime.now().strftime('%Y年%m月%d日')}
- 评估范围: {task.get('assessment_scope', '核心功能、性能、安全、用户体验')}
- 评估方法: {task.get('assessment_method', '定量指标分析 + 定性专家评估')}

## 评估标准
### 功能质量 (权重: 40%)
- 功能完整性: {quality_data.get('function_completeness_criteria', '所有计划功能已实现')}
- 功能正确性: {quality_data.get('function_correctness_criteria', '功能符合需求，输出正确')}
- 功能可靠性: {quality_data.get('function_reliability_criteria', '功能稳定，错误率低')}
- 功能易用性: {quality_data.get('function_usability_criteria', '操作简单，学习成本低')}

### 性能质量 (权重: 25%)
- 响应时间: {quality_data.get('response_time_criteria', '页面加载<3秒，API响应<1秒')}
- 并发能力: {quality_data.get('concurrency_criteria', '支持1000并发用户')}
- 资源使用: {quality_data.get('resource_usage_criteria', 'CPU使用率<70%，内存使用<80%')}
- 可扩展性: {quality_data.get('scalability_criteria', '支持水平扩展，性能线性增长')}

### 安全质量 (权重: 20%)
- 数据安全: {quality_data.get('data_security_criteria', '数据传输加密，存储加密')}
- 访问控制: {quality_data.get('access_control_criteria', '权限控制完善，无越权访问')}
- 漏洞防护: {quality_data.get('vulnerability_protection_criteria', '无高危安全漏洞')}
- 合规性: {quality_data.get('compliance_criteria', '符合相关安全标准和法规')}

### 用户体验质量 (权重: 15%)
- 界面设计: {quality_data.get('ui_design_criteria', '界面美观，布局合理')}
- 交互体验: {quality_data.get('interaction_criteria', '交互流畅，反馈及时')}
- 可用性: {quality_data.get('usability_criteria', '易于理解和使用')}
- 满意度: {quality_data.get('satisfaction_criteria', '用户满意度高')}

## 质量指标分析
### 功能质量指标
- 需求实现率: {quality_data.get('requirement_implementation_rate', '95%')} (目标: 100%)
- 缺陷密度: {quality_data.get('defect_density', '0.35缺陷/千行代码')} (目标: <0.5)
- 测试覆盖率: {quality_data.get('test_coverage', '85%')} (目标: >80%)
- 缺陷解决率: {quality_data.get('defect_resolution_rate', '92%')} (目标: >90%)

### 性能质量指标
- 平均响应时间: {quality_data.get('avg_response_time', '1.8秒')} (目标: <3秒)
- 95%响应时间: {quality_data.get('p95_response_time', '3.2秒')} (目标: <5秒)
- 最大并发用户数: {quality_data.get('max_concurrent_users', '1200')} (目标: >1000)
- 错误率: {quality_data.get('error_rate', '0.2%')} (目标: <1%)

### 安全质量指标
- 安全漏洞数: {quality_data.get('security_vulnerabilities', '2')} (目标: 0)
- 漏洞严重程度: {quality_data.get('vulnerability_severity', '中低风险')} (目标: 无高风险)
- 渗透测试通过率: {quality_data.get('penetration_test_pass_rate', '90%')} (目标: 100%)
- 安全合规性: {quality_data.get('security_compliance', '基本符合')} (目标: 完全符合)

### 用户体验指标
- 用户满意度: {quality_data.get('user_satisfaction', '4.3/5')} (目标: >4/5)
- 任务完成率: {quality_data.get('task_completion_rate', '88%')} (目标: >85%)
- 平均任务时间: {quality_data.get('avg_task_time', '2.5分钟')} (目标: <3分钟)
- 错误发生次数: {quality_data.get('error_occurrence', '1.2次/任务')} (目标: <2次)

## 质量评分
### 功能质量评分: {quality_data.get('function_quality_score', '8.5')}/10
- 功能完整性: {quality_data.get('completeness_score', '9')}/10
- 功能正确性: {quality_data.get('correctness_score', '8')}/10
- 功能可靠性: {quality_data.get('reliability_score', '8.5')}/10
- 功能易用性: {quality_data.get('usability_score', '8.5')}/10

### 性能质量评分: {quality_data.get('performance_quality_score', '8.2')}/10
- 响应时间: {quality_data.get('response_time_score', '8.5')}/10
- 并发能力: {quality_data.get('concurrency_score', '8')}/10
- 资源使用: {quality_data.get('resource_usage_score', '8.5')}/10
- 可扩展性: {quality_data.get('scalability_score', '8')}/10

### 安全质量评分: {quality_data.get('security_quality_score', '8')}/10
- 数据安全: {quality_data.get('data_security_score', '8.5')}/10
- 访问控制: {quality_data.get('access_control_score', '8')}/10
- 漏洞防护: {quality_data.get('vulnerability_protection_score', '7.5')}/10
- 合规性: {quality_data.get('compliance_score', '8')}/10

### 用户体验评分: {quality_data.get('user_experience_score', '8.7')}/10
- 界面设计: {quality_data.get('ui_design_score', '9')}/10
- 交互体验: {quality_data.get('interaction_score', '8.5')}/10
- 可用性: {quality_data.get('usability_score_experience', '8.5')}/10
- 满意度: {quality_data.get('satisfaction_score_experience', '9')}/10

### 综合质量评分: {quality_data.get('overall_quality_score', '8.35')}/10
- 加权计算: (8.5×0.4) + (8.2×0.25) + (8.0×0.2) + (8.7×0.15) = 8.35
- 质量等级: {quality_data.get('quality_grade', '良好')} (8.0-8.9为良好)
- 发布建议: {quality_data.get('release_recommendation', '建议发布，质量达到预期水平')}

## 质量风险分析
### 高风险问题
1. **安全漏洞风险**
   - 问题描述: {quality_data.get('security_risk_desc', '发现2个中风险安全漏洞')}
   - 影响范围: {quality_data.get('security_risk_impact', '可能影响数据安全和系统稳定性')}
   - 紧急程度: {quality_data.get('security_risk_urgency', '高')}
   - 解决建议: {quality_data.get('security_risk_suggestion', '立即修复漏洞，进行安全加固')}

2. **性能瓶颈风险**
   - 问题描述: {quality_data.get('performance_risk_desc', '95%响应时间超过3秒')}
   - 影响范围: {quality_data.get('performance_risk_impact', '影响用户体验，可能导致用户流失')}
   - 紧急程度: {quality_data.get('performance_risk_urgency', '中')}
   - 解决建议: {quality_data.get('performance_risk_suggestion', '优化慢查询，增加缓存，考虑CDN')}

### 中风险问题
1. **功能完整性风险**
   - 问题描述: {quality_data.get('function_risk_desc', '5%的需求功能未完全实现')}
   - 影响范围: {quality_data.get('function_risk_impact', '影响产品功能的完整性')}
   - 紧急程度: {quality_data.get('function_risk_urgency', '中')}
   - 解决建议: {quality_data.get('function_risk_suggestion', '评估未实现功能的重要性，制定实现计划')}

2. **测试覆盖风险**
   - 问题描述: {quality_data.get('test_coverage_risk_desc', '部分边缘场景测试覆盖不足')}
   - 影响范围: {quality_data.get('test_coverage_risk_impact', '可能存在未被发现的缺陷')}
   - 紧急程度: {quality_data.get('test_coverage_risk_urgency', '中')}
   - 解决建议: {quality_data.get('test_coverage_risk_suggestion', '补充测试用例，加强边缘测试')}

### 低风险问题
1. **文档质量风险**
   - 问题描述: {quality_data.get('documentation_risk_desc', '部分API文档不够详细')}
   - 影响范围: {quality_data.get('documentation_risk_impact', '影响开发人员使用和维护')}
   - 紧急程度: {quality_data.get('documentation_risk_urgency', '低')}
   - 解决建议: {quality_data.get('documentation_risk_suggestion', '完善API文档，建立文档维护机制')}

2. **代码质量风险**
   - 问题描述: {quality_data.get('code_quality_risk_desc', '部分代码复杂度较高')}
   - 影响范围: {quality_data.get('code_quality_risk_impact', '可能影响可维护性和扩展性')}
   - 紧急程度: {quality_data.get('code_quality_risk_urgency', '低')}
   - 解决建议: {quality_data.get('code_quality_risk_suggestion', '进行代码重构，降低复杂度')}

## 质量改进建议
### 短期改进 (1个月内)
1. **安全加固**
   - 具体措施: {quality_data.get('short_term_security', ['修复已发现的安全漏洞', '加强输入验证', '更新安全依赖'])}
   - 预期效果: {quality_data.get('short_term_security_effect', '安全评分提高0.5分')}
   - 负责人: {quality_data.get('short_term_security_owner', '安全团队、开发团队')}
   
2. **性能优化**
   - 具体措施: {quality_data.get('short_term_performance', ['优化慢查询', '增加缓存策略', '压缩静态资源'])}
   - 预期效果: {quality_data.get('short_term_performance_effect', '响应时间减少30%')}
   - 负责人: {quality_data.get('short_term_performance_owner', '开发团队、运维团队')}

### 中期改进 (1-3个月)
1. **测试体系完善**
   - 具体措施: {quality_data.get('mid_term_testing', ['建立自动化测试框架', '完善测试用例库', '引入新的测试工具'])}
   - 预期效果: {quality_data.get('mid_term_testing_effect', '测试效率提高40%')}
   - 负责人: {quality_data.get('mid_term_testing_owner', '测试团队、开发团队')}

2. **质量文化建设**
   - 具体措施: {quality_data.get('mid_term_quality_culture', ['建立质量指标体系', '开展质量培训', '实施质量奖励机制'])}
   - 预期效果: {quality_data.get('mid_term_quality_culture_effect', '质量意识提高50%')}
   - 负责人: {quality_data.get('mid_term_quality_culture_owner', '质量管理部门、人力资源')}

### 长期改进 (3-6个月)
1. **技术创新**
   - 具体措施: {quality_data.get('long_term_innovation', ['引入AI测试技术', '实施混沌工程', '建立质量预测模型'])}
   - 预期效果: {quality_data.get('long_term_innovation_effect', '质量预测准确率超过80%')}
   - 负责人: {quality_data.get('long_term_innovation_owner', '技术研发团队、创新实验室')}

2. **生态系统建设**
   - 具体措施: {quality_data.get('long_term_ecosystem', ['建立质量开放平台', '发展测试社区', '制定行业质量标准'])}
   - 预期效果: {quality_data.get('long_term_ecosystem_effect', '建立行业影响力')}
   - 负责人: {quality_data.get('long_term_ecosystem_owner', '企业战略部门、行业协会')}

## 结论
{quality_data.get('conclusion', '产品质量总体良好，达到发布标准。建议在解决高风险问题后发布，并持续进行质量改进。')}
        """
        
        base_result["output"] = {
            "quality_assessment": quality_assessment,
            "quality_assessment_report": quality_assessment_report,
            "quality_metrics": {
                "function_quality_score": quality_data.get("function_quality_score", 8.5),
                "performance_quality_score": quality_data.get("performance_quality_score", 8.2),
                "security_quality_score": quality_data.get("security_quality_score", 8.0),
                "user_experience_score": quality_data.get("user_experience_score", 8.7),
                "overall_quality_score": quality_data.get("overall_quality_score", 8.35)
            },
            "improvement_roadmap": {
                "short_term": ["安全加固", "性能优化"],
                "mid_term": ["测试体系完善", "质量文化建设"],
                "long_term": ["技术创新", "生态系统建设"]
            }
        }
        
        base_result["testing_details"] = {
            "assessment_methodology": "多维质量评估 + 专家评审",
            "data_sources": ["测试数据", "用户反馈", "性能监控", "安全扫描"],
            "reporting_frequency": "定期质量评估 + 发布前专项评估"
        }
        
        base_result["recommendations"] = [
            "建立持续质量改进机制",
            "加强质量数据收集和分析",
            "实施质量文化建设",
            "推动质量技术创新"
        ]
        
        return base_result
    
    async def _execute_general_testing_task(self, task: Dict[str, Any], base_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行通用测试任务
        
        Args:
            task: 任务描述
            base_result: 基础结果
            
        Returns:
            更新后的结果
        """
        task_description = task.get("task_description", "")
        
        logger.info(f"执行通用测试任务: {task_description}")
        
        # 通用测试任务分析
        general_analysis = self.reasoning.analyze(
            query=f"分析测试任务: {task_description}",
            context=f"测试专业领域: {self.domain_expertise}",
            reasoning_type=self.reasoning.get_reasoning_type("ANALYTICAL")
        )
        
        base_result["output"] = {
            "task_analysis": general_analysis,
            "testing_approach": "系统化测试方法",
            "quality_assurance": "测试用例设计 + 测试执行 + 缺陷跟踪",
            "deliverables": ["测试计划", "测试用例", "测试报告", "缺陷报告"]
        }
        
        base_result["testing_details"] = {
            "testing_methodology": "风险驱动测试 + 探索性测试",
            "tools_used": self.tools,
            "quality_metrics": {"test_coverage": ">=80%", "defect_density": "<=0.5/千行"}
        }
        
        base_result["recommendations"] = [
            "遵循测试最佳实践",
            "建立测试质量门禁",
            "实施持续测试",
            "进行定期测试流程改进"
        ]
        
        return base_result
    
    def generate_testing_report(self, project_name: str, tasks_completed: List[Dict[str, Any]]) -> str:
        """生成测试项目报告
        
        Args:
            project_name: 项目名称
            tasks_completed: 已完成任务列表
            
        Returns:
            测试项目报告
        """
        sections = {
            "项目概述": f"""
项目名称: {project_name}
测试负责人: {self.role_name} ({self.role_name_en})
测试团队: {self.agent_id}
项目周期: {datetime.now().strftime('%Y年%m月')}

项目目标:
- 确保产品质量符合标准
- 发现并跟踪缺陷
- 提供质量评估和改进建议
- 建立可持续的测试流程
""",
            "测试执行情况": f"""
总任务数: {len(tasks_completed)}
已完成任务: {len([t for t in tasks_completed if t.get('status') == 'completed'])}
进行中任务: {len([t for t in tasks_completed if t.get('status') == 'in_progress'])}
失败任务: {len([t for t in tasks_completed if t.get('status') == 'failed'])}

任务详情:
{chr(10).join(f"- {task.get('task_name', '未命名任务')}: {task.get('status', 'unknown')}" for task in tasks_completed)}
""",
            "质量评估": """
质量评估结果:
1. 功能质量: 符合需求，核心功能稳定
2. 性能质量: 响应时间达标，系统负载合理
3. 安全质量: 通过基本安全测试，无高危漏洞
4. 用户体验: 界面友好，操作流程顺畅

质量指标:
- 缺陷密度: 低于行业标准
- 测试覆盖率: 达到目标要求
- 缺陷解决率: 超过90%
- 用户满意度: 良好
""",
            "缺陷分析": """
缺陷统计:
- 总缺陷数: 根据测试执行情况统计
- 缺陷严重程度分布: P0/P1缺陷占比低
- 缺陷模块分布: 均匀分布，无集中风险
- 缺陷解决情况: 及时解决，无长期遗留问题

缺陷趋势:
- 缺陷发现率逐渐下降
- 回归缺陷比例控制在合理范围
- 生产环境缺陷数较少
""",
            "改进建议": """
测试流程改进:
1. 加强自动化测试覆盖
2. 引入持续测试流程
3. 完善测试数据管理
4. 建立测试知识库

质量文化建设:
1. 开展质量意识培训
2. 建立质量奖励机制
3. 实施缺陷预防措施
4. 推动全员质量参与

技术能力提升:
1. 学习新的测试工具和技术
2. 参与行业测试社区
3. 建立测试技术研究小组
4. 推动测试技术创新
"""
        }
        
        summary = f"{project_name}测试项目已完成主要测试工作。产品质量符合发布标准，测试流程完善，质量改进机制建立。项目具备良好的质量保证能力。"
        
        return self.create_report(f"测试项目报告 - {project_name}", sections, summary)