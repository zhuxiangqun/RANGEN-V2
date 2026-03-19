#!/usr/bin/env python3
"""
T19: 物理控制测试
测试 KeyboardMouseHand, ScreenCaptureHand, SandboxExecutor
"""

import sys
sys.path.insert(0, '.')

import pytest
import tempfile
import os


class TestKeyboardMouseHand:
    """测试键盘鼠标控制"""
    
    def test_import(self):
        """测试 KeyboardMouseHand 可以导入"""
        from src.hands.keyboard_mouse_hand import KeyboardMouseHand
        hand = KeyboardMouseHand()
        assert hand is not None


class TestScreenCaptureHand:
    """测试屏幕捕获"""
    
    def test_import(self):
        """测试 ScreenCaptureHand 可以导入"""
        from src.hands.screen_capture_hand import ScreenCaptureHand
        hand = ScreenCaptureHand()
        assert hand is not None


class TestTMWebDriver:
    """测试浏览器驱动"""
    
    def test_import(self):
        """测试 TMWebDriver 可以导入"""
        from src.hands.tmwebdriver import TMWebDriver
        driver = TMWebDriver()
        assert driver is not None


class TestSandboxExecutor:
    """测试沙箱执行器"""
    
    def test_import(self):
        """测试 SandboxExecutor 可以导入"""
        from src.core.sandbox.sandbox_executor import SandboxExecutor
        executor = SandboxExecutor()
        assert executor is not None
    
    def test_execute_skill_method_exists(self):
        """测试 execute_skill 方法存在"""
        from src.core.sandbox.sandbox_executor import SandboxExecutor
        executor = SandboxExecutor()
        assert hasattr(executor, 'execute_skill')


class TestPhysicalControlComponents:
    """测试物理控制组件"""
    
    def test_all_physical_hands_import(self):
        """测试所有物理控制 Hands 可导入"""
        from src.hands.keyboard_mouse_hand import KeyboardMouseHand
        from src.hands.screen_capture_hand import ScreenCaptureHand
        from src.hands.tmwebdriver import TMWebDriver
        
        assert KeyboardMouseHand is not None
        assert ScreenCaptureHand is not None
        assert TMWebDriver is not None


class TestTampermonkeyIntegration:
    """测试 Tampermonkey 集成"""
    
    def test_script_exists(self):
        """测试脚本文件存在"""
        script_path = 'src/hands/tampermonkey_script.js'
        assert os.path.exists(script_path), f"Script not found: {script_path}"
    
    def test_script_format(self):
        """测试脚本格式"""
        script_path = 'src/hands/tampermonkey_script.js'
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        assert '// ==UserScript==' in content
        assert '// ==/UserScript==' in content
        assert '@match' in content
        assert 'GM_xmlhttpRequest' in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
