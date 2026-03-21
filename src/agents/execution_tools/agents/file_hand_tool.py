#!/usr/bin/env python3
"""
文件 Hand 工具 - 将 Hands 能力暴露给主流程工具链

使 ReAct/推理 Agent 在主对话中可调用「读取文件」等能力，
无需经过 SOP 节点。
"""

import time
import logging
from typing import Dict, Any, Optional

from .base_tool import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class FileReadHandTool(BaseTool):
    """文件读取工具 - 封装 FileReadHand，供主流程工具链调用"""

    def __init__(self):
        super().__init__(
            tool_name="file_read",
            description="读取本地文件内容；参数: path(必填), encoding(可选,默认utf-8), parse_json(可选)"
        )
        self._hand = None

    def _get_hand(self):
        if self._hand is None:
            try:
                from src.hands.file_hand import FileReadHand
                self._hand = FileReadHand()
            except Exception as e:
                logger.warning(f"FileReadHand 不可用: {e}")
        return self._hand

    async def call(
        self,
        query: str = "",
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ToolResult:
        path = kwargs.get("path") or (context or {}).get("path") or (query.strip() if query else "")
        if not path:
            return ToolResult(success=False, data=None, error="缺少 path 参数")
        start = time.time()
        try:
            hand = self._get_hand()
            if hand is None:
                return ToolResult(success=False, data=None, error="文件 Hand 未初始化")
            result = await hand.execute(path=path, encoding=kwargs.get("encoding", "utf-8"))
            out = result.output if result.success else None
            err = None if result.success else getattr(result, "error", "unknown")
            return ToolResult(
                success=result.success,
                data=out,
                error=err,
                execution_time=time.time() - start
            )
        except Exception as e:
            logger.exception("file_read tool failed")
            return ToolResult(success=False, data=None, error=str(e), execution_time=time.time() - start)
