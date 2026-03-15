#!/usr/bin/env pythonconfig.DEFAULT_MAX_RETRIES
"""
模块清理管理器
安全地识别和清理重复、废弃的模块
"""

import logging
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ModuleCleanupManager:
    """模块清理管理器"""

    def __init__(self, utils_dir: str = "src/utils"):
        self.utils_dir = Path(utils_dir)
        self.backup_dir = Path("backup/module_cleanup") / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.cleanup_plan = {}
        self.risk_assessment = {}

        # 创建备份目录
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"模块清理管理器初始化完成，备份目录: {self.backup_dir}")

    def analyze_modules(self) -> Dict[str, Dict]:
        """分析所有模块的重复和使用情况"""
        logger.info("开始分析模块重复和使用情况...")

        all_files = [f for f in os.listdir(self.utils_dir) if f.endswith('.py') and not f.startswith('__')]
        analysis_result = {}

        for file in all_files:
            file_path = self.utils_dir / file
            module_name = file.replace('.py', '')

            # 分析模块特征
            features = self._analyze_module_features(file_path)

            # 分析引用情况
            references = self._analyze_module_references(module_name, all_files)

            # 风险评估
            risk_level = self._assess_cleanup_risk(file, features, references)

            analysis_result[file] = {
                'module_name': module_name,
                'features': features,
                'references': references,
                'risk_level': risk_level,
                'file_size': file_path.stat().st_size if file_path.exists() else 0
            }

        logger.info(f"模块分析完成，共分析 {len(analysis_result)} 个模块")
        return analysis_result

    def _analyze_module_features(self, file_path: Path) -> Dict[str, Any]:
        """分析模块特征"""
        features = {
            'has_class': False,
            'class_count': 0,
            'function_count': 0,
            'import_count': 0,
            'has_main': False,
            'has_async': False,
            'complexity_score': 0
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 分析类
            classes = re.findall(r'class\s+\w+', content)
            features['has_class'] = len(classes) > 0
            features['class_count'] = len(classes)

            # 分析函数
            functions = re.findall(r'def\s+\w+', content)
            features['function_count'] = len(functions)

            # 分析导入
            imports = re.findall(r'(?:from|import)\s+', content)
            features['import_count'] = len(imports)

            # 检查是否有main函数
            features['has_main'] = 'if __name__ == "__main__"' in content

            # 检查是否有异步代码
            features['has_async'] = 'async def' in content or 'await' in content

            # 计算复杂度分数
            features['complexity_score'] = (
                features['class_count'] * 2 +
                features['function_count'] +
                features['import_count'] // 2
            )

        except Exception as e:
            logger.warning(f"分析模块特征失败 {file_path}: {e}")

        return features

    def _analyze_module_references(self, module_name: str, all_files: List[str]) -> Dict[str, Any]:
        """分析模块引用情况"""
        references = {
            'total_references': 0,
            'internal_references': 0,
            'external_references': 0,
            'referencing_files': []
        }

        # 引用模式
        patterns = [
            fr'from\s+.*{re.escape(module_name)}',
            fr'import\s+.*{re.escape(module_name)}',
            fr'{re.escape(module_name)}\s*\.',
            fr'get_{re.escape(module_name)}',
            fr'{re.escape(module_name)}_manager',
            fr'{re.escape(module_name)}_center'
        ]

        for other_file in all_files:
            if other_file == f"{module_name}.py":
                continue

            other_path = self.utils_dir / other_file
            try:
                with open(other_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                file_references = 0
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    file_references += len(matches)

                if file_references > 0:
                    references['total_references'] += file_references
                    references['internal_references'] += file_references
                    references['referencing_files'].append(other_file)

            except Exception as e:
                logger.debug(f"分析引用失败 {other_path}: {e}")

        return references

    def _assess_cleanup_risk(self, file: str, features: Dict, references: Dict) -> str:
        """评估清理风险"""
        risk_score = 0

        # 引用数量风险
        if references['total_references'] > config.DEFAULT_SMALL_LIMIT:
            risk_score += config.DEFAULT_MAX_RETRIES  # 高风险
        elif references['total_references'] > config.DEFAULT_TOP_K:
            risk_score += 2  # 中风险
        elif references['total_references'] > 0:
            risk_score += 1  # 低风险

        # 功能复杂度风险
        if features['complexity_score'] > 20:
            risk_score += 2
        elif features['complexity_score'] > config.DEFAULT_SMALL_LIMIT:
            risk_score += 1

        # 文件大小风险
        if features.get('file_size', 0) > config.DEFAULT_TOP_K0000:  # config.DEFAULT_TOP_K0KB
            risk_score += 1

        # 特殊文件风险
        special_files = ['__init__.py', 'compatibility_layer.py']
        if file in special_files:
            risk_score += config.DEFAULT_SMALL_LIMIT  # 极高风险

        # 核心模块风险
        core_modules = ['unified_config_center', 'unified_monitoring_center', 'unified_data_center']
        if any(core in file for core in core_modules):
            risk_score += config.DEFAULT_SMALL_LIMIT

        # 风险等级判断
        if risk_score >= config.DEFAULT_SMALL_LIMIT:
            return "极高风险"
        elif risk_score >= config.DEFAULT_TOP_K:
            return "高风险"
        elif risk_score >= 2:
            return "中风险"
        else:
            return "低风险"

    def generate_cleanup_plan(self, analysis_result: Dict[str, Dict]) -> Dict[str, List[str]]:
        """生成清理计划"""
        cleanup_plan = {
            'low_risk': [],
            'medium_risk': [],
            'high_risk': [],
            'extreme_risk': []
        }

        for file, info in analysis_result.items():
            risk_level = info['risk_level']

            if risk_level == "低风险":
                cleanup_plan['low_risk'].append(file)
            elif risk_level == "中风险":
                cleanup_plan['medium_risk'].append(file)
            elif risk_level == "高风险":
                cleanup_plan['high_risk'].append(file)
            else:  # 极高风险
                cleanup_plan['extreme_risk'].append(file)

        # 记录清理计划
        self.cleanup_plan = cleanup_plan

        return cleanup_plan

    def execute_safe_cleanup(self, risk_levels: List[str] = None) -> Dict[str, Any]:
        """执行安全的清理操作"""
        if risk_levels is None:
            risk_levels = ['low_risk']  # 默认只清理低风险模块

        logger.info(f"开始安全清理，风险等级: {risk_levels}")

        cleanup_result = {
            'processed': 0,
            'backed_up': 0,
            'skipped': 0,
            'errors': 0,
            'backup_dir': str(self.backup_dir)
        }

        for risk_level in risk_levels:
            if risk_level not in self.cleanup_plan:
                logger.warning(f"未知风险等级: {risk_level}")
                continue

            modules_to_clean = self.cleanup_plan[risk_level]

            for module in modules_to_clean:
                try:
                    # 备份文件
                    source_path = self.utils_dir / module
                    backup_path = self.backup_dir / module

                    if source_path.exists():
                        # 创建备份
                        import shutil
                        shutil.copy2(source_path, backup_path)
                        cleanup_result['backed_up'] += 1

                        # 这里不实际删除，只是备份
                        # shutil.move(source_path, source_path.with_suffix('.bak'))
                        logger.info(f"已备份模块: {module}")
                        cleanup_result['processed'] += 1
                    else:
                        logger.warning(f"模块不存在: {module}")
                        cleanup_result['skipped'] += 1

                except Exception as e:
                    logger.error(f"清理模块失败 {module}: {e}")
                    cleanup_result['errors'] += 1

        logger.info(f"安全清理完成: {cleanup_result}")
        return cleanup_result

    def restore_modules(self, modules: List[str] = None) -> int:
        """恢复已备份的模块"""
        restored_count = 0

        try:
            if modules is None:
                # 恢复所有备份的模块
                backup_files = list(self.backup_dir.glob("*.py"))
            else:
                backup_files = [self.backup_dir / module for module in modules]

            for backup_file in backup_files:
                if backup_file.exists():
                    target_file = self.utils_dir / backup_file.name

                    # 恢复文件
                    import shutil
                    shutil.copy2(backup_file, target_file)
                    restored_count += 1

                    logger.info(f"已恢复模块: {backup_file.name}")

        except Exception as e:
            logger.error(f"恢复模块失败: {e}")

        return restored_count

    def generate_cleanup_report(self) -> str:
        """生成清理报告"""
        report = []
        report.append("模块清理分析报告")
        report.append("=" * config.DEFAULT_TOP_K0)

        total_modules = sum(len(modules) for modules in self.cleanup_plan.values())
        report.append(f"总模块数: {total_modules}")

        for risk_level, modules in self.cleanup_plan.items():
            report.append(f"\n{risk_level.upper()} ({len(modules)} 个):")
            for module in modules[:config.DEFAULT_SMALL_LIMIT]:  # 只显示前config.DEFAULT_SMALL_LIMIT个
                report.append(f"  • {module}")
            if len(modules) > config.DEFAULT_SMALL_LIMIT:
                report.append(f"  ... 还有 {len(modules) - config.DEFAULT_SMALL_LIMIT} 个")

        report.append("\n备份目录:")
        report.append(f"  {self.backup_dir}")

        report.append("\n⚠️ 注意事项:")
        report.append("• 建议先备份所有文件")
        report.append("• 从低风险模块开始清理")
        report.append("• 清理后进行全面测试")
        report.append("• 可使用restore_modules()恢复")

        return "\n".join(report)


# ===== 便捷函数 =====

def analyze_and_plan_cleanup() -> ModuleCleanupManager:
    """分析模块并制定清理计划"""
    manager = ModuleCleanupManager()

    # 分析模块
    analysis = manager.analyze_modules()

    # 生成清理计划
    cleanup_plan = manager.generate_cleanup_plan(analysis)

    # 生成报告
    report = manager.generate_cleanup_report()
    print(report)

    return manager

def execute_low_risk_cleanup() -> Dict[str, Any]:
    """执行低风险模块清理"""
    manager = analyze_and_plan_cleanup()
    return manager.execute_safe_cleanup(['low_risk'])

if __name__ == "__main__":
    # 分析并制定清理计划
    manager = analyze_and_plan_cleanup()

    # 可选：执行低风险清理
    # result = manager.execute_safe_cleanup(['low_risk'])
    # print(f"清理结果: {result}")
