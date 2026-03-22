#!/usr/bin/env python3
"""
文档与代码同步管理系统

提供命令行接口来管理文档与代码的同步更新。
"""

import asyncio
import argparse
import logging
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.documentation_sync_system import get_sync_system
from src.core.change_detection_system import get_change_detection_system
from src.core.documentation_update_trigger import get_documentation_update_trigger
from src.core.quality_assurance_system import get_quality_assurance_system
from src.core.version_control_integration import get_version_control_integration

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DocumentationSyncManager:
    """文档同步管理器"""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or Path(__file__).parent.parent / "config" / "documentation_sync_config.yaml"
        self.config = self._load_config()

        # 初始化系统组件
        self._init_system_components()

        # 初始化数据目录
        self._ensure_data_directories()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if not self.config_path.exists():
                logger.warning(f"配置文件不存在: {self.config_path}, 使用默认配置")
                return self._get_default_config()

            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            logger.info(f"已加载配置文件: {self.config_path}")
            return config

        except Exception as e:
            logger.error(f"加载配置文件失败: {e}, 使用默认配置")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'monitoring': {
                'source_dirs': ['src'],
                'doc_dirs': ['docs'],
                'doc_filter_mode': 'all',
                'ignored_patterns': ['__pycache__', '*.pyc', '*.pyo', '.git']
            }
        }

    def _init_system_components(self):
        """初始化系统组件"""
        monitoring_config = self.config.get('monitoring', {})
        filter_config = {
            'doc_filter_mode': monitoring_config.get('doc_filter_mode', 'all'),
            'selective_docs': monitoring_config.get('selective_docs', []),
            'categorized_docs': monitoring_config.get('categorized_docs', {})
        }

        # 创建同步系统实例（使用单例模式的替代方案）
        from src.core.documentation_sync_system import DocumentationSyncSystem
        self.sync_system = DocumentationSyncSystem(
            source_dirs=monitoring_config.get('source_dirs', ['src']),
            doc_dirs=monitoring_config.get('doc_dirs', ['docs']),
            filter_config=filter_config
        )

        self.change_detector = get_change_detection_system()
        self.update_trigger = get_documentation_update_trigger()
        self.quality_assurance = get_quality_assurance_system()
        self.version_control = get_version_control_integration()

    def _ensure_data_directories(self):
        """确保数据目录存在"""
        directories = [
            'data',
            'reports',
            'logs',
            'reports/sync_reports',
            'reports/quality_reports',
            'reports/version_reports'
        ]

        for dir_path in directories:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

    async def initialize_system(self):
        """初始化系统"""
        logger.info("初始化文档同步系统...")

        try:
            # 初始化版本控制集成
            vc_initialized = await self.version_control.initialize_version_control()
            if not vc_initialized:
                logger.warning("版本控制集成初始化失败，将在只读模式下运行")

            # 初始化变更检测系统
            # 这里可以添加更多的初始化逻辑

            logger.info("文档同步系统初始化完成")
            return True

        except Exception as e:
            logger.error(f"系统初始化失败: {e}")
            return False

    async def perform_full_sync_check(self) -> Dict[str, Any]:
        """执行完整同步检查"""
        logger.info("执行完整同步检查...")

        try:
            # 1. 执行同步检查
            sync_report = await self.sync_system.perform_sync_check()

            # 2. 执行质量检查
            quality_report = await self.quality_assurance.perform_quality_check(sync_report)

            # 3. 执行版本控制同步
            version_result = await self.version_control.perform_version_controlled_sync(
                sync_report, quality_report
            )

            # 4. 生成综合报告
            summary = {
                'timestamp': sync_report.scan_time.isoformat(),
                'sync_status': sync_report.sync_status,
                'changes_detected': len(sync_report.changes),
                'quality_score': quality_report.overall_score,
                'issues_found': quality_report.total_issues,
                'version_control_actions': version_result.get('actions_taken', []),
                'recommendations': sync_report.recommendations + quality_report.recommendations
            }

            logger.info(f"完整同步检查完成: 状态={sync_report.sync_status}, 质量评分={quality_report.overall_score:.1f}")
            return summary

        except Exception as e:
            logger.error(f"完整同步检查失败: {e}")
            return {'error': str(e), 'status': 'failed'}

    async def perform_manual_sync(self, sync_type: str = "auto_update") -> Dict[str, Any]:
        """执行手动同步"""
        logger.info(f"执行手动同步: {sync_type}")

        try:
            result = await self.update_trigger.trigger_manual_sync(sync_type)
            logger.info(f"手动同步完成: {result.action_taken}")
            return {
                'trigger_id': result.trigger_id,
                'success': result.success,
                'action_taken': result.action_taken,
                'execution_time': result.execution_time,
                'result_data': result.result_data
            }

        except Exception as e:
            logger.error(f"手动同步失败: {e}")
            return {'error': str(e), 'status': 'failed'}

    async def generate_all_reports(self) -> Dict[str, Any]:
        """生成所有报告"""
        logger.info("生成所有报告...")

        try:
            results = {}

            # 生成同步报告
            sync_report = await self.sync_system.perform_sync_check()
            await self.sync_system.export_report(
                sync_report,
                'reports/sync_reports/latest_sync_report.md'
            )
            results['sync_report'] = 'reports/sync_reports/latest_sync_report.md'

            # 生成质量报告
            quality_report = await self.quality_assurance.perform_quality_check(sync_report)
            await self.quality_assurance.export_quality_report(
                quality_report,
                'reports/quality_reports/latest_quality_report.md'
            )
            results['quality_report'] = 'reports/quality_reports/latest_quality_report.md'

            # 生成版本报告
            await self.version_control.export_version_report(
                'reports/version_reports/latest_version_report.md'
            )
            results['version_report'] = 'reports/version_reports/latest_version_report.md'

            # 生成综合报告
            summary_report = await self._generate_summary_report(sync_report, quality_report)
            results['summary_report'] = 'reports/summary_report.md'

            logger.info("所有报告生成完成")
            return results

        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            return {'error': str(e), 'status': 'failed'}

    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            status = {
                'sync_system': {
                    'last_report_time': self.sync_system.last_report.scan_time.isoformat()
                    if self.sync_system.last_report else None,
                    'last_sync_status': self.sync_system.last_report.sync_status
                    if self.sync_system.last_report else None
                },
                'change_detector': await self.change_detector.get_detection_stats(),
                'update_trigger': await self.update_trigger.get_system_status(),
                'quality_assurance': {
                    'baseline_score': self.quality_assurance.baseline_score,
                    'total_reports': len(self.quality_assurance.quality_history)
                },
                'version_control': await self.version_control.get_version_control_status()
            }

            return status

        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return {'error': str(e), 'status': 'error'}

    async def start_continuous_monitoring(self):
        """启动持续监控"""
        logger.info("启动持续监控模式...")

        try:
            # 启动变更检测
            detection_task = asyncio.create_task(self.change_detector.start_detection())

            # 启动更新触发器
            trigger_task = asyncio.create_task(self.update_trigger.start_all_triggers())

            # 等待任务完成
            await asyncio.gather(detection_task, trigger_task)

        except KeyboardInterrupt:
            logger.info("收到中断信号，正在停止监控...")
            self.change_detector.stop_detection()
            self.update_trigger.stop_all_triggers()

        except Exception as e:
            logger.error(f"持续监控异常: {e}")

    async def _generate_summary_report(self, sync_report, quality_report) -> str:
        """生成综合报告"""
        lines = []

        lines.append("# 文档同步系统综合报告")
        lines.append("")
        lines.append(f"**生成时间**: {sync_report.scan_time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        lines.append("## 📊 系统概览")
        lines.append("")
        lines.append(f"- 同步状态: {sync_report.sync_status}")
        lines.append(f"- 变更数量: {len(sync_report.changes)}")
        lines.append(f"- 冲突数量: {len(sync_report.conflicts)}")
        lines.append(f"- 质量评分: {quality_report.overall_score:.1f}/100")
        lines.append(f"- 问题数量: {quality_report.total_issues}")
        lines.append("")

        lines.append("## 🔍 详细状态")
        lines.append("")

        # 同步状态详情
        lines.append("### 同步检查结果")
        lines.append("")
        lines.append(f"- 代码实体: {len(sync_report.code_entities)}")
        lines.append(f"- 文档实体: {len(sync_report.doc_entities)}")
        lines.append("")

        if sync_report.changes:
            lines.append("最近变更:")
            for change in sync_report.changes[:5]:
                lines.append(f"- {change.change_type}: {change.entity_name}")
            lines.append("")

        # 质量状态详情
        lines.append("### 质量检查结果")
        lines.append("")
        lines.append(f"- 总体评分: {quality_report.overall_score:.1f}/100")
        lines.append(f"- 符合度评分: {quality_report.compliance_score:.1f}/100")
        lines.append("")

        if quality_report.issues_by_severity:
            lines.append("问题严重程度分布:")
            for severity, count in quality_report.issues_by_severity.items():
                severity_icon = {"critical": "🔴", "major": "🟠", "minor": "🟡", "info": "ℹ️"}.get(severity, "❓")
                lines.append(f"- {severity_icon} {severity}: {count}")
            lines.append("")

        # 建议
        all_recommendations = sync_report.recommendations + quality_report.recommendations
        if all_recommendations:
            lines.append("## 💡 系统建议")
            lines.append("")
            for rec in all_recommendations[:10]:
                lines.append(f"- {rec}")
            lines.append("")

        # 保存报告
        report_path = Path('reports/summary_report.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        return str(report_path)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="文档与代码同步管理系统")
    parser.add_argument('command', choices=[
        'init', 'sync', 'manual-sync', 'reports', 'status', 'monitor'
    ], help="要执行的命令")
    parser.add_argument('--sync-type', choices=['check_only', 'auto_update', 'full_regeneration'],
                       default='auto_update', help="同步类型")
    parser.add_argument('--output-dir', default='reports', help="输出目录")
    parser.add_argument('--verbose', '-v', action='store_true', help="详细输出")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 创建管理器
    manager = DocumentationSyncManager()

    try:
        if args.command == 'init':
            # 初始化系统
            success = await manager.initialize_system()
            if success:
                print("✅ 系统初始化完成")
            else:
                print("❌ 系统初始化失败")
                sys.exit(1)

        elif args.command == 'sync':
            # 执行完整同步检查
            result = await manager.perform_full_sync_check()
            if 'error' not in result:
                print("✅ 同步检查完成")
                print(f"状态: {result['sync_status']}")
                print(f"变更: {result['changes_detected']}")
                print(f"质量评分: {result.get('quality_score', 'N/A')}")
            else:
                print(f"❌ 同步检查失败: {result['error']}")
                sys.exit(1)

        elif args.command == 'manual-sync':
            # 执行手动同步
            result = await manager.perform_manual_sync(args.sync_type)
            if result.get('success', False):
                print("✅ 手动同步完成")
                print(f"操作: {result['action_taken']}")
                print(f"执行时间: {result['execution_time']:.2f}秒")
            else:
                print(f"❌ 手动同步失败: {result.get('error', '未知错误')}")
                sys.exit(1)

        elif args.command == 'reports':
            # 生成所有报告
            results = await manager.generate_all_reports()
            if 'error' not in results:
                print("✅ 报告生成完成")
                for report_type, path in results.items():
                    print(f"- {report_type}: {path}")
            else:
                print(f"❌ 报告生成失败: {results['error']}")
                sys.exit(1)

        elif args.command == 'status':
            # 获取系统状态
            status = await manager.get_system_status()
            print(json.dumps(status, indent=2, ensure_ascii=False, default=str))

        elif args.command == 'monitor':
            # 启动持续监控
            print("启动持续监控模式 (按Ctrl+C停止)...")
            await manager.start_continuous_monitoring()

    except KeyboardInterrupt:
        print("\n收到中断信号，正在退出...")
    except Exception as e:
        logger.error(f"命令执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
