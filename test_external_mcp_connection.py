#!/usr/bin/env python3
"""
外部MCP服务器连接测试和启用脚本

使用方式：
    python test_external_mcp_connection.py --server github
    python test_external_mcp_connection.py --list
    python test_external_mcp_connection.py --enable-all
"""

import asyncio
import argparse
import os
import sys
from typing import Dict, List, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_github_mcp() -> bool:
    """测试GitHub MCP服务器连接"""
    print("\n" + "=" * 60)
    print("测试: GitHub MCP 服务器")
    print("=" * 60)
    
    try:
        from src.gateway.mcp import MCPRegistry, MCPConnection
        
        # 创建连接
        connection = MCPConnection(
            name="github",
            server_url="npx -y @modelcontextprotocol/server-github",
            transport="stdio"
        )
        
        # 设置环境变量（需要用户配置）
        github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
        if not github_token:
            print("⚠️  GITHUB_PERSONAL_ACCESS_TOKEN 未设置")
            print("   请在 .env 中设置: GITHUB_PERSONAL_ACCESS_TOKEN=your_token")
            print("   可以从 https://github.com/settings/tokens 生成")
            return False
        
        # 尝试连接
        from src.gateway.mcp import MCPClient
        client = MCPClient(connection)
        
        print("正在连接...")
        success = await client.connect()
        
        if success:
            print("✅ GitHub MCP 服务器连接成功!")
            
            # 获取工具列表
            tools = await client.list_tools()
            print(f"   可用工具: {len(tools)} 个")
            for tool in tools[:5]:
                print(f"   - {tool.name}")
            
            await client.disconnect()
            return True
        else:
            print(f"❌ 连接失败: {connection.last_error}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


async def test_slack_mcp() -> bool:
    """测试Slack MCP服务器连接"""
    print("\n" + "=" * 60)
    print("测试: Slack MCP 服务器")
    print("=" * 60)
    
    slack_token = os.getenv("SLACK_BOT_TOKEN")
    if not slack_token:
        print("⚠️  SLACK_BOT_TOKEN 未设置")
        print("   请在 .env 中设置: SLACK_BOT_TOKEN=xoxb-...")
        return False
    
    try:
        from src.gateway.mcp import MCPRegistry, MCPConnection, MCPClient
        
        connection = MCPConnection(
            name="slack",
            server_url="npx -y @modelcontextprotocol/server-slack",
            transport="stdio"
        )
        
        client = MCPClient(connection)
        success = await client.connect()
        
        if success:
            print("✅ Slack MCP 服务器连接成功!")
            tools = await client.list_tools()
            print(f"   可用工具: {len(tools)} 个")
            await client.disconnect()
            return True
        else:
            print(f"❌ 连接失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


async def test_brave_search_mcp() -> bool:
    """测试Brave Search MCP服务器连接"""
    print("\n" + "=" * 60)
    print("测试: Brave Search MCP 服务器")
    print("=" * 60)
    
    brave_key = os.getenv("BRAVE_API_KEY")
    if not brave_key:
        print("⚠️  BRAVE_API_KEY 未设置")
        print("   请在 .env 中设置: BRAVE_API_KEY=your_key")
        print("   可以从 https://brave.com/search/api/ 申请")
        return False
    
    try:
        from src.gateway.mcp import MCPConnection, MCPClient
        
        connection = MCPConnection(
            name="brave-search",
            server_url="npx -y @modelcontextprotocol/server-brave-search",
            transport="stdio"
        )
        
        client = MCPClient(connection)
        success = await client.connect()
        
        if success:
            print("✅ Brave Search MCP 服务器连接成功!")
            tools = await client.list_tools()
            print(f"   可用工具: {len(tools)} 个")
            await client.disconnect()
            return True
        else:
            print(f"❌ 连接失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


async def enable_external_mcp_from_config():
    """从配置文件启用外部MCP服务器"""
    print("\n" + "=" * 60)
    print("从配置文件启用外部MCP服务器")
    print("=" * 60)
    
    import yaml
    
    config_path = "config/mcp_config.yaml"
    if not os.path.exists(config_path):
        print(f"❌ 配置文件不存在: {config_path}")
        return
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    external_servers = config.get('external_servers', {})
    
    results = {}
    for server_name, server_config in external_servers.items():
        enabled = server_config.get('enabled', False)
        print(f"\n{server_name}: {'已启用' if enabled else '未启用'}")
        
        if enabled:
            # 尝试连接
            print(f"   尝试连接...")
            # 这里可以添加实际的连接逻辑
            results[server_name] = "enabled"
        else:
            results[server_name] = "disabled"
    
    return results


async def add_server_to_registry(name: str, server_url: str, transport: str = "stdio"):
    """添加MCP服务器到注册表"""
    from src.gateway.mcp import get_mcp_registry
    
    registry = get_mcp_registry()
    
    try:
        connection_id = await registry.add_server(name, server_url, transport)
        print(f"✅ 服务器添加成功: {name} (ID: {connection_id})")
        return connection_id
    except Exception as e:
        print(f"❌ 添加服务器失败: {e}")
        return None


async def list_registered_servers():
    """列出已注册的MCP服务器"""
    from src.gateway.mcp import get_mcp_registry
    
    registry = get_mcp_registry()
    connections = registry.list_connections()
    
    print("\n已注册的MCP服务器:")
    print("-" * 40)
    
    if not connections:
        print("  (无)")
    else:
        for conn in connections:
            status = "✅ 已连接" if conn['connected'] else "❌ 未连接"
            print(f"  - {conn['name']}: {status}")
            print(f"    工具数: {conn.get('tools_count', 0)}")


async def main():
    parser = argparse.ArgumentParser(description="外部MCP服务器管理工具")
    parser.add_argument("--server", choices=["github", "slack", "brave-search", "all"],
                       help="测试指定服务器")
    parser.add_argument("--list", action="store_true", help="列出已注册的服务器")
    parser.add_argument("--enable-all", action="store_true", help="从配置启用所有服务器")
    parser.add_argument("--add", nargs=3, metavar=("NAME", "URL", "TRANSPORT"),
                       help="添加新服务器")
    
    args = parser.parse_args()
    
    if args.list:
        await list_registered_servers()
    elif args.server:
        if args.server == "github":
            await test_github_mcp()
        elif args.server == "slack":
            await test_slack_mcp()
        elif args.server == "brave-search":
            await test_brave_search_mcp()
        elif args.server == "all":
            await test_github_mcp()
            await test_slack_mcp()
            await test_brave_search_mcp()
    elif args.enable_all:
        await enable_external_mcp_from_config()
    elif args.add:
        name, url, transport = args.add
        await add_server_to_registry(name, url, transport)
    else:
        # 默认显示帮助
        parser.print_help()
        print("\n" + "=" * 60)
        print("快速开始:")
        print("=" * 60)
        print("1. 设置环境变量:")
        print("   export GITHUB_PERSONAL_ACCESS_TOKEN=your_token")
        print("   export SLACK_BOT_TOKEN=xoxb-...")
        print("   export BRAVE_API_KEY=your_key")
        print("\n2. 编辑 config/mcp_config.yaml:")
        print("   将 enabled: false 改为 enabled: true")
        print("\n3. 测试连接:")
        print("   python test_external_mcp_connection.py --server github")


if __name__ == "__main__":
    asyncio.run(main())
