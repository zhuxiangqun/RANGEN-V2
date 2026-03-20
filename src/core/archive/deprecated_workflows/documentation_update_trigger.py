"""
文档更新触发器

提供多种方式触发文档更新，确保文档与代码同步。
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import json
import aiohttp
from concurrent.futures import ThreadPoolExecutor

from .documentation_sync_system import DocumentationSyncSystem, SyncReport, get_sync_system

logger = logging.getLogger(__name__)


@dataclass
class UpdateTrigger:
    """更新触发器"""
    trigger_id: str
    trigger_type: str  # manual, automatic, scheduled, webhook
    condition: Dict[str, Any]
    action: str  # sync_check, auto_update, full_regeneration
    priority: int = 1
    enabled: bool = True
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0


@dataclass
class TriggerResult:
    """触发结果"""
    trigger_id: str
    success: bool
    action_taken: str
    result_data: Dict[str, Any]
    execution_time: float
    timestamp: datetime
    error_message: Optional[str] = None


class WebhookTrigger:
    """Webhook触发器"""

    def __init__(self, port: int = 8080, path: str = "/webhook/docs-sync",
                 config: Dict[str, Any] = None):
        self.port = port
        self.path = path
        self.config = config or {}
        self.server = None
        self.handlers: Dict[str, Callable] = {}

        # 安全配置
        self.security_config = self.config.get('security', {})
        self.allowed_tokens = set(self.security_config.get('bearer_tokens', []))
        self.enable_signature_verification = self.security_config.get('enable_signature_verification', False)
        self.webhook_secret = self.security_config.get('webhook_secret', '')

        # 速率限制
        self.rate_limit_config = self.security_config.get('rate_limit', {})
        self.max_requests_per_minute = self.rate_limit_config.get('max_requests_per_minute', 10)
        self.request_counts: Dict[str, List[datetime]] = {}

        logger.info(f"Webhook触发器初始化: 端口 {port}, 路径 {path}, 安全验证 {'启用' if self.allowed_tokens else '禁用'}")

    async def start_webhook_server(self):
        """启动Webhook服务器"""
        try:
            from aiohttp import web

            app = web.Application()
            app.router.add_post(self.path, self._handle_webhook)

            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, 'localhost', self.port)
            await site.start()

            logger.info(f"Webhook服务器启动在 http://localhost:{self.port}{self.path}")

            # 保持服务器运行
            while True:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"启动Webhook服务器失败: {e}")

    async def _handle_webhook(self, request):
        """处理Webhook请求"""
        try:
            # 验证请求
            if not await self._validate_webhook_request(request):
                return aiohttp.web.Response(status=401, text="Unauthorized")

            # 解析请求数据
            data = await request.json()

            # 检查是否是相关的变更
            if self._is_relevant_change(data):
                # 触发文档同步
                result = await self._trigger_sync_from_webhook(data)

                return aiohttp.web.json_response({
                    'status': 'success',
                    'triggered_sync': True,
                    'result': result
                })
            else:
                return aiohttp.web.json_response({
                    'status': 'ignored',
                    'message': 'Change not relevant for documentation sync'
                })

        except Exception as e:
            logger.error(f"处理Webhook请求失败: {e}")
            return aiohttp.web.json_response({
                'status': 'error',
                'message': str(e)
            }, status=500)

    async def _validate_webhook_request(self, request) -> bool:
        """验证Webhook请求"""
        try:
            # 1. 检查速率限制
            client_ip = self._get_client_ip(request)
            if not self._check_rate_limit(client_ip):
                logger.warning(f"速率限制: IP {client_ip} 超出请求限制")
                return False

            # 2. Bearer Token验证
            if self.allowed_tokens:
                auth_header = request.headers.get('Authorization', '')
                if not auth_header.startswith('Bearer '):
                    logger.warning(f"无效的认证头: {auth_header[:20]}...")
                    return False

                token = auth_header[7:]  # 移除 "Bearer " 前缀
                if token not in self.allowed_tokens:
                    logger.warning(f"无效的Bearer token")
                    return False

            # 3. 签名验证（如果启用）
            if self.enable_signature_verification and self.webhook_secret:
                if not await self._verify_webhook_signature(request):
                    logger.warning("Webhook签名验证失败")
                    return False

            # 4. 检查请求内容类型
            if request.content_type != 'application/json':
                logger.warning(f"不支持的内容类型: {request.content_type}")
                return False

            # 5. 检查请求方法
            if request.method != 'POST':
                logger.warning(f"不支持的HTTP方法: {request.method}")
                return False

            return True

        except Exception as e:
            logger.error(f"Webhook验证过程中出错: {e}")
            return False

    def _get_client_ip(self, request) -> str:
        """获取客户端IP地址"""
        # 检查代理头
        x_forwarded_for = request.headers.get('X-Forwarded-For', '')
        if x_forwarded_for:
            # 取第一个IP（最原始的客户端IP）
            return x_forwarded_for.split(',')[0].strip()

        # 检查其他代理头
        x_real_ip = request.headers.get('X-Real-IP', '')
        if x_real_ip:
            return x_real_ip

        # 使用直接连接的IP
        peername = request.transport.get_extra_info('peername')
        if peername:
            return peername[0]

        return 'unknown'

    def _check_rate_limit(self, client_ip: str) -> bool:
        """检查速率限制"""
        now = datetime.now()
        cutoff_time = now - timedelta(minutes=1)

        # 清理过期的请求记录
        if client_ip in self.request_counts:
            self.request_counts[client_ip] = [
                timestamp for timestamp in self.request_counts[client_ip]
                if timestamp > cutoff_time
            ]
        else:
            self.request_counts[client_ip] = []

        # 检查是否超过限制
        if len(self.request_counts[client_ip]) >= self.max_requests_per_minute:
            return False

        # 记录当前请求
        self.request_counts[client_ip].append(now)
        return True

    async def _verify_webhook_signature(self, request) -> bool:
        """验证Webhook签名"""
        try:
            import hmac
            import hashlib

            signature_header = request.headers.get('X-Hub-Signature-256', '')
            if not signature_header.startswith('sha256='):
                return False

            expected_signature = signature_header[7:]  # 移除 "sha256=" 前缀

            # 读取请求体
            body = await request.read()

            # 计算预期签名
            secret_bytes = self.webhook_secret.encode('utf-8')
            body_hash = hmac.new(secret_bytes, body, hashlib.sha256).hexdigest()

            # 使用安全的比较方式防止时序攻击
            return hmac.compare_digest(expected_signature, body_hash)

        except Exception as e:
            logger.error(f"签名验证失败: {e}")
            return False

    def _is_relevant_change(self, webhook_data: Dict[str, Any]) -> bool:
        """检查是否是相关的变更"""
        # 检查是否包含源代码或文档的变更
        commits = webhook_data.get('commits', [])

        for commit in commits:
            added_files = commit.get('added', [])
            modified_files = commit.get('modified', [])
            removed_files = commit.get('removed', [])

            all_files = added_files + modified_files + removed_files

            # 检查是否有相关的文件变更
            for file_path in all_files:
                if (file_path.startswith(('src/', 'docs/')) and
                    file_path.endswith(('.py', '.md', '.rst', '.txt'))):
                    return True

        return False

    async def _trigger_sync_from_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """从Webhook触发同步"""
        sync_system = get_sync_system()

        # 执行同步检查
        report = await sync_system.perform_sync_check()

        # 执行自动更新
        update_result = await sync_system.perform_auto_update(report)

        return {
            'sync_status': report.sync_status,
            'changes_detected': len(report.changes),
            'documents_updated': len(update_result.get('updated', [])),
            'conflicts_found': len(report.conflicts)
        }


class ScheduledTrigger:
    """定时触发器"""

    def __init__(self, schedule_config: Dict[str, Any]):
        self.schedule_config = schedule_config
        self.is_running = False

    async def start_scheduled_triggers(self):
        """启动定时触发器"""
        if self.is_running:
            return

        self.is_running = True
        logger.info("启动定时触发器")

        try:
            while self.is_running:
                # 计算下次执行时间
                next_run = self._calculate_next_run_time()
                wait_seconds = (next_run - datetime.now()).total_seconds()

                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)

                # 执行定时任务
                await self._execute_scheduled_task()

        except Exception as e:
            logger.error(f"定时触发器异常: {e}")
        finally:
            self.is_running = False

    def stop_scheduled_triggers(self):
        """停止定时触发器"""
        self.is_running = False
        logger.info("停止定时触发器")

    def _calculate_next_run_time(self) -> datetime:
        """计算下次执行时间"""
        # 支持cron表达式或简单的时间间隔
        schedule_type = self.schedule_config.get('type', 'interval')

        if schedule_type == 'interval':
            # 简单的间隔执行
            interval_hours = self.schedule_config.get('interval_hours', 24)
            return datetime.now() + timedelta(hours=interval_hours)
        elif schedule_type == 'daily':
            # 每天固定时间执行
            hour = self.schedule_config.get('hour', 2)  # 默认凌晨2点
            minute = self.schedule_config.get('minute', 0)

            now = datetime.now()
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

            if next_run <= now:
                next_run += timedelta(days=1)

            return next_run
        else:
            # 默认24小时执行一次
            return datetime.now() + timedelta(hours=24)

    async def _execute_scheduled_task(self):
        """执行定时任务"""
        try:
            logger.info("执行定时文档同步任务")

            sync_system = get_sync_system()

            # 执行同步检查
            report = await sync_system.perform_sync_check()

            # 检查是否需要更新
            if report.sync_status != 'synced':
                # 执行自动更新
                update_result = await sync_system.perform_auto_update(report)

                logger.info(f"定时同步完成: 检测到 {len(report.changes)} 个变更，更新了 {len(update_result.get('updated', []))} 个文档")

                # 生成报告
                await self._generate_scheduled_report(report, update_result)
            else:
                logger.info("定时同步检查: 文档与代码已同步")

        except Exception as e:
            logger.error(f"定时任务执行失败: {e}")

    async def _generate_scheduled_report(self, report: SyncReport, update_result: Dict[str, Any]):
        """生成定时报告"""
        try:
            report_dir = Path('reports/scheduled_sync')
            report_dir.mkdir(parents=True, exist_ok=True)

            report_file = report_dir / f"scheduled_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

            # 生成Markdown报告
            content = await self._format_scheduled_report(report, update_result)

            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"定时同步报告已生成: {report_file}")

        except Exception as e:
            logger.error(f"生成定时报告失败: {e}")

    async def _format_scheduled_report(self, report: SyncReport, update_result: Dict[str, Any]) -> str:
        """格式化定时报告"""
        lines = []

        lines.append("# 定时文档同步报告")
        lines.append("")
        lines.append(f"**执行时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**同步状态**: {report.sync_status}")
        lines.append("")

        lines.append("## 📊 执行统计")
        lines.append("")
        lines.append(f"- 代码实体数量: {len(report.code_entities)}")
        lines.append(f"- 文档实体数量: {len(report.doc_entities)}")
        lines.append(f"- 检测到变更: {len(report.changes)}")
        lines.append(f"- 更新文档数量: {len(update_result.get('updated', []))}")
        lines.append(f"- 发现冲突: {len(report.conflicts)}")
        lines.append("")

        if report.recommendations:
            lines.append("## 💡 推荐操作")
            lines.append("")
            for rec in report.recommendations:
                lines.append(f"- {rec}")
            lines.append("")

        return "\n".join(lines)


class ManualTrigger:
    """手动触发器"""

    def __init__(self):
        self.trigger_history: List[TriggerResult] = []

    async def trigger_manual_sync(self, trigger_type: str = "full_sync",
                                options: Dict[str, Any] = None) -> TriggerResult:
        """手动触发同步"""
        trigger_id = f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()

        try:
            logger.info(f"手动触发文档同步: {trigger_type}")

            sync_system = get_sync_system()

            if trigger_type == "check_only":
                # 仅检查，不更新
                report = await sync_system.perform_sync_check()
                result_data = {
                    'sync_status': report.sync_status,
                    'changes_found': len(report.changes),
                    'conflicts_found': len(report.conflicts),
                    'recommendations': report.recommendations
                }
                action_taken = "sync_check"

            elif trigger_type == "auto_update":
                # 执行自动更新
                report = await sync_system.perform_sync_check()
                update_result = await sync_system.perform_auto_update(report)
                result_data = {
                    'sync_status': report.sync_status,
                    'changes_found': len(report.changes),
                    'documents_updated': len(update_result.get('updated', [])),
                    'conflicts_found': len(report.conflicts)
                }
                action_taken = "auto_update"

            elif trigger_type == "full_regeneration":
                # 完整重新生成
                result_data = await self._perform_full_regeneration()
                action_taken = "full_regeneration"

            else:
                raise ValueError(f"不支持的触发类型: {trigger_type}")

            execution_time = (datetime.now() - start_time).total_seconds()

            result = TriggerResult(
                trigger_id=trigger_id,
                success=True,
                action_taken=action_taken,
                result_data=result_data,
                execution_time=execution_time,
                timestamp=datetime.now()
            )

            # 记录历史
            self.trigger_history.append(result)

            logger.info(f"手动触发完成: {action_taken}, 耗时 {execution_time:.2f}秒")
            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()

            result = TriggerResult(
                trigger_id=trigger_id,
                success=False,
                action_taken=trigger_type,
                result_data={},
                execution_time=execution_time,
                timestamp=datetime.now(),
                error_message=str(e)
            )

            self.trigger_history.append(result)

            logger.error(f"手动触发失败: {e}")
            return result

    async def _perform_full_regeneration(self) -> Dict[str, Any]:
        """执行完整文档重新生成"""
        # 这里可以实现完整的文档重新生成逻辑
        # 包括基于代码自动生成API文档、架构文档等

        sync_system = get_sync_system()

        # 执行完整扫描
        report = await sync_system.perform_sync_check()

        # 重新生成所有文档
        # 这里可以调用专门的文档生成器

        return {
            'full_scan_completed': True,
            'entities_processed': len(report.code_entities) + len(report.doc_entities),
            'regeneration_status': 'simulated'  # 暂时模拟
        }

    async def get_trigger_history(self, limit: int = 10) -> List[TriggerResult]:
        """获取触发历史"""
        return self.trigger_history[-limit:] if limit > 0 else self.trigger_history

    async def clear_trigger_history(self, days_to_keep: int = 30):
        """清理触发历史"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        self.trigger_history = [
            result for result in self.trigger_history
            if result.timestamp > cutoff_date
        ]

        logger.info(f"触发历史已清理，保留 {len(self.trigger_history)} 条记录")


