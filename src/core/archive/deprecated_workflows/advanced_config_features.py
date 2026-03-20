"""
高级配置功能 - 热更新、分发、监控告警、权限管理

提供企业级的配置管理高级功能
"""

import os
import json
import time
import threading
import hashlib
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class HotReloadManager:
    """热更新管理器"""

    def __init__(self, config_system, check_interval: int = 30):
        self.config_system = config_system
        self.check_interval = check_interval
        self.last_check_time = datetime.now()
        self.file_hashes: Dict[str, str] = {}
        self.reload_callbacks: List[Callable] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start_monitoring(self):
        """开始监控配置文件变化"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("🔥 热更新监控已启动")

    def stop_monitoring(self):
        """停止监控"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("🛑 热更新监控已停止")

    def add_reload_callback(self, callback: Callable):
        """添加重载回调函数"""
        self.reload_callbacks.append(callback)

    def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                if self._check_config_files_changed():
                    logger.info("📁 检测到配置文件变更，触发热更新")
                    self._trigger_hot_reload()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"热更新监控错误: {e}")
                time.sleep(self.check_interval)

    def _check_config_files_changed(self) -> bool:
        """检查配置文件是否发生变化"""
        config_files = [
            "dynamic_config.json",
            "routing_config.json",
            "config_changes.log"
        ]

        changed = False
        for file_path in config_files:
            if os.path.exists(file_path):
                current_hash = self._calculate_file_hash(file_path)
                if file_path not in self.file_hashes or self.file_hashes[file_path] != current_hash:
                    self.file_hashes[file_path] = current_hash
                    changed = True

        return changed

    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""

    def _trigger_hot_reload(self):
        """触发热更新"""
        try:
            # 重新加载配置
            if hasattr(self.config_system, 'load_config'):
                self.config_system.load_config()

            # 执行回调函数
            for callback in self.reload_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"热更新回调执行失败: {e}")

            logger.info("✅ 热更新完成")

        except Exception as e:
            logger.error(f"热更新失败: {e}")

class ConfigDistributionManager:
    """配置分发管理器"""

    def __init__(self, config_system, distribution_strategy: str = "push"):
        self.config_system = config_system
        self.distribution_strategy = distribution_strategy
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.sync_status: Dict[str, str] = {}
        self._sync_thread: Optional[threading.Thread] = None
        self._running = False

    def register_node(self, node_id: str, node_info: Dict[str, Any]):
        """注册节点"""
        self.nodes[node_id] = {
            **node_info,
            'registered_at': datetime.now().isoformat(),
            'last_sync': None,
            'sync_status': 'pending'
        }
        self.sync_status[node_id] = 'pending'
        logger.info(f"📡 已注册配置分发节点: {node_id}")

    def unregister_node(self, node_id: str):
        """注销节点"""
        if node_id in self.nodes:
            del self.nodes[node_id]
            if node_id in self.sync_status:
                del self.sync_status[node_id]
            logger.info(f"📡 已注销配置分发节点: {node_id}")

    def start_distribution(self):
        """启动配置分发"""
        if self._running:
            return

        self._running = True
        self._sync_thread = threading.Thread(target=self._distribution_loop, daemon=True)
        self._sync_thread.start()
        logger.info("🚀 配置分发服务已启动")

    def stop_distribution(self):
        """停止配置分发"""
        self._running = False
        if self._sync_thread:
            self._sync_thread.join(timeout=5)
        logger.info("🛑 配置分发服务已停止")

    def _distribution_loop(self):
        """分发循环"""
        while self._running:
            try:
                self._sync_configs_to_nodes()
                time.sleep(60)  # 每分钟同步一次
            except Exception as e:
                logger.error(f"配置分发错误: {e}")
                time.sleep(60)

    def _sync_configs_to_nodes(self):
        """同步配置到节点"""
        current_config = self._get_current_config()

        for node_id, node_info in self.nodes.items():
            try:
                if self.distribution_strategy == "push":
                    self._push_config_to_node(node_id, node_info, current_config)
                elif self.distribution_strategy == "pull":
                    self._notify_node_to_pull(node_id, node_info)

                self.sync_status[node_id] = 'success'
                self.nodes[node_id]['last_sync'] = datetime.now().isoformat()

            except Exception as e:
                self.sync_status[node_id] = 'failed'
                logger.error(f"节点 {node_id} 配置同步失败: {e}")

    def _push_config_to_node(self, node_id: str, node_info: Dict[str, Any], config: Dict[str, Any]):
        """推送配置到节点"""
        # 这里实现具体的推送逻辑
        # 例如通过HTTP API、消息队列等
        endpoint = node_info.get('endpoint')
        if endpoint:
            # 模拟推送
            logger.info(f"📤 推送配置到节点 {node_id}: {endpoint}")

    def _notify_node_to_pull(self, node_id: str, node_info: Dict[str, Any]):
        """通知节点拉取配置"""
        # 发送拉取通知
        logger.info(f"📥 通知节点 {node_id} 拉取配置")

    def _get_current_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        if hasattr(self.config_system, 'get_routing_config'):
            return self.config_system.get_routing_config()
        return {}

    def get_distribution_status(self) -> Dict[str, Any]:
        """获取分发状态"""
        return {
            'total_nodes': len(self.nodes),
            'active_nodes': len([n for n in self.sync_status.values() if n == 'success']),
            'failed_nodes': len([n for n in self.sync_status.values() if n == 'failed']),
            'node_status': self.sync_status,
            'nodes': self.nodes
        }

