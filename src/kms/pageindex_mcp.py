"""
PageIndex MCP Integration

将 PageIndex 作为 MCP 工具暴露（通过 KMS API）

⚠️ 此模块现在通过 HTTP API 调用独立的 KMS 服务
"""

import logging
from typing import Dict, Any, List, Optional

from .kms_client import KMSClient, get_kms_client

logger = logging.getLogger(__name__)


class PageIndexMCPTools:
    """
    PageIndex MCP 工具集
    
    通过 MCP 协议暴露 PageIndex 功能
    ⚠️ 现在通过 KMS API 调用独立服务
    """
    
    def __init__(
        self,
        kms_client: Optional[KMSClient] = None,
        api_url: Optional[str] = None
    ):
        """
        初始化 PageIndex MCP 工具
        
        Args:
            kms_client: KMS 客户端实例
            api_url: KMS API 地址（可选）
        """
        if kms_client:
            self.client = kms_client
        elif api_url:
            self.client = KMSClient(api_url=api_url)
        else:
            self.client = get_kms_client()
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        获取 MCP 工具列表
        
        返回符合 MCP 规范的工具定义
        """
        return [
            {
                "name": "pageindex_index_document",
                "description": "为 PDF、Markdown 或文本文件建立 PageIndex 树结构索引。适用于长文档的专业分析，如财务报告、法律合同、技术手册。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "document_path": {
                            "type": "string",
                            "description": "文档路径 (PDF/MD/TXT)"
                        },
                        "document_description": {
                            "type": "string",
                            "description": "文档描述（可选），帮助 LLM 更好地理解文档内容"
                        }
                    },
                    "required": ["document_path"]
                }
            },
            {
                "name": "pageindex_query",
                "description": "使用推理式检索查询已索引的文档。像人类专家一样在文档树结构中导航，找到相关内容。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "查询问题"
                        },
                        "document_path": {
                            "type": "string",
                            "description": "可选，指定文档路径"
                        },
                        "mode": {
                            "type": "string",
                            "enum": ["vector_only", "pageindex_only", "hybrid", "auto"],
                            "default": "auto",
                            "description": "检索模式"
                        },
                        "top_k": {
                            "type": "integer",
                            "default": 5,
                            "description": "返回结果数量"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "pageindex_list_documents",
                "description": "列出所有已索引的文档",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "pageindex_get_tree",
                "description": "获取文档的树结构（用于可视化或调试）",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "document_path": {
                            "type": "string",
                            "description": "文档路径"
                        }
                    },
                    "required": ["document_path"]
                }
            }
        ]
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        调用 MCP 工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        try:
            if tool_name == "pageindex_index_document":
                return self._index_document(arguments)
            
            elif tool_name == "pageindex_query":
                return self._query(arguments)
            
            elif tool_name == "pageindex_list_documents":
                return self._list_documents()
            
            elif tool_name == "pageindex_get_tree":
                return self._get_tree(arguments)
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}"
                }
        
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _index_document(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """索引文档"""
        try:
            result = self.client.pageindex_index_document(
                document_path=args["document_path"],
                document_description=args.get("document_description", "")
            )
            return result
        except Exception as e:
            logger.error(f"Failed to index document: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _query(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """查询"""
        try:
            result = self.client.pageindex_query(
                query=args["query"],
                document_path=args.get("document_path"),
                mode=args.get("mode", "auto"),
                top_k=args.get("top_k", 5)
            )
            return result
        except Exception as e:
            logger.error(f"Failed to query: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _list_documents(self) -> Dict[str, Any]:
        """列出已索引文档"""
        try:
            result = self.client.pageindex_list_documents()
            return result
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_tree(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """获取树结构"""
        try:
            result = self.client.pageindex_get_tree(
                document_path=args["document_path"]
            )
            return result
        except Exception as e:
            logger.error(f"Failed to get tree: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """
        获取 MCP 资源列表
        
        返回可用的文档资源
        """
        try:
            result = self.client.pageindex_list_documents()
            docs = result.get("documents", [])
            
            resources = []
            for doc in docs:
                resources.append({
                    "uri": f"pageindex://document/{doc}",
                    "name": doc.split("/")[-1] if isinstance(doc, str) else str(doc),
                    "description": f"Indexed document: {doc}",
                    "mimeType": "application/json"
                })
            
            return resources
        except Exception as e:
            logger.warning(f"Failed to get resources: {e}")
            return []
    
    def is_available(self) -> bool:
        """检查 KMS 服务是否可用"""
        return self.client.is_available()


# ==================== MCP Server 集成 ====================

class PageIndexMCPServer:
    """
    PageIndex MCP 服务器
    
    标准的 MCP 服务器实现
    """
    
    def __init__(
        self,
        pageindex_tools: Optional[PageIndexMCPTools] = None,
        kms_client: Optional[KMSClient] = None,
        server_name: str = "pageindex"
    ):
        if pageindex_tools:
            self.tools = pageindex_tools
        else:
            self.tools = PageIndexMCPTools(kms_client=kms_client)
        self.server_name = server_name
    
    async def handle_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理 MCP 请求
        
        标准的 MCP 协议处理
        """
        if method == "tools/list":
            return {"tools": self.tools.get_tools()}
        
        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {}) or {}
            
            result = self.tools.call_tool(tool_name, arguments)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": str(result)
                    }
                ]
            }
        
        elif method == "resources/list":
            return {"resources": self.tools.get_resources()}
        
        elif method == "resources/read":
            uri = params.get("uri", "")
            
            if uri.startswith("pageindex://document/"):
                doc_path = uri.replace("pageindex://document/", "")
                result = self.tools.call_tool("pageindex_get_tree", {"document_path": doc_path})
                return result
            
            return {"success": False, "error": f"Unknown resource: {uri}"}
        
        else:
            return {"success": False, "error": f"Unknown method: {method}"}


# ==================== 便捷函数 ====================

_pageindex_mcp_tools: Optional[PageIndexMCPTools] = None


def get_pageindex_mcp_tools(
    kms_client: Optional[KMSClient] = None,
    api_url: Optional[str] = None
) -> PageIndexMCPTools:
    """获取 PageIndex MCP 工具实例"""
    global _pageindex_mcp_tools
    if _pageindex_mcp_tools is None:
        _pageindex_mcp_tools = PageIndexMCPTools(kms_client=kms_client, api_url=api_url)
    return _pageindex_mcp_tools


def reset_pageindex_mcp_tools():
    """重置 PageIndex MCP 工具"""
    global _pageindex_mcp_tools
    _pageindex_mcp_tools = None
