#!/usr/bin/env python3
"""
Slack集成Hand
与Slack API集成，发送消息、管理频道、处理交互等
"""

import aiohttp
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base import BaseHand, HandCategory, HandSafetyLevel, HandCapability, HandExecutionResult


class SlackHand(BaseHand):
    """Slack集成Hand"""
    
    def __init__(self):
        super().__init__(
            name="slack",
            description="Slack API集成：发送消息、管理频道、处理交互",
            category=HandCategory.API_INTEGRATION,
            safety_level=HandSafetyLevel.MODERATE,
        )
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = "https://slack.com/api"
        self.default_token: Optional[str] = None
        
        # 缓存频道和用户信息
        self.channel_cache: Dict[str, Dict[str, Any]] = {}
        self.user_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_expiry = {}  # 缓存过期时间
    
    def validate_parameters(self, **kwargs) -> bool:
        """验证参数"""
        operation = kwargs.get("operation")
        required_operations = ["send_message", "list_channels", "get_user_info", "post_to_thread", "upload_file", "set_token"]
        if operation and operation not in required_operations:
            return False
        return True
    
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
                    "description": "操作类型：send_message, list_channels, get_user_info, post_to_thread, upload_file",
                    "allowed_values": ["send_message", "list_channels", "get_user_info", "post_to_thread", "upload_file", "set_token"]
                },
                {
                    "name": "token",
                    "type": "string",
                    "required": False,
                    "description": "Slack Bot Token (xoxb-开头) 或 User Token"
                },
                {
                    "name": "channel",
                    "type": "string",
                    "required": False,
                    "description": "频道ID或频道名称"
                },
                {
                    "name": "text",
                    "type": "string",
                    "required": False,
                    "description": "消息文本"
                },
                {
                    "name": "blocks",
                    "type": "array",
                    "required": False,
                    "description": "Slack Block Kit格式的消息块"
                },
                {
                    "name": "thread_ts",
                    "type": "string",
                    "required": False,
                    "description": "线程时间戳（用于回复线程）"
                },
                {
                    "name": "user",
                    "type": "string",
                    "required": False,
                    "description": "用户ID"
                },
                {
                    "name": "file_path",
                    "type": "string",
                    "required": False,
                    "description": "文件路径（用于上传文件）"
                },
                {
                    "name": "file_name",
                    "type": "string",
                    "required": False,
                    "description": "文件名（用于上传文件）"
                },
                {
                    "name": "file_type",
                    "type": "string",
                    "required": False,
                    "description": "文件类型（自动检测，可手动指定）"
                },
                {
                    "name": "limit",
                    "type": "integer",
                    "required": False,
                    "description": "返回结果限制数"
                },
                {
                    "name": "types",
                    "type": "string",
                    "required": False,
                    "description": "频道类型过滤（public_channel, private_channel, mpim, im）"
                }
            ],
            examples=[
                {
                    "description": "发送消息到Slack频道",
                    "parameters": {
                        "operation": "send_message",
                        "channel": "general",
                        "text": "Hello from RANGEN系统！",
                        "token": "xoxb-your-bot-token"
                    }
                },
                {
                    "description": "列出所有公共频道",
                    "parameters": {
                        "operation": "list_channels",
                        "types": "public_channel",
                        "token": "xoxb-your-bot-token"
                    }
                },
                {
                    "description": "设置默认token",
                    "parameters": {
                        "operation": "set_token",
                        "token": "xoxb-your-bot-token"
                    }
                }
            ]
        )
    
    async def execute(self, **kwargs) -> HandExecutionResult:
        """执行Slack操作"""
        start_time = datetime.now()
        
        try:
            operation = kwargs.get("operation")
            if not operation:
                return HandExecutionResult(
                    hand_name=self.name,
                    success=False,
                    output={},
                    error="缺少 operation 参数"
                )
            
            token = kwargs.get("token") or self.default_token
            
            if not token and operation != "set_token":
                return HandExecutionResult(
                    hand_name=self.name,
                    success=False,
                    output={},
                    error="Slack token未提供。请提供token参数或使用set_token操作设置默认token。"
                )
            
            if operation == "send_message":
                result = await self._send_message(token, **kwargs)
            elif operation == "list_channels":
                result = await self._list_channels(token, **kwargs)
            elif operation == "get_user_info":
                result = await self._get_user_info(token, **kwargs)
            elif operation == "post_to_thread":
                result = await self._post_to_thread(token, **kwargs)
            elif operation == "upload_file":
                result = await self._upload_file(token, **kwargs)
            elif operation == "set_token":
                result = await self._set_token(**kwargs)
            else:
                return HandExecutionResult(
                    hand_name=self.name,
                    success=False,
                    output={},
                    error=f"不支持的操作: {operation}"
                )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            await self._record_hook_event(
                operation=operation,
                success=True,
                execution_time=execution_time,
                result_summary=f"Slack操作成功: {operation}"
            )
            
            return HandExecutionResult(
                hand_name=self.name,
                success=True,
                output=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            self.logger.error(f"Slack操作失败: {error_msg}")
            
            await self._record_hook_event(
                operation=kwargs.get("operation"),
                success=False,
                execution_time=execution_time,
                error=error_msg
            )
            
            return HandExecutionResult(
                hand_name=self.name,
                success=False,
                output={},
                error=error_msg,
                execution_time=execution_time
            )
    
    async def _set_token(self, token: Optional[str], **kwargs) -> Dict[str, Any]:
        """设置默认Slack token"""
        if token and not token.startswith(("xoxb-", "xoxp-", "xoxa-")):
            self.logger.warning(f"Token格式可能不正确: {token[:10]}...")
        
        self.default_token = token
        
        # 验证token
        validation_result = await self._validate_token(token)
        
        if token:
            if token.startswith("xoxb-"):
                token_type = "bot"
            elif token.startswith("xoxp-"):
                token_type = "user"
            else:
                token_type = "app"
        else:
            token_type = "unknown"
        
        return {
            "token_set": True,
            "token_preview": f"{token[:10]}..." if token else "None",
            "token_type": token_type,
            "validation_result": validation_result
        }
    
    async def _validate_token(self, token: Optional[str]) -> Dict[str, Any]:
        """验证Slack token"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/auth.test",
                    headers={"Authorization": f"Bearer {token}"}
                ) as response:
                    data = await response.json()
                    
                    if data.get("ok"):
                        return {
                            "valid": True,
                            "team": data.get("team"),
                            "user": data.get("user"),
                            "team_id": data.get("team_id"),
                            "user_id": data.get("user_id"),
                            "url": data.get("url")
                        }
                    else:
                        return {
                            "valid": False,
                            "error": data.get("error", "未知错误")
                        }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    async def _send_message(self, token: Optional[str], channel: str, text: str, **kwargs) -> Dict[str, Any]:
        """发送消息到Slack频道"""
        # 如果channel是频道名，尝试转换为ID
        channel_id = await self._resolve_channel_id(token, channel)
        
        # 准备消息数据
        data = {
            "channel": channel_id,
            "text": text
        }
        
        # 添加可选参数
        if "blocks" in kwargs:
            if isinstance(kwargs["blocks"], list):
                data["blocks"] = json.dumps(kwargs["blocks"])
            else:
                data["blocks"] = kwargs["blocks"]
        
        if "thread_ts" in kwargs:
            data["thread_ts"] = kwargs["thread_ts"]
        
        if "attachments" in kwargs:
            if isinstance(kwargs["attachments"], list):
                data["attachments"] = json.dumps(kwargs["attachments"])
            else:
                data["attachments"] = kwargs["attachments"]
        
        # 发送请求
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=data
            ) as response:
                result = await response.json()
                
                if result.get("ok"):
                    return {
                        "message_sent": True,
                        "channel": channel_id,
                        "ts": result.get("ts"),  # 消息时间戳
                        "message": result.get("message", {}),
                        "permalink": f"https://slack.com/archives/{channel_id}/p{result.get('ts', '').replace('.', '')}"
                    }
                else:
                    error = result.get("error", "未知错误")
                    raise ValueError(f"发送消息失败: {error}")
    
    async def _list_channels(self, token: Optional[str], **kwargs) -> Dict[str, Any]:
        """列出Slack频道"""
        params = {
            "exclude_archived": kwargs.get("exclude_archived", True),
            "limit": kwargs.get("limit", 100)
        }
        
        # 频道类型过滤
        types = kwargs.get("types", "public_channel")
        if types:
            params["types"] = types
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/conversations.list",
                headers={"Authorization": f"Bearer {token}"},
                params=params
            ) as response:
                result = await response.json()
                
                if result.get("ok"):
                    channels = result.get("channels", [])
                    
                    # 更新缓存
                    for channel in channels:
                        channel_id = channel.get("id")
                        if channel_id:
                            self.channel_cache[channel_id] = channel
                            self.cache_expiry[f"channel_{channel_id}"] = datetime.now().timestamp() + 300  # 5分钟缓存
                    
                    # 简化频道信息
                    simplified_channels = []
                    for channel in channels:
                        simplified_channels.append({
                            "id": channel.get("id"),
                            "name": channel.get("name"),
                            "is_channel": channel.get("is_channel"),
                            "is_private": channel.get("is_private"),
                            "is_archived": channel.get("is_archived"),
                            "num_members": channel.get("num_members"),
                            "purpose": channel.get("purpose", {}).get("value", ""),
                            "topic": channel.get("topic", {}).get("value", "")
                        })
                    
                    return {
                        "channels": simplified_channels,
                        "total_count": len(channels),
                        "response_metadata": result.get("response_metadata", {})
                    }
                else:
                    error = result.get("error", "未知错误")
                    raise ValueError(f"获取频道列表失败: {error}")
    
    async def _get_user_info(self, token: Optional[str], user: str, **kwargs) -> Dict[str, Any]:
        """获取用户信息"""
        # 检查缓存
        cache_key = f"user_{user}"
        if cache_key in self.user_cache and self.cache_expiry.get(cache_key, 0) > datetime.now().timestamp():
            return self.user_cache[cache_key]
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/users.info",
                headers={"Authorization": f"Bearer {token}"},
                params={"user": user}
            ) as response:
                result = await response.json()
                
                if result.get("ok"):
                    user_info = result.get("user", {})
                    
                    # 简化用户信息
                    simplified_info = {
                        "id": user_info.get("id"),
                        "name": user_info.get("name"),
                        "real_name": user_info.get("real_name"),
                        "display_name": user_info.get("profile", {}).get("display_name"),
                        "email": user_info.get("profile", {}).get("email"),
                        "title": user_info.get("profile", {}).get("title"),
                        "phone": user_info.get("profile", {}).get("phone"),
                        "is_admin": user_info.get("is_admin"),
                        "is_owner": user_info.get("is_owner"),
                        "is_bot": user_info.get("is_bot"),
                        "tz": user_info.get("tz"),
                        "tz_label": user_info.get("tz_label"),
                        "tz_offset": user_info.get("tz_offset")
                    }
                    
                    # 更新缓存
                    self.user_cache[cache_key] = simplified_info
                    self.cache_expiry[cache_key] = datetime.now().timestamp() + 600  # 10分钟缓存
                    
                    return simplified_info
                else:
                    error = result.get("error", "未知错误")
                    raise ValueError(f"获取用户信息失败: {error}")
    
    async def _post_to_thread(self, token: Optional[str], channel: str, thread_ts: str, text: str, **kwargs) -> Dict[str, Any]:
        """回复到线程"""
        # 直接使用send_message，但指定thread_ts
        return await self._send_message(
            token=token,
            channel=channel,
            text=text,
            thread_ts=thread_ts,
            **kwargs
        )
    
    async def _upload_file(self, token: Optional[str], **kwargs) -> Dict[str, Any]:
        """上传文件到Slack"""
        file_path = kwargs.get("file_path")
        if not file_path:
            raise ValueError("上传文件需要file_path参数")
        
        # 读取文件
        try:
            with open(file_path, "rb") as f:
                file_content = f.read()
        except Exception as e:
            raise ValueError(f"读取文件失败: {e}")
        
        # 准备表单数据
        form_data = aiohttp.FormData()
        form_data.add_field("file", file_content, filename=kwargs.get("file_name") or file_path.split("/")[-1])
        
        if "channels" in kwargs:
            form_data.add_field("channels", kwargs["channels"])
        
        if "initial_comment" in kwargs:
            form_data.add_field("initial_comment", kwargs["initial_comment"])
        
        if "filetype" in kwargs:
            form_data.add_field("filetype", kwargs["filetype"])
        
        if "title" in kwargs:
            form_data.add_field("title", kwargs["title"])
        
        # 上传文件
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/files.upload",
                headers={"Authorization": f"Bearer {token}"},
                data=form_data
            ) as response:
                result = await response.json()
                
                if result.get("ok"):
                    file_info = result.get("file", {})
                    return {
                        "file_uploaded": True,
                        "file_id": file_info.get("id"),
                        "name": file_info.get("name"),
                        "title": file_info.get("title"),
                        "permalink": file_info.get("permalink"),
                        "url_private": file_info.get("url_private"),
                        "size": file_info.get("size"),
                        "mimetype": file_info.get("mimetype")
                    }
                else:
                    error = result.get("error", "未知错误")
                    raise ValueError(f"上传文件失败: {error}")
    
    async def _resolve_channel_id(self, token: Optional[str], channel: str) -> str:
        """解析频道ID（如果提供的是频道名）"""
        # 如果已经是ID格式（以C、G、D开头）
        if channel.startswith(("C", "G", "D")):
            return channel
        
        # 检查缓存
        for channel_id, channel_info in self.channel_cache.items():
            if channel_info.get("name") == channel:
                if self.cache_expiry.get(f"channel_{channel_id}", 0) > datetime.now().timestamp():
                    return channel_id
        
        # 获取频道列表以查找ID
        try:
            result = await self._list_channels(token, types="public_channel,private_channel,mpim,im")
            channels = result.get("channels", [])
            
            for channel_info in channels:
                if channel_info.get("name") == channel:
                    return channel_info.get("id")
        except Exception as e:
            self.logger.warning(f"解析频道ID失败，尝试直接使用: {e}")
        
        # 如果没找到，假设输入的就是ID
        return channel
    
    async def _record_hook_event(self, **kwargs):
        """记录Hook事件（简化实现）"""
        # 实际应用中应该调用Hook系统
        operation = kwargs.get("operation", "unknown")
        success = kwargs.get("success", False)
        
        if not success:
            self.logger.warning(f"Slack操作失败: {operation}")


# 创建默认实例
slack_hand = SlackHand()