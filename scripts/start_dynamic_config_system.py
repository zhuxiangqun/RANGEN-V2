#!/usr/bin/env python3
"""
动态配置管理系统启动脚本

提供多种启动方式：
1. 简单启动 - 基础功能
2. 完整启动 - 所有高级功能
3. 开发模式 - 调试和测试
4. 生产模式 - 高可用和监控
"""

import sys
import os
import logging
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_dependencies():
    """检查依赖"""
    try:
        import langchain
        import langgraph
        logger.info("✅ 核心依赖检查通过")
        return True
    except ImportError as e:
        logger.error(f"❌ 缺少核心依赖: {e}")
        logger.info("请运行: pip install -r requirements_langgraph.txt")
        return False


def start_basic_mode(api_port: int = 8080, web_port: int = 8081):
    """启动基础模式"""
    logger.info("🚀 启动动态配置管理系统 - 基础模式")

    try:
        from src.core.intelligent_router import IntelligentRouter

        # 创建基础路由器（禁用高级功能）
        router = IntelligentRouter(enable_advanced_features=False)

        logger.info("✅ 基础模式启动成功")
        logger.info("📊 可用功能:")
        logger.info("   • 智能路由")
        logger.info("   • 基本配置管理")
        logger.info("   • 规则引擎")

        return router

    except Exception as e:
        logger.error(f"❌ 基础模式启动失败: {e}")
        return None


def start_full_mode(api_port: int = 8080, web_port: int = 8081):
    """启动完整模式"""
    logger.info("🚀 启动动态配置管理系统 - 完整模式")

    try:
        # 设置端口环境变量
        os.environ['DYNAMIC_CONFIG_API_PORT'] = str(api_port)
        os.environ['DYNAMIC_CONFIG_WEB_PORT'] = str(web_port)

        from src.core.intelligent_router import IntelligentRouter

        # 创建完整功能的路由器
        router = IntelligentRouter(enable_advanced_features=True)

        logger.info("✅ 完整模式启动成功")
        logger.info("📊 系统状态:")
        logger.info(f"   • 配置API服务器: http://localhost:{api_port}")
        logger.info(f"   • Web管理界面: http://localhost:{web_port}")
        logger.info("   • 热更新监控: 运行中")
        logger.info("   • 配置分发服务: 运行中")
        logger.info("   • 高级功能: 已启用")

        # 等待用户输入保持运行
        logger.info("💡 按 Ctrl+C 停止系统")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 系统正在关闭...")

        return router

    except Exception as e:
        logger.error(f"❌ 完整模式启动失败: {e}")
        return None


def start_development_mode(api_port: int = 8080, web_port: int = 8081):
    """启动开发模式"""
    logger.info("🚀 启动动态配置管理系统 - 开发模式")

    try:
        # 设置开发环境
        os.environ['ENVIRONMENT'] = 'development'
        os.environ['LOG_LEVEL'] = 'DEBUG'
        os.environ['DYNAMIC_CONFIG_API_PORT'] = str(api_port)
        os.environ['DYNAMIC_CONFIG_WEB_PORT'] = str(web_port)

        from src.core.intelligent_router import IntelligentRouter

        # 创建开发模式的路由器
        router = IntelligentRouter(enable_advanced_features=True)

        logger.info("✅ 开发模式启动成功")
        logger.info("📊 开发功能:")
        logger.info("   • 详细日志记录")
        logger.info("   • 调试信息输出")
        logger.info("   • 热重载支持")
        logger.info("   • 测试接口开放")

        # 在开发模式下保持运行并提供交互式shell
        logger.info("💡 进入开发模式，系统保持运行...")
        logger.info("   您可以打开另一个终端进行测试")

        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 开发模式正在关闭...")

        return router

    except Exception as e:
        logger.error(f"❌ 开发模式启动失败: {e}")
        return None


