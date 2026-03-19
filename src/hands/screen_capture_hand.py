#!/usr/bin/env python3
"""
ScreenCaptureHand - 屏幕捕获能力
"""
import logging
import time
from typing import Optional, Tuple
from src.hands.base import BaseHand, HandExecutionResult, HandCategory, HandSafetyLevel

logger = logging.getLogger(__name__)

mss = None
try:
    import mss
    mss_available = True
except ImportError:
    mss_available = False

PIL_available = False
try:
    from PIL import ImageGrab
    PIL_available = True
except ImportError:
    pass


class ScreenCaptureHand(BaseHand):
    """屏幕捕获Hand
    
    功能：
    - 全屏截图
    - 区域截图
    - 多显示器支持
    """
    
    def __init__(self):
        super().__init__(
            name="screen_capture",
            description="截取屏幕或指定区域的图像",
            category=HandCategory.MONITORING,
            safety_level=HandSafetyLevel.SAFE
        )
        self._screenshot_func = self._detect_screenshot_method()
    
    def _detect_screenshot_method(self) -> Optional[str]:
        """检测可用的截图方法"""
        if mss_available:
            logger.info("ScreenCaptureHand: Using mss for screenshot")
            return "mss"
        elif PIL_available:
            logger.info("ScreenCaptureHand: Using PIL for screenshot")
            return "PIL"
        else:
            logger.warning("ScreenCaptureHand: No screenshot library available")
            return None
    
    async def execute(self, **kwargs) -> HandExecutionResult:
        """执行屏幕捕获
        
        Args:
            region: 可选，指定区域 (x, y, width, height)
            output_path: 可选，保存路径
            
        Returns:
            截图结果
        """
        start_time = time.time()
        
        try:
            if self._screenshot_func is None:
                return HandExecutionResult(
                    hand_name=self.name,
                    success=False,
                    output=None,
                    error="No screenshot library available. Install mss or Pillow.",
                    execution_time=time.time() - start_time
                )
            
            region = kwargs.get("region")
            output_path = kwargs.get("output_path")
            
            if self._screenshot_func == "mss":
                screenshot = self._capture_mss(region, output_path)
            else:
                screenshot = self._capture_pil(region, output_path)
            
            return HandExecutionResult(
                hand_name=self.name,
                success=True,
                output={"screenshot": screenshot, "path": output_path},
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"ScreenCaptureHand failed: {e}")
            return HandExecutionResult(
                hand_name=self.name,
                success=False,
                output=None,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _capture_mss(self, region: Optional[Tuple[int, int, int, int]], output_path: Optional[str]) -> str:
        """使用mss库截图"""
        if mss is None:
            raise ImportError("mss library not available")
        
        with mss.mss() as sct:
            if region:
                monitor = {"left": region[0], "top": region[1], "width": region[2], "height": region[3]}
            else:
                monitor = sct.monitors[1]
            
            if output_path:
                sct.shot(output=output_path, mon=monitor)
                return output_path
            else:
                return "Screenshot captured (no path specified)"
    
    def _capture_pil(self, region: Optional[Tuple[int, int, int, int]], output_path: Optional[str]) -> str:
        """使用PIL库截图"""
        if not PIL_available:
            raise ImportError("PIL library not available")
        
        from PIL import ImageGrab
        
        if region:
            screenshot = ImageGrab.grab(bbox=region)
        else:
            screenshot = ImageGrab.grab()
        
        if output_path:
            screenshot.save(output_path)
            return output_path
        else:
            return "Screenshot captured (no path specified)"
    
    def validate_parameters(self, **kwargs) -> bool:
        """验证参数"""
        region = kwargs.get("region")
        if region:
            if not isinstance(region, (tuple, list)) or len(region) != 4:
                return False
            if not all(isinstance(x, int) for x in region):
                return False
        return True
