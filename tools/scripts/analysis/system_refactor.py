#!/usr/bin/env python3
"""
系统重构脚本
处理重复的类、方法和类型混乱问题
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Set, Tuple
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemRefactor:
    """系统重构器"""

    def __init__(self, src_dir: str = "src"):
        self.src_dir = Path(src_dir)
        self.duplicate_methods = {}
        self.duplicate_classes = {}
        self.pass_methods = []
        self.type_inconsistencies = []

    def scan_duplicates(self):
        """扫描重复的方法和类"""
        logger.info("🔍 开始扫描重复内容...")

        # 扫描重复方法
        self._scan_duplicate_methods()

        # 扫描重复类
        self._scan_duplicate_classes()

        # 扫描pass方法
        self._scan_pass_methods()

        # 扫描类型不一致
        self._scan_type_inconsistencies()

        logger.info("✅ 扫描完成")

    def _scan_duplicate_methods(self):
        """扫描重复方法"""
        method_pattern = r'def\s+(\w+)\s*\('
        method_files = {}

        for py_file in self.src_dir.rglob("*.py"):
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                methods = re.findall(method_pattern, content)

                for method in methods:
                    if method not in method_files:
                        method_files[method] = []
                    method_files[method].append(str(py_file))

        # 找出重复的方法
        for method, files in method_files.items():
            if len(files) > 1:
                self.duplicate_methods[method] = files
                logger.info(f"发现重复方法: {method} 在 {len(files)} 个文件中")

    def _scan_duplicate_classes(self):
        """扫描重复类"""
        class_pattern = r'class\s+(\w+)'
        class_files = {}

        for py_file in self.src_dir.rglob("*.py"):
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                classes = re.findall(class_pattern, content)

                for class_name in classes:
                    if class_name not in class_files:
                        class_files[class_name] = []
                    class_files[class_name].append(str(py_file))

        # 找出重复的类
        for class_name, files in class_files.items():
            if len(files) > 1:
                self.duplicate_classes[class_name] = files
                logger.info(f"发现重复类: {class_name} 在 {len(files)} 个文件中")

    def _scan_pass_methods(self):
        """扫描pass方法"""
        pass_pattern = r'def\s+\w+\s*\([^)]*\)[^:]*:\s*\n\s*pass'

        for py_file in self.src_dir.rglob("*.py"):
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if re.search(pass_pattern, content, re.MULTILINE):
                    self.pass_methods.append(str(py_file))
                    logger.info(f"发现pass方法: {py_file}")

    def _scan_type_inconsistencies(self):
        """扫描类型不一致"""
        # 检查参数类型不一致
        param_pattern = r'def\s+\w+\s*\([^)]*\)[^:]*:\s*\n\s*"""([^"]*)"'

        for py_file in self.src_dir.rglob("*.py"):
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 这里可以添加更复杂的类型检查逻辑
                pass

    def generate_refactor_report(self) -> str:
        """生成重构报告"""
        report = []
        report.append("# 系统重构报告")
        report.append("")

        # 重复方法报告
        if self.duplicate_methods:
            report.append("## 🔴 重复方法")
            for method, files in self.duplicate_methods.items():
                report.append(f"### {method}")
                for file in files:
                    report.append(f"- {file}")
                report.append("")

        # 重复类报告
        if self.duplicate_classes:
            report.append("## 🔴 重复类")
            for class_name, files in self.duplicate_classes.items():
                report.append(f"### {class_name}")
                for file in files:
                    report.append(f"- {file}")
                report.append("")

        # pass方法报告
        if self.pass_methods:
            report.append("## 🟡 Pass方法")
            for file in self.pass_methods:
                report.append(f"- {file}")
            report.append("")

        # 建议
        report.append("## 💡 重构建议")
        report.append("")
        report.append("### 1. 统一配置管理")
        report.append("- 使用 `UnifiedConfigManager` 替代所有重复的配置管理类")
        report.append("- 统一参数获取接口")
        report.append("")

        report.append("### 2. 方法合并")
        report.append("- 将功能相似的方法合并到基类中")
        report.append("- 使用继承和组合减少重复")
        report.append("")

        report.append("### 3. 类型统一")
        report.append("- 统一参数命名规范")
        report.append("- 统一返回类型")
        report.append("")

        report.append("### 4. 实现缺失方法")
        report.append("- 替换所有pass方法为实际实现")
        report.append("- 或标记为抽象方法")

        return "\n".join(report)

    def refactor_unified_config(self):
        """重构统一配置管理"""
        logger.info("🔄 开始重构统一配置管理...")

        # 1. 更新所有使用旧配置管理的地方
        self._update_config_imports()

        # 2. 替换重复的方法调用
        self._replace_duplicate_method_calls()

        logger.info("✅ 统一配置管理重构完成")

    def _update_config_imports(self):
        """更新配置导入"""
        # 查找所有导入旧配置管理的地方
        old_imports = [
            "from intelligent_config_manager import",
            "from utils.intelligent_config_manager import",
            "from src.utils.intelligent_config_manager import"
        ]

        new_import = "from unified_config_manager import get_unified_config_manager"

        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                updated = False
                for old_import in old_imports:
                    if old_import in content:
                        content = content.replace(old_import, new_import)
                        updated = True

                if updated:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"更新导入: {py_file}")

            except Exception as e:
                logger.error(f"更新导入失败 {py_file}: {e}")

    def _replace_duplicate_method_calls(self):
        """替换重复的方法调用"""
        # 替换 _get_parameter_from_unified_config 调用
        old_call = "_get_parameter_from_unified_config"
        new_call = "get_unified_config_manager().get_parameter"

        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                if old_call in content:
                    # 使用正则表达式替换方法调用
                    pattern = r'(\w+)\._get_parameter_from_unified_config\s*\('
                    replacement = r'get_unified_config_manager().get_parameter('

                    content = re.sub(pattern, replacement, content)

                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"替换方法调用: {py_file}")

            except Exception as e:
                logger.error(f"替换方法调用失败 {py_file}: {e}")

    def cleanup_duplicate_files(self):
        """清理重复的文件"""
        logger.info("🧹 开始清理重复文件...")

        # 标记为删除的文件
        files_to_delete = [
            "src/utils/unified_agent_config_interface.py",  # 功能已合并到统一配置管理器
            "src/utils/truly_intelligent_learning.py",     # 功能已合并
        ]

        for file_path in files_to_delete:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"删除重复文件: {file_path}")
                except Exception as e:
                    logger.error(f"删除文件失败 {file_path}: {e}")

        logger.info("✅ 重复文件清理完成")

def main():
    """主函数"""
    refactor = SystemRefactor()

    # 1. 扫描系统
    refactor.scan_duplicates()

    # 2. 生成报告
    report = refactor.generate_refactor_report()

    # 保存报告
    with open("SYSTEM_REFACTOR_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report)

    print("重构报告已保存到 SYSTEM_REFACTOR_REPORT.md")

    # 3. 执行重构
    refactor.refactor_unified_config()

    # 4. 清理重复文件
    refactor.cleanup_duplicate_files()

    print("系统重构完成！")

if __name__ == "__main__":
    main()
