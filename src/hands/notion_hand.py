#!/usr/bin/env python3
"""
Notion集成Hand
与Notion API集成，管理页面、数据库、块等
"""

import aiohttp
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from urllib.parse import urlencode

from .base import BaseHand, HandCategory, HandSafetyLevel, HandCapability


class NotionHand(BaseHand):
    """Notion集成Hand"""
    
    def __init__(self):
        super().__init__(
            name="notion",
            description="Notion API集成：管理页面、数据库、块等",
            category=HandCategory.API_INTEGRATION,
            safety_level=HandSafetyLevel.MODERATE,
            version="1.0.0"
        )
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = "https://api.notion.com/v1"
        self.default_token: Optional[str] = None
        
        # 缓存页面和数据库信息
        self.page_cache: Dict[str, Dict[str, Any]] = {}
        self.database_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_expiry = {}  # 缓存过期时间
    
    def get_capability(self) -> HandCapability:
        """获取能力定义"""
        return HandCapability(
            name=self.name,
            description=self.description,
            category=self.category,
            safety_level=self.safety_level,
            version=self.version,
            parameters=[
                {
                    "name": "operation",
                    "type": "string",
                    "required": True,
                    "description": "操作类型：list_databases, get_database, query_database, create_database, update_database, list_pages, get_page, create_page, update_page, search, get_block, get_block_children, append_block_children, set_token, get_user, list_users",
                    "allowed_values": ["list_databases", "get_database", "query_database", "create_database", "update_database", "list_pages", "get_page", "create_page", "update_page", "search", "get_block", "get_block_children", "append_block_children", "set_token", "get_user", "list_users"]
                },
                {
                    "name": "token",
                    "type": "string",
                    "required": False,
                    "description": "Notion Integration Token (secret_开头)"
                },
                {
                    "name": "database_id",
                    "type": "string",
                    "required": False,
                    "description": "数据库ID"
                },
                {
                    "name": "page_id",
                    "type": "string",
                    "required": False,
                    "description": "页面ID"
                },
                {
                    "name": "block_id",
                    "type": "string",
                    "required": False,
                    "description": "块ID"
                },
                {
                    "name": "parent",
                    "type": "object",
                    "required": False,
                    "description": "父对象信息（创建页面或数据库时使用）"
                },
                {
                    "name": "properties",
                    "type": "object",
                    "required": False,
                    "description": "页面或数据库属性"
                },
                {
                    "name": "title",
                    "type": "array",
                    "required": False,
                    "description": "标题文本数组"
                },
                {
                    "name": "filter",
                    "type": "object",
                    "required": False,
                    "description": "数据库查询过滤器"
                },
                {
                    "name": "sorts",
                    "type": "array",
                    "required": False,
                    "description": "数据库查询排序规则"
                },
                {
                    "name": "page_size",
                    "type": "integer",
                    "required": False,
                    "description": "每页数量（默认100，最大100）"
                },
                {
                    "name": "start_cursor",
                    "type": "string",
                    "required": False,
                    "description": "分页起始游标"
                },
                {
                    "name": "query",
                    "type": "string",
                    "required": False,
                    "description": "搜索查询字符串"
                },
                {
                    "name": "children",
                    "type": "array",
                    "required": False,
                    "description": "块子元素数组"
                },
                {
                    "name": "content",
                    "type": "string",
                    "required": False,
                    "description": "文本内容"
                },
                {
                    "name": "icon",
                    "type": "object",
                    "required": False,
                    "description": "图标信息"
                },
                {
                    "name": "cover",
                    "type": "object",
                    "required": False,
                    "description": "封面图片信息"
                },
                {
                    "name": "user_id",
                    "type": "string",
                    "required": False,
                    "description": "用户ID"
                },
                {
                    "name": "archived",
                    "type": "boolean",
                    "required": False,
                    "description": "是否归档"
                }
            ],
            examples=[
                {
                    "description": "查询数据库",
                    "parameters": {
                        "operation": "query_database",
                        "database_id": "your_database_id",
                        "token": "secret_your_token"
                    }
                },
                {
                    "description": "创建页面",
                    "parameters": {
                        "operation": "create_page",
                        "parent": {"database_id": "your_database_id"},
                        "properties": {"Name": {"title": [{"text": {"content": "新页面"}}]}},
                        "token": "secret_your_token"
                    }
                },
                {
                    "description": "搜索内容",
                    "parameters": {
                        "operation": "search",
                        "query": "重要笔记",
                        "token": "secret_your_token"
                    }
                },
                {
                    "description": "设置Notion token",
                    "parameters": {
                        "operation": "set_token",
                        "token": "secret_your_token"
                    }
                }
            ]
        )
    
    async def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """执行Notion操作"""
        start_time = datetime.now()
        
        try:
            # 获取token（优先使用参数中的token，其次使用默认token）
            token = kwargs.get("token") or self.default_token
            
            if not token and operation != "set_token":
                raise ValueError("Notion token未提供。请提供token参数或使用set_token操作设置默认token。")
            
            # 根据操作类型调用相应的方法
            if operation == "list_databases":
                result = await self._list_databases(token, **kwargs)
            elif operation == "get_database":
                result = await self._get_database(token, **kwargs)
            elif operation == "query_database":
                result = await self._query_database(token, **kwargs)
            elif operation == "create_database":
                result = await self._create_database(token, **kwargs)
            elif operation == "update_database":
                result = await self._update_database(token, **kwargs)
            elif operation == "list_pages":
                result = await self._list_pages(token, **kwargs)
            elif operation == "get_page":
                result = await self._get_page(token, **kwargs)
            elif operation == "create_page":
                result = await self._create_page(token, **kwargs)
            elif operation == "update_page":
                result = await self._update_page(token, **kwargs)
            elif operation == "search":
                result = await self._search(token, **kwargs)
            elif operation == "get_block":
                result = await self._get_block(token, **kwargs)
            elif operation == "get_block_children":
                result = await self._get_block_children(token, **kwargs)
            elif operation == "append_block_children":
                result = await self._append_block_children(token, **kwargs)
            elif operation == "set_token":
                result = await self._set_token(**kwargs)
            elif operation == "get_user":
                result = await self._get_user(token, **kwargs)
            elif operation == "list_users":
                result = await self._list_users(token, **kwargs)
            else:
                raise ValueError(f"不支持的操作: {operation}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 记录Hook事件
            await self._record_hook_event(
                operation=operation,
                success=True,
                execution_time=execution_time,
                result_summary=f"Notion操作成功: {operation}"
            )
            
            return {
                "success": True,
                "result": result,
                "execution_time": execution_time
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            self.logger.error(f"Notion操作失败: {error_msg}")
            
            # 记录错误事件
            await self._record_hook_event(
                operation=operation,
                success=False,
                execution_time=execution_time,
                error=error_msg
            )
            
            return {
                "success": False,
                "error": error_msg,
                "execution_time": execution_time
            }
    
    async def _set_token(self, token: str, **kwargs) -> Dict[str, Any]:
        """设置默认Notion token"""
        if not token.startswith("secret_"):
            self.logger.warning(f"Token格式可能不正确: {token[:10]}...")
        
        self.default_token = token
        
        # 验证token
        validation_result = await self._validate_token(token)
        
        return {
            "token_set": True,
            "token_preview": f"{token[:10]}...",
            "validation_result": validation_result
        }
    
    async def _validate_token(self, token: str) -> Dict[str, Any]:
        """验证Notion token"""
        try:
            headers = self._get_headers(token)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/users/me",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "valid": True,
                            "user": data.get("name"),
                            "user_id": data.get("id"),
                            "type": data.get("type"),
                            "workspace": data.get("workspace_name")
                        }
                    else:
                        error_data = await response.json()
                        return {
                            "valid": False,
                            "status_code": response.status,
                            "error": error_data.get("message", "未知错误")
                        }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    def _get_headers(self, token: str) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"  # 使用稳定的API版本
        }
        
        # 添加可选的Notion-Version参数
        if hasattr(self, 'notion_version'):
            headers["Notion-Version"] = self.notion_version
        
        return headers
    
    async def _list_databases(self, token: str, **kwargs) -> Dict[str, Any]:
        """列出数据库（通过搜索）"""
        # Notion没有直接的列出数据库API，我们通过搜索来获取数据库
        page_size = kwargs.get("page_size", 100)
        start_cursor = kwargs.get("start_cursor")
        
        data = {
            "filter": {
                "value": "database",
                "property": "object"
            },
            "page_size": min(page_size, 100)
        }
        
        if start_cursor:
            data["start_cursor"] = start_cursor
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/search",
                headers=self._get_headers(token),
                json=data
            ) as response:
                if response.status == 200:
                    search_result = await response.json()
                    databases = search_result.get("results", [])
                    
                    # 更新缓存
                    for db in databases:
                        db_id = db.get("id")
                        if db_id:
                            self.database_cache[db_id] = db
                            self.cache_expiry[f"db_{db_id}"] = datetime.now().timestamp() + 300
                    
                    # 简化数据库信息
                    simplified_dbs = []
                    for db in databases:
                        title_text = ""
                        title = db.get("title", [])
                        if title and len(title) > 0:
                            title_text = title[0].get("plain_text", "")
                        
                        simplified_dbs.append({
                            "id": db.get("id"),
                            "title": title_text,
                            "url": db.get("url"),
                            "created_time": db.get("created_time"),
                            "last_edited_time": db.get("last_edited_time"),
                            "archived": db.get("archived", False),
                            "icon": db.get("icon"),
                            "cover": db.get("cover")
                        })
                    
                    return {
                        "databases": simplified_dbs,
                        "has_more": search_result.get("has_more", False),
                        "next_cursor": search_result.get("next_cursor"),
                        "total_count": len(databases)
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"获取数据库列表失败: {error_data.get('message', '未知错误')}")
    
    async def _get_database(self, token: str, database_id: str, **kwargs) -> Dict[str, Any]:
        """获取数据库详细信息"""
        cache_key = f"db_{database_id}"
        if cache_key in self.database_cache and self.cache_expiry.get(cache_key, 0) > datetime.now().timestamp():
            return self.database_cache[cache_key]
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/databases/{database_id}",
                headers=self._get_headers(token)
            ) as response:
                if response.status == 200:
                    db_data = await response.json()
                    
                    # 更新缓存
                    self.database_cache[cache_key] = db_data
                    self.cache_expiry[cache_key] = datetime.now().timestamp() + 300
                    
                    return db_data
                else:
                    error_data = await response.json()
                    raise ValueError(f"获取数据库信息失败: {error_data.get('message', '未知错误')}")
    
    async def _query_database(self, token: str, database_id: str, **kwargs) -> Dict[str, Any]:
        """查询数据库"""
        page_size = kwargs.get("page_size", 100)
        start_cursor = kwargs.get("start_cursor")
        
        data = {
            "page_size": min(page_size, 100)
        }
        
        if "filter" in kwargs:
            data["filter"] = kwargs["filter"]
        
        if "sorts" in kwargs:
            data["sorts"] = kwargs["sorts"]
        
        if start_cursor:
            data["start_cursor"] = start_cursor
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/databases/{database_id}/query",
                headers=self._get_headers(token),
                json=data
            ) as response:
                if response.status == 200:
                    query_result = await response.json()
                    pages = query_result.get("results", [])
                    
                    # 更新缓存
                    for page in pages:
                        page_id = page.get("id")
                        if page_id:
                            self.page_cache[page_id] = page
                            self.cache_expiry[f"page_{page_id}"] = datetime.now().timestamp() + 300
                    
                    # 简化页面信息
                    simplified_pages = []
                    for page in pages:
                        # 提取页面标题
                        title_text = ""
                        properties = page.get("properties", {})
                        for prop_name, prop_value in properties.items():
                            if prop_value.get("type") == "title" and prop_value.get("title"):
                                if len(prop_value["title"]) > 0:
                                    title_text = prop_value["title"][0].get("plain_text", "")
                                break
                        
                        simplified_pages.append({
                            "id": page.get("id"),
                            "title": title_text,
                            "url": page.get("url"),
                            "created_time": page.get("created_time"),
                            "last_edited_time": page.get("last_edited_time"),
                            "archived": page.get("archived", False),
                            "icon": page.get("icon"),
                            "cover": page.get("cover"),
                            "properties": properties
                        })
                    
                    return {
                        "pages": simplified_pages,
                        "has_more": query_result.get("has_more", False),
                        "next_cursor": query_result.get("next_cursor"),
                        "total_count": len(pages)
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"查询数据库失败: {error_data.get('message', '未知错误')}")
    
    async def _create_database(self, token: str, **kwargs) -> Dict[str, Any]:
        """创建数据库"""
        parent = kwargs.get("parent")
        if not parent:
            raise ValueError("创建数据库需要parent参数")
        
        data = {
            "parent": parent,
            "properties": kwargs.get("properties", {}),
            "title": kwargs.get("title", [])
        }
        
        if "icon" in kwargs:
            data["icon"] = kwargs["icon"]
        
        if "cover" in kwargs:
            data["cover"] = kwargs["cover"]
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/databases",
                headers=self._get_headers(token),
                json=data
            ) as response:
                if response.status == 200:
                    db_data = await response.json()
                    
                    # 更新缓存
                    db_id = db_data.get("id")
                    self.database_cache[f"db_{db_id}"] = db_data
                    self.cache_expiry[f"db_{db_id}"] = datetime.now().timestamp() + 300
                    
                    return {
                        "database_created": True,
                        "database": db_data,
                        "id": db_id,
                        "url": db_data.get("url")
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"创建数据库失败: {error_data.get('message', '未知错误')}")
    
    async def _update_database(self, token: str, database_id: str, **kwargs) -> Dict[str, Any]:
        """更新数据库"""
        data = {}
        
        if "properties" in kwargs:
            data["properties"] = kwargs["properties"]
        
        if "title" in kwargs:
            data["title"] = kwargs["title"]
        
        if "icon" in kwargs:
            data["icon"] = kwargs["icon"]
        
        if "cover" in kwargs:
            data["cover"] = kwargs["cover"]
        
        if "archived" in kwargs:
            data["archived"] = kwargs["archived"]
        
        if not data:
            raise ValueError("更新数据库需要至少一个参数：properties, title, icon, cover 或 archived")
        
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                f"{self.base_url}/databases/{database_id}",
                headers=self._get_headers(token),
                json=data
            ) as response:
                if response.status == 200:
                    db_data = await response.json()
                    
                    # 更新缓存
                    self.database_cache[f"db_{database_id}"] = db_data
                    self.cache_expiry[f"db_{database_id}"] = datetime.now().timestamp() + 300
                    
                    return {
                        "database_updated": True,
                        "database": db_data
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"更新数据库失败: {error_data.get('message', '未知错误')}")
    
    async def _list_pages(self, token: str, **kwargs) -> Dict[str, Any]:
        """列出页面（通过搜索）"""
        page_size = kwargs.get("page_size", 100)
        start_cursor = kwargs.get("start_cursor")
        
        data = {
            "filter": {
                "value": "page",
                "property": "object"
            },
            "page_size": min(page_size, 100)
        }
        
        if start_cursor:
            data["start_cursor"] = start_cursor
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/search",
                headers=self._get_headers(token),
                json=data
            ) as response:
                if response.status == 200:
                    search_result = await response.json()
                    pages = search_result.get("results", [])
                    
                    # 更新缓存
                    for page in pages:
                        page_id = page.get("id")
                        if page_id:
                            self.page_cache[page_id] = page
                            self.cache_expiry[f"page_{page_id}"] = datetime.now().timestamp() + 300
                    
                    # 简化页面信息
                    simplified_pages = []
                    for page in pages:
                        # 提取页面标题
                        title_text = ""
                        properties = page.get("properties", {})
                        for prop_name, prop_value in properties.items():
                            if prop_value.get("type") == "title" and prop_value.get("title"):
                                if len(prop_value["title"]) > 0:
                                    title_text = prop_value["title"][0].get("plain_text", "")
                                break
                        
                        # 如果没有从properties中找到标题，尝试从页面标题获取
                        if not title_text and page.get("properties"):
                            for prop_name, prop_value in page["properties"].items():
                                if prop_value.get("type") == "title":
                                    title_array = prop_value.get("title", [])
                                    if title_array and len(title_array) > 0:
                                        title_text = title_array[0].get("plain_text", "")
                                    break
                        
                        simplified_pages.append({
                            "id": page.get("id"),
                            "title": title_text,
                            "url": page.get("url"),
                            "created_time": page.get("created_time"),
                            "last_edited_time": page.get("last_edited_time"),
                            "archived": page.get("archived", False),
                            "icon": page.get("icon"),
                            "cover": page.get("cover")
                        })
                    
                    return {
                        "pages": simplified_pages,
                        "has_more": search_result.get("has_more", False),
                        "next_cursor": search_result.get("next_cursor"),
                        "total_count": len(pages)
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"获取页面列表失败: {error_data.get('message', '未知错误')}")
    
    async def _get_page(self, token: str, page_id: str, **kwargs) -> Dict[str, Any]:
        """获取页面详细信息"""
        cache_key = f"page_{page_id}"
        if cache_key in self.page_cache and self.cache_expiry.get(cache_key, 0) > datetime.now().timestamp():
            return self.page_cache[cache_key]
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/pages/{page_id}",
                headers=self._get_headers(token)
            ) as response:
                if response.status == 200:
                    page_data = await response.json()
                    
                    # 更新缓存
                    self.page_cache[cache_key] = page_data
                    self.cache_expiry[cache_key] = datetime.now().timestamp() + 300
                    
                    return page_data
                else:
                    error_data = await response.json()
                    raise ValueError(f"获取页面信息失败: {error_data.get('message', '未知错误')}")
    
    async def _create_page(self, token: str, **kwargs) -> Dict[str, Any]:
        """创建页面"""
        parent = kwargs.get("parent")
        if not parent:
            raise ValueError("创建页面需要parent参数")
        
        data = {
            "parent": parent,
            "properties": kwargs.get("properties", {})
        }
        
        if "children" in kwargs:
            data["children"] = kwargs["children"]
        
        if "icon" in kwargs:
            data["icon"] = kwargs["icon"]
        
        if "cover" in kwargs:
            data["cover"] = kwargs["cover"]
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/pages",
                headers=self._get_headers(token),
                json=data
            ) as response:
                if response.status == 200:
                    page_data = await response.json()
                    
                    # 更新缓存
                    page_id = page_data.get("id")
                    self.page_cache[f"page_{page_id}"] = page_data
                    self.cache_expiry[f"page_{page_id}"] = datetime.now().timestamp() + 300
                    
                    return {
                        "page_created": True,
                        "page": page_data,
                        "id": page_id,
                        "url": page_data.get("url")
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"创建页面失败: {error_data.get('message', '未知错误')}")
    
    async def _update_page(self, token: str, page_id: str, **kwargs) -> Dict[str, Any]:
        """更新页面"""
        data = {}
        
        if "properties" in kwargs:
            data["properties"] = kwargs["properties"]
        
        if "icon" in kwargs:
            data["icon"] = kwargs["icon"]
        
        if "cover" in kwargs:
            data["cover"] = kwargs["cover"]
        
        if "archived" in kwargs:
            data["archived"] = kwargs["archived"]
        
        if not data:
            raise ValueError("更新页面需要至少一个参数：properties, icon, cover 或 archived")
        
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                f"{self.base_url}/pages/{page_id}",
                headers=self._get_headers(token),
                json=data
            ) as response:
                if response.status == 200:
                    page_data = await response.json()
                    
                    # 更新缓存
                    self.page_cache[f"page_{page_id}"] = page_data
                    self.cache_expiry[f"page_{page_id}"] = datetime.now().timestamp() + 300
                    
                    return {
                        "page_updated": True,
                        "page": page_data
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"更新页面失败: {error_data.get('message', '未知错误')}")
    
    async def _search(self, token: str, **kwargs) -> Dict[str, Any]:
        """搜索内容"""
        page_size = kwargs.get("page_size", 100)
        start_cursor = kwargs.get("start_cursor")
        
        data = {
            "page_size": min(page_size, 100)
        }
        
        if "query" in kwargs:
            data["query"] = kwargs["query"]
        
        if "filter" in kwargs:
            data["filter"] = kwargs["filter"]
        else:
            # 默认搜索所有类型
            data["filter"] = {
                "value": "page",
                "property": "object"
            }
        
        if start_cursor:
            data["start_cursor"] = start_cursor
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/search",
                headers=self._get_headers(token),
                json=data
            ) as response:
                if response.status == 200:
                    search_result = await response.json()
                    results = search_result.get("results", [])
                    
                    # 简化搜索结果
                    simplified_results = []
                    for result in results:
                        # 提取标题
                        title_text = ""
                        obj_type = result.get("object")
                        
                        if obj_type == "page":
                            properties = result.get("properties", {})
                            for prop_name, prop_value in properties.items():
                                if prop_value.get("type") == "title" and prop_value.get("title"):
                                    if len(prop_value["title"]) > 0:
                                        title_text = prop_value["title"][0].get("plain_text", "")
                                    break
                        elif obj_type == "database":
                            title = result.get("title", [])
                            if title and len(title) > 0:
                                title_text = title[0].get("plain_text", "")
                        
                        simplified_results.append({
                            "id": result.get("id"),
                            "object": obj_type,
                            "title": title_text,
                            "url": result.get("url"),
                            "created_time": result.get("created_time"),
                            "last_edited_time": result.get("last_edited_time"),
                            "archived": result.get("archived", False),
                            "icon": result.get("icon"),
                            "cover": result.get("cover")
                        })
                    
                    return {
                        "results": simplified_results,
                        "has_more": search_result.get("has_more", False),
                        "next_cursor": search_result.get("next_cursor"),
                        "total_count": len(results),
                        "query": kwargs.get("query", "")
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"搜索失败: {error_data.get('message', '未知错误')}")
    
    async def _get_block(self, token: str, block_id: str, **kwargs) -> Dict[str, Any]:
        """获取块信息"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/blocks/{block_id}",
                headers=self._get_headers(token)
            ) as response:
                if response.status == 200:
                    block_data = await response.json()
                    
                    return block_data
                else:
                    error_data = await response.json()
                    raise ValueError(f"获取块信息失败: {error_data.get('message', '未知错误')}")
    
    async def _get_block_children(self, token: str, block_id: str, **kwargs) -> Dict[str, Any]:
        """获取块的子块"""
        page_size = kwargs.get("page_size", 100)
        start_cursor = kwargs.get("start_cursor")
        
        params = {
            "page_size": str(min(page_size, 100))
        }
        
        if start_cursor:
            params["start_cursor"] = start_cursor
        
        url = f"{self.base_url}/blocks/{block_id}/children"
        if params:
            url += "?" + urlencode(params)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._get_headers(token)
            ) as response:
                if response.status == 200:
                    children_result = await response.json()
                    blocks = children_result.get("results", [])
                    
                    return {
                        "blocks": blocks,
                        "has_more": children_result.get("has_more", False),
                        "next_cursor": children_result.get("next_cursor"),
                        "total_count": len(blocks)
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"获取块子元素失败: {error_data.get('message', '未知错误')}")
    
    async def _append_block_children(self, token: str, block_id: str, children: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """追加块的子块"""
        if not children:
            raise ValueError("追加子块需要children参数")
        
        data = {
            "children": children
        }
        
        if "after" in kwargs:
            data["after"] = kwargs["after"]
        
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                f"{self.base_url}/blocks/{block_id}/children",
                headers=self._get_headers(token),
                json=data
            ) as response:
                if response.status == 200:
                    result_data = await response.json()
                    
                    return {
                        "children_appended": True,
                        "result": result_data
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"追加块子元素失败: {error_data.get('message', '未知错误')}")
    
    async def _get_user(self, token: str, **kwargs) -> Dict[str, Any]:
        """获取用户信息"""
        user_id = kwargs.get("user_id")
        
        if user_id:
            url = f"{self.base_url}/users/{user_id}"
        else:
            url = f"{self.base_url}/users/me"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._get_headers(token)
            ) as response:
                if response.status == 200:
                    user_data = await response.json()
                    
                    # 简化用户信息
                    simplified_info = {
                        "id": user_data.get("id"),
                        "name": user_data.get("name"),
                        "type": user_data.get("type"),
                        "avatar_url": user_data.get("avatar_url"),
                        "person": user_data.get("person"),
                        "bot": user_data.get("bot")
                    }
                    
                    return simplified_info
                else:
                    error_data = await response.json()
                    raise ValueError(f"获取用户信息失败: {error_data.get('message', '未知错误')}")
    
    async def _list_users(self, token: str, **kwargs) -> Dict[str, Any]:
        """列出用户"""
        page_size = kwargs.get("page_size", 100)
        start_cursor = kwargs.get("start_cursor")
        
        params = {
            "page_size": str(min(page_size, 100))
        }
        
        if start_cursor:
            params["start_cursor"] = start_cursor
        
        url = f"{self.base_url}/users"
        if params:
            url += "?" + urlencode(params)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._get_headers(token)
            ) as response:
                if response.status == 200:
                    users_result = await response.json()
                    users = users_result.get("results", [])
                    
                    # 简化用户信息
                    simplified_users = []
                    for user in users:
                        simplified_users.append({
                            "id": user.get("id"),
                            "name": user.get("name"),
                            "type": user.get("type"),
                            "avatar_url": user.get("avatar_url"),
                            "person": user.get("person"),
                            "bot": user.get("bot")
                        })
                    
                    return {
                        "users": simplified_users,
                        "has_more": users_result.get("has_more", False),
                        "next_cursor": users_result.get("next_cursor"),
                        "total_count": len(users)
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"获取用户列表失败: {error_data.get('message', '未知错误')}")
    
    async def _record_hook_event(self, **kwargs):
        """记录Hook事件（简化实现）"""
        # 实际应用中应该调用Hook系统
        operation = kwargs.get("operation", "unknown")
        success = kwargs.get("success", False)
        
        if not success:
            self.logger.warning(f"Notion操作失败: {operation}")


# 创建默认实例
notion_hand = NotionHand()