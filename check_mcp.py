#!/usr/bin/env python3
"""检查MCP库是否安装"""
try:
    from mcp import Server
    print("✅ MCP库已安装")
    print(f"   版本: {Server}")
except ImportError as e:
    print(f"❌ MCP库未安装: {e}")
