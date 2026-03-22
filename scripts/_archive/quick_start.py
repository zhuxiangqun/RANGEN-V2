#!/usr/bin/env python3
"""
动态配置管理系统快速启动脚本

最简单的启动方式，适合初次使用和测试。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """快速启动系统"""
    import argparse

    parser = argparse.ArgumentParser(description='动态配置管理系统快速启动')
    parser.add_argument('--api-port', type=int, default=8080, help='API服务器端口')
    parser.add_argument('--web-port', type=int, default=8081, help='Web界面端口')
    parser.add_argument('--enable-advanced', action='store_true', help='启用高级功能（需要完整依赖）')

    args = parser.parse_args()

    print("🚀 快速启动动态配置管理系统...")

    try:
        import os
        # 设置端口环境变量
        os.environ['DYNAMIC_CONFIG_API_PORT'] = str(args.api_port)
        os.environ['DYNAMIC_CONFIG_WEB_PORT'] = str(args.web_port)

        from src.core.intelligent_router import DynamicRoutingManager

        # 创建路由器
        enable_advanced = args.enable_advanced
        router = DynamicRoutingManager(enable_advanced_features=enable_advanced)

        if enable_advanced:
            print("   • 高级功能: 已启用")
        else:
            print("   • 基础功能: 已启用（高级功能需完整依赖）")

        print("✅ 系统启动成功！")
        print("")
        print("🌐 访问地址:")
        print(f"   • Web管理界面: http://localhost:{args.web_port}")
        print(f"   • REST API: http://localhost:{args.api_port}")
        print("")
        print("📖 快速使用示例:")
        print("")
        print("# 更新配置阈值")
        print("router.update_routing_threshold('simple_max_complexity', 0.08)")
        print("")
        print("# 获取配置")
        config = router.get_routing_config()
        print(f"当前配置包含 {len(config.get('thresholds', {}))} 个阈值")
        print("")
        print("💡 按 Ctrl+C 停止系统")

        # 保持运行
        import time
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 系统已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("请检查依赖是否完整安装")

if __name__ == '__main__':
    main()
