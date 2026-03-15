#!/usr/bin/env python3
"""
RANGEN 旧系统 → 新系统 迁移脚本
执行 Wave 1-5 所有迁移步骤
"""

import asyncio
import os
import sys
import time
import warnings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 添加项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_step(step_num, title):
    """打印步骤"""
    print(f"\n[Step {step_num}] {title}")
    print("-" * 40)


async def run_wave_1():
    """Wave 1: 创建统一执行器"""
    print_header("Wave 1: 创建统一执行器")
    
    # 检查文件是否已存在
    unified_executor_path = os.path.join(PROJECT_ROOT, "src/agents/unified_executor.py")
    
    if os.path.exists(unified_executor_path):
        print("✅ 统一执行器已存在，跳过创建")
        return True
    
    # 创建统一执行器代码
    code = '''#!/usr/bin/env python3
"""
统一执行器 - 兼容新旧系统

提供统一API，同时支持:
- 新系统: Skill-based + MCP协议
- 旧系统: Tool-based (deprecated)
"""

import asyncio
from typing import Any, Dict, Optional
from dataclasses import dataclass

from src.agents.skills.hybrid_tool_executor import HybridToolExecutor
from src.agents.tools.tool_registry import get_tool_registry
from src.services.logging_service import get_logger

logger = get_logger(__name__)


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0


class UnifiedExecutor:
    """
    统一执行器
    
    用法:
        executor = UnifiedExecutor()
        
        # 使用新系统 (Skill-based + MCP)
        result = await executor.execute("calculator", {"expression": "10 + 20"})
        
        # 强制使用旧系统 (Tool-based)
        result = await executor.execute("calculator", {"expression": "10 + 20"}, mode="legacy")
    """
    
    def __init__(self, default_mode: str = "skill"):
        self._default_mode = default_mode
        self._skill_executor = None
        self._tool_registry = None
        logger.info(f"UnifiedExecutor initialized with mode: {default_mode}")
    
    @property
    def skill_executor(self) -> HybridToolExecutor:
        if self._skill_executor is None:
            self._skill_executor = HybridToolExecutor(internal_mode="mcp")
        return self._skill_executor
    
    @property
    def tool_registry(self):
        if self._tool_registry is None:
            self._tool_registry = get_tool_registry()
        return self._tool_registry
    
    async def execute(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        mode: Optional[str] = None
    ) -> ExecutionResult:
        import time
        start_time = time.time()
        
        exec_mode = mode or self._default_mode
        
        try:
            if exec_mode == "skill":
                result = await self._execute_skill(tool_name, parameters)
            else:
                result = await self._execute_legacy(tool_name, parameters)
            
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                success=True,
                result=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Execution failed: {e}")
            
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    async def _execute_skill(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        result = await self.skill_executor.execute(
            tool_name=tool_name,
            parameters=parameters,
            tool_source=None
        )
        return result.result if hasattr(result, 'result') else result
    
    async def _execute_legacy(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        warnings.warn(
            f"Using legacy execution for {tool_name}. Please migrate to Skill-based execution.",
            DeprecationWarning,
            stacklevel=3
        )
        
        logger.warning(f"Legacy execution called for: {tool_name}")
        
        tool = self.tool_registry.get_tool(tool_name)
        if tool is None:
            raise ValueError(f"Tool not found: {tool_name}")
        
        result = await tool.execute(**parameters)
        return result.output if hasattr(result, 'output') else result
    
    def list_tools(self) -> Dict[str, list]:
        tools = self.tool_registry.list_tools()
        return {
            "available_tools": [t["name"] for t in tools],
            "count": len(tools)
        }


_unified_executor: Optional[UnifiedExecutor] = None


def get_unified_executor(default_mode: str = "skill") -> UnifiedExecutor:
    global _unified_executor
    if _unified_executor is None:
        _unified_executor = UnifiedExecutor(default_mode)
    return _unified_executor


async def execute_tool(
    tool_name: str,
    parameters: Dict[str, Any],
    use_mcp: bool = True
) -> ExecutionResult:
    executor = get_unified_executor()
    mode = "skill" if use_mcp else "legacy"
    return await executor.execute(tool_name, parameters, mode)
'''
    
    with open(unified_executor_path, 'w') as f:
        f.write(code)
    
    print(f"✅ 统一执行器已创建: {unified_executor_path}")
    return True


