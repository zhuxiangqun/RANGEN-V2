"""
PageIndex MCP Integration

将PageIndex作为MCP工具暴露
"""

import logging
from typing import Dict, Any, List, Optional

from src.kms.pageindex import PageIndex, PageIndexConfig
from src.kms.pageindex_rag_integration import PageIndexRAGIntegration
from src.kms.pageindex_rag_integration import PageIndexRAGIntegration, HybridRetrievalResult

logger = logging.getLogger(__name__)


class PageIndexMCPTools:
    """
    PageIndex MCP工具集
    
    通过MCP协议暴露PageIndex功能
    """
    
    def __init__(
        self,
        pageindex: Optional[PageIndex] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.config = config or {}
        
        # 初始化PageIndex
        if pageindex:
            self.pageindex = pageindex
        else:
            pi_config = PageIndexConfig(
                index_storage_path=self.config.get("index_storage_path", "./data/pageindex"),
                model=self.config.get("model", "deepseek-chat"),
                max_pages_per_node=self.config.get("max_pages_per_node", 10),
                max_tokens_per_node=self.config.get("max_tokens_per_node", 20000)
            )
            self.pageindex = PageIndex(pi_config)
        
        # 初始化集成
        self.integration = PageIndexRAGIntegration(
            pageindex=self.pageindex,
            config=self.config
        )
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        获取MCP工具列表
        
        返回符合MCP规范的工具定义
        """
        return [
            {
                "name": "pageindex_index_document",
                "description": "为PDF、Markdown或文本文件建立PageIndex树结构索引。适用于长文档的专业分析，如财务报告、法律合同、技术手册。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "document_path": {
                            "type": "string",
                            "description": "文档路径 (PDF/MD/TXT)"
                        },
                        "document_description": {
                            "type": "string",
                            "description": "文档描述（可选），帮助LLM更好地理解文档内容"
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
                            "description": "检索模式：vector_only(仅向量), pageindex_only(仅推理), hybrid(混合), auto(自动)"
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
        调用MCP工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        try:
            if tool_name == "pageindex_index_document":
                return await self._index_document(arguments)
            
            elif tool_name == "pageindex_query":
                return await self._query(arguments)
            
            elif tool_name == "pageindex_list_documents":
                return await self._list_documents()
            
            elif tool_name == "pageindex_get_tree":
                return await self._get_tree(arguments)
            
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
    
    async def _index_document(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """索引文档"""
        document_path = args["document_path"]
        description = args.get("document_description", "")
        
        tree = await self.pageindex.index_document(
            document_path=document_path,
            document_description=description
        )
        
        all_nodes = tree.get_all_nodes()
        
        return {
            "success": True,
            "message": f"Document indexed successfully",
            "document": document_path,
            "total_nodes": len(all_nodes),
            "root_title": tree.title,
            "tree_structure": tree.to_dict()
        }
    
    async def _query(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """查询"""
        query = args["query"]
        document_path = args.get("document_path")
        mode = args.get("mode", "auto")
        top_k = args.get("top_k", 5)
        
        results = await self.integration.query(
            query=query,
            mode=mode,
            top_k=top_k,
            document_path=document_path
        )
        
        formatted_results = []
        for r in results:
            formatted_results.append({
                "content": r.content[:1000] if r.content else "",  # 截断
                "source": r.source,
                "relevance_score": r.relevance_score,
                "page_reference": r.page_reference,
                "node_id": r.node_id,
                "reasoning": r.reasoning
            })
        
        return {
            "success": True,
            "query": query,
            "results": formatted_results,
            "result_count": len(formatted_results)
        }
    
    async def _list_documents(self) -> Dict[str, Any]:
        """列出已索引文档"""
        docs = self.pageindex.get_indexed_documents()
        
        return {
            "success": True,
            "documents": docs,
            "count": len(docs)
        }
    
    async def _get_tree(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """获取树结构"""
        document_path = args["document_path"]
        
        # 尝试加载索引
        try:
            tree = await self.pageindex.load_index(document_path)
        except FileNotFoundError:
            return {
                "success": False,
                "error": f"Document not indexed: {document_path}"
            }
        
        return {
            "success": True,
            "document": document_path,
            "tree": tree.to_dict()
        }
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """
        获取MCP资源列表
        
        返回可用的文档资源
        """
        docs = self.pageindex.get_indexed_documents()
        
        resources = []
        for doc in docs:
            resources.append({
                "uri": f"pageindex://document/{doc}",
                "name": doc.split("/")[-1],
                "description": f"Indexed document: {doc}",
                "mimeType": "application/json"
            })
        
        return resources


# ==================== MCP Server 集成 ====================

class PageIndexMCPServer:
    """
    PageIndex MCP服务器
    
    标准的MCP服务器实现
    """
    
    def __init__(
        self,
        pageindex_tools: PageIndexMCPTools,
        server_name: str = "pageindex"
    ):
        self.tools = pageindex_tools
        self.server_name = server_name
    
    async def handle_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理MCP请求
        
        标准的MCP协议处理
        """
        if method == "tools/list":
            return {
                "tools": self.tools.get_tools()
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            result = await self.tools.call_tool(tool_name, arguments)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": str(result)
                    }
                ]
            }
        
        elif method == "resources/list":
            return {
                "resources": self.tools.get_resources()
            }
        
        elif method == "resources/read":
            uri = params.get("uri", "")
            
            # 解析URI
            if uri.startswith("pageindex://document/"):
                doc_path = uri.replace("pageindex://document/", "")
                result = await self.tools.call_tool("pageindex_get_tree", {"document_path": doc_path})
                return result
            
            return {
                "success": False,
                "error": f"Unknown resource: {uri}"
            }
        
        else:
            return {
                "success": False,
                "error": f"Unknown method: {method}"
            }


# ==================== 便捷函数 ====================

_pageindex_mcp_tools: Optional[PageIndexMCPTools] = None


def get_pageindex_mcp_tools(
    pageindex: Optional[PageIndex] = None,
    config: Optional[Dict[str, Any]] = None
) -> PageIndexMCPTools:
    """获取PageIndex MCP工具实例"""
    global _pageindex_mcp_tools
    if _pageindex_mcp_tools is None:
        _pageindex_mcp_tools = PageIndexMCPTools(pageindex, config)
    return _pageindex_mcp_tools
