#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本清理工具

将scripts目录中的脚本按类型分类到新的架构中。
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Set

class ScriptCleaner:
    """脚本清理器"""
    
    def __init__(self, project_root: str = None):
        self.project_root = project_root or str(Path(__file__).parent.parent.parent)
        self.scripts_dir = os.path.join(self.project_root, "scripts")
        self.tools_dir = os.path.join(self.project_root, "tools")
        
        # 脚本分类
        self.script_categories = {
            "evaluation": [
                "frames_async_evaluation.py",
                "unified_async_evaluation.py", 
                "performance_benchmark_test.py",
                "accuracy_evaluation.py",
                "lightweight_evaluation.py",
                "robust_evaluation.py",
                "memory_safe_evaluation.py"
            ],
            "testing": [
                "test_*.py",
                "*_test.py",
                "comprehensive_system_test.py",
                "advanced_system_test.py",
                "system_health_check.py",
                "system_integrity_check.py"
            ],
            "analysis": [
                "analyze_*.py",
                "comprehensive_*.py",
                "quality_*.py",
                "performance_*.py",
                "system_*.py",
                "deep_*.py"
            ],
            "maintenance": [
                "cleanup_*.py",
                "fix_*.py",
                "refactor_*.py",
                "optimize_*.py",
                "migrate_*.py",
                "update_*.py",
                "normalize_*.py",
                "batch_*.py",
                "precise_*.py",
                "smart_*.py",
                "ultimate_*.py",
                "final_*.py"
            ],
            "deployment": [
                "deploy_*.py",
                "deploy.py",
                "deploy_to_production.sh"
            ]
        }
        
        self.logger = logging.getLogger(__name__)
    
    def analyze_scripts(self) -> Dict[str, List[str]]:
        """分析scripts目录中的脚本"""
        analysis = {
            "total_scripts": 0,
            "categorized_scripts": {},
            "uncategorized_scripts": [],
            "duplicate_scripts": [],
            "archived_scripts": []
        }
        
        try:
            if not os.path.exists(self.scripts_dir):
                self.logger.error(f"Scripts目录不存在: {self.scripts_dir}")
                return analysis
            
            # 获取所有脚本文件
            script_files = []
            for root, dirs, files in os.walk(self.scripts_dir):
                # 跳过__pycache__和archive目录
                dirs[:] = [d for d in dirs if d != '__pycache__' and d != 'archive']
                
                for file in files:
                    if file.endswith('.py') or file.endswith('.sh'):
                        script_files.append(os.path.join(root, file))
            
            analysis["total_scripts"] = len(script_files)
            
            # 分类脚本
            for script_file in script_files:
                script_name = os.path.basename(script_file)
                categorized = False
                
                for category, patterns in self.script_categories.items():
                    if self._matches_patterns(script_name, patterns):
                        if category not in analysis["categorized_scripts"]:
                            analysis["categorized_scripts"][category] = []
                        analysis["categorized_scripts"][category].append(script_file)
                        categorized = True
                        break
                
                if not categorized:
                    analysis["uncategorized_scripts"].append(script_file)
            
            # 检查重复脚本
            analysis["duplicate_scripts"] = self._find_duplicate_scripts(script_files)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"分析脚本失败: {e}")
            return analysis
    
    def _matches_patterns(self, filename: str, patterns: List[str]) -> bool:
        """检查文件名是否匹配模式"""
        import fnmatch
        
        for pattern in patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
        return False
    
    def _find_duplicate_scripts(self, script_files: List[str]) -> List[List[str]]:
        """查找重复脚本"""
        duplicates = []
        file_contents = {}
        
        try:
            for script_file in script_files:
                try:
                    with open(script_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 简单的重复检测（基于内容哈希）
                    content_hash = hash(content)
                    if content_hash in file_contents:
                        # 找到重复
                        duplicate_group = [file_contents[content_hash], script_file]
                        if duplicate_group not in duplicates:
                            duplicates.append(duplicate_group)
                    else:
                        file_contents[content_hash] = script_file
                
                except Exception as e:
                    self.logger.warning(f"无法读取文件 {script_file}: {e}")
        
        except Exception as e:
            self.logger.error(f"查找重复脚本失败: {e}")
        
        return duplicates
    
    def create_target_directories(self):
        """创建目标目录"""
        try:
            target_dirs = [
                os.path.join(self.tools_dir, "scripts", "evaluation"),
                os.path.join(self.tools_dir, "scripts", "testing"),
                os.path.join(self.tools_dir, "scripts", "analysis"),
                os.path.join(self.tools_dir, "maintenance"),
                os.path.join(self.tools_dir, "deployment"),
                os.path.join(self.tools_dir, "scripts", "archive")
            ]
            
            for target_dir in target_dirs:
                os.makedirs(target_dir, exist_ok=True)
                self.logger.info(f"创建目录: {target_dir}")
        
        except Exception as e:
            self.logger.error(f"创建目标目录失败: {e}")
    
    def move_scripts(self, analysis: Dict[str, List[str]], dry_run: bool = True):
        """移动脚本到对应目录"""
        try:
            moved_scripts = []
            
            # 移动分类的脚本
            for category, scripts in analysis["categorized_scripts"].items():
                target_dir = self._get_target_directory(category)
                
                for script_file in scripts:
                    script_name = os.path.basename(script_file)
                    target_file = os.path.join(target_dir, script_name)
                    
                    if dry_run:
                        self.logger.info(f"[DRY RUN] 将移动: {script_file} -> {target_file}")
                        moved_scripts.append((script_file, target_file))
                    else:
                        try:
                            shutil.move(script_file, target_file)
                            self.logger.info(f"已移动: {script_file} -> {target_file}")
                            moved_scripts.append((script_file, target_file))
                        except Exception as e:
                            self.logger.error(f"移动失败 {script_file}: {e}")
            
            # 移动未分类的脚本到archive
            archive_dir = os.path.join(self.tools_dir, "scripts", "archive")
            for script_file in analysis["uncategorized_scripts"]:
                script_name = os.path.basename(script_file)
                target_file = os.path.join(archive_dir, script_name)
                
                if dry_run:
                    self.logger.info(f"[DRY RUN] 将移动到archive: {script_file} -> {target_file}")
                    moved_scripts.append((script_file, target_file))
                else:
                    try:
                        shutil.move(script_file, target_file)
                        self.logger.info(f"已移动到archive: {script_file} -> {target_file}")
                        moved_scripts.append((script_file, target_file))
                    except Exception as e:
                        self.logger.error(f"移动到archive失败 {script_file}: {e}")
            
            return moved_scripts
        
        except Exception as e:
            self.logger.error(f"移动脚本失败: {e}")
            return []
    
    def _get_target_directory(self, category: str) -> str:
        """获取目标目录"""
        category_mapping = {
            "evaluation": os.path.join(self.tools_dir, "scripts", "evaluation"),
            "testing": os.path.join(self.tools_dir, "scripts", "testing"),
            "analysis": os.path.join(self.tools_dir, "scripts", "analysis"),
            "maintenance": os.path.join(self.tools_dir, "maintenance"),
            "deployment": os.path.join(self.tools_dir, "deployment")
        }
        
        return category_mapping.get(category, os.path.join(self.tools_dir, "scripts", "archive"))
    
    def generate_cleanup_report(self, analysis: Dict[str, List[str]], 
                              moved_scripts: List[tuple], 
                              output_file: str = None) -> str:
        """生成清理报告"""
        try:
            report_content = f"""# 脚本清理报告

## 清理概览

- **总脚本数**: {analysis['total_scripts']}
- **已分类脚本**: {sum(len(scripts) for scripts in analysis['categorized_scripts'].values())}
- **未分类脚本**: {len(analysis['uncategorized_scripts'])}
- **重复脚本**: {len(analysis['duplicate_scripts'])}
- **已移动脚本**: {len(moved_scripts)}

## 分类详情

"""
            
            # 分类详情
            for category, scripts in analysis['categorized_scripts'].items():
                report_content += f"### {category.title()} ({len(scripts)} 个)\n"
                for script in scripts:
                    report_content += f"- {os.path.basename(script)}\n"
                report_content += "\n"
            
            # 未分类脚本
            if analysis['uncategorized_scripts']:
                report_content += "### 未分类脚本\n"
                for script in analysis['uncategorized_scripts']:
                    report_content += f"- {os.path.basename(script)}\n"
                report_content += "\n"
            
            # 重复脚本
            if analysis['duplicate_scripts']:
                report_content += "### 重复脚本\n"
                for i, duplicate_group in enumerate(analysis['duplicate_scripts'], 1):
                    report_content += f"#### 重复组 {i}\n"
                    for script in duplicate_group:
                        report_content += f"- {os.path.basename(script)}\n"
                    report_content += "\n"
            
            # 移动记录
            if moved_scripts:
                report_content += "### 移动记录\n"
                for source, target in moved_scripts:
                    report_content += f"- {os.path.basename(source)} -> {os.path.relpath(target, self.project_root)}\n"
                report_content += "\n"
            
            # 建议
            report_content += """## 建议

1. **定期清理**: 建议定期运行此清理工具
2. **脚本规范**: 新脚本应遵循命名规范，便于自动分类
3. **重复处理**: 检查重复脚本，保留最新版本
4. **文档更新**: 更新相关文档以反映新的目录结构

"""
            
            # 保存报告
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                self.logger.info(f"清理报告已保存到: {output_file}")
            
            return report_content
        
        except Exception as e:
            self.logger.error(f"生成清理报告失败: {e}")
            return f"生成报告失败: {e}"

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='脚本清理工具')
    parser.add_argument('--dry-run', action='store_true', help='试运行，不实际移动文件')
    parser.add_argument('--output-report', type=str, help='输出报告文件路径')
    parser.add_argument('--project-root', type=str, help='项目根目录路径')
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建清理器
    cleaner = ScriptCleaner(args.project_root)
    
    # 分析脚本
    print("分析scripts目录...")
    analysis = cleaner.analyze_scripts()
    
    # 打印分析结果
    print(f"\n分析结果:")
    print(f"总脚本数: {analysis['total_scripts']}")
    for category, scripts in analysis['categorized_scripts'].items():
        print(f"{category}: {len(scripts)} 个")
    print(f"未分类: {len(analysis['uncategorized_scripts'])} 个")
    print(f"重复: {len(analysis['duplicate_scripts'])} 组")
    
    # 创建目标目录
    print("\n创建目标目录...")
    cleaner.create_target_directories()
    
    # 移动脚本
    print(f"\n{'试运行' if args.dry_run else '执行'}脚本移动...")
    moved_scripts = cleaner.move_scripts(analysis, dry_run=args.dry_run)
    
    # 生成报告
    print("\n生成清理报告...")
    report = cleaner.generate_cleanup_report(analysis, moved_scripts, args.output_report)
    
    if not args.dry_run:
        print(f"\n清理完成！移动了 {len(moved_scripts)} 个脚本")
    else:
        print(f"\n试运行完成！将移动 {len(moved_scripts)} 个脚本")

if __name__ == "__main__":
    main()
