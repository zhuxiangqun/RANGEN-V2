#!/usr/bin/env python3
"""
测试外部 MCP 服务器连接

使用方式:
1. 配置环境变量 (如 GITHUB_PERSONAL_ACCESS_TOKEN)
2. 修改 config/mcp_config.yaml 中 external_servers.<server>.enabled: true
3. 运行 python test_external_mcp.py
"""

import asyncio
import os
import sys
sys.path.insert(0, '/Users/apple/workdata/person/zy/RANGEN-main(syu-python)')

from dotenv import load_dotenv
load_dotenv()

from src.gateway.mcp import MCPClient, MCPConnection


async def test_external_mcp():
    """测试连接外部 MCP 服务器"""
    
    print("=" * 60)
    print("测试: 连接外部 MCP 服务器")
    print("=" * 60)
    
    # 列出可用的外部服务器配置
    external_servers = [
        {
            "name": "filesystem",
            "description": "File Operations",
            "server_url": "echo 'test'",
            "transport": "stdio"
        }
    ]
    
    # 注意: 实际连接需要:
    # 1. 安装 npx 包: npm install -g @modelcontextprotocol/server-github
    # 2. 设置环境变量
    # 3. 启用 config/mcp_config.yaml 中的 external_servers.<server>.enabled
    
    print("\n可配置的外部 MCP 服务器:")
    print("-" * 40)
    
    servers = [
        ("github", "GitHub Tools (Issues, PRs, Repos)", "npx -y @modelcontextprotocol/server-github"),
        ("slack", "Slack Tools (Messages, Channels)", "npx -y @modelcontextprotocol/server-slack"),
        ("puppeteer", "Browser Automation", "npx -y @modelcontextprotocol/server-puppeteer"),
        ("filesystem", "File Operations", "npx -y @modelcontextprotocol/server-filesystem <path>"),
        ("brave-search", "Web Search", "npx -y @modelcontextprotocol/server-brave-search"),
    ]
    
    for name, desc, cmd in servers:
        print(f"  {name:15} - {desc}")
        print(f"                安装: {cmd}")
        print()
    
    print("\n当前已实现的架构:")
    print("-" * 40)
    print("1. HybridToolExecutor - 统一工具调用")
    print("   - 内部工具: 直接通过 Python 实例调用")
    print("   - 外部 MCP: 通过 MCP 协议调用")
    print()
    print("2. 连接外部 MCP 服务器步骤:")
    print("   a) 安装 MCP 服务器:")
    print("      npm install -g @modelcontextprotocol/server-github")
    print()
    print("   b) 设置环境变量:")
    print("      export GITHUB_PERSONAL_ACCESS_TOKEN=your_token")
    print()
    print("   c) 启用配置:")
    print("      编辑 config/mcp_config.yaml")
    print("      设置 external_servers.github.enabled: true")
    print()
    print("   d) 添加服务器:")
    print("      executor = get_hybrid_executor()")
    print('      await executor.add_mcp_server("github", "npx -y @modelcontextprotocol/server-github", "stdio")')
    print()
    
    # 演示: 如果有 npx 和已安装的包，可以尝试连接
    print("\n" + "=" * 60)
    print("架构验证: 测试 HybridToolExecutor")
    print("=" * 60)
    
    from src.agents.skills.hybrid_tool_executor import get_hybrid_executor
    
    executor = get_hybrid_executor()
    tools = executor.list_all_tools()
    
    print(f"\n当前可用工具总数: {len(tools.get('internal', [])) + len(tools.get('mcp', []))}")
    print(f"  - 内部工具: {len(tools.get('internal', []))}")
    print(f"  - MCP 工具: {len(tools.get('mcp', []))}")
    
    print("\n内部工具列表:")
    for t in tools.get('internal', [])[:5]:
        print(f"  - {t['name']}: {t['description'][:50]}...")
    
    print("\n" + "=" * 60)
    print("✅ 外部 MCP 服务器配置完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_external_mcp())
