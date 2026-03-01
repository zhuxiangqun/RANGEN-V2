#!/usr/bin/env python3
"""
高可用性和容灾系统

提供负载均衡、故障转移、数据同步等高可用功能
"""

import os
import json
import time
import threading
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import subprocess

logger = logging.getLogger(__name__)

class LoadBalancer:
    """负载均衡器"""

    def __init__(self, nodes: List[Dict[str, Any]]):
        self.nodes = nodes
        self.health_checks = {}
        self.current_index = 0
        self.lock = threading.Lock()

        # 启动健康检查
        self._start_health_checks()

    def get_next_node(self, strategy: str = 'round_robin') -> Optional[Dict[str, Any]]:
        """获取下一个可用节点"""

        with self.lock:
            healthy_nodes = [node for node in self.nodes
                           if self._is_node_healthy(node)]

            if not healthy_nodes:
                logger.error("没有健康的节点可用")
                return None

            if strategy == 'round_robin':
                node = healthy_nodes[self.current_index % len(healthy_nodes)]
                self.current_index += 1
            elif strategy == 'least_connections':
                node = min(healthy_nodes, key=lambda x: x.get('connections', 0))
            elif strategy == 'random':
                import random
                node = random.choice(healthy_nodes)
            else:
                node = healthy_nodes[0]

            # 增加连接数
            node['connections'] = node.get('connections', 0) + 1

            return node

    def release_connection(self, node: Dict[str, Any]):
        """释放连接"""
        with self.lock:
            if 'connections' in node:
                node['connections'] = max(0, node['connections'] - 1)

    def _is_node_healthy(self, node: Dict[str, Any]) -> bool:
        """检查节点是否健康"""
        node_id = node['id']
        last_check = self.health_checks.get(node_id, {})

        # 检查是否在检查间隔内
        now = time.time()
        if now - last_check.get('timestamp', 0) < 30:  # 30秒检查间隔
            return last_check.get('healthy', False)

        # 执行健康检查
        healthy = self._perform_health_check(node)
        self.health_checks[node_id] = {
            'healthy': healthy,
            'timestamp': now,
            'last_check': datetime.now().isoformat()
        }

        return healthy

    def _perform_health_check(self, node: Dict[str, Any]) -> bool:
        """执行健康检查"""
        try:
            import requests

            url = f"http://{node['host']}:{node['port']}/health"
            response = requests.get(url, timeout=5)

            return response.status_code == 200

        except Exception as e:
            logger.warning(f"节点健康检查失败 {node['id']}: {e}")
            return False

    def _start_health_checks(self):
        """启动健康检查线程"""

        def health_check_worker():
            while True:
                try:
                    # 更新所有节点的健康状态
                    for node in self.nodes:
                        self._is_node_healthy(node)
                    time.sleep(30)  # 每30秒检查一次
                except Exception as e:
                    logger.error(f"健康检查线程错误: {e}")
                    time.sleep(30)

        thread = threading.Thread(target=health_check_worker, daemon=True)
        thread.start()

    def get_status(self) -> Dict[str, Any]:
        """获取负载均衡器状态"""
        total_nodes = len(self.nodes)
        healthy_nodes = len([node for node in self.nodes if self._is_node_healthy(node)])

        return {
            'total_nodes': total_nodes,
            'healthy_nodes': healthy_nodes,
            'unhealthy_nodes': total_nodes - healthy_nodes,
            'nodes': [
                {
                    'id': node['id'],
                    'host': node['host'],
                    'port': node['port'],
                    'healthy': self._is_node_healthy(node),
                    'connections': node.get('connections', 0)
                }
                for node in self.nodes
            ]
        }