class DocumentationUpdateTrigger:
    """文档更新触发器系统"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # 从配置中读取安全设置
        security_config = self.config.get('security', {})

        # 从配置中读取触发器设置
        update_trigger_config = self.config.get('update_trigger', {})

        webhook_config = update_trigger_config.get('webhook', {})
        self.webhook_trigger = WebhookTrigger(
            port=webhook_config.get('port', 8080),
            path=webhook_config.get('path', '/webhook/docs-sync'),
            config=security_config
        )

        scheduled_config = update_trigger_config.get('scheduled', {})
        self.scheduled_trigger = ScheduledTrigger({
            'type': 'daily',
            'hour': scheduled_config.get('hour', 2),
            'minute': scheduled_config.get('minute', 0)
        })

        self.manual_trigger = ManualTrigger()

        self.active_triggers: Dict[str, asyncio.Task] = {}

    async def start_all_triggers(self):
        """启动所有触发器"""
        logger.info("启动所有文档更新触发器")

        # 启动Webhook触发器
        webhook_task = asyncio.create_task(self.webhook_trigger.start_webhook_server())
        self.active_triggers['webhook'] = webhook_task

        # 启动定时触发器
        scheduled_task = asyncio.create_task(self.scheduled_trigger.start_scheduled_triggers())
        self.active_triggers['scheduled'] = scheduled_task

        logger.info("所有触发器已启动")

    def stop_all_triggers(self):
        """停止所有触发器"""
        logger.info("停止所有文档更新触发器")

        for name, task in self.active_triggers.items():
            if not task.done():
                task.cancel()

        self.scheduled_trigger.stop_scheduled_triggers()
        self.active_triggers.clear()

        logger.info("所有触发器已停止")

    async def trigger_manual_sync(self, trigger_type: str = "auto_update",
                                options: Dict[str, Any] = None) -> TriggerResult:
        """手动触发同步"""
        return await self.manual_trigger.trigger_manual_sync(trigger_type, options)

    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'webhook_active': 'webhook' in self.active_triggers and not self.active_triggers['webhook'].done(),
            'scheduled_active': 'scheduled' in self.active_triggers and not self.active_triggers['scheduled'].done(),
            'manual_trigger_history': len(await self.manual_trigger.get_trigger_history(limit=0)),
            'webhook_config': {
                'port': self.webhook_trigger.port,
                'path': self.webhook_trigger.path
            },
            'scheduled_config': self.scheduled_trigger.schedule_config
        }

    async def configure_scheduled_trigger(self, config: Dict[str, Any]):
        """配置定时触发器"""
        old_config = self.scheduled_trigger.schedule_config
        self.scheduled_trigger.schedule_config = config

        # 如果定时器正在运行，需要重启
        if 'scheduled' in self.active_triggers and not self.active_triggers['scheduled'].done():
            logger.info("重新配置定时触发器")
            self.scheduled_trigger.stop_scheduled_triggers()
            await asyncio.sleep(1)  # 等待停止完成

            # 重启定时触发器
            scheduled_task = asyncio.create_task(self.scheduled_trigger.start_scheduled_triggers())
            self.active_triggers['scheduled'] = scheduled_task

        logger.info(f"定时触发器配置已更新: {old_config} -> {config}")


# 全局单例实例
_update_trigger = None

def get_documentation_update_trigger() -> DocumentationUpdateTrigger:
    """获取文档更新触发器实例"""
    global _update_trigger
    if _update_trigger is None:
        _update_trigger = DocumentationUpdateTrigger()
    return _update_trigger