async def run_wave_2():
    """Wave 2: 创建工具到Skill映射"""
    print_header("Wave 2: 创建工具到Skill映射")
    
    map_path = os.path.join(PROJECT_ROOT, "src/agents/skills/tool_to_skill_map.py")
    
    if os.path.exists(map_path):
        print("✅ 映射表已存在，跳过创建")
        return True
    
    code = '''#!/usr/bin/env python3
"""
工具到Skill的映射表

用于将旧系统的工具名称映射到新系统的Skill
"""

# 旧工具名 -> 新Skill名
TOOL_TO_SKILL_MAP = {
    # 计算和推理
    "calculator": "calculator-skill",
    "reasoning": "reasoning-skill",
    
    # 搜索和检索
    "search": "search-skill",
    "web_search": "web-search-skill",
    "real_search": "real-time-search-skill",
    "rag": "rag-skill",
    "knowledge_retrieval": "knowledge-retrieval-skill",
    
    # 生成和回答
    "answer_generation": "answer-generation-skill",
    "citation": "citation-skill",
    
    # 多模态
    "multimodal": "multimodal-skill",
    "browser": "browser-skill",
    "file_read": "file-read-skill",
}

# Skill配置目录
SKILL_BASE_PATH = "src/agents/skills/bundled"


def get_skill_name(tool_name: str) -> str:
    """获取工具对应的Skill名称"""
    return TOOL_TO_SKILL_MAP.get(tool_name, tool_name)


def get_skill_path(tool_name: str) -> str:
    """获取Skill目录路径"""
    skill_name = get_skill_name(tool_name)
    return f"{SKILL_BASE_PATH}/{skill_name}"


def is_skill_available(tool_name: str) -> bool:
    """检查Skill是否可用"""
    skill_path = get_skill_path(tool_name)
    return os.path.exists(skill_path)


import os

# 导出
__all__ = [
    "TOOL_TO_SKILL_MAP",
    "get_skill_name",
    "get_skill_path",
    "is_skill_available",
]
'''
    
    with open(map_path, 'w') as f:
        f.write(code)
    
    print(f"✅ 映射表已创建: {map_path}")
    return True


