"""
核心系统问题分析和解决方案生成模块
"""
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from .config import RPA_CONFIG

logger = logging.getLogger(__name__)


class CoreSystemAnalyzer:
    """核心系统问题分析器"""
    
    def __init__(self):
        self.config = RPA_CONFIG
    
    async def analyze(self, core_log_path: Path, 
                     eval_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析核心系统问题并生成解决方案
        
        Args:
            core_log_path: 核心系统日志路径
            eval_result: 评测结果
            
        Returns:
            分析结果，包含问题、原因和解决方案
        """
        issues = []
        solutions = []
        
        # 分析1: 检查日志中的错误
        if core_log_path.exists():
            log_issues = await self._analyze_log_errors(core_log_path)
            issues.extend(log_issues)
        
        # 分析2: 分析评测结果
        if eval_result.get("status") == "success":
            eval_issues = await self._analyze_evaluation_results(eval_result)
            issues.extend(eval_issues)
        
        # 分析3: 性能问题分析
        performance_issues = await self._analyze_performance(core_log_path, eval_result)
        issues.extend(performance_issues)
        
        # 生成解决方案
        for issue in issues:
            solution = await self._generate_solution(issue)
            if solution:
                solutions.append(solution)
        
        return {
            "status": "success",
            "issues_found": len(issues),
            "issues": issues,
            "solutions": solutions,
            "analyzed_at": datetime.now().isoformat()
        }
    
    async def _analyze_log_errors(self, log_path: Path) -> List[Dict[str, Any]]:
        """分析日志中的错误"""
        issues = []
        
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            error_patterns = [
                (r"ERROR|Exception|Traceback", "error", "high"),
                (r"WARNING|Warning", "warning", "medium"),
                (r"timeout|Timeout", "timeout", "high"),
                (r"memory|Memory", "memory", "medium"),
            ]
            
            error_count = {}
            for line in lines[-1000:]:  # 只分析最后1000行
                for pattern, error_type, severity in error_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        error_count[error_type] = error_count.get(error_type, 0) + 1
            
            for error_type, count in error_count.items():
                if count > 0:
                    issues.append({
                        "type": error_type,
                        "severity": next(s for p, t, s in error_patterns if t == error_type),
                        "count": count,
                        "message": f"发现 {count} 个 {error_type} 错误",
                    })
        
        except Exception as e:
            logger.error(f"分析日志错误失败: {e}")
        
        return issues
    
    async def _analyze_evaluation_results(self, eval_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析评测结果"""
        issues = []
        
        # 检查评测报告文件
        report_path = Path(RPA_CONFIG["evaluation_system"]["report_path"])
        
        # 查找最新的评测报告
        if report_path.exists():
            report_files = sorted(report_path.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
            if report_files:
                latest_report = report_files[0]
                report_issues = await self._parse_evaluation_report(latest_report)
                issues.extend(report_issues)
        
        return issues
    
    async def _parse_evaluation_report(self, report_path: Path) -> List[Dict[str, Any]]:
        """解析评测报告"""
        issues = []
        
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找准确率信息
            accuracy_match = re.search(r"准确率[：:]\s*(\d+\.?\d*)%", content)
            if accuracy_match:
                accuracy = float(accuracy_match.group(1))
                if accuracy < 50:
                    issues.append({
                        "type": "low_accuracy",
                        "severity": "high",
                        "message": f"准确率过低: {accuracy}%",
                        "value": accuracy
                    })
            
            # 查找性能问题
            if "性能" in content or "performance" in content.lower():
                if "慢" in content or "slow" in content.lower():
                    issues.append({
                        "type": "performance",
                        "severity": "medium",
                        "message": "检测到性能问题"
                    })
        
        except Exception as e:
            logger.error(f"解析评测报告失败: {e}")
        
        return issues
    
    async def _analyze_performance(self, log_path: Path, 
                                  eval_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析性能问题"""
        issues = []
        
        # 检查运行时间
        if "duration" in eval_result:
            duration = eval_result["duration"]
            if duration > 3600:  # 超过1小时
                issues.append({
                    "type": "slow_execution",
                    "severity": "medium",
                    "message": f"执行时间过长: {duration:.2f}秒",
                    "value": duration
                })
        
        return issues
    
    async def _generate_solution(self, issue: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """生成解决方案"""
        issue_type = issue.get("type")
        
        solutions_map = {
            "error": {
                "title": "修复错误",
                "description": "检查日志中的错误信息，修复代码中的bug",
                "steps": [
                    "1. 查看详细错误日志",
                    "2. 定位错误代码位置",
                    "3. 修复错误并测试",
                    "4. 重新运行系统"
                ]
            },
            "timeout": {
                "title": "解决超时问题",
                "description": "增加超时时间或优化代码性能",
                "steps": [
                    "1. 检查超时配置",
                    "2. 优化慢查询或处理逻辑",
                    "3. 增加超时时间（如果必要）",
                    "4. 重新运行测试"
                ]
            },
            "low_accuracy": {
                "title": "提高准确率",
                "description": "分析错误样本，改进模型或逻辑",
                "steps": [
                    "1. 分析错误样本",
                    "2. 检查模型选择逻辑",
                    "3. 优化提示词或参数",
                    "4. 重新训练或调整模型"
                ]
            },
            "performance": {
                "title": "优化性能",
                "description": "优化代码性能，减少执行时间",
                "steps": [
                    "1. 分析性能瓶颈",
                    "2. 优化慢查询或处理",
                    "3. 使用缓存或并行处理",
                    "4. 重新测试性能"
                ]
            },
        }
        
        solution_template = solutions_map.get(issue_type)
        if solution_template:
            return {
                "issue": issue,
                "solution": solution_template,
                "priority": issue.get("severity", "medium")
            }
        
        return None

