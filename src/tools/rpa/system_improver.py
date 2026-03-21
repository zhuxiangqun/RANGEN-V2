"""
核心系统自动改进模块
根据执行结果分析问题，自动改进核心系统
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from .config import RPA_CONFIG

logger = logging.getLogger(__name__)


class SystemImprover:
    """核心系统自动改进器"""
    
    def __init__(self):
        self.config = RPA_CONFIG
        self.improvements_dir = RPA_CONFIG["rpa"]["work_dir"] / "improvements"
        self.improvements_dir.mkdir(parents=True, exist_ok=True)
    
    async def analyze_and_improve(
        self, 
        analysis_result: Dict[str, Any],
        eval_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析执行结果并生成改进方案
        
        Args:
            analysis_result: 问题分析结果
            eval_result: 评测结果
            
        Returns:
            改进方案和建议
        """
        improvements = []
        suggestions = []
        
        # 分析问题
        issues = analysis_result.get("issues", [])
        solutions = analysis_result.get("solutions", [])
        
        # 生成改进建议
        for issue in issues:
            improvement = await self._generate_improvement(issue, eval_result)
            if improvement:
                improvements.append(improvement)
        
        # 生成系统级改进建议
        system_improvements = await self._generate_system_improvements(
            analysis_result, eval_result
        )
        improvements.extend(system_improvements)
        
        # 保存改进方案
        improvement_file = self.improvements_dir / f"improvements_{int(datetime.now().timestamp())}.json"
        with open(improvement_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "improvements": improvements,
                "suggestions": suggestions
            }, f, indent=2, ensure_ascii=False)
        
        return {
            "status": "success",
            "improvements": improvements,
            "suggestions": suggestions,
            "improvement_file": str(improvement_file)
        }
    
    async def _generate_improvement(
        self, 
        issue: Dict[str, Any], 
        eval_result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """生成单个问题的改进方案"""
        issue_type = issue.get("type")
        
        improvement_templates = {
            "low_accuracy": {
                "title": "提高准确率",
                "priority": "high",
                "actions": [
                    "分析错误样本，找出共同模式",
                    "检查模型选择逻辑是否正确",
                    "优化提示词或参数",
                    "考虑增加训练数据或调整模型"
                ],
                "code_changes": [],
                "config_changes": []
            },
            "performance": {
                "title": "优化性能",
                "priority": "medium",
                "actions": [
                    "分析性能瓶颈",
                    "优化慢查询或处理逻辑",
                    "使用缓存或并行处理",
                    "调整并发参数"
                ],
                "code_changes": [],
                "config_changes": []
            },
            "error": {
                "title": "修复错误",
                "priority": "high",
                "actions": [
                    "查看详细错误日志",
                    "定位错误代码位置",
                    "修复错误并测试",
                    "添加错误处理机制"
                ],
                "code_changes": [],
                "config_changes": []
            },
        }
        
        template = improvement_templates.get(issue_type)
        if template:
            return {
                "issue": issue,
                "improvement": template,
                "estimated_impact": "high" if template["priority"] == "high" else "medium"
            }
        
        return None
    
    async def _generate_system_improvements(
        self,
        analysis_result: Dict[str, Any],
        eval_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成系统级改进建议"""
        improvements = []
        
        # 基于准确率的改进
        if "accuracy" in str(eval_result):
            improvements.append({
                "type": "accuracy_improvement",
                "title": "系统准确率改进",
                "priority": "high",
                "description": "基于评测结果改进系统准确率",
                "actions": [
                    "分析错误样本",
                    "优化模型选择策略",
                    "改进提示词工程",
                    "调整参数配置"
                ]
            })
        
        # 基于性能的改进
        if "duration" in str(eval_result):
            improvements.append({
                "type": "performance_improvement",
                "title": "系统性能改进",
                "priority": "medium",
                "description": "基于执行时间改进系统性能",
                "actions": [
                    "优化慢查询",
                    "增加缓存使用",
                    "调整并发参数",
                    "优化资源使用"
                ]
            })
        
        return improvements

