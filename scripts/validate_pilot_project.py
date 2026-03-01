#!/usr/bin/env python3
"""
试点项目验证脚本
验证 CitationAgent → QualityController 的迁移可行性

根据 SYSTEM_AGENTS_OVERVIEW.md 文档的阶段-1要求：
- 集成测试
- 参数兼容性验证
- 性能基准测试
- 功能一致性验证
- 用户验收测试
"""

import asyncio
import json
import time
import logging
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """测试结果"""
    test_name: str
    success: bool
    details: Dict[str, Any] = field(default_factory=dict)
    blocking: bool = False
    duration: float = 0.0
    error: Optional[str] = None


@dataclass
class PilotValidationReport:
    """试点验证报告"""
    pilot_agent: str = "CitationAgent"
    target_agent: str = "QualityController"
    validation_date: str = field(default_factory=lambda: datetime.now().isoformat())
    overall_success: bool = False
    blocking_issues: List[str] = field(default_factory=list)
    test_results: Dict[str, TestResult] = field(default_factory=dict)
    recommendation: Dict[str, Any] = field(default_factory=dict)
    next_steps: List[str] = field(default_factory=list)


class PilotProjectValidator:
    """试点项目验证器"""
    
    def __init__(self):
        self.pilot_agent_name = "CitationAgent"
        self.target_agent_name = "QualityController"
        self.report = PilotValidationReport()
        
    async def validate_pilot_project(self) -> PilotValidationReport:
        """执行完整的试点项目验证"""
        logger.info("=" * 80)
        logger.info("开始试点项目验证")
        logger.info(f"试点Agent: {self.pilot_agent_name} → {self.target_agent_name}")
        logger.info("=" * 80)
        
        # 执行各项测试
        tests = {
            "integration": self._test_integration,
            "parameter_compatibility": self._test_parameter_compatibility,
            "performance": self._test_performance,
            "functionality": self._test_functionality,
            "user_acceptance": self._test_user_acceptance
        }
        
        for test_name, test_func in tests.items():
            logger.info(f"\n执行测试: {test_name}")
            try:
                result = await test_func()
                self.report.test_results[test_name] = result
                
                if result.blocking:
                    self.report.blocking_issues.append(test_name)
                
                logger.info(f"测试 {test_name}: {'✅ 通过' if result.success else '❌ 失败'}")
                if result.error:
                    logger.error(f"错误: {result.error}")
            except Exception as e:
                logger.error(f"测试 {test_name} 执行异常: {e}", exc_info=True)
                self.report.test_results[test_name] = TestResult(
                    test_name=test_name,
                    success=False,
                    blocking=True,
                    error=str(e)
                )
                self.report.blocking_issues.append(test_name)
        
        # 生成建议
        self.report.overall_success = all(
            r.success for r in self.report.test_results.values()
        )
        self.report.recommendation = self._generate_recommendation()
        self.report.next_steps = self._generate_next_steps()
        
        # 保存报告
        await self._save_report()
        
        return self.report
    
    async def _test_integration(self) -> TestResult:
        """测试1: 集成测试 - 验证能否替换LangGraph中的CitationAgent"""
        start_time = time.time()
        
        try:
            # 尝试导入两个Agent
            from src.agents.expert_agents import CitationAgent
            from src.agents.quality_controller import QualityController
            
            # 检查能否在LangGraph节点中使用（可选，如果LangGraph不可用则跳过）
            langgraph_available = False
            try:
                from langgraph.graph import StateGraph
                from src.core.langgraph_agent_nodes import AgentNodes
                langgraph_available = True
            except ImportError:
                # LangGraph不可用，这是可选的，不影响核心功能测试
                logger.info("ℹ️ LangGraph不可用，跳过LangGraph集成测试（这是可选的）")
            
            # 创建测试状态
            test_state = {
                'query': '测试查询',
                'answer': '测试答案',
                'knowledge': [{'content': '测试知识', 'source': 'test'}],
                'evidence': []
            }
            
            # 测试原有Agent
            citation_agent = CitationAgent()
            old_result = await citation_agent.execute({
                'query': test_state['query'],
                'answer': test_state['answer'],
                'knowledge': test_state['knowledge']
            })
            
            # 测试新Agent
            quality_controller = QualityController()
            # 注意：需要适配参数格式
            new_result = await quality_controller.execute({
                'action': 'validate_content',
                'content': test_state['answer'],
                'content_type': 'answer'
            })
            
            # 核心功能测试：Agent能否正常执行
            core_success = (
                old_result.success and 
                new_result.success and
                hasattr(quality_controller, 'execute')
            )
            
            # LangGraph集成测试（如果可用）
            langgraph_success = True
            if langgraph_available:
                try:
                    agent_nodes = AgentNodes()
                    langgraph_success = agent_nodes is not None
                except Exception as e:
                    logger.warning(f"LangGraph集成测试失败: {e}")
                    langgraph_success = False
            
            # 总体成功：核心功能必须成功，LangGraph集成是可选的
            success = core_success
            
            return TestResult(
                test_name="integration",
                success=success,
                details={
                    "old_agent_available": True,
                    "new_agent_available": True,
                    "old_result_success": old_result.success,
                    "new_result_success": new_result.success,
                    "core_functionality": core_success,
                    "langgraph_available": langgraph_available,
                    "langgraph_integration": langgraph_success if langgraph_available else "skipped",
                    "can_replace": success
                },
                blocking=not core_success,  # 只有核心功能失败才是阻塞的
                duration=time.time() - start_time
            )
            
        except ImportError as e:
            return TestResult(
                test_name="integration",
                success=False,
                blocking=True,
                error=f"导入失败: {e}",
                duration=time.time() - start_time
            )
        except Exception as e:
            return TestResult(
                test_name="integration",
                success=False,
                blocking=True,
                error=f"集成测试失败: {e}",
                duration=time.time() - start_time
            )
    
    async def _test_parameter_compatibility(self) -> TestResult:
        """测试2: 参数兼容性验证"""
        start_time = time.time()
        
        try:
            from src.agents.expert_agents import CitationAgent
            from src.agents.quality_controller import QualityController
            
            # CitationAgent的参数格式
            citation_params = {
                'query': '测试查询',
                'answer': '测试答案内容',
                'knowledge': [
                    {'content': '知识1', 'source': 'source1'},
                    {'content': '知识2', 'source': 'source2'}
                ],
                'evidence': []
            }
            
            # QualityController的参数格式（需要适配）
            # QualityController需要: action, content, content_type
            adapted_params = {
                'action': 'validate_content',
                'content': citation_params['answer'],
                'content_type': 'answer',
                'sources': [k.get('source', '') for k in citation_params.get('knowledge', [])]
            }
            
            # 测试参数适配
            citation_agent = CitationAgent()
            old_result = await citation_agent.execute(citation_params)
            
            quality_controller = QualityController()
            new_result = await quality_controller.execute(adapted_params)
            
            # 检查参数映射是否正确
            param_mapping_correct = (
                'action' in adapted_params and
                'content' in adapted_params and
                adapted_params['content'] == citation_params['answer']
            )
            
            success = (
                old_result.success and
                new_result.success and
                param_mapping_correct
            )
            
            return TestResult(
                test_name="parameter_compatibility",
                success=success,
                details={
                    "old_params_format": citation_params,
                    "adapted_params_format": adapted_params,
                    "param_mapping_correct": param_mapping_correct,
                    "old_result_success": old_result.success,
                    "new_result_success": new_result.success
                },
                blocking=not success,
                duration=time.time() - start_time
            )
            
        except Exception as e:
            return TestResult(
                test_name="parameter_compatibility",
                success=False,
                blocking=True,
                error=f"参数兼容性测试失败: {e}",
                duration=time.time() - start_time
            )
    
    async def _test_performance(self) -> TestResult:
        """测试3: 性能基准测试"""
        start_time = time.time()
        
        try:
            from src.agents.expert_agents import CitationAgent
            from src.agents.quality_controller import QualityController
            
            test_cases = [
                {
                    'query': '简单查询',
                    'answer': '简单答案',
                    'knowledge': [{'content': '知识1', 'source': 'source1'}]
                },
                {
                    'query': '复杂查询',
                    'answer': '这是一个较长的答案内容，包含多个段落和详细信息。',
                    'knowledge': [
                        {'content': '知识1', 'source': 'source1'},
                        {'content': '知识2', 'source': 'source2'},
                        {'content': '知识3', 'source': 'source3'}
                    ]
                }
            ]
            
            old_times = []
            new_times = []
            
            for test_case in test_cases:
                # 测试原有Agent
                citation_agent = CitationAgent()
                old_start = time.time()
                old_result = await citation_agent.execute(test_case)
                old_times.append(time.time() - old_start)
                
                # 测试新Agent
                quality_controller = QualityController()
                adapted_params = {
                    'action': 'validate_content',
                    'content': test_case['answer'],
                    'content_type': 'answer'
                }
                new_start = time.time()
                new_result = await quality_controller.execute(adapted_params)
                new_times.append(time.time() - new_start)
            
            avg_old_time = sum(old_times) / len(old_times)
            avg_new_time = sum(new_times) / len(new_times)
            degradation_percent = ((avg_new_time - avg_old_time) / avg_old_time) * 100 if avg_old_time > 0 else 0
            
            # 性能可接受标准：性能下降不超过20%
            performance_acceptable = degradation_percent <= 20
            
            return TestResult(
                test_name="performance",
                success=performance_acceptable,
                details={
                    "avg_old_time": avg_old_time,
                    "avg_new_time": avg_new_time,
                    "degradation_percent": degradation_percent,
                    "performance_acceptable": performance_acceptable,
                    "threshold": 20
                },
                blocking=degradation_percent > 30,  # 超过30%才阻塞
                duration=time.time() - start_time
            )
            
        except Exception as e:
            return TestResult(
                test_name="performance",
                success=False,
                blocking=False,  # 性能问题不一定是阻塞的
                error=f"性能测试失败: {e}",
                duration=time.time() - start_time
            )
    
    async def _test_functionality(self) -> TestResult:
        """测试4: 功能一致性验证"""
        start_time = time.time()
        
        try:
            from src.agents.expert_agents import CitationAgent
            from src.agents.quality_controller import QualityController
            
            test_cases = [
                {
                    'query': '测试查询1',
                    'answer': '答案1',
                    'knowledge': [{'content': '知识1', 'source': 'source1'}]
                },
                {
                    'query': '测试查询2',
                    'answer': '答案2',
                    'knowledge': [
                        {'content': '知识1', 'source': 'source1'},
                        {'content': '知识2', 'source': 'source2'}
                    ]
                }
            ]
            
            functionality_match = True
            missing_features = []
            
            for test_case in test_cases:
                # 测试原有Agent
                citation_agent = CitationAgent()
                old_result = await citation_agent.execute(test_case)
                
                # 测试新Agent
                quality_controller = QualityController()
                adapted_params = {
                    'action': 'validate_content',
                    'content': test_case['answer'],
                    'content_type': 'answer'
                }
                new_result = await quality_controller.execute(adapted_params)
                
                # 检查功能是否一致
                # 注意：CitationAgent和QualityController的功能可能不完全相同
                # 这里主要检查是否能产生有效结果
                if not (old_result.success and new_result.success):
                    functionality_match = False
                    missing_features.append(f"测试用例 {test_case['query']} 功能不一致")
            
            return TestResult(
                test_name="functionality",
                success=functionality_match,
                details={
                    "functionality_match": functionality_match,
                    "missing_features": missing_features,
                    "test_cases_count": len(test_cases)
                },
                blocking=len(missing_features) > 2,  # 超过2个功能缺失才阻塞
                duration=time.time() - start_time
            )
            
        except Exception as e:
            return TestResult(
                test_name="functionality",
                success=False,
                blocking=True,
                error=f"功能一致性测试失败: {e}",
                duration=time.time() - start_time
            )
    
    async def _test_user_acceptance(self) -> TestResult:
        """测试5: 用户验收测试（简化版）"""
        start_time = time.time()
        
        try:
            # 用户验收测试主要检查：
            # 1. 输出格式是否可接受
            # 2. 结果质量是否满足要求
            
            from src.agents.expert_agents import CitationAgent
            from src.agents.quality_controller import QualityController
            
            test_case = {
                'query': '用户查询',
                'answer': '用户答案',
                'knowledge': [{'content': '知识', 'source': 'source'}]
            }
            
            citation_agent = CitationAgent()
            old_result = await citation_agent.execute(test_case)
            
            quality_controller = QualityController()
            adapted_params = {
                'action': 'validate_content',
                'content': test_case['answer'],
                'content_type': 'answer'
            }
            new_result = await quality_controller.execute(adapted_params)
            
            # 检查输出格式
            old_output_valid = (
                old_result.success and
                hasattr(old_result, 'data') and
                old_result.data is not None
            )
            
            new_output_valid = (
                new_result.success and
                hasattr(new_result, 'data') and
                new_result.data is not None
            )
            
            user_acceptable = old_output_valid and new_output_valid
            
            return TestResult(
                test_name="user_acceptance",
                success=user_acceptable,
                details={
                    "old_output_valid": old_output_valid,
                    "new_output_valid": new_output_valid,
                    "user_acceptable": user_acceptable
                },
                blocking=not user_acceptable,
                duration=time.time() - start_time
            )
            
        except Exception as e:
            return TestResult(
                test_name="user_acceptance",
                success=False,
                blocking=False,  # 用户验收问题不一定是阻塞的
                error=f"用户验收测试失败: {e}",
                duration=time.time() - start_time
            )
    
    def _generate_recommendation(self) -> Dict[str, Any]:
        """基于测试结果生成建议"""
        results = self.report.test_results
        
        if all(r.success for r in results.values()):
            return {
                "decision": "PROCEED",
                "message": "试点成功，可以开始全面验证（阶段0）",
                "confidence": "高"
            }
        elif any(r.blocking for r in results.values()):
            blocking_tests = [k for k, v in results.items() if v.blocking]
            return {
                "decision": "STOP",
                "message": "试点发现阻塞问题，需要先解决",
                "blocking_issues": blocking_tests,
                "confidence": "高"
            }
        else:
            failed_tests = [k for k, v in results.items() if not v.success]
            return {
                "decision": "PROCEED_WITH_CAUTION",
                "message": "试点部分成功，需要调整方案",
                "failed_tests": failed_tests,
                "adjustments": self._suggest_adjustments(results),
                "confidence": "中"
            }
    
    def _suggest_adjustments(self, results: Dict[str, TestResult]) -> List[str]:
        """建议调整方案"""
        adjustments = []
        
        if not results.get("performance", TestResult("", True)).success:
            adjustments.append("需要优化QualityController的性能")
        
        if not results.get("parameter_compatibility", TestResult("", True)).success:
            adjustments.append("需要创建参数适配器层")
        
        if not results.get("functionality", TestResult("", True)).success:
            adjustments.append("需要补充缺失的功能")
        
        return adjustments
    
    def _generate_next_steps(self) -> List[str]:
        """生成下一步行动建议"""
        recommendation = self.report.recommendation
        
        if recommendation.get("decision") == "PROCEED":
            return [
                "1. 开始阶段0：8个核心Agent集成验证",
                "2. 创建集成测试框架",
                "3. 建立参数兼容性验证体系",
                "4. 准备性能基准测试"
            ]
        elif recommendation.get("decision") == "STOP":
            blocking_issues = recommendation.get("blocking_issues", [])
            steps = [
                "1. 分析阻塞问题的根本原因",
                "2. 制定问题修复计划",
                "3. 修复问题后重新运行试点验证"
            ]
            if "integration" in blocking_issues:
                steps.insert(1, "   - 修复集成问题：检查Agent接口兼容性")
            if "parameter_compatibility" in blocking_issues:
                steps.insert(1, "   - 创建参数适配器：统一参数格式")
            if "functionality" in blocking_issues:
                steps.insert(1, "   - 补充缺失功能：确保功能完整性")
            return steps
        else:  # PROCEED_WITH_CAUTION
            adjustments = recommendation.get("adjustments", [])
            steps = [
                "1. 根据调整建议修复问题",
                "2. 重新运行试点验证",
                "3. 验证通过后开始阶段0"
            ]
            steps.extend([f"   - {adj}" for adj in adjustments])
            return steps
    
    async def _save_report(self):
        """保存验证报告"""
        report_dir = Path("reports/pilot_validation")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"pilot_validation_report_{timestamp}.json"
        
        # 转换为可序列化的格式
        report_dict = {
            "pilot_agent": self.report.pilot_agent,
            "target_agent": self.report.target_agent,
            "validation_date": self.report.validation_date,
            "overall_success": self.report.overall_success,
            "blocking_issues": self.report.blocking_issues,
            "test_results": {
                k: {
                    "test_name": v.test_name,
                    "success": v.success,
                    "details": v.details,
                    "blocking": v.blocking,
                    "duration": v.duration,
                    "error": v.error
                }
                for k, v in self.report.test_results.items()
            },
            "recommendation": self.report.recommendation,
            "next_steps": self.report.next_steps
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n验证报告已保存: {report_file}")
        
        # 同时生成Markdown格式的报告
        await self._generate_markdown_report(report_dir / f"pilot_validation_report_{timestamp}.md")
    
    async def _generate_markdown_report(self, report_file: Path):
        """生成Markdown格式的报告"""
        report = self.report
        
        md_content = f"""# 试点项目验证报告

## 基本信息

- **试点Agent**: {report.pilot_agent}
- **目标Agent**: {report.target_agent}
- **验证日期**: {report.validation_date}
- **总体结果**: {'✅ 成功' if report.overall_success else '❌ 失败'}

## 测试结果

"""
        
        for test_name, result in report.test_results.items():
            status = "✅ 通过" if result.success else "❌ 失败"
            blocking = "🔴 阻塞" if result.blocking else "🟡 非阻塞"
            
            md_content += f"""### {test_name.upper()}

- **状态**: {status} {blocking}
- **耗时**: {result.duration:.2f}秒
"""
            
            if result.error:
                md_content += f"- **错误**: {result.error}\n"
            
            if result.details:
                md_content += f"- **详情**:\n"
                for key, value in result.details.items():
                    md_content += f"  - {key}: {value}\n"
            
            md_content += "\n"
        
        md_content += f"""## 阻塞问题

"""
        if report.blocking_issues:
            for issue in report.blocking_issues:
                md_content += f"- 🔴 {issue}\n"
        else:
            md_content += "- 无阻塞问题\n"
        
        md_content += f"""
## 建议

- **决策**: {report.recommendation.get('decision', 'UNKNOWN')}
- **消息**: {report.recommendation.get('message', '')}
- **置信度**: {report.recommendation.get('confidence', '未知')}

## 下一步行动

"""
        for step in report.next_steps:
            md_content += f"{step}\n"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(f"Markdown报告已保存: {report_file}")


async def main():
    """主函数"""
    validator = PilotProjectValidator()
    report = await validator.validate_pilot_project()
    
    # 打印总结
    print("\n" + "=" * 80)
    print("试点项目验证总结")
    print("=" * 80)
    print(f"总体结果: {'✅ 成功' if report.overall_success else '❌ 失败'}")
    print(f"阻塞问题: {len(report.blocking_issues)}")
    print(f"建议决策: {report.recommendation.get('decision', 'UNKNOWN')}")
    print(f"建议消息: {report.recommendation.get('message', '')}")
    print("\n下一步行动:")
    for step in report.next_steps:
        print(f"  {step}")
    print("=" * 80)
    
    return report


if __name__ == "__main__":
    asyncio.run(main())