def start_production_mode(api_port: int = 8080, web_port: int = 8081):
    """启动生产模式"""
    logger.info("🚀 启动动态配置管理系统 - 生产模式")

    try:
        # 设置生产环境
        os.environ['ENVIRONMENT'] = 'production'
        os.environ['LOG_LEVEL'] = 'WARNING'
        os.environ['DYNAMIC_CONFIG_API_PORT'] = str(api_port)
        os.environ['DYNAMIC_CONFIG_WEB_PORT'] = str(web_port)

        from scripts.production.high_availability_system import HighAvailabilityCluster
        from scripts.production.backup_restore_system import BackupRestoreSystem
        from scripts.production.security_hardening import SecurityHardeningSuite

        # 集群配置（使用自定义端口）
        cluster_config = {
            'primary': {
                'id': 'node1',
                'host': 'localhost',
                'port': api_port
            },
            'standby': [
                {
                    'id': 'node2',
                    'host': 'localhost',
                    'port': web_port
                }
            ],
            'nodes': [
                {
                    'id': 'node1',
                    'host': 'localhost',
                    'port': api_port
                },
                {
                    'id': 'node2',
                    'host': 'localhost',
                    'port': web_port
                }
            ]
        }

        # 启动高可用集群
        cluster = HighAvailabilityCluster(cluster_config)
        cluster.start_cluster()

        # 初始化备份系统
        from src.core.intelligent_router import IntelligentRouter
        router = IntelligentRouter(enable_advanced_features=True)
        backup_system = BackupRestoreSystem(router)
        backup_system.schedule_backups()

        # 应用安全加固
        security = SecurityHardeningSuite()
        security.apply_security_hardening()

        logger.info("✅ 生产模式启动成功")
        logger.info("📊 生产功能:")
        logger.info("   • 高可用集群: 已启动")
        logger.info("   • 自动备份: 已调度")
        logger.info("   • 安全加固: 已应用")
        logger.info("   • 监控告警: 已启用")

        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 生产模式正在关闭...")
            cluster.stop_cluster()

        return cluster

    except Exception as e:
        logger.error(f"❌ 生产模式启动失败: {e}")
        return None


def show_usage_examples(router):
    """显示使用示例"""
    if not router:
        return

    print("\n" + "="*60)
    print("📚 动态配置管理系统使用示例")
    print("="*60)

    try:
        # 基本配置操作
        print("\n🔧 配置管理示例:")
        print("# 更新阈值")
        print("router.update_routing_threshold('simple_max_complexity', 0.08)")
        router.update_routing_threshold('simple_max_complexity', 0.08)
        print("✅ 阈值已更新")

        print("\n# 添加关键词")
        print("router.add_routing_keyword('question_words', 'what')")
        router.add_routing_keyword('question_words', 'what')
        print("✅ 关键词已添加")

        # 应用模板
        print("\n🎨 模板应用示例:")
        print("# 应用保守模板")
        print("router.apply_config_template('conservative')")
        router.apply_config_template('conservative')
        print("✅ 模板已应用")

        # 获取配置
        print("\n📊 配置查看示例:")
        print("# 获取当前配置")
        config = router.get_routing_config()
        print(f"当前配置包含 {len(config.get('thresholds', {}))} 个阈值")

        # 测试路由
        print("\n🔀 路由测试示例:")
        print("# 测试查询路由")
        test_query = "如何使用Python进行数据分析？"
        result = router.route_query(test_query)
        print(f"查询: {test_query}")
        print(f"路由结果: {result.route_type} (置信度: {result.confidence:.2f})")

        print("\n💡 系统正在运行，您可以:")
        print("1. 打开浏览器访问 http://localhost:8081 查看Web界面")
        print("2. 使用API访问 http://localhost:8080 进行配置管理")
        print("3. 查看日志了解系统运行状态")

    except Exception as e:
        print(f"❌ 示例执行失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='动态配置管理系统启动器')
    parser.add_argument(
        'mode',
        choices=['basic', 'full', 'dev', 'prod'],
        help='启动模式: basic(基础), full(完整), dev(开发), prod(生产)'
    )
    parser.add_argument(
        '--api-port',
        type=int,
        default=8080,
        help='API服务器端口 (默认: 8080)'
    )
    parser.add_argument(
        '--web-port',
        type=int,
        default=8081,
        help='Web管理界面端口 (默认: 8081)'
    )
    parser.add_argument(
        '--skip-checks',
        action='store_true',
        help='跳过依赖检查'
    )
    parser.add_argument(
        '--examples',
        action='store_true',
        help='启动后显示使用示例'
    )

    args = parser.parse_args()

    # 检查依赖
    if not args.skip_checks and not check_dependencies():
        sys.exit(1)

    # 根据模式启动
    router = None

    if args.mode == 'basic':
        router = start_basic_mode(args.api_port, args.web_port)
    elif args.mode == 'full':
        router = start_full_mode(args.api_port, args.web_port)
    elif args.mode == 'dev':
        router = start_development_mode(args.api_port, args.web_port)
    elif args.mode == 'prod':
        start_production_mode(args.api_port, args.web_port)
        return  # 生产模式自己处理循环

    # 显示使用示例
    if args.examples and router:
        show_usage_examples(router)


if __name__ == '__main__':
    main()
