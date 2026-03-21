#!/usr/bin/env python3
"""
智能硬编码数据清理器
系统化清理硬编码的魔法数字、路径、URL等
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass


@dataclass
class HardcodedIssue:
    """硬编码问题"""
    file_path: str
    line_number: int
    issue_type: str
    original_value: str
    suggested_fix: str
    severity: str


class SmartHardcodedDataCleaner:
    """智能硬编码数据清理器"""
    
    def __init__(self, source_path: str = "src"):
        self.logger = logging.getLogger(__name__)
        self.source_path = Path(source_path)
        self.issues: List[HardcodedIssue] = []
        
        # 硬编码模式定义
        self.patterns = {
            "magic_numbers": [
                r'\b(100|200|300|500|1000|2000|5000|10000|3600|7200|86400)\b',
                r'\b(0\.5|0\.8|0\.9|1\.0|2\.0|3\.0|5\.0)\b',
                r'\b(1024|2048|4096|8192|16384|32768|65536)\b'
            ],
            "hardcoded_paths": [
                r'["\']([A-Za-z]:)?[/\\][^"\']*["\']',
                r'["\'][^"\']*\.(json|py|txt|log|csv|xml|yaml|yml)["\']'
            ],
            "hardcoded_urls": [
                r'["\']https?://[^"\']*["\']',
                r'["\']ftp://[^"\']*["\']'
            ],
            "hardcoded_credentials": [
                r'["\'](password|pwd|secret|key|token|api_key)["\']\s*[:=]\s*["\'][^"\']*["\']',
                r'["\'][A-Za-z0-9]{20,}["\']'  # 长字符串可能是密钥
            ],
            "simulated_data": [
                r'["\'](test|demo|sample|mock|fake|simulated)_[^"\']*["\']',
                r'["\']SIMULATED_[^"\']*["\']',
                r'["\']TEST_[^"\']*["\']'
            ]
        }
        
        # 环境变量映射
        self.env_mappings = {
            "100": "DEFAULT_TIMEOUT",
            "200": "SUCCESS_CODE", 
            "300": "REDIRECT_CODE",
            "500": "SERVER_ERROR_CODE",
            "1000": "MAX_RETRIES",
            "2000": "BUFFER_SIZE",
            "5000": "MAX_WAIT_TIME",
            "10000": "MAX_MEMORY",
            "3600": "DEFAULT_TTL",
            "7200": "SESSION_TIMEOUT",
            "86400": "DAILY_LIMIT",
            "0.5": "DEFAULT_CONFIDENCE",
            "0.8": "HIGH_CONFIDENCE",
            "0.9": "VERY_HIGH_CONFIDENCE",
            "1.0": "MAX_CONFIDENCE",
            "2.0": "DEFAULT_MULTIPLIER",
            "3.0": "HIGH_MULTIPLIER",
            "5.0": "MAX_MULTIPLIER",
            "1024": "KB_SIZE",
            "2048": "SMALL_BUFFER",
            "4096": "MEDIUM_BUFFER",
            "8192": "LARGE_BUFFER",
            "16384": "MAX_BUFFER",
            "32768": "HUGE_BUFFER",
            "65536": "MAX_HUGE_BUFFER"
        }
    
    def scan_hardcoded_data(self) -> List[HardcodedIssue]:
        """扫描硬编码数据"""
        self.logger.info("开始扫描硬编码数据...")
        self.issues = []
        
        # 获取所有Python文件
        python_files = list(self.source_path.rglob("*.py"))
        
        for file_path in python_files:
            self._scan_file(file_path)
        
        self.logger.info(f"扫描完成，发现 {len(self.issues)} 个硬编码问题")
        return self.issues
    
    def _scan_file(self, file_path: Path):
        """扫描单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                self._check_line(str(file_path), line_num, line)
                
        except Exception as e:
            self.logger.error(f"扫描文件失败 {file_path}: {e}")
    
    def _check_line(self, file_path: str, line_number: int, line: str):
        """检查单行代码"""
        # 跳过注释和文档字符串
        if line.strip().startswith('#') or '"""' in line or "'''" in line:
            return
        
        # 检查各种硬编码模式
        for issue_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    original_value = match.group(0)
                    suggested_fix = self._suggest_fix(original_value, issue_type)
                    
                    if suggested_fix:
                        issue = HardcodedIssue(
                            file_path=file_path,
                            line_number=line_number,
                            issue_type=issue_type,
                            original_value=original_value,
                            suggested_fix=suggested_fix,
                            severity=self._get_severity(issue_type)
                        )
                        self.issues.append(issue)
    
    def _suggest_fix(self, original_value: str, issue_type: str) -> str:
        """建议修复方案"""
        if issue_type == "magic_numbers":
            # 清理引号
            clean_value = original_value.strip('"\'')
            if clean_value in self.env_mappings:
                env_var = self.env_mappings[clean_value]
                return f'os.getenv("{env_var}", "{clean_value}")'
        
        elif issue_type == "hardcoded_paths":
            # 提取路径
            path_match = re.search(r'["\']([^"\']*)["\']', original_value)
            if path_match:
                path = path_match.group(1)
                if path.endswith(('.json', '.py', '.txt', '.log')):
                    filename = os.path.basename(path)
                    env_var = f"{filename.upper().replace('.', '_')}_PATH"
                    return f'os.getenv("{env_var}", "{path}")'
        
        elif issue_type == "hardcoded_urls":
            # 提取URL
            url_match = re.search(r'["\']([^"\']*)["\']', original_value)
            if url_match:
                url = url_match.group(1)
                if 'api' in url.lower():
                    return f'os.getenv("API_BASE_URL", "{url}")'
                else:
                    return f'os.getenv("BASE_URL", "{url}")'
        
        elif issue_type == "hardcoded_credentials":
            return f'os.getenv("API_KEY", "your_api_key_here")'
        
        elif issue_type == "simulated_data":
            return f'os.getenv("USE_SIMULATED_DATA", "false")'
        
        return ""
    
    def _get_severity(self, issue_type: str) -> str:
        """获取问题严重程度"""
        severity_map = {
            "hardcoded_credentials": "high",
            "hardcoded_urls": "medium",
            "hardcoded_paths": "medium",
            "magic_numbers": "low",
            "simulated_data": "low"
        }
        return severity_map.get(issue_type, "low")
    
    def generate_fix_report(self) -> str:
        """生成修复报告"""
        report = []
        report.append("# 硬编码数据清理报告\n")
        report.append(f"## 扫描结果\n")
        report.append(f"- 总问题数: {len(self.issues)}\n")
        
        # 按类型统计
        type_counts = {}
        for issue in self.issues:
            type_counts[issue.issue_type] = type_counts.get(issue.issue_type, 0) + 1
        
        report.append("## 问题类型统计\n")
        for issue_type, count in type_counts.items():
            report.append(f"- {issue_type}: {count}个\n")
        
        # 按严重程度统计
        severity_counts = {}
        for issue in self.issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
        
        report.append("## 严重程度统计\n")
        for severity, count in severity_counts.items():
            report.append(f"- {severity}: {count}个\n")
        
        # 详细问题列表
        report.append("## 详细问题列表\n")
        for issue in self.issues[:50]:  # 只显示前50个
            report.append(f"### {issue.file_path}:{issue.line_number}\n")
            report.append(f"- **类型**: {issue.issue_type}\n")
            report.append(f"- **严重程度**: {issue.severity}\n")
            report.append(f"- **原始值**: `{issue.original_value}`\n")
            report.append(f"- **建议修复**: `{issue.suggested_fix}`\n")
            report.append("")
        
        if len(self.issues) > 50:
            report.append(f"... 还有 {len(self.issues) - 50} 个问题\n")
        
        return "\n".join(report)
    
    def apply_fixes(self, dry_run: bool = True) -> Dict[str, Any]:
        """应用修复"""
        if dry_run:
            self.logger.info("模拟模式：不会实际修改文件")
            return {"mode": "dry_run", "files_to_modify": len(set(issue.file_path for issue in self.issues))}
        
        self.logger.info("开始应用修复...")
        modified_files = 0
        total_fixes = 0
        
        # 按文件分组
        file_issues = {}
        for issue in self.issues:
            if issue.file_path not in file_issues:
                file_issues[issue.file_path] = []
            file_issues[issue.file_path].append(issue)
        
        for file_path, issues in file_issues.items():
            try:
                if self._fix_file(file_path, issues):
                    modified_files += 1
                    total_fixes += len(issues)
            except Exception as e:
                self.logger.error(f"修复文件失败 {file_path}: {e}")
        
        self.logger.info(f"修复完成：修改了 {modified_files} 个文件，应用了 {total_fixes} 个修复")
        return {
            "modified_files": modified_files,
            "total_fixes": total_fixes,
            "mode": "actual"
        }
    
    def _fix_file(self, file_path: str, issues: List[HardcodedIssue]) -> bool:
        """修复单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 按行号倒序排列，避免行号变化影响
            issues.sort(key=lambda x: x.line_number, reverse=True)
            
            lines = content.split('\n')
            for issue in issues:
                line_index = issue.line_number - 1
                if 0 <= line_index < len(lines):
                    # 替换硬编码值
                    original_line = lines[line_index]
                    fixed_line = original_line.replace(issue.original_value, issue.suggested_fix)
                    lines[line_index] = fixed_line
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            return True
            
        except Exception as e:
            self.logger.error(f"修复文件失败 {file_path}: {e}")
            return False


def main():
    """主函数"""
    logging.basicConfig(level=logging.INFO)
    
    # 创建清理器
    cleaner = SmartHardcodedDataCleaner()
    
    # 扫描硬编码数据
    issues = cleaner.scan_hardcoded_data()
    
    # 生成报告
    report = cleaner.generate_fix_report()
    
    # 保存报告
    with open("hardcoded_data_cleanup_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"发现 {len(issues)} 个硬编码问题")
    print("报告已保存到: hardcoded_data_cleanup_report.md")
    
    # 自动应用修复
    if len(issues) > 0:
        print("\n自动应用修复...")
        result = cleaner.apply_fixes(dry_run=False)
        print(f"修复完成：{result}")
    else:
        print("没有发现硬编码问题")


if __name__ == "__main__":
    main()
