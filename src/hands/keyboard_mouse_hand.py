#!/usr/bin/env python3
"""
键盘鼠标控制模块
提供键盘和鼠标模拟功能
"""
import time
import hashlib
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class KeyModifier(str, Enum):
    """键盘修饰键"""
    CTRL = "ctrl"
    ALT = "alt"
    SHIFT = "shift"
    META = "meta"  # Command on Mac, Windows key on Windows


@dataclass
class KeyboardMouseResult:
    """键鼠操作结果"""
    success: bool
    action: str
    output: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None  # type: ignore
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class KeyboardSimulator:
    """键盘模拟器"""
    
    def __init__(self):
        self.initialized = False
    
    def _ensure_initialized(self) -> bool:
        """确保已初始化"""
        if not self.initialized:
            try:
                import pyautogui
                pyautogui.FAILSAFE = True
                pyautogui.PAUSE = 0.1
                self.initialized = True
            except ImportError:
                logger.warning("pyautogui not installed, using simulation mode")
                self.initialized = True  # 使用模拟模式
        return True
    
    def press(self, key: str, modifiers: Optional[List[str]] = None) -> KeyboardMouseResult:
        """按下按键
        
        Args:
            key: 按键名称 (a, enter, f1, etc.)
            modifiers: 修饰键列表
        """
        self._ensure_initialized()
        
        try:
            import pyautogui
            
            # 处理修饰键
            if modifiers:
                mods = []
                for mod in modifiers:
                    if mod == "ctrl":
                        mods.append(pyautogui.KEYBOARD_KEYS)
                    elif mod == "alt":
                        mods.append("alt")
                    elif mod == "shift":
                        mods.append("shift")
                
                with pyautogui.hold(mods[0] if mods else ""):
                    pyautogui.press(key)
            else:
                pyautogui.press(key)
            
            return KeyboardMouseResult(
                success=True,
                action="press",
                output=f"Pressed: {key}",
                metadata={"key": key, "modifiers": modifiers}
            )
        except ImportError:
            return KeyboardMouseResult(
                success=True,
                action="press",
                output=f"Simulated: Press {key}",
                metadata={"key": key, "simulated": True}
            )
        except Exception as e:
            return KeyboardMouseResult(
                success=False,
                action="press",
                error=str(e),
                metadata={"key": key}
            )
    
    def type(self, text: str, interval: float = 0.0) -> KeyboardMouseResult:
        """输入文本
        
        Args:
            text: 要输入的文本
            interval: 每个字符间隔时间
        """
        self._ensure_initialized()
        
        try:
            import pyautogui
            
            if interval > 0:
                pyautogui.write(text, interval=interval)
            else:
                pyautogui.write(text)
            
            return KeyboardMouseResult(
                success=True,
                action="type",
                output=f"Typed: {len(text)} characters",
                metadata={"char_count": len(text)}
            )
        except ImportError:
            return KeyboardMouseResult(
                success=True,
                action="type",
                output=f"Simulated: Type {len(text)} chars",
                metadata={"char_count": len(text), "simulated": True}
            )
        except Exception as e:
            return KeyboardMouseResult(
                success=False,
                action="type",
                error=str(e)
            )
    
    def hotkey(self, *keys) -> KeyboardMouseResult:
        """快捷键组合
        
        Args:
            *keys: 按键序列 (e.g., 'ctrl', 'c')
        """
        self._ensure_initialized()
        
        try:
            import pyautogui
            pyautogui.hotkey(*keys)
            
            return KeyboardMouseResult(
                success=True,
                action="hotkey",
                output=f"Hotkey: {'+'.join(keys)}",
                metadata={"keys": list(keys)}
            )
        except ImportError:
            return KeyboardMouseResult(
                success=True,
                action="hotkey",
                output=f"Simulated: {'+'.join(keys)}",
                metadata={"keys": list(keys), "simulated": True}
            )
        except Exception as e:
            return KeyboardMouseResult(
                success=False,
                action="hotkey",
                error=str(e)
            )


