#!/usr/bin/env python3
"""
ADB控制模块
通过Android Debug Bridge控制Android设备
对齐pc-agent-loop的移动设备控制能力
"""
import subprocess
import time
import hashlib
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


@dataclass
class ADBResult:
    """ADB操作结果"""
    success: bool
    action: str
    output: Any = None
    error: Optional[str] = None
    device_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ADBController:
    """ADB控制器
    
    通过ADB命令控制Android设备
    对齐pc-agent-loop的移动设备控制能力
    """
    
    def __init__(self, device_id: Optional[str] = None):
        """初始化
        
        Args:
            device_id: 设备ID (serial number)，默认选择第一个设备
        """
        self.device_id = device_id
        self.session_id = hashlib.md5(f"{time.time()}".encode()).hexdigest()[:8]
        self.is_connected = False
        
        logger.info(f"ADB Controller initialized (session: {self.session_id})")
    
    def _run_command(self, command: List[str], timeout: int = 30) -> tuple:
        """执行ADB命令
        
        Args:
            command: 命令列表
            timeout: 超时时间
            
        Returns:
            (returncode, stdout, stderr)
        """
        try:
            # 添加设备选择
            if self.device_id and "adb" in command[0]:
                # 在adb和子命令之间插入-s device_id
                cmd = [command[0]]
                if command[1] not in ("devices", "start-server", "kill-server"):
                    cmd.extend(["-s", self.device_id])
                cmd.extend(command[1:])
            else:
                cmd = command
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timeout"
        except FileNotFoundError:
            return -1, "", "ADB not found. Please install Android SDK platform-tools."
        except Exception as e:
            return -1, "", str(e)
    
    def connect(self) -> ADBResult:
        """连接设备"""
        try:
            returncode, stdout, stderr = self._run_command(["adb", "devices"])
            
            if returncode != 0:
                return ADBResult(
                    success=False,
                    action="connect",
                    error=stderr or "Failed to get devices"
                )
            
            # 解析设备列表
            devices = []
            lines = stdout.strip().split("\n")[1:]  # Skip header
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        devices.append({
                            "id": parts[0],
                            "status": parts[1]
                        })
            
            # 如果没有指定设备，选择第一个在线设备
            if not self.device_id:
                for dev in devices:
                    if dev["status"] == "device":
                        self.device_id = dev["id"]
                        break
            
            if not self.device_id:
                return ADBResult(
                    success=False,
                    action="connect",
                    error="No devices found"
                )
            
            self.is_connected = True
            
            return ADBResult(
                success=True,
                action="connect",
                output={
                    "device_id": self.device_id,
                    "devices": devices,
                    "message": f"Connected to {self.device_id}"
                },
                device_id=self.device_id,
                metadata={"devices_count": len(devices)}
            )
        except Exception as e:
            return ADBResult(
                success=False,
                action="connect",
                error=str(e)
            )
    
    def shell(self, command: str, timeout: int = 30) -> ADBResult:
        """执行Shell命令
        
        Args:
            command: Shell命令
            timeout: 超时时间
            
        Returns:
            ADBResult
        """
        if not self.is_connected and self.device_id:
            self.connect()
        
        returncode, stdout, stderr = self._run_command(
            ["adb", "shell", command],
            timeout=timeout
        )
        
        return ADBResult(
            success=returncode == 0,
            action="shell",
            output=stdout,
            error=stderr if returncode != 0 else None,
            device_id=self.device_id,
            metadata={"command": command, "returncode": returncode}
        )
    
    def tap(self, x: int, y: int) -> ADBResult:
        """点击屏幕位置
        
        Args:
            x: X坐标
            y: Y坐标
        """
        return self.shell(f"input tap {x} {y}")
    
    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> ADBResult:
        """滑动屏幕
        
        Args:
            x1, y1: 起始坐标
            x2, y2: 结束坐标
            duration: 持续时间(毫秒)
        """
        return self.shell(f"input swipe {x1} {y1} {x2} {y2} {duration}")
    
    def text(self, text: str) -> ADBResult:
        """输入文本
        
        Args:
            text: 要输入的文本
        """
        # 处理特殊字符
        escaped = text.replace(" ", "%s")
        return self.shell(f"input text {escaped}")
    
    def keyevent(self, keycode: int) -> ADBResult:
        """发送按键事件
        
        Args:
            keycode: 按键码
                4 = back
                3 = home
                26 = power
                24 = volume_up
                25 = volume_down
        """
        return self.shell(f"input keyevent {keycode}")
    
    def press_back(self) -> ADBResult:
        """按返回键"""
        return self.keyevent(4)
    
    def press_home(self) -> ADBResult:
        """按Home键"""
        return self.keyevent(3)
    
    def press_power(self) -> ADBResult:
        """按电源键"""
        return self.keyevent(26)
    
    def screenshot(self, save_path: str = "/sdcard/screenshot.png") -> ADBResult:
        """截图
        
        Args:
            save_path: 保存路径
        """
        # 执行截图命令
        result = self.shell(f"screencap -p {save_path}")
        
        if not result.success:
            return result
        
        # 拉取到本地（简化处理）
        return ADBResult(
            success=True,
            action="screenshot",
            output=f"Screenshot saved to {save_path}",
            device_id=self.device_id,
            metadata={"path": save_path}
        )
            success=True,
            action="screenshot",
            output=f"Screenshot saved to {save_path}",
           _id,
            metadata device_id=self.device={"path": save_path}
        )
    
    def start_app(self, package_name: str) -> ADBResult:
        """启动应用
        
        Args:
            package_name: 应用包名
        """
        return self.shell(f"monkey -p {package_name} -c android.intent.category.LAUNCHER 1")
    
    def stop_app(self, package_name: str) -> ADBResult:
        """停止应用
        
        Args:
            package_name: 应用包名
        """
        return self.shell(f"am force-stop {package_name}")
    
    def get_screen_size(self) -> Optional[Dict[str, int]]:
        """获取屏幕尺寸"""
        result = self.shell("wm size")
        
        if result.success and result.output:
            # 解析输出: Physical size: 1080x1920
            try:
                size_str = result.output.strip().split(": ")[1]
                width, height = map(int, size_str.split("x"))
                return {"width": width, "height": height}
            except:
                pass
        
        return None
    
    def get_current_app(self) -> Optional[str]:
        """获取当前应用包名"""
        result = self.shell("dumpsys activity activities | grep mResumedActivity")
        
        if result.success and result.output:
            try:
                # 解析输出获取包名
                parts = result.output.split("/")
                if len(parts) >= 1:
                    pkg = parts[0].strip()
                    return pkg
            except:
                pass
        
        return None
    
    def list_packages(self) -> List[str]:
        """列出已安装应用"""
        result = self.shell("pm list packages")
        
        packages = []
        if result.success and result.output:
            for line in result.output.strip().split("\n"):
                if line.startswith("package:"):
                    packages.append(line.replace("package:", "").strip())
        
        return packages
    
    def install_apk(self, apk_path: str) -> ADBResult:
        """安装APK
        
        Args:
            apk_path: APK文件路径
        """
        returncode, stdout, stderr = self._run_command(
            ["adb", "install", "-r", apk_path]  # -r for reinstall
        )
        
        return ADBResult(
            success=returncode == 0,
            action="install",
            output=stdout,
            error=stderr if returncode != 0 else None,
            device_id=self.device_id,
            metadata={"apk_path": apk_path}
        )
    
    def uninstall(self, package_name: str) -> ADBResult:
        """卸载应用
        
        Args:
            package_name: 应用包名
        """
        returncode, stdout, stderr = self._run_command(
            ["adb", "uninstall", package_name]
        )
        
        return ADBResult(
            success=returncode == 0,
            action="uninstall",
            output=stdout,
            error=stderr if returncode != 0 else None,
            device_id=self.device_id,
            metadata={"package_name": package_name}
        )
    
    def forward(self, local: str, remote: str) -> ADBResult:
        """端口转发
        
        Args:
            local: 本地端口 (e.g., tcp:5037)
            remote: 远程端口
        """
        returncode, stdout, stderr = self._run_command(
            ["adb", "forward", local, remote]
        )
        
        return ADBResult(
            success=returncode == 0,
            action="forward",
            output=stdout,
            error=stderr if returncode != 0 else None,
            device_id=self.device_id
        )
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "session_id": self.session_id,
            "device_id": self.device_id,
            "is_connected": self.is_connected,
            "screen_size": self.get_screen_size(),
            "current_app": self.get_current_app()
        }


