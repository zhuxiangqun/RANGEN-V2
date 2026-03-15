#!/usr/bin/env python3
"""
MCP Server Manager

Manages MCP server processes and lifecycle
"""

import asyncio
import subprocess
import signal
import sys
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

from src.services.logging_service import get_logger
from src.services.mcp_config_service import (
    get_mcp_config_service,
    MCPServerConfig,
    MCPConfig
)

logger = get_logger(__name__)


@dataclass
class MCPServerProcess:
    """MCP server process information"""
    config: MCPServerConfig
    process: Optional[subprocess.Popen] = None
    pid: Optional[int] = None
    status: str = "stopped"  # stopped, starting, running, error
    start_time: Optional[float] = None
    error_message: Optional[str] = None
    
    # Statistics
    request_count: int = 0
    error_count: int = 0
    last_request_time: Optional[float] = None


class MCPServerManager:
    """MCP server manager"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.config_service = get_mcp_config_service()
        self.config: Optional[MCPConfig] = None
        self.servers: Dict[str, MCPServerProcess] = {}
        self._initialized = True
        
        logger.info("MCPServerManager initialized")
    
    async def initialize(self) -> bool:
        """Initialize the MCP server manager"""
        try:
            self.config = self.config_service.load_config()
            
            if not self.config or not self.config.enabled:
                logger.info("MCP is disabled in configuration")
                return False
            
            # Create server processes for enabled servers
            enabled_servers = self.config_service.get_enabled_servers()
            for server_config in enabled_servers:
                self.servers[server_config.name] = MCPServerProcess(config=server_config)
                logger.info(f"Registered MCP server: {server_config.name}")
            
            # Auto-start servers if configured
            if self.config.integration.auto_start_servers:
                await self.start_all_servers()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP server manager: {e}")
            return False
    
    async def start_server(self, server_name: str) -> bool:
        """Start an MCP server"""
        if server_name not in self.servers:
            logger.error(f"MCP server not found: {server_name}")
            return False
        
        server = self.servers[server_name]
        
        if server.status == "running":
            logger.warning(f"MCP server already running: {server_name}")
            return True
        
        try:
            server.status = "starting"
            server.error_message = None
            
            # Build command based on transport
            if server.config.transport == "stdio":
                cmd = self._build_stdio_command(server.config)
            elif server.config.transport == "http" and server.config.http_enabled:
                cmd = self._build_http_command(server.config)
            else:
                server.status = "error"
                server.error_message = f"Unsupported transport: {server.config.transport}"
                logger.error(server.error_message)
                return False
            
            # Start the process
            logger.info(f"Starting MCP server '{server_name}' with command: {cmd}")
            
            # Use subprocess.Popen to start the process
            # Redirect stdout/stderr to capture output
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            server.process = process
            server.pid = process.pid
            server.start_time = asyncio.get_event_loop().time()
            
            # Wait a bit to check if process started successfully
            await asyncio.sleep(0.5)
            
            # Check process status
            return_code = process.poll()
            if return_code is not None:
                # Process exited immediately
                stderr_output = process.stderr.read() if process.stderr else ""
                server.status = "error"
                server.error_message = f"Process exited with code {return_code}: {stderr_output}"
                logger.error(f"Failed to start MCP server '{server_name}': {server.error_message}")
                return False
            
            server.status = "running"
            logger.info(f"MCP server '{server_name}' started successfully (PID: {server.pid})")
            
            # Start background task to monitor process
            asyncio.create_task(self._monitor_server_process(server_name))
            
            return True
            
        except Exception as e:
            server.status = "error"
            server.error_message = str(e)
            logger.error(f"Failed to start MCP server '{server_name}': {e}")
            return False
    
    async def stop_server(self, server_name: str) -> bool:
        """Stop an MCP server"""
        if server_name not in self.servers:
            logger.error(f"MCP server not found: {server_name}")
            return False
        
        server = self.servers[server_name]
        
        if server.status != "running" or not server.process:
            logger.warning(f"MCP server not running: {server_name}")
            return True
        
        try:
            logger.info(f"Stopping MCP server '{server_name}' (PID: {server.pid})")
            
            # Send SIGTERM
            server.process.terminate()
            
            # Wait for process to terminate
            try:
                await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, server.process.wait),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                # Force kill if not terminated
                logger.warning(f"MCP server '{server_name}' not responding to SIGTERM, sending SIGKILL")
                server.process.kill()
                await asyncio.get_event_loop().run_in_executor(None, server.process.wait)
            
            server.status = "stopped"
            server.process = None
            server.pid = None
            
            logger.info(f"MCP server '{server_name}' stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop MCP server '{server_name}': {e}")
            return False
    
    async def restart_server(self, server_name: str) -> bool:
        """Restart an MCP server"""
        if server_name not in self.servers:
            logger.error(f"MCP server not found: {server_name}")
            return False
        
        # Stop if running
        if self.servers[server_name].status == "running":
            await self.stop_server(server_name)
        
        # Start again
        return await self.start_server(server_name)
    
    async def start_all_servers(self) -> Dict[str, bool]:
        """Start all enabled MCP servers"""
        results = {}
        
        for server_name in list(self.servers.keys()):
            success = await self.start_server(server_name)
            results[server_name] = success
        
        return results
    
    async def stop_all_servers(self) -> Dict[str, bool]:
        """Stop all MCP servers"""
        results = {}
        
        for server_name in list(self.servers.keys()):
            success = await self.stop_server(server_name)
            results[server_name] = success
        
        return results
    
    async def get_server_status(self, server_name: str) -> Dict[str, Any]:
        """Get status of an MCP server"""
        if server_name not in self.servers:
            return {
                "status": "not_found",
                "error": f"Server not found: {server_name}"
            }
        
        server = self.servers[server_name]
        
        # Update process status if running
        if server.process and server.status == "running":
            return_code = server.process.poll()
            if return_code is not None:
                server.status = "stopped"
                server.error_message = f"Process exited with code {return_code}"
        
        result = {
            "name": server_name,
            "status": server.status,
            "config": {
                "transport": server.config.transport,
                "enabled": server.config.enabled,
                "description": server.config.description
            },
            "process": {
                "pid": server.pid,
                "start_time": server.start_time
            },
            "statistics": {
                "request_count": server.request_count,
                "error_count": server.error_count,
                "last_request_time": server.last_request_time
            }
        }
        
        if server.error_message:
            result["error"] = server.error_message
        
        if server.config.transport == "http" and server.config.http_enabled:
            result["config"]["http_endpoint"] = server.config.http_endpoint
        
        return result
    
    async def get_all_server_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all MCP servers"""
        results = {}
        
        for server_name in self.servers:
            results[server_name] = await self.get_server_status(server_name)
        
        return results
    
    def _build_stdio_command(self, config: MCPServerConfig) -> str:
        """Build command for stdio transport"""
        cmd_parts = []
        
        # Add Python interpreter if command starts with python
        if config.stdio_command.startswith("python"):
            cmd_parts.append(sys.executable)
            cmd_parts.append("-m")
            # Extract module path from command
            # Command format: "python -m src.agents.tools.mcp_server"
            # or "python src/agents/tools/mcp_server.py"
            if " -m " in config.stdio_command:
                module = config.stdio_command.split(" -m ")[1].strip()
                cmd_parts.append(module)
            elif ".py" in config.stdio_command:
                script = config.stdio_command.replace("python", "").strip()
                cmd_parts.append(script)
            else:
                # Assume it's a module
                cmd_parts.append(config.stdio_command.replace("python", "").strip())
        else:
            # Use command as-is
            cmd_parts.append(config.stdio_command)
        
        # Add arguments
        cmd_parts.extend(config.stdio_args)
        
        return " ".join(cmd_parts)
    
    def _build_http_command(self, config: MCPServerConfig) -> str:
        """Build command for HTTP transport"""
        cmd_parts = []
        
        # For HTTP transport, we need to pass --http flag to the server
        if config.stdio_command:
            # Start with stdio command
            stdio_cmd = self._build_stdio_command(config)
            cmd_parts.append(stdio_cmd)
            
            # Add HTTP arguments
            cmd_parts.append("--http")
            cmd_parts.append(f"--host {config.http_host}")
            cmd_parts.append(f"--port {config.http_port}")
        
        return " ".join(cmd_parts)
    
    async def _monitor_server_process(self, server_name: str):
        """Monitor a server process for crashes"""
        if server_name not in self.servers:
            return
        
        server = self.servers[server_name]
        
        if not server.process:
            return
        
        try:
            # Wait for process to exit
            await asyncio.get_event_loop().run_in_executor(None, server.process.wait)
            
            # Process exited
            return_code = server.process.returncode
            server.status = "stopped"
            
            if return_code != 0:
                server.error_message = f"Process crashed with exit code {return_code}"
                logger.error(f"MCP server '{server_name}' crashed: {server.error_message}")
                
                # Try to read stderr for more details
                if server.process.stderr:
                    try:
                        stderr_output = server.process.stderr.read()
                        if stderr_output:
                            logger.error(f"MCP server '{server_name}' stderr: {stderr_output}")
                    except:
                        pass
            else:
                logger.info(f"MCP server '{server_name}' stopped normally")
        
        except Exception as e:
            logger.error(f"Error monitoring MCP server '{server_name}': {e}")
    
    def record_request(self, server_name: str, success: bool = True):
        """Record a request to an MCP server"""
        if server_name in self.servers:
            server = self.servers[server_name]
            server.request_count += 1
            server.last_request_time = asyncio.get_event_loop().time()
            
            if not success:
                server.error_count += 1


# Singleton instance
_mcp_server_manager: Optional[MCPServerManager] = None


def get_mcp_server_manager() -> MCPServerManager:
    """Get the singleton MCPServerManager instance"""
    global _mcp_server_manager
    if _mcp_server_manager is None:
        _mcp_server_manager = MCPServerManager()
    return _mcp_server_manager


async def initialize_mcp_server_manager() -> bool:
    """Initialize the MCP server manager"""
    manager = get_mcp_server_manager()
    return await manager.initialize()