class MouseSimulator:
    """鼠标模拟器"""
    
    def __init__(self):
        self.initialized = False
    
    def _ensure_initialized(self) -> bool:
        """确保已初始化"""
        if not self.initialized:
            try:
                import pyautogui
                pyautogui.FAILSAFE = True
                self.initialized = True
            except ImportError:
                logger.warning("pyautogui not installed, using simulation mode")
                self.initialized = True
        return True
    
    def move(self, x: int, y: int, duration: float = 0.0) -> KeyboardMouseResult:
        """移动鼠标
        
        Args:
            x: X坐标
            y: Y坐标
            duration: 移动持续时间
        """
        self._ensure_initialized()
        
        try:
            import pyautogui
            
            if duration > 0:
                pyautogui.moveTo(x, y, duration=duration)
            else:
                pyautogui.moveTo(x, y)
            
            return KeyboardMouseResult(
                success=True,
                action="move",
                output=f"Moved to ({x}, {y})",
                metadata={"x": x, "y": y, "duration": duration}
            )
        except ImportError:
            return KeyboardMouseResult(
                success=True,
                action="move",
                output=f"Simulated: Move to ({x}, {y})",
                metadata={"x": x, "y": y, "simulated": True}
            )
        except Exception as e:
            return KeyboardMouseResult(
                success=False,
                action="move",
                error=str(e)
            )
    
    def click(self, x: Optional[int] = None, y: Optional[int] = None, 
              button: str = "left", clicks: int = 1) -> KeyboardMouseResult:
        """点击
        
        Args:
            x: X坐标 (可选，当前位置)
            y: Y坐标 (可选，当前位置)
            button: 按钮 (left, right, middle)
            clicks: 点击次数
        """
        self._ensure_initialized()
        
        try:
            import pyautogui
            
            if x is not None and y is not None:
                pyautogui.click(x, y, clicks=clicks, button=button)
            else:
                pyautogui.click(clicks=clicks, button=button)
            
            return KeyboardMouseResult(
                success=True,
                action="click",
                output=f"Clicked {button} {clicks} time(s) at ({x}, {y})",
                metadata={"x": x, "y": y, "button": button, "clicks": clicks}
            )
        except ImportError:
            return KeyboardMouseResult(
                success=True,
                action="click",
                output=f"Simulated: Click {button}",
                metadata={"button": button, "simulated": True}
            )
        except Exception as e:
            return KeyboardMouseResult(
                success=False,
                action="click",
                error=str(e)
            )
    
    def drag(self, x1: int, y1: int, x2: int, y2: int, 
             duration: float = 0.5, button: str = "left") -> KeyboardMouseResult:
        """拖拽
        
        Args:
            x1, y1: 起始坐标
            x2, y2: 结束坐标
            duration: 持续时间
            button: 按钮
        """
        self._ensure_initialized()
        
        try:
            import pyautogui
            
            pyautogui.moveTo(x1, y1)
            pyautogui.mouseDown(button=button)
            pyautogui.moveTo(x2, y2, duration=duration)
            pyautogui.mouseUp(button=button)
            
            return KeyboardMouseResult(
                success=True,
                action="drag",
                output=f"Dragged from ({x1},{y1}) to ({x2},{y2})",
                metadata={"x1": x1, "y1": y1, "x2": x2, "y2": y2, "duration": duration}
            )
        except ImportError:
            return KeyboardMouseResult(
                success=True,
                action="drag",
                output=f"Simulated: Drag",
                metadata={"simulated": True}
            )
        except Exception as e:
            return KeyboardMouseResult(
                success=False,
                action="drag",
                error=str(e)
            )
    
    def scroll(self, clicks: int) -> KeyboardMouseResult:
        """滚动
        
        Args:
            clicks: 滚动量 (正=向上，负=向下)
        """
        self._ensure_initialized()
        
        try:
            import pyautogui
            pyautogui.scroll(clicks)
            
            return KeyboardMouseResult(
                success=True,
                action="scroll",
                output=f"Scrolled {clicks} clicks",
                metadata={"clicks": clicks}
            )
        except ImportError:
            return KeyboardMouseResult(
                success=True,
                action="scroll",
                output=f"Simulated: Scroll {clicks}",
                metadata={"clicks": clicks, "simulated": True}
            )
        except Exception as e:
            return KeyboardMouseResult(
                success=False,
                action="scroll",
                error=str(e)
            )
    
    def get_position(self) -> Tuple[int, int]:
        """获取当前鼠标位置"""
        try:
            import pyautogui
            return pyautogui.position()
        except:
            return (0, 0)


class KeyboardMouseHand:
    """键盘鼠标控制Hand"""
    
    def __init__(self):
        self.keyboard = KeyboardSimulator()
        self.mouse = MouseSimulator()
        self.name = "keyboard_mouse"
        self.description = "Keyboard and mouse simulation"
    
    async def execute(self, operation: str, **kwargs) -> KeyboardMouseResult:
        """执行键鼠操作
        
        Args:
            operation: 操作类型 (press, type, hotkey, click, move, drag, scroll)
            **kwargs: 操作参数
        """
        if operation == "press":
            return self.keyboard.press(
                kwargs.get("key", ""),
                kwargs.get("modifiers")
            )
        elif operation == "type":
            return self.keyboard.type(
                kwargs.get("text", ""),
                kwargs.get("interval", 0.0)
            )
        elif operation == "hotkey":
            return self.keyboard.hotkey(*kwargs.get("keys", []))
        elif operation == "click":
            return self.mouse.click(
                kwargs.get("x"),
                kwargs.get("y"),
                kwargs.get("button", "left"),
                kwargs.get("clicks", 1)
            )
        elif operation == "move":
            return self.mouse.move(
                kwargs.get("x", 0),
                kwargs.get("y", 0),
                kwargs.get("duration", 0.0)
            )
        elif operation == "drag":
            return self.mouse.drag(
                kwargs.get("x1", 0),
                kwargs.get("y1", 0),
                kwargs.get("x2", 0),
                kwargs.get("y2", 0),
                kwargs.get("duration", 0.5)
            )
        elif operation == "scroll":
            return self.mouse.scroll(kwargs.get("clicks", 0))
        else:
            return KeyboardMouseResult(
                success=False,
                action=operation,
                error=f"Unknown operation: {operation}"
            )


# 便捷函数
def create_keyboard_hand() -> KeyboardMouseHand:
    """创建键鼠控制Hand"""
    return KeyboardMouseHand()
