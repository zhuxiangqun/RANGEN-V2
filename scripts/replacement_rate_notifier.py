#!/usr/bin/env python3
"""
替换比例变化通知器

自动监控替换比例变化并发送通知。
"""

import sys
import time
import re
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ReplacementRateNotifier:
    """替换比例变化通知器"""
    
    def __init__(self, log_file: str, check_interval: int = 10):
        """
        初始化通知器
        
        Args:
            log_file: 监控日志文件路径
            check_interval: 检查间隔（秒）
        """
        self.log_file = Path(log_file)
        self.check_interval = check_interval
        self.last_position = 0
        self.last_rate = None
        self.notification_count = 0
        
    def get_current_rate_from_log(self) -> Optional[float]:
        """从日志中提取当前替换比例"""
        if not self.log_file.exists():
            return None
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                # 读取最后100行
                lines = f.readlines()[-100:]
                
                # 查找最新的替换比例
                for line in reversed(lines):
                    # 匹配 "替换比例: X%" 或 "替换比例已增加: X% → Y%"
                    match = re.search(r'替换比例[已增加:：\s]+(\d+(?:\.\d+)?)%', line)
                    if match:
                        rate = float(match.group(1)) / 100.0
                        return rate
                    
                    # 匹配 "第 X 次检查 (替换比例: Y%)"
                    match = re.search(r'第\s*\d+\s*次检查.*?替换比例[：:]\s*(\d+(?:\.\d+)?)%', line)
                    if match:
                        rate = float(match.group(1)) / 100.0
                        return rate
        except Exception as e:
            logger.error(f"读取日志文件失败: {e}")
        
        return None
    
    def check_rate_increase(self) -> Optional[Tuple[float, float]]:
        """检查替换比例是否增加"""
        if not self.log_file.exists():
            return None
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                # 读取新内容
                f.seek(self.last_position)
                new_lines = f.readlines()
                self.last_position = f.tell()
                
                # 查找替换比例增加的记录
                for line in new_lines:
                    # 匹配 "✅ 替换比例已增加: X% → Y%"
                    match = re.search(r'替换比例已增加[：:]\s*(\d+(?:\.\d+)?)%\s*→\s*(\d+(?:\.\d+)?)%', line)
                    if match:
                        old_rate = float(match.group(1)) / 100.0
                        new_rate = float(match.group(2)) / 100.0
                        return (old_rate, new_rate)
        except Exception as e:
            logger.error(f"检查日志失败: {e}")
        
        return None
    
    def send_notification(self, old_rate: float, new_rate: float, method: str = "console"):
        """发送通知"""
        old_percent = f"{old_rate:.0%}"
        new_percent = f"{new_rate:.0%}"
        
        message = f"""
{'='*60}
🎉 替换比例已增加！
{'='*60}
Agent: ReActAgent → ReasoningExpert
替换比例: {old_percent} → {new_percent}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*60}
"""
        
        if method == "console":
            print(message)
            logger.info(f"替换比例已增加: {old_percent} → {new_percent}")
        elif method == "file":
            notification_file = Path("logs/replacement_notifications.log")
            with open(notification_file, 'a', encoding='utf-8') as f:
                f.write(message)
            logger.info(f"通知已保存到: {notification_file}")
        
        self.notification_count += 1
    
    def monitor(self, method: str = "console"):
        """开始监控"""
        logger.info(f"开始监控替换比例变化...")
        logger.info(f"监控日志: {self.log_file}")
        logger.info(f"检查间隔: {self.check_interval}秒")
        logger.info(f"通知方式: {method}")
        logger.info(f"{'='*60}")
        
        # 初始化：读取当前替换比例
        current_rate = self.get_current_rate_from_log()
        if current_rate is not None:
            self.last_rate = current_rate
            logger.info(f"当前替换比例: {current_rate:.0%}")
        
        try:
            while True:
                # 检查替换比例是否增加
                rate_change = self.check_rate_increase()
                
                if rate_change:
                    old_rate, new_rate = rate_change
                    self.send_notification(old_rate, new_rate, method)
                    self.last_rate = new_rate
                
                # 检查当前替换比例（用于首次启动或日志轮转）
                current_rate = self.get_current_rate_from_log()
                if current_rate is not None and current_rate != self.last_rate:
                    if self.last_rate is not None:
                        logger.info(f"检测到替换比例变化: {self.last_rate:.0%} → {current_rate:.0%}")
                    self.last_rate = current_rate
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info(f"\n监控已停止。共发送 {self.notification_count} 次通知。")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="替换比例变化通知器")
    parser.add_argument(
        "--log-file",
        type=str,
        default="logs/react_agent_replacement.log",
        help="监控日志文件路径（默认: logs/react_agent_replacement.log）"
    )
    parser.add_argument(
        "--check-interval",
        type=int,
        default=10,
        help="检查间隔（秒，默认: 10）"
    )
    parser.add_argument(
        "--method",
        type=str,
        choices=["console", "file"],
        default="console",
        help="通知方式：console（控制台）或 file（文件，默认: console）"
    )
    
    args = parser.parse_args()
    
    notifier = ReplacementRateNotifier(
        log_file=args.log_file,
        check_interval=args.check_interval
    )
    
    notifier.monitor(method=args.method)


if __name__ == "__main__":
    main()