class FailoverManager:
    """故障转移管理器"""

    def __init__(self, primary_node: Dict[str, Any], standby_nodes: List[Dict[str, Any]]):
        self.primary_node = primary_node
        self.standby_nodes = standby_nodes
        self.current_primary = primary_node
        self.failover_history = []
        self.lock = threading.Lock()

        # 故障检测配置
        self.failure_threshold = 3  # 连续失败次数阈值
        self.health_check_interval = 10  # 健康检查间隔（秒）
        self.failover_timeout = 60  # 故障转移超时（秒）

        # 启动故障检测
        self._start_failover_monitoring()

    def check_and_failover(self) -> bool:
        """检查并执行故障转移"""

        with self.lock:
            if self._is_primary_healthy():
                return False  # 主节点正常，无需转移

            logger.warning("检测到主节点故障，开始故障转移")

            # 尝试故障转移
            success = self._perform_failover()

            # 记录故障转移历史
            self.failover_history.append({
                'timestamp': datetime.now().isoformat(),
                'from_node': self.current_primary['id'],
                'to_node': self.current_primary['id'] if not success else None,
                'success': success,
                'reason': 'primary_node_failure'
            })

            return success

    def manual_failover(self, target_node_id: str) -> bool:
        """手动故障转移"""

        with self.lock:
            # 查找目标节点
            target_node = None
            for node in self.standby_nodes:
                if node['id'] == target_node_id:
                    target_node = node
                    break

            if not target_node:
                logger.error(f"目标节点不存在: {target_node_id}")
                return False

            logger.info(f"执行手动故障转移到节点: {target_node_id}")

            # 执行故障转移
            success = self._switch_to_node(target_node)

            if success:
                self.failover_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'from_node': self.current_primary['id'],
                    'to_node': target_node_id,
                    'success': True,
                    'reason': 'manual_failover'
                })

            return success

    def _is_primary_healthy(self) -> bool:
        """检查主节点是否健康"""
        try:
            import requests

            url = f"http://{self.current_primary['host']}:{self.current_primary['port']}/health"
            response = requests.get(url, timeout=5)

            return response.status_code == 200

        except Exception:
            return False

    def _perform_failover(self) -> bool:
        """执行自动故障转移"""

        # 尝试每个备用节点
        for standby_node in self.standby_nodes:
            if self._is_node_available(standby_node):
                logger.info(f"尝试故障转移到节点: {standby_node['id']}")

                if self._switch_to_node(standby_node):
                    logger.info(f"故障转移成功: {standby_node['id']}")
                    return True
                else:
                    logger.warning(f"故障转移失败: {standby_node['id']}")

        logger.error("所有备用节点都不可用，无法完成故障转移")
        return False

    def _is_node_available(self, node: Dict[str, Any]) -> bool:
        """检查节点是否可用"""
        try:
            import requests

            url = f"http://{node['host']}:{node['port']}/health"
            response = requests.get(url, timeout=5)

            return response.status_code == 200

        except Exception:
            return False

    def _switch_to_node(self, new_primary: Dict[str, Any]) -> bool:
        """切换到新主节点"""

        try:
            # 1. 通知新主节点准备接管
            if not self._notify_node_takeover(new_primary):
                return False

            # 2. 等待数据同步完成
            if not self._wait_for_data_sync(new_primary, timeout=self.failover_timeout):
                return False

            # 3. 更新DNS/负载均衡器配置
            self._update_load_balancer_config(new_primary)

            # 4. 验证新主节点功能
            if not self._verify_new_primary(new_primary):
                return False

            # 5. 更新当前主节点引用
            old_primary = self.current_primary
            self.current_primary = new_primary

            # 6. 通知旧主节点（如果可用）
            self._notify_old_primary(old_primary)

            logger.info(f"成功切换到新主节点: {new_primary['id']}")
            return True

        except Exception as e:
            logger.error(f"切换主节点失败: {e}")
            return False

    def _notify_node_takeover(self, node: Dict[str, Any]) -> bool:
        """通知节点接管"""
        try:
            import requests

            url = f"http://{node['host']}:{node['port']}/api/failover/takeover"
            response = requests.post(url, timeout=10)

            return response.status_code == 200

        except Exception as e:
            logger.error(f"通知节点接管失败 {node['id']}: {e}")
            return False

    def _wait_for_data_sync(self, node: Dict[str, Any], timeout: int) -> bool:
        """等待数据同步完成"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                import requests

                url = f"http://{node['host']}:{node['port']}/api/failover/sync_status"
                response = requests.get(url, timeout=5)
                data = response.json()

                if data.get('sync_complete', False):
                    return True

                time.sleep(2)  # 等待2秒后重试

            except Exception:
                time.sleep(2)

        return False

    def _update_load_balancer_config(self, new_primary: Dict[str, Any]):
        """更新负载均衡器配置"""
        # 这里应该更新负载均衡器的配置
        # 例如更新DNS记录、Nginx配置等
        logger.info("更新负载均衡器配置")

    def _verify_new_primary(self, node: Dict[str, Any]) -> bool:
        """验证新主节点功能"""
        try:
            import requests

            # 检查健康状态
            health_url = f"http://{node['host']}:{node['port']}/health"
            response = requests.get(health_url, timeout=5)
            if response.status_code != 200:
                return False

            # 检查API功能
            api_url = f"http://{node['host']}:{node['port']}/api/config"
            response = requests.get(api_url, timeout=5)
            if response.status_code != 200:
                return False

            return True

        except Exception as e:
            logger.error(f"验证新主节点失败 {node['id']}: {e}")
            return False

    def _notify_old_primary(self, old_primary: Dict[str, Any]):
        """通知旧主节点"""
        try:
            import requests

            url = f"http://{old_primary['host']}:{old_primary['port']}/api/failover/demoted"
            requests.post(url, timeout=5)

        except Exception:
            # 旧主节点可能已经不可用，忽略错误
            pass

    def _start_failover_monitoring(self):
        """启动故障转移监控"""

        def failover_monitor_worker():
            consecutive_failures = 0

            while True:
                try:
                    if self._is_primary_healthy():
                        consecutive_failures = 0
                    else:
                        consecutive_failures += 1

                        if consecutive_failures >= self.failure_threshold:
                            logger.warning(f"主节点连续失败 {consecutive_failures} 次，触发故障转移")
                            self.check_and_failover()
                            consecutive_failures = 0  # 重置计数器

                    time.sleep(self.health_check_interval)

                except Exception as e:
                    logger.error(f"故障转移监控错误: {e}")
                    time.sleep(self.health_check_interval)

        thread = threading.Thread(target=failover_monitor_worker, daemon=True)
        thread.start()

    def get_status(self) -> Dict[str, Any]:
        """获取故障转移状态"""
        return {
            'current_primary': self.current_primary['id'],
            'primary_healthy': self._is_primary_healthy(),
            'standby_nodes': [
                {
                    'id': node['id'],
                    'available': self._is_node_available(node)
                }
                for node in self.standby_nodes
            ],
            'recent_failovers': self.failover_history[-5:]  # 最近5次故障转移
        }


class DataSynchronizationManager:
    """数据同步管理器"""

    def __init__(self, nodes: List[Dict[str, Any]]):
        self.nodes = nodes
        self.sync_status = {}
        self.sync_interval = 30  # 30秒同步间隔

        # 启动数据同步
        self._start_data_sync()

    def sync_data_to_nodes(self, data: Dict[str, Any], node_ids: List[str] = None):
        """同步数据到节点"""

        target_nodes = [node for node in self.nodes
                       if not node_ids or node['id'] in node_ids]

        for node in target_nodes:
            try:
                self._sync_data_to_node(data, node)
                self.sync_status[node['id']] = {
                    'status': 'success',
                    'last_sync': datetime.now().isoformat()
                }

            except Exception as e:
                logger.error(f"数据同步失败 {node['id']}: {e}")
                self.sync_status[node['id']] = {
                    'status': 'failed',
                    'last_sync': datetime.now().isoformat(),
                    'error': str(e)
                }

    def get_sync_status(self) -> Dict[str, Any]:
        """获取同步状态"""
        return {
            'nodes': [
                {
                    'id': node['id'],
                    'status': self.sync_status.get(node['id'], {}).get('status', 'unknown'),
                    'last_sync': self.sync_status.get(node['id'], {}).get('last_sync')
                }
                for node in self.nodes
            ],
            'overall_status': self._calculate_overall_status()
        }

    def _sync_data_to_node(self, data: Dict[str, Any], node: Dict[str, Any]):
        """同步数据到单个节点"""
        import requests

        url = f"http://{node['host']}:{node['port']}/api/sync/data"

        response = requests.post(url, json=data, timeout=30)

        if response.status_code != 200:
            raise Exception(f"同步失败: HTTP {response.status_code}")

    def _start_data_sync(self):
        """启动数据同步"""

        def sync_worker():
            while True:
                try:
                    # 这里可以实现定期全量同步逻辑
                    time.sleep(self.sync_interval)
                except Exception as e:
                    logger.error(f"数据同步线程错误: {e}")
                    time.sleep(self.sync_interval)

        thread = threading.Thread(target=sync_worker, daemon=True)
        thread.start()

    def _calculate_overall_status(self) -> str:
        """计算整体同步状态"""
        statuses = [status.get('status', 'unknown') for status in self.sync_status.values()]

        if all(s == 'success' for s in statuses):
            return 'healthy'
        elif any(s == 'failed' for s in statuses):
            return 'degraded'
        else:
            return 'unknown'


class HighAvailabilityCluster:
    """高可用集群"""

    def __init__(self, nodes_config: Dict[str, Any]):
        self.nodes_config = nodes_config

        # 初始化组件
        self.load_balancer = LoadBalancer(nodes_config['nodes'])
        self.failover_manager = FailoverManager(
            nodes_config['primary'],
            nodes_config['standby']
        )
        self.data_sync = DataSynchronizationManager(nodes_config['nodes'])

        # 集群状态
        self.cluster_status = 'initializing'

        logger.info("高可用集群已初始化")

    def start_cluster(self):
        """启动集群"""
        try:
            # 验证集群配置
            self._validate_cluster_config()

            # 启动所有节点服务
            self._start_cluster_services()

            # 等待集群稳定
            self._wait_for_cluster_stable()

            self.cluster_status = 'active'
            logger.info("高可用集群启动成功")

        except Exception as e:
            self.cluster_status = 'failed'
            logger.error(f"高可用集群启动失败: {e}")
            raise

    def stop_cluster(self):
        """停止集群"""
        try:
            # 停止所有节点服务
            self._stop_cluster_services()

            self.cluster_status = 'stopped'
            logger.info("高可用集群已停止")

        except Exception as e:
            logger.error(f"停止集群时出错: {e}")

    def get_cluster_status(self) -> Dict[str, Any]:
        """获取集群状态"""
        return {
            'cluster_status': self.cluster_status,
            'load_balancer': self.load_balancer.get_status(),
            'failover': self.failover_manager.get_status(),
            'data_sync': self.data_sync.get_sync_status(),
            'timestamp': datetime.now().isoformat()
        }

    def perform_maintenance(self, maintenance_type: str, **kwargs) -> bool:
        """执行维护操作"""

        try:
            if maintenance_type == 'rolling_update':
                return self._perform_rolling_update(**kwargs)
            elif maintenance_type == 'backup':
                return self._perform_cluster_backup(**kwargs)
            elif maintenance_type == 'scale_out':
                return self._perform_scale_out(**kwargs)
            elif maintenance_type == 'scale_in':
                return self._perform_scale_in(**kwargs)
            else:
                raise ValueError(f"不支持的维护类型: {maintenance_type}")

        except Exception as e:
            logger.error(f"维护操作失败 {maintenance_type}: {e}")
            return False

    def _validate_cluster_config(self):
        """验证集群配置"""
        required_keys = ['primary', 'standby', 'nodes']

        for key in required_keys:
            if key not in self.nodes_config:
                raise ValueError(f"集群配置缺少必需项: {key}")

        # 验证节点配置
        all_nodes = [self.nodes_config['primary']] + self.nodes_config['standby']

        for node in all_nodes:
            required_node_keys = ['id', 'host', 'port']
            for key in required_node_keys:
                if key not in node:
                    raise ValueError(f"节点配置缺少必需项: {key}")

    def _start_cluster_services(self):
        """启动集群服务"""
        # 这里应该实现实际的服务启动逻辑
        # 例如通过systemd、docker-compose等启动服务
        logger.info("启动集群服务...")

        # 模拟启动时间
        time.sleep(5)

    def _stop_cluster_services(self):
        """停止集群服务"""
        logger.info("停止集群服务...")

        # 模拟停止时间
        time.sleep(3)

    def _wait_for_cluster_stable(self, timeout: int = 120):
        """等待集群稳定"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self.get_cluster_status()

            # 检查所有组件是否健康
            if (status['load_balancer']['healthy_nodes'] > 0 and
                status['failover']['primary_healthy'] and
                status['data_sync']['overall_status'] in ['healthy', 'unknown']):
                logger.info("集群已达到稳定状态")
                return

            time.sleep(5)

        raise TimeoutError("集群未能达到稳定状态")

    def _perform_rolling_update(self, new_image: str = None) -> bool:
        """执行滚动更新"""
        logger.info("开始滚动更新...")

        # 对每个节点逐个更新
        all_nodes = [self.nodes_config['primary']] + self.nodes_config['standby']

        for node in all_nodes:
            try:
                # 从负载均衡器中移除节点
                logger.info(f"从负载均衡器移除节点: {node['id']}")

                # 更新节点
                self._update_node(node, new_image)

                # 验证节点健康
                if not self._wait_for_node_healthy(node, timeout=60):
                    raise Exception(f"节点更新后未恢复健康: {node['id']}")

                # 重新加入负载均衡器
                logger.info(f"节点重新加入负载均衡器: {node['id']}")

            except Exception as e:
                logger.error(f"更新节点失败 {node['id']}: {e}")
                # 可以实现回滚逻辑
                return False

        logger.info("滚动更新完成")
        return True

    def _perform_cluster_backup(self, backup_type: str = 'full') -> bool:
        """执行集群备份"""
        logger.info(f"开始集群备份: {backup_type}")

        # 在主节点上执行备份
        # 这里应该调用备份恢复系统的逻辑

        logger.info("集群备份完成")
        return True

    def _perform_scale_out(self, new_nodes: List[Dict[str, Any]]) -> bool:
        """执行扩容"""
        logger.info("开始集群扩容...")

        for node in new_nodes:
            try:
                # 启动新节点
                self._start_node(node)

                # 等待节点就绪
                if not self._wait_for_node_healthy(node, timeout=120):
                    raise Exception(f"新节点启动失败: {node['id']}")

                # 添加到负载均衡器
                self.load_balancer.nodes.append(node)

                # 开始数据同步
                self.data_sync.nodes.append(node)

                logger.info(f"成功添加新节点: {node['id']}")

            except Exception as e:
                logger.error(f"添加新节点失败 {node['id']}: {e}")
                return False

        logger.info("集群扩容完成")
        return True

    def _perform_scale_in(self, node_ids: List[str]) -> bool:
        """执行缩容"""
        logger.info("开始集群缩容...")

        for node_id in node_ids:
            try:
                # 从负载均衡器移除
                self.load_balancer.nodes = [
                    node for node in self.load_balancer.nodes
                    if node['id'] != node_id
                ]

                # 从数据同步移除
                self.data_sync.nodes = [
                    node for node in self.data_sync.nodes
                    if node['id'] != node_id
                ]

                # 停止节点
                self._stop_node_by_id(node_id)

                logger.info(f"成功移除节点: {node_id}")

            except Exception as e:
                logger.error(f"移除节点失败 {node_id}: {e}")
                return False

        logger.info("集群缩容完成")
        return True

    def _update_node(self, node: Dict[str, Any], new_image: str):
        """更新节点"""
        # 这里应该实现实际的节点更新逻辑
        # 例如更新Docker镜像、重新部署等
        logger.info(f"更新节点 {node['id']} 到新版本")

        # 模拟更新时间
        time.sleep(10)

    def _start_node(self, node: Dict[str, Any]):
        """启动节点"""
        logger.info(f"启动节点 {node['id']}")

        # 模拟启动时间
        time.sleep(15)

    def _stop_node_by_id(self, node_id: str):
        """停止节点"""
        logger.info(f"停止节点 {node_id}")

        # 模拟停止时间
        time.sleep(5)

    def _wait_for_node_healthy(self, node: Dict[str, Any], timeout: int) -> bool:
        """等待节点健康"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                import requests

                url = f"http://{node['host']}:{node['port']}/health"
                response = requests.get(url, timeout=5)

                if response.status_code == 200:
                    return True

            except Exception:
                pass

            time.sleep(5)

        return False


if __name__ == '__main__':
    # 配置示例
    cluster_config = {
        'primary': {
            'id': 'node1',
            'host': '192.168.1.10',
            'port': 8080
        },
        'standby': [
            {
                'id': 'node2',
                'host': '192.168.1.11',
                'port': 8080
            },
            {
                'id': 'node3',
                'host': '192.168.1.12',
                'port': 8080
            }
        ],
        'nodes': [
            {
                'id': 'node1',
                'host': '192.168.1.10',
                'port': 8080
            },
            {
                'id': 'node2',
                'host': '192.168.1.11',
                'port': 8080
            },
            {
                'id': 'node3',
                'host': '192.168.1.12',
                'port': 8080
            }
        ]
    }

    # 创建高可用集群
    cluster = HighAvailabilityCluster(cluster_config)

    # 启动集群
    cluster.start_cluster()

    # 获取集群状态
    status = cluster.get_cluster_status()
    print("集群状态:", json.dumps(status, indent=2, ensure_ascii=False))

    # 执行滚动更新
    cluster.perform_maintenance('rolling_update', new_image='config-service:v2.0.0')

    # 扩容集群
    new_nodes = [{
        'id': 'node4',
        'host': '192.168.1.13',
        'port': 8080
    }]
    cluster.perform_maintenance('scale_out', new_nodes=new_nodes)