class ADBHand:
    """ADB控制Hand"""
    
    def __init__(self, device_id: Optional[str] = None):
        self.controller = ADBController(device_id)
        self.name = "adb_control"
        self.description = "Android device control via ADB"
    
    async def execute(self, operation: str, **kwargs) -> ADBResult:
        """执行ADB操作
        
        Args:
            operation: 操作类型
            **kwargs: 操作参数
        """
        # 确保已连接
        if not self.controller.is_connected:
            connect_result = self.controller.connect()
            if not connect_result.success:
                return connect_result
        
        # 执行对应操作
        if operation == "connect":
            return self.controller.connect()
        elif operation == "shell":
            return self.controller.shell(kwargs.get("command", ""))
        elif operation == "tap":
            return self.controller.tap(kwargs.get("x", 0), kwargs.get("y", 0))
        elif operation == "swipe":
            return self.controller.swipe(
                kwargs.get("x1", 0), kwargs.get("y1", 0),
                kwargs.get("x2", 0), kwargs.get("y2", 0),
                kwargs.get("duration", 300)
            )
        elif operation == "text":
            return self.controller.text(kwargs.get("text", ""))
        elif operation == "keyevent":
            return self.controller.keyevent(kwargs.get("keycode", 0))
        elif operation == "back":
            return self.controller.press_back()
        elif operation == "home":
            return self.controller.press_home()
        elif operation == "power":
            return self.controller.press_power()
        elif operation == "screenshot":
            return self.controller.screenshot(kwargs.get("save_path", "/sdcard/screenshot.png"))
        elif operation == "start_app":
            return self.controller.start_app(kwargs.get("package_name", ""))
        elif operation == "stop_app":
            return self.controller.stop_app(kwargs.get("package_name", ""))
        elif operation == "list_packages":
            packages = self.controller.list_packages()
            return ADBResult(
                success=True,
                action="list_packages",
                output=packages,
                device_id=self.controller.device_id
            )
        elif operation == "install":
            return self.controller.install_apk(kwargs.get("apk_path", ""))
        elif operation == "uninstall":
            return self.controller.uninstall(kwargs.get("package_name", ""))
        else:
            return ADBResult(
                success=False,
                action=operation,
                error=f"Unknown operation: {operation}"
            )


# 便捷函数
def create_adb_hand(device_id: Optional[str] = None) -> ADBHand:
    """创建ADB控制Hand"""
    return ADBHand(device_id)
