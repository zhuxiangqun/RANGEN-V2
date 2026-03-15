#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评测报告生成器

生成各种格式的评测报告。
"""

import os
import json
from typing import Dict, Any
from datetime import datetime

from ..interfaces import ReportGeneratorInterface, EvaluationReport

class ReportGenerator(ReportGeneratorInterface):
    """评测报告生成器"""
    
    def __init__(self):
        self.templates = {
            "markdown": self._generate_markdown_report,
            "json": self._generate_json_report,
            "html": self._generate_html_report
        }
    
    def generate_report(self, report: EvaluationReport, format: str = "markdown") -> str:
        """生成评测报告"""
        if format not in self.templates:
            raise ValueError(f"不支持的报告格式: {format}")
        
        return self.templates[format](report)
    
    def save_report(self, report: EvaluationReport, filepath: str, format: str = "markdown") -> None:
        """保存评测报告"""
        content = self.generate_report(report, format)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_markdown_report(self, report: EvaluationReport) -> str:
        """生成Markdown格式报告"""
        success_rate = (report.successful_queries / report.total_queries * 100) if report.total_queries > 0 else 0
        
        content = f"""# FRAMES基准评测报告

## 评测概览

- **评测时间**: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}
- **总查询数**: {report.total_queries}
- **成功数**: {report.successful_queries}
- **失败数**: {report.failed_queries}
- **成功率**: {success_rate:.1f}%
- **平均准确率**: {report.average_accuracy:.3f}
- **平均执行时间**: {report.average_execution_time:.2f}秒

## 性能指标

### 执行时间统计
- **平均执行时间**: {report.average_execution_time:.2f}秒
- **最快执行时间**: {min([r.execution_time for r in report.results if r.success], default=0):.2f}秒
- **最慢执行时间**: {max([r.execution_time for r in report.results if r.success], default=0):.2f}秒

### 准确率分布
"""
        
        # 添加准确率分布
        if report.results:
            accuracies = [r.metadata.get("accuracy", 0.0) for r in report.results if r.success and r.metadata]
            if accuracies:
                high_accuracy = sum(1 for acc in accuracies if acc >= 0.8)
                medium_accuracy = sum(1 for acc in accuracies if 0.5 <= acc < 0.8)
                low_accuracy = sum(1 for acc in accuracies if acc < 0.5)
                
                content += f"""
- **高准确率 (≥80%)**: {high_accuracy} 个
- **中等准确率 (50%-80%)**: {medium_accuracy} 个
- **低准确率 (<50%)**: {low_accuracy} 个
"""
        
        content += f"""

## 详细结果

### 成功案例
"""
        
        # 添加成功案例
        successful_results = [r for r in report.results if r.success]
        for i, result in enumerate(successful_results[:5]):  # 只显示前5个
            accuracy = result.metadata.get("accuracy", 0.0) if result.metadata else 0.0
            content += f"""
#### 案例 {i+1}
- **查询**: {result.query[:100]}{'...' if len(result.query) > 100 else ''}
- **答案**: {result.answer[:100]}{'...' if len(result.answer) > 100 else ''}
- **准确率**: {accuracy:.3f}
- **执行时间**: {result.execution_time:.2f}秒
- **置信度**: {result.confidence:.3f}
"""
        
        content += f"""

### 失败案例
"""
        
        # 添加失败案例
        failed_results = [r for r in report.results if not r.success]
        for i, result in enumerate(failed_results[:5]):  # 显示前5个
            content += f"""
#### 失败案例 {i+1}
- **查询**: {result.query[:100]}{'...' if len(result.query) > 100 else ''}
- **答案**: {result.answer[:200]}{'...' if len(result.answer) > 200 else ''}
- **错误**: {result.error if result.error else '无错误信息'}
- **执行时间**: {result.execution_time:.2f}秒
- **置信度**: {result.confidence:.3f}
"""
            
            # 添加智能质量诊断信息
            if result.metadata:
                is_mock = result.metadata.get("is_mock_response", False)
                is_meaningful = result.metadata.get("is_meaningful", False)
                accuracy = result.metadata.get("accuracy", 0.0)
                quality_score = result.metadata.get("quality_score", 0.0)
                
                content += f"""- **智能质量诊断**:
  - 是否为模拟回答: {'是' if is_mock else '否'}
  - 是否有意义: {'是' if is_meaningful else '否'}
  - 准确率: {accuracy:.3f}
  - 质量分数: {quality_score:.3f}
"""
        
        content += f"""

## 系统信息

- **评测系统版本**: 1.0.0
- **报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **数据集信息**: {report.metadata.get('dataset_info', {}) if report.metadata else {}}

---
*此报告由RANGEN评测系统自动生成*
"""
        
        return content
    
    def _generate_json_report(self, report: EvaluationReport) -> str:
        """生成JSON格式报告"""
        report_dict = {
            "evaluation_type": "frames_benchmark",
            "generated_at": report.generated_at.isoformat(),
            "summary": {
                "total_queries": report.total_queries,
                "successful_queries": report.successful_queries,
                "failed_queries": report.failed_queries,
                "success_rate": (report.successful_queries / report.total_queries) if report.total_queries > 0 else 0,
                "average_accuracy": report.average_accuracy,
                "average_execution_time": report.average_execution_time
            },
            "results": [
                {
                    "query": result.query,
                    "answer": result.answer,
                    "confidence": result.confidence,
                    "execution_time": result.execution_time,
                    "success": result.success,
                    "error": result.error,
                    "metadata": result.metadata
                }
                for result in report.results
            ],
            "metadata": report.metadata
        }
        
        return json.dumps(report_dict, indent=2, ensure_ascii=False)
    
    def _generate_html_report(self, report: EvaluationReport) -> str:
        """生成HTML格式报告"""
        success_rate = (report.successful_queries / report.total_queries * 100) if report.total_queries > 0 else 0
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FRAMES基准评测报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; background-color: #e9e9e9; border-radius: 5px; }}
        .success {{ color: #28a745; }}
        .failure {{ color: #dc3545; }}
        .result {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>FRAMES基准评测报告</h1>
        <p>生成时间: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <h2>评测概览</h2>
    <div class="metric">总查询数: {report.total_queries}</div>
    <div class="metric success">成功数: {report.successful_queries}</div>
    <div class="metric failure">失败数: {report.failed_queries}</div>
    <div class="metric">成功率: {success_rate:.1f}%</div>
    <div class="metric">平均准确率: {report.average_accuracy:.3f}</div>
    <div class="metric">平均执行时间: {report.average_execution_time:.2f}秒</div>
    
    <h2>详细结果</h2>
    <table>
        <tr>
            <th>查询</th>
            <th>答案</th>
            <th>成功</th>
            <th>准确率</th>
            <th>执行时间</th>
            <th>置信度</th>
        </tr>
"""
        
        for result in report.results:
            accuracy = result.metadata.get("accuracy", 0.0) if result.metadata else 0.0
            success_class = "success" if result.success else "failure"
            success_text = "是" if result.success else "否"
            
            html += f"""
        <tr>
            <td>{result.query[:50]}{'...' if len(result.query) > 50 else ''}</td>
            <td>{result.answer[:50]}{'...' if len(result.answer) > 50 else ''}</td>
            <td class="{success_class}">{success_text}</td>
            <td>{accuracy:.3f}</td>
            <td>{result.execution_time:.2f}秒</td>
            <td>{result.confidence:.3f}</td>
        </tr>
"""
        
        html += """
    </table>
</body>
</html>
"""
        
        return html
