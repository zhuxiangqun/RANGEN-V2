"""
报告生成模块
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from .config import RPA_CONFIG

logger = logging.getLogger(__name__)


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self):
        self.reports_dir = RPA_CONFIG["rpa"]["reports_dir"]
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate(self, run_id: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成完整的运行报告
        
        Args:
            run_id: 运行ID
            results: 运行结果
            
        Returns:
            报告生成结果
        """
        report_path = self.reports_dir / f"rpa_report_{run_id}.md"
        
        try:
            report_content = self._generate_markdown_report(results)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            # 同时保存JSON格式
            json_path = self.reports_dir / f"rpa_report_{run_id}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            return {
                "status": "success",
                "report_path": str(report_path),
                "json_path": str(json_path)
            }
        
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _generate_markdown_report(self, results: Dict[str, Any]) -> str:
        """生成Markdown格式的报告"""
        lines = []
        
        # 标题
        lines.append(f"# RPA系统运行报告")
        lines.append("")
        lines.append(f"**运行ID**: {results.get('run_id')}")
        lines.append(f"**开始时间**: {results.get('start_time')}")
        lines.append(f"**结束时间**: {results.get('end_time')}")
        lines.append(f"**状态**: {results.get('status', 'unknown')}")
        lines.append("")
        
        # 配置信息
        lines.append("## 运行配置")
        config = results.get('config', {})
        lines.append(f"- 样本数量: {config.get('sample_count', 'N/A')}")
        lines.append(f"- 超时时间: {config.get('timeout', 'N/A')}秒")
        lines.append("")
        
        # 各步骤结果
        lines.append("## 执行步骤")
        steps = results.get('steps', {})
        
        for step_name, step_result in steps.items():
            lines.append(f"### {step_name.replace('_', ' ').title()}")
            
            if isinstance(step_result, dict):
                status = step_result.get('status', 'unknown')
                lines.append(f"**状态**: {status}")
                
                if 'duration' in step_result:
                    lines.append(f"**耗时**: {step_result['duration']:.2f}秒")
                
                if 'issues' in step_result:
                    issues = step_result['issues']
                    lines.append(f"**发现问题**: {len(issues)}个")
                    for issue in issues[:5]:  # 只显示前5个
                        lines.append(f"- {issue.get('message', 'N/A')}")
                
                if 'solutions' in step_result:
                    solutions = step_result['solutions']
                    lines.append(f"**解决方案**: {len(solutions)}个")
                    for solution in solutions[:3]:  # 只显示前3个
                        sol = solution.get('solution', {})
                        lines.append(f"- {sol.get('title', 'N/A')}")
            
            lines.append("")
        
        # 总结
        lines.append("## 总结")
        if results.get('status') == 'success':
            lines.append("✅ 运行成功完成")
        else:
            lines.append(f"❌ 运行失败: {results.get('error', '未知错误')}")
        
        return "\n".join(lines)