class AlertManager:
    """告警管理器"""

    def __init__(self):
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
        self.alert_channels: Dict[str, Callable] = {}
        self.alert_history: List[Dict[str, Any]] = []

    def add_alert_rule(self, rule_id: str, rule_config: Dict[str, Any]):
        """添加告警规则"""
        self.alert_rules[rule_id] = rule_config
        logger.info(f"🚨 已添加告警规则: {rule_id}")

    def add_alert_channel(self, channel_name: str, sender: Callable):
        """添加告警通道"""
        self.alert_channels[channel_name] = sender
        logger.info(f"📢 已添加告警通道: {channel_name}")

    def trigger_alert(self, alert_id: str, alert_data: Dict[str, Any]):
        """触发告警"""
        if alert_id in self.active_alerts:
            # 更新现有告警
            self.active_alerts[alert_id]['last_triggered'] = datetime.now().isoformat()
            self.active_alerts[alert_id]['trigger_count'] += 1
        else:
            # 创建新告警
            alert = {
                'id': alert_id,
                'data': alert_data,
                'created_at': datetime.now().isoformat(),
                'last_triggered': datetime.now().isoformat(),
                'trigger_count': 1,
                'status': 'active'
            }
            self.active_alerts[alert_id] = alert

        # 发送告警通知
        self._send_alert_notifications(alert_id, alert_data)

        # 记录告警历史
        self.alert_history.append({
            'alert_id': alert_id,
            'timestamp': datetime.now().isoformat(),
            'data': alert_data
        })

        # 保留最近1000条历史记录
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]

        logger.warning(f"🚨 告警触发: {alert_id}")

    def resolve_alert(self, alert_id: str):
        """解决告警"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id]['status'] = 'resolved'
            self.active_alerts[alert_id]['resolved_at'] = datetime.now().isoformat()
            logger.info(f"✅ 告警已解决: {alert_id}")

    def get_alert_status(self) -> Dict[str, Any]:
        """获取告警状态"""
        return {
            'active_alerts': len(self.active_alerts),
            'total_alerts_today': len([a for a in self.alert_history
                                     if a['timestamp'].startswith(datetime.now().strftime('%Y-%m-%d'))]),
            'alert_rules': len(self.alert_rules),
            'alert_channels': list(self.alert_channels.keys()),
            'active_alert_details': self.active_alerts
        }

    def _send_alert_notifications(self, alert_id: str, alert_data: Dict[str, Any]):
        """发送告警通知"""
        for channel_name, sender in self.alert_channels.items():
            try:
                sender(alert_id, alert_data)
            except Exception as e:
                logger.error(f"告警通道 {channel_name} 发送失败: {e}")

class AccessControlManager:
    """访问控制管理器"""

    def __init__(self):
        self.roles: Dict[str, Dict[str, Any]] = {}
        self.users: Dict[str, Dict[str, Any]] = {}
        self.permissions: Dict[str, List[str]] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.audit_log: List[Dict[str, Any]] = []

        self._load_default_roles()

    def _load_default_roles(self):
        """加载默认角色"""
        self.roles = {
            'admin': {
                'name': '管理员',
                'permissions': ['*'],  # 所有权限
                'description': '完全访问权限'
            },
            'operator': {
                'name': '运维人员',
                'permissions': [
                    'config.read',
                    'config.update.thresholds',
                    'config.update.keywords',
                    'config.monitor'
                ],
                'description': '配置运维权限'
            },
            'developer': {
                'name': '开发人员',
                'permissions': [
                    'config.read',
                    'config.update.templates',
                    'config.test'
                ],
                'description': '开发调试权限'
            },
            'viewer': {
                'name': '查看者',
                'permissions': [
                    'config.read',
                    'config.monitor'
                ],
                'description': '只读权限'
            }
        }

    def add_user(self, user_id: str, user_info: Dict[str, Any]):
        """添加用户"""
        self.users[user_id] = {
            **user_info,
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        logger.info(f"👤 已添加用户: {user_id}")

    def assign_role(self, user_id: str, role_name: str):
        """分配角色"""
        if user_id not in self.users:
            raise ValueError(f"用户 {user_id} 不存在")

        if role_name not in self.roles:
            raise ValueError(f"角色 {role_name} 不存在")

        self.users[user_id]['role'] = role_name
        logger.info(f"🔑 已为用户 {user_id} 分配角色: {role_name}")

    def check_permission(self, user_id: str, permission: str) -> bool:
        """检查权限"""
        if user_id not in self.users:
            return False

        user = self.users[user_id]
        if user.get('status') != 'active':
            return False

        role_name = user.get('role')
        if not role_name or role_name not in self.roles:
            return False

        role_permissions = self.roles[role_name]['permissions']

        # 检查通配符权限
        if '*' in role_permissions:
            return True

        # 检查具体权限
        return permission in role_permissions

    def create_session(self, user_id: str, ip_address: str = "") -> Optional[str]:
        """创建会话"""
        if user_id not in self.users:
            return None

        session_id = hashlib.md5(f"{user_id}_{datetime.now().isoformat()}".encode()).hexdigest()[:16]

        self.sessions[session_id] = {
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'ip_address': ip_address,
            'status': 'active'
        }

        # 记录审计日志
        self._audit_log('session_created', user_id, {'session_id': session_id, 'ip_address': ip_address})

        return session_id

    def validate_session(self, session_id: str) -> Optional[str]:
        """验证会话"""
        session = self.sessions.get(session_id)
        if not session or session['status'] != 'active':
            return None

        # 检查会话是否过期（24小时）
        created_at = datetime.fromisoformat(session['created_at'])
        if datetime.now() - created_at > timedelta(hours=24):
            session['status'] = 'expired'
            return None

        # 更新最后活动时间
        session['last_activity'] = datetime.now().isoformat()

        return session['user_id']

    def destroy_session(self, session_id: str):
        """销毁会话"""
        if session_id in self.sessions:
            user_id = self.sessions[session_id]['user_id']
            self.sessions[session_id]['status'] = 'destroyed'
            self._audit_log('session_destroyed', user_id, {'session_id': session_id})

    def authorize_action(self, session_id: str, action: str, resource: str = "") -> bool:
        """授权操作"""
        user_id = self.validate_session(session_id)
        if not user_id:
            return False

        permission = f"{action}"
        if resource:
            permission = f"{action}.{resource}"

        has_permission = self.check_permission(user_id, permission)

        # 记录审计日志
        self._audit_log('action_attempt', user_id, {
            'action': action,
            'resource': resource,
            'authorized': has_permission,
            'session_id': session_id
        })

        return has_permission

    def _audit_log(self, event_type: str, user_id: str, details: Dict[str, Any]):
        """审计日志"""
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'details': details
        }

        self.audit_log.append(audit_entry)

        # 保留最近5000条审计记录
        if len(self.audit_log) > 5000:
            self.audit_log = self.audit_log[-5000:]

    def get_audit_log(self, user_id: str = None, event_type: str = None,
                     limit: int = 100) -> List[Dict[str, Any]]:
        """获取审计日志"""
        logs = self.audit_log

        if user_id:
            logs = [log for log in logs if log['user_id'] == user_id]

        if event_type:
            logs = [log for log in logs if log['event_type'] == event_type]

        return logs[-limit:]

    def get_access_status(self) -> Dict[str, Any]:
        """获取访问状态"""
        active_sessions = len([s for s in self.sessions.values() if s['status'] == 'active'])

        return {
            'total_users': len(self.users),
            'active_users': len([u for u in self.users.values() if u.get('status') == 'active']),
            'total_roles': len(self.roles),
            'active_sessions': active_sessions,
            'recent_audit_events': len(self.audit_log[-100:])  # 最近100条审计事件
        }

class NotificationManager:
    """通知管理器"""

    def __init__(self):
        self.channels: Dict[str, Callable] = {}
        self.templates: Dict[str, str] = {}
        self._load_default_templates()

    def _load_default_templates(self):
        """加载默认通知模板"""
        self.templates = {
            'config_changed': "配置已变更 - {change_type}: {details}",
            'alert_triggered': "🚨 配置告警 - {alert_id}: {message}",
            'system_error': "❌ 系统错误 - {error_type}: {message}",
            'maintenance_notice': "🔧 维护通知 - {maintenance_type}: {message}"
        }

    def add_channel(self, name: str, sender: Callable):
        """添加通知通道"""
        self.channels[name] = sender

    def send_notification(self, template_name: str, context: Dict[str, Any],
                         channels: List[str] = None):
        """发送通知"""
        if template_name not in self.templates:
            logger.error(f"通知模板 {template_name} 不存在")
            return

        message = self.templates[template_name].format(**context)

        target_channels = channels or list(self.channels.keys())

        for channel_name in target_channels:
            if channel_name in self.channels:
                try:
                    self.channels[channel_name](message, context)
                except Exception as e:
                    logger.error(f"通知通道 {channel_name} 发送失败: {e}")

    def add_template(self, name: str, template: str):
        """添加通知模板"""
        self.templates[name] = template

class AdvancedConfigSystem:
    """完整的先进配置系统"""

    def __init__(self):
        # 核心组件
        from src.core.dynamic_config_system import DynamicConfigManager
        self.config_manager = DynamicConfigManager()

        # 高级功能组件
        self.hot_reload = HotReloadManager(self.config_manager.config)
        self.distribution = ConfigDistributionManager(self.config_manager)
        self.alert_manager = AlertManager()
        self.access_control = AccessControlManager()
        self.notifications = NotificationManager()

        # 设置默认告警规则
        self._setup_default_alert_rules()

        # 设置默认通知通道
        self._setup_default_notification_channels()

    def _setup_default_alert_rules(self):
        """设置默认告警规则"""
        self.alert_manager.add_alert_rule('config_validation_failed', {
            'name': '配置验证失败',
            'severity': 'high',
            'channels': ['console', 'log']
        })

        self.alert_manager.add_alert_rule('config_sync_failed', {
            'name': '配置同步失败',
            'severity': 'medium',
            'channels': ['console']
        })

    def _setup_default_notification_channels(self):
        """设置默认通知通道"""
        # 控制台通知
        self.notifications.add_channel('console', self._console_notification)

        # 日志通知
        self.notifications.add_channel('log', self._log_notification)

    def _console_notification(self, message: str, context: Dict[str, Any]):
        """控制台通知"""
        print(f"[NOTIFICATION] {message}")

    def _log_notification(self, message: str, context: Dict[str, Any]):
        """日志通知"""
        logger.info(f"NOTIFICATION: {message}")

    def start_all_services(self):
        """启动所有高级服务"""
        self.hot_reload.start_monitoring()
        self.distribution.start_distribution()
        logger.info("🚀 所有高级配置服务已启动")

    def stop_all_services(self):
        """停止所有高级服务"""
        self.hot_reload.stop_monitoring()
        self.distribution.stop_distribution()
        logger.info("🛑 所有高级配置服务已停止")

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'config_status': self.config_manager.get_config_status(),
            'distribution_status': self.distribution.get_distribution_status(),
            'alert_status': self.alert_manager.get_alert_status(),
            'access_status': self.access_control.get_access_status(),
            'services': {
                'hot_reload': 'running' if self.hot_reload._running else 'stopped',
                'distribution': 'running' if self.distribution._running else 'stopped'
            }
        }