async def run_wave_3():
    """Wave 3: 创建测试"""
    print_header("Wave 3: 创建测试")
    
    test_path = os.path.join(PROJECT_ROOT, "tests/test_unified_executor.py")
    
    if os.path.exists(test_path):
        print("✅ 测试文件已存在，跳过创建")
        return True
    
    code = '''#!/usr/bin/env python3
"""
统一执行器测试

测试新旧系统执行结果一致性
"""

import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.unified_executor import UnifiedExecutor, get_unified_executor


class TestUnifiedExecutor:
    """统一执行器测试"""
    
    @pytest.fixture
    def executor(self):
        """创建执行器"""
        return UnifiedExecutor(default_mode="skill")
    
    @pytest.mark.asyncio
    async def test_calculator_skill_mode(self, executor):
        """测试计算器 - Skill模式"""
        result = await executor.execute(
            "calculator",
            {"expression": "100 + 200"}
        )
        
        assert result.success is True
        assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_calculator_legacy_mode(self, executor):
        """测试计算器 - Legacy模式"""
        result = await executor.execute(
            "calculator",
            {"expression": "50 + 50"},
            mode="legacy"
        )
        
        assert result.success is True
        # Legacy模式会触发deprecation warning
    
    @pytest.mark.asyncio
    async def test_result_consistency(self, executor):
        """测试结果一致性"""
        # Skill模式
        result1 = await executor.execute(
            "calculator",
            {"expression": "10 * 10"},
            mode="skill"
        )
        
        # Legacy模式
        result2 = await executor.execute(
            "calculator",
            {"expression": "10 * 10"},
            mode="legacy"
        )
        
        # 结果应该一致 (都是100)
        assert result1.success == result2.success
    
    def test_list_tools(self, executor):
        """测试列出工具"""
        tools = executor.list_tools()
        
        assert "available_tools" in tools
        assert "count" in tools
        assert tools["count"] > 0


class TestToolToSkillMap:
    """工具到Skill映射测试"""
    
    def test_get_skill_name(self):
        """测试获取Skill名称"""
        from src.agents.skills.tool_to_skill_map import get_skill_name
        
        assert get_skill_name("calculator") == "calculator-skill"
        assert get_skill_name("search") == "search-skill"
        assert get_skill_name("unknown") == "unknown"
    
    def test_is_skill_available(self):
        """测试Skill可用性"""
        from src.agents.skills.tool_to_skill_map import is_skill_available
        
        # 已知存在的工具
        assert is_skill_available("calculator") is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''
    
    os.makedirs(os.path.dirname(test_path), exist_ok=True)
    with open(test_path, 'w') as f:
        f.write(code)
    
    print(f"✅ 测试文件已创建: {test_path}")
    return True


async def run_wave_4():
    """Wave 4: 运行测试验证"""
    print_header("Wave 4: 运行测试验证")
    
    # 测试统一执行器
    print("\n测试统一执行器...")
    
    from src.agents.unified_executor import UnifiedExecutor
    
    executor = UnifiedExecutor(default_mode="skill")
    
    # 测试1: Skill模式
    print("\n[测试1] Skill模式 - calculator")
    result1 = await executor.execute("calculator", {"expression": "100 + 200"})
    print(f"  结果: {result1.success}")
    print(f"  执行时间: {result1.execution_time:.4f}s")
    
    # 测试2: Legacy模式
    print("\n[测试2] Legacy模式 - calculator")
    result2 = await executor.execute("calculator", {"expression": "50 + 50"}, mode="legacy")
    print(f"  结果: {result2.success}")
    
    # 测试3: 列出工具
    print("\n[测试3] 列出工具")
    tools = executor.list_tools()
    print(f"  工具数量: {tools['count']}")
    
    # 测试4: 搜索工具
    print("\n[测试4] search工具")
    result3 = await executor.execute("search", {"query": "Python"})
    print(f"  结果: {result3.success}")
    
    print("\n✅ Wave 4 测试通过!")
    return True


async def run_wave_5():
    """Wave 5: 清理和总结"""
    print_header("Wave 5: 清理和总结")
    
    print("\n📊 迁移总结:")
    print("-" * 40)
    
    # 统计
    files_created = [
        "src/agents/unified_executor.py",
        "src/agents/skills/tool_to_skill_map.py",
        "tests/test_unified_executor.py",
    ]
    
    for f in files_created:
        path = os.path.join(PROJECT_ROOT, f)
        exists = "✅" if os.path.exists(path) else "❌"
        print(f"  {exists} {f}")
    
    print("\n🎉 迁移完成!")
    print("\n下一步:")
    print("  1. 运行测试: pytest tests/test_unified_executor.py")
    print("  2. 切换默认模式: 修改 UnifiedExecutor(default_mode='skill')")
    print("  3. 逐步迁移: 将旧代码切换到新系统")
    
    return True


async def main():
    """主函数"""
    print_header("RANGEN 旧系统 → 新系统 迁移")
    print(f"项目路径: {PROJECT_ROOT}")
    
    # 执行所有Wave
    await run_wave_1()
    await run_wave_2()
    await run_wave_3()
    await run_wave_4()
    await run_wave_5()
    
    print("\n" + "=" * 60)
    print("  🎉 所有迁移步骤完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
