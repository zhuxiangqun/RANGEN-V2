#!/usr/bin/env python3
"""
RPA系统主程序入口
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from rpa_system.core_controller import RPAController
from rpa_system.web_ui import app, init_controller
from rpa_system.config import RPA_CONFIG


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(RPA_CONFIG["rpa"]["logs_dir"] / "rpa_system.log"),
            logging.StreamHandler()
        ]
    )


async def run_cli_mode(sample_count: int, timeout: float):
    """CLI模式运行"""
    controller = RPAController()
    
    print("🚀 启动RPA系统（CLI模式）")
    print(f"配置: 样本数量={sample_count}, 超时={timeout}秒")
    print("-" * 60)
    
    results = await controller.run_full_cycle(
        sample_count=sample_count,
        timeout=timeout
    )
    
    print("-" * 60)
    print(f"运行完成: {results.get('status')}")
    print(f"报告路径: {results.get('report_path', 'N/A')}")
    
    if results.get('status') == 'error':
        print(f"错误: {results.get('error', '未知错误')}")
        return 1
    
    return 0


def run_web_mode():
    """Web UI模式运行"""
    try:
        from rpa_system.web_ui import app, FLASK_AVAILABLE
        if not FLASK_AVAILABLE:
            print("错误: Flask未安装，无法启动Web UI")
            print("请运行: pip install flask flask-cors")
            return 1
    except ImportError:
        print("错误: 无法导入Web UI模块")
        return 1
    
    print("🌐 启动RPA系统（Web UI模式）")
    print(f"访问地址: http://{RPA_CONFIG['ui']['host']}:{RPA_CONFIG['ui']['port']}")
    print("-" * 60)
    
    init_controller()
    app.run(
        host=RPA_CONFIG["ui"]["host"],
        port=RPA_CONFIG["ui"]["port"],
        debug=RPA_CONFIG["ui"]["debug"]
    )
    return 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='RPA系统 - 自动化运行、评测、修复和改进核心系统')
    parser.add_argument('--mode', choices=['cli', 'web'], default='web',
                       help='运行模式: cli (命令行) 或 web (Web界面)')
    parser.add_argument('--sample-count', type=int, default=10,
                       help='样本数量（仅CLI模式）')
    parser.add_argument('--timeout', type=float, default=1800.0,
                       help='超时时间（秒，仅CLI模式）')
    
    args = parser.parse_args()
    
    setup_logging()
    
    if args.mode == 'cli':
        return asyncio.run(run_cli_mode(args.sample_count, args.timeout))
    else:
        run_web_mode()
        return 0


if __name__ == '__main__':
    sys.exit(main())

