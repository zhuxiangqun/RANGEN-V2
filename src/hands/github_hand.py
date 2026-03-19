#!/usr/bin/env python3
"""
GitHub集成Hand
与GitHub API集成，管理仓库、Issues、Pull Requests等
"""

import aiohttp
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
import base64

from .base import BaseHand, HandCategory, HandSafetyLevel, HandCapability, HandExecutionResult


class GitHubHand(BaseHand):
    """GitHub集成Hand"""
    
    def __init__(self):
        super().__init__(
            name="github",
            description="GitHub API集成：管理仓库、Issues、Pull Requests、Webhooks等",
            category=HandCategory.API_INTEGRATION,
            safety_level=HandSafetyLevel.MODERATE,
        )
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = "https://api.github.com"
        self.default_token: Optional[str] = None
        
        # 缓存仓库和用户信息
        self.repo_cache: Dict[str, Dict[str, Any]] = {}
        self.user_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_expiry = {}  # 缓存过期时间
    
    def validate_parameters(self, **kwargs) -> bool:
        """验证参数"""
        operation = kwargs.get("operation")
        required_operations = ["list_repos", "get_repo", "create_repo", "create_issue", "list_issues", 
                              "get_issue", "create_pr", "list_prs", "get_pr", "create_webhook", 
                              "list_webhooks", "set_token", "search_repos", "get_user", "update_file", 
                              "get_file", "list_branches", "list_commits"]
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
                    "description": "操作类型：list_repos, get_repo, create_repo, create_issue, list_issues, get_issue, create_pr, list_prs, get_pr, create_webhook, list_webhooks, set_token, search_repos, get_user",
                    "allowed_values": ["list_repos", "get_repo", "create_repo", "create_issue", "list_issues", "get_issue", "create_pr", "list_prs", "get_pr", "create_webhook", "list_webhooks", "set_token", "search_repos", "get_user", "update_file", "get_file", "list_branches", "list_commits"]
                },
                {
                    "name": "token",
                    "type": "string",
                    "required": False,
                    "description": "GitHub Personal Access Token (ghp_开头)"
                },
                {
                    "name": "owner",
                    "type": "string",
                    "required": False,
                    "description": "仓库所有者（用户名或组织名）"
                },
                {
                    "name": "repo",
                    "type": "string",
                    "required": False,
                    "description": "仓库名称"
                },
                {
                    "name": "visibility",
                    "type": "string",
                    "required": False,
                    "description": "仓库可见性：public, private, internal",
                    "allowed_values": ["public", "private", "internal"]
                },
                {
                    "name": "title",
                    "type": "string",
                    "required": False,
                    "description": "Issue或PR标题"
                },
                {
                    "name": "body",
                    "type": "string",
                    "required": False,
                    "description": "Issue或PR正文"
                },
                {
                    "name": "labels",
                    "type": "array",
                    "required": False,
                    "description": "Issue标签列表"
                },
                {
                    "name": "assignees",
                    "type": "array",
                    "required": False,
                    "description": "负责人列表"
                },
                {
                    "name": "state",
                    "type": "string",
                    "required": False,
                    "description": "Issue或PR状态：open, closed, all",
                    "allowed_values": ["open", "closed", "all"]
                },
                {
                    "name": "head",
                    "type": "string",
                    "required": False,
                    "description": "PR源分支"
                },
                {
                    "name": "base",
                    "type": "string",
                    "required": False,
                    "description": "PR目标分支"
                },
                {
                    "name": "webhook_url",
                    "type": "string",
                    "required": False,
                    "description": "Webhook回调URL"
                },
                {
                    "name": "events",
                    "type": "array",
                    "required": False,
                    "description": "Webhook事件类型列表"
                },
                {
                    "name": "search_query",
                    "type": "string",
                    "required": False,
                    "description": "搜索查询字符串"
                },
                {
                    "name": "page",
                    "type": "integer",
                    "required": False,
                    "description": "页码（默认1）"
                },
                {
                    "name": "per_page",
                    "type": "integer",
                    "required": False,
                    "description": "每页数量（默认30，最大100）"
                },
                {
                    "name": "path",
                    "type": "string",
                    "required": False,
                    "description": "文件路径"
                },
                {
                    "name": "content",
                    "type": "string",
                    "required": False,
                    "description": "文件内容（Base64编码）"
                },
                {
                    "name": "message",
                    "type": "string",
                    "required": False,
                    "description": "提交消息"
                },
                {
                    "name": "branch",
                    "type": "string",
                    "required": False,
                    "description": "分支名称"
                },
                {
                    "name": "sha",
                    "type": "string",
                    "required": False,
                    "description": "文件SHA值（用于更新）"
                },
                {
                    "name": "issue_number",
                    "type": "integer",
                    "required": False,
                    "description": "Issue编号"
                },
                {
                    "name": "pr_number",
                    "type": "integer",
                    "required": False,
                    "description": "Pull Request编号"
                },
                {
                    "name": "webhook_id",
                    "type": "integer",
                    "required": False,
                    "description": "Webhook ID"
                },
                {
                    "name": "username",
                    "type": "string",
                    "required": False,
                    "description": "GitHub用户名"
                },
                {
                    "name": "since",
                    "type": "string",
                    "required": False,
                    "description": "起始时间（ISO格式，如2023-01-01T00:00:00Z）"
                },
                {
                    "name": "until",
                    "type": "string",
                    "required": False,
                    "description": "结束时间（ISO格式）"
                }
            ],
            examples=[
                {
                    "description": "列出用户的所有仓库",
                    "parameters": {
                        "operation": "list_repos",
                        "token": "ghp_your_token"
                    }
                },
                {
                    "description": "创建新的Issue",
                    "parameters": {
                        "operation": "create_issue",
                        "owner": "your_username",
                        "repo": "your_repo",
                        "title": "Bug修复",
                        "body": "发现了一个bug，需要修复...",
                        "labels": ["bug", "high-priority"],
                        "token": "ghp_your_token"
                    }
                },
                {
                    "description": "创建Pull Request",
                    "parameters": {
                        "operation": "create_pr",
                        "owner": "your_username",
                        "repo": "your_repo",
                        "title": "新功能添加",
                        "body": "添加了一个新功能...",
                        "head": "feature-branch",
                        "base": "main",
                        "token": "ghp_your_token"
                    }
                },
                {
                    "description": "设置GitHub token",
                    "parameters": {
                        "operation": "set_token",
                        "token": "ghp_your_token"
                    }
                }
            ]
        )
    
    async def execute(self, **kwargs) -> HandExecutionResult:
        """执行GitHub操作"""
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
                    error="GitHub token未提供。请提供token参数或使用set_token操作设置默认token。"
                )
            
            if operation == "list_repos":
                result = await self._list_repositories(token, **kwargs)
            elif operation == "get_repo":
                result = await self._get_repository(token, **kwargs)
            elif operation == "create_repo":
                result = await self._create_repository(token, **kwargs)
            elif operation == "create_issue":
                result = await self._create_issue(token, **kwargs)
            elif operation == "list_issues":
                result = await self._list_issues(token, **kwargs)
            elif operation == "get_issue":
                result = await self._get_issue(token, **kwargs)
            elif operation == "create_pr":
                result = await self._create_pull_request(token, **kwargs)
            elif operation == "list_prs":
                result = await self._list_pull_requests(token, **kwargs)
            elif operation == "get_pr":
                result = await self._get_pull_request(token, **kwargs)
            elif operation == "create_webhook":
                result = await self._create_webhook(token, **kwargs)
            elif operation == "list_webhooks":
                result = await self._list_webhooks(token, **kwargs)
            elif operation == "set_token":
                result = await self._set_token(**kwargs)
            elif operation == "search_repos":
                result = await self._search_repositories(token, **kwargs)
            elif operation == "get_user":
                result = await self._get_user(token, **kwargs)
            elif operation == "update_file":
                result = await self._update_file(token, **kwargs)
            elif operation == "get_file":
                result = await self._get_file(token, **kwargs)
            elif operation == "list_branches":
                result = await self._list_branches(token, **kwargs)
            elif operation == "list_commits":
                result = await self._list_commits(token, **kwargs)
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
                result_summary=f"GitHub操作成功: {operation}"
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
            self.logger.error(f"GitHub操作失败: {error_msg}")
            
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
        """设置默认GitHub token"""
        if token and not token.startswith(("ghp_", "github_pat_")):
            self.logger.warning(f"Token格式可能不正确: {token[:10]}...")
        
        self.default_token = token
        
        # 验证token
        validation_result = await self._validate_token(token)
        
        token_type = "classic" if token and token.startswith("ghp_") else "fine-grained" if token else "unknown"
        
        return {
            "token_set": True,
            "token_preview": f"{token[:10]}..." if token else "None",
            "token_type": token_type,
            "validation_result": validation_result
        }
    
    async def _validate_token(self, token: Optional[str]) -> Dict[str, Any]:
        """验证GitHub token"""
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/user",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "valid": True,
                            "user": data.get("login"),
                            "name": data.get("name"),
                            "email": data.get("email"),
                            "rate_limit": {
                                "limit": response.headers.get("X-RateLimit-Limit"),
                                "remaining": response.headers.get("X-RateLimit-Remaining"),
                                "reset": response.headers.get("X-RateLimit-Reset")
                            }
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
    
    def _get_headers(self, token: Optional[str]) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    async def _list_repositories(self, token: Optional[str], **kwargs) -> Dict[str, Any]:
        """列出仓库"""
        username = kwargs.get("username")  # 如果未指定，则列出当前用户的仓库
        visibility = kwargs.get("visibility", "all")  # all, public, private
        page = kwargs.get("page", 1)
        per_page = kwargs.get("per_page", 30)
        
        if username:
            # 列出指定用户的仓库
            url = f"{self.base_url}/users/{username}/repos"
        else:
            # 列出当前用户的仓库
            url = f"{self.base_url}/user/repos"
        
        params = {
            "visibility": visibility,
            "page": page,
            "per_page": min(per_page, 100),
            "sort": "updated",
            "direction": "desc"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._get_headers(token),
                params=params
            ) as response:
                if response.status == 200:
                    repos = await response.json()
                    
                    # 更新缓存
                    for repo in repos:
                        repo_id = str(repo.get("id"))
                        self.repo_cache[repo_id] = repo
                        self.cache_expiry[f"repo_{repo_id}"] = datetime.now().timestamp() + 300
                    
                    # 简化仓库信息
                    simplified_repos = []
                    for repo in repos:
                        simplified_repos.append({
                            "id": repo.get("id"),
                            "name": repo.get("name"),
                            "full_name": repo.get("full_name"),
                            "owner": repo.get("owner", {}).get("login"),
                            "description": repo.get("description"),
                            "html_url": repo.get("html_url"),
                            "private": repo.get("private"),
                            "fork": repo.get("fork"),
                            "language": repo.get("language"),
                            "stargazers_count": repo.get("stargazers_count"),
                            "forks_count": repo.get("forks_count"),
                            "open_issues_count": repo.get("open_issues_count"),
                            "pushed_at": repo.get("pushed_at"),
                            "created_at": repo.get("created_at"),
                            "updated_at": repo.get("updated_at"),
                            "default_branch": repo.get("default_branch")
                        })
                    
                    return {
                        "repositories": simplified_repos,
                        "total_count": len(repos),
                        "page": page,
                        "per_page": per_page
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"获取仓库列表失败: {error_data.get('message', '未知错误')}")
    
    async def _get_repository(self, token: Optional[str], owner: str, repo: str, **kwargs) -> Dict[str, Any]:
        """获取仓库详细信息"""
        cache_key = f"repo_{owner}/{repo}"
        if cache_key in self.repo_cache and self.cache_expiry.get(cache_key, 0) > datetime.now().timestamp():
            return self.repo_cache[cache_key]
        
        url = f"{self.base_url}/repos/{owner}/{repo}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._get_headers(token)
            ) as response:
                if response.status == 200:
                    repo_data = await response.json()
                    
                    # 更新缓存
                    self.repo_cache[cache_key] = repo_data
                    self.cache_expiry[cache_key] = datetime.now().timestamp() + 300
                    
                    return repo_data
                else:
                    error_data = await response.json()
                    raise ValueError(f"获取仓库信息失败: {error_data.get('message', '未知错误')}")
    
    async def _create_repository(self, token: Optional[str], **kwargs) -> Dict[str, Any]:
        """创建仓库"""
        name = kwargs.get("name")
        if not name:
            raise ValueError("创建仓库需要name参数")
        
        data = {
            "name": name,
            "description": kwargs.get("description", ""),
            "private": kwargs.get("visibility", "public") == "private",
            "auto_init": kwargs.get("auto_init", True),
            "gitignore_template": kwargs.get("gitignore_template"),
            "license_template": kwargs.get("license_template")
        }
        
        # 如果是组织仓库
        org = kwargs.get("org")
        if org:
            url = f"{self.base_url}/orgs/{org}/repos"
        else:
            url = f"{self.base_url}/user/repos"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self._get_headers(token),
                json=data
            ) as response:
                if response.status == 201:
                    repo_data = await response.json()
                    
                    # 更新缓存
                    repo_id = str(repo_data.get("id"))
                    self.repo_cache[repo_id] = repo_data
                    self.cache_expiry[f"repo_{repo_id}"] = datetime.now().timestamp() + 300
                    
                    return {
                        "repository_created": True,
                        "repository": repo_data,
                        "html_url": repo_data.get("html_url"),
                        "ssh_url": repo_data.get("ssh_url"),
                        "clone_url": repo_data.get("clone_url")
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"创建仓库失败: {error_data.get('message', '未知错误')}")
    
    async def _create_issue(self, token: Optional[str], owner: str, repo: str, title: str, **kwargs) -> Dict[str, Any]:
        """创建Issue"""
        if not title:
            raise ValueError("创建Issue需要title参数")
        
        data = {
            "title": title,
            "body": kwargs.get("body", ""),
            "labels": kwargs.get("labels", []),
            "assignees": kwargs.get("assignees", [])
        }
        
        url = f"{self.base_url}/repos/{owner}/{repo}/issues"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self._get_headers(token),
                json=data
            ) as response:
                if response.status == 201:
                    issue_data = await response.json()
                    
                    return {
                        "issue_created": True,
                        "issue_number": issue_data.get("number"),
                        "title": issue_data.get("title"),
                        "state": issue_data.get("state"),
                        "html_url": issue_data.get("html_url"),
                        "created_at": issue_data.get("created_at"),
                        "user": issue_data.get("user", {}).get("login")
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"创建Issue失败: {error_data.get('message', '未知错误')}")
    
    async def _list_issues(self, token: Optional[str], owner: str, repo: str, **kwargs) -> Dict[str, Any]:
        """列出仓库的Issues"""
        state = kwargs.get("state", "open")
        page = kwargs.get("page", 1)
        per_page = kwargs.get("per_page", 30)
        
        url = f"{self.base_url}/repos/{owner}/{repo}/issues"
        
        params = {
            "state": state,
            "page": page,
            "per_page": min(per_page, 100),
            "sort": "updated",
            "direction": "desc"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._get_headers(token),
                params=params
            ) as response:
                if response.status == 200:
                    issues = await response.json()
                    
                    # 简化Issue信息
                    simplified_issues = []
                    for issue in issues:
                        simplified_issues.append({
                            "number": issue.get("number"),
                            "title": issue.get("title"),
                            "state": issue.get("state"),
                            "user": issue.get("user", {}).get("login"),
                            "labels": [label.get("name") for label in issue.get("labels", [])],
                            "assignees": [assignee.get("login") for assignee in issue.get("assignees", [])],
                            "created_at": issue.get("created_at"),
                            "updated_at": issue.get("updated_at"),
                            "html_url": issue.get("html_url")
                        })
                    
                    return {
                        "issues": simplified_issues,
                        "total_count": len(issues),
                        "page": page,
                        "per_page": per_page,
                        "state": state
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"获取Issues列表失败: {error_data.get('message', '未知错误')}")
    
    async def _get_issue(self, token: Optional[str], owner: str, repo: str, issue_number: int, **kwargs) -> Dict[str, Any]:
        """获取Issue详细信息"""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._get_headers(token)
            ) as response:
                if response.status == 200:
                    issue_data = await response.json()
                    
                    return {
                        "issue": issue_data,
                        "number": issue_data.get("number"),
                        "title": issue_data.get("title"),
                        "state": issue_data.get("state"),
                        "body": issue_data.get("body"),
                        "user": issue_data.get("user", {}).get("login"),
                        "labels": [label.get("name") for label in issue_data.get("labels", [])],
                        "assignees": [assignee.get("login") for assignee in issue_data.get("assignees", [])],
                        "created_at": issue_data.get("created_at"),
                        "updated_at": issue_data.get("updated_at"),
                        "html_url": issue_data.get("html_url"),
                        "comments": issue_data.get("comments")
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"获取Issue信息失败: {error_data.get('message', '未知错误')}")
    
    async def _create_pull_request(self, token: Optional[str], owner: str, repo: str, title: str, head: str, base: str, **kwargs) -> Dict[str, Any]:
        """创建Pull Request"""
        if not title or not head or not base:
            raise ValueError("创建Pull Request需要title, head, base参数")
        
        data = {
            "title": title,
            "body": kwargs.get("body", ""),
            "head": head,
            "base": base,
            "draft": kwargs.get("draft", False),
            "maintainer_can_modify": kwargs.get("maintainer_can_modify", True)
        }
        
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self._get_headers(token),
                json=data
            ) as response:
                if response.status == 201:
                    pr_data = await response.json()
                    
                    return {
                        "pr_created": True,
                        "pr_number": pr_data.get("number"),
                        "title": pr_data.get("title"),
                        "state": pr_data.get("state"),
                        "head": pr_data.get("head", {}).get("ref"),
                        "base": pr_data.get("base", {}).get("ref"),
                        "html_url": pr_data.get("html_url"),
                        "created_at": pr_data.get("created_at"),
                        "user": pr_data.get("user", {}).get("login")
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"创建Pull Request失败: {error_data.get('message', '未知错误')}")
    
    async def _list_pull_requests(self, token: Optional[str], owner: str, repo: str, **kwargs) -> Dict[str, Any]:
        """列出仓库的Pull Requests"""
        state = kwargs.get("state", "open")
        page = kwargs.get("page", 1)
        per_page = kwargs.get("per_page", 30)
        
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        
        params = {
            "state": state,
            "page": page,
            "per_page": min(per_page, 100),
            "sort": "updated",
            "direction": "desc"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._get_headers(token),
                params=params
            ) as response:
                if response.status == 200:
                    prs = await response.json()
                    
                    # 简化PR信息
                    simplified_prs = []
                    for pr in prs:
                        simplified_prs.append({
                            "number": pr.get("number"),
                            "title": pr.get("title"),
                            "state": pr.get("state"),
                            "user": pr.get("user", {}).get("login"),
                            "head": pr.get("head", {}).get("ref"),
                            "base": pr.get("base", {}).get("ref"),
                            "created_at": pr.get("created_at"),
                            "updated_at": pr.get("updated_at"),
                            "html_url": pr.get("html_url"),
                            "draft": pr.get("draft"),
                            "mergeable": pr.get("mergeable"),
                            "merged": pr.get("merged")
                        })
                    
                    return {
                        "pull_requests": simplified_prs,
                        "total_count": len(prs),
                        "page": page,
                        "per_page": per_page,
                        "state": state
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"获取Pull Requests列表失败: {error_data.get('message', '未知错误')}")
    
    async def _get_pull_request(self, token: Optional[str], owner: str, repo: str, pr_number: int, **kwargs) -> Dict[str, Any]:
        """获取Pull Request详细信息"""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._get_headers(token)
            ) as response:
                if response.status == 200:
                    pr_data = await response.json()
                    
                    return {
                        "pull_request": pr_data,
                        "number": pr_data.get("number"),
                        "title": pr_data.get("title"),
                        "state": pr_data.get("state"),
                        "body": pr_data.get("body"),
                        "user": pr_data.get("user", {}).get("login"),
                        "head": pr_data.get("head", {}),
                        "base": pr_data.get("base", {}),
                        "created_at": pr_data.get("created_at"),
                        "updated_at": pr_data.get("updated_at"),
                        "html_url": pr_data.get("html_url"),
                        "mergeable": pr_data.get("mergeable"),
                        "merged": pr_data.get("merged"),
                        "comments": pr_data.get("comments"),
                        "commits": pr_data.get("commits")
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"获取Pull Request信息失败: {error_data.get('message', '未知错误')}")
    
    async def _create_webhook(self, token: Optional[str], owner: str, repo: str, webhook_url: str, **kwargs) -> Dict[str, Any]:
        """创建Webhook"""
        if not webhook_url:
            raise ValueError("创建Webhook需要webhook_url参数")
        
        data = {
            "name": "web",
            "active": True,
            "events": kwargs.get("events", ["push", "pull_request"]),
            "config": {
                "url": webhook_url,
                "content_type": "json",
                "secret": kwargs.get("secret", ""),
                "insecure_ssl": kwargs.get("insecure_ssl", "0")
            }
        }
        
        url = f"{self.base_url}/repos/{owner}/{repo}/hooks"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self._get_headers(token),
                json=data
            ) as response:
                if response.status == 201:
                    webhook_data = await response.json()
                    
                    return {
                        "webhook_created": True,
                        "webhook_id": webhook_data.get("id"),
                        "url": webhook_data.get("config", {}).get("url"),
                        "events": webhook_data.get("events"),
                        "active": webhook_data.get("active"),
                        "created_at": webhook_data.get("created_at")
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"创建Webhook失败: {error_data.get('message', '未知错误')}")
    
    async def _list_webhooks(self, token: Optional[str], owner: str, repo: str, **kwargs) -> Dict[str, Any]:
        """列出仓库的Webhooks"""
        page = kwargs.get("page", 1)
        per_page = kwargs.get("per_page", 30)
        
        url = f"{self.base_url}/repos/{owner}/{repo}/hooks"
        
        params = {
            "page": page,
            "per_page": min(per_page, 100)
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._get_headers(token),
                params=params
            ) as response:
                if response.status == 200:
                    webhooks = await response.json()
                    
                    # 简化Webhook信息
                    simplified_webhooks = []
                    for webhook in webhooks:
                        simplified_webhooks.append({
                            "id": webhook.get("id"),
                            "name": webhook.get("name"),
                            "active": webhook.get("active"),
                            "events": webhook.get("events"),
                            "config": webhook.get("config"),
                            "created_at": webhook.get("created_at"),
                            "updated_at": webhook.get("updated_at"),
                            "url": webhook.get("url")
                        })
                    
                    return {
                        "webhooks": simplified_webhooks,
                        "total_count": len(webhooks),
                        "page": page,
                        "per_page": per_page
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"获取Webhooks列表失败: {error_data.get('message', '未知错误')}")
    
    async def _search_repositories(self, token: Optional[str], search_query: str, **kwargs) -> Dict[str, Any]:
        """搜索仓库"""
        if not search_query:
            raise ValueError("搜索仓库需要search_query参数")
        
        page = kwargs.get("page", 1)
        per_page = kwargs.get("per_page", 30)
        
        url = f"{self.base_url}/search/repositories"
        
        params = {
            "q": search_query,
            "page": page,
            "per_page": min(per_page, 100),
            "sort": kwargs.get("sort", "stars"),
            "order": kwargs.get("order", "desc")
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._get_headers(token),
                params=params
            ) as response:
                if response.status == 200:
                    search_result = await response.json()
                    
                    return {
                        "total_count": search_result.get("total_count", 0),
                        "incomplete_results": search_result.get("incomplete_results", False),
                        "items": search_result.get("items", []),
                        "page": page,
                        "per_page": per_page,
                        "query": search_query
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"搜索仓库失败: {error_data.get('message', '未知错误')}")
    
    async def _get_user(self, token: Optional[str], **kwargs) -> Dict[str, Any]:
        """获取用户信息"""
        username = kwargs.get("username")  # 如果未指定，则获取当前用户
        
        if username:
            url = f"{self.base_url}/users/{username}"
        else:
            url = f"{self.base_url}/user"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._get_headers(token)
            ) as response:
                if response.status == 200:
                    user_data = await response.json()
                    
                    # 更新缓存
                    cache_key = f"user_{user_data.get('login')}"
                    self.user_cache[cache_key] = user_data
                    self.cache_expiry[cache_key] = datetime.now().timestamp() + 600
                    
                    # 简化用户信息
                    simplified_info = {
                        "login": user_data.get("login"),
                        "name": user_data.get("name"),
                        "email": user_data.get("email"),
                        "avatar_url": user_data.get("avatar_url"),
                        "html_url": user_data.get("html_url"),
                        "company": user_data.get("company"),
                        "blog": user_data.get("blog"),
                        "location": user_data.get("location"),
                        "bio": user_data.get("bio"),
                        "public_repos": user_data.get("public_repos"),
                        "followers": user_data.get("followers"),
                        "following": user_data.get("following"),
                        "created_at": user_data.get("created_at"),
                        "updated_at": user_data.get("updated_at")
                    }
                    
                    return simplified_info
                else:
                    error_data = await response.json()
                    raise ValueError(f"获取用户信息失败: {error_data.get('message', '未知错误')}")
    
    async def _update_file(self, token: Optional[str], owner: str, repo: str, path: str, content: str, message: str, **kwargs) -> Dict[str, Any]:
        """创建或更新文件"""
        if not path or not content or not message:
            raise ValueError("更新文件需要path, content, message参数")
        
        # 获取文件的当前SHA（如果存在）
        sha = kwargs.get("sha")
        if not sha:
            try:
                file_info = await self._get_file(token, owner, repo, path, **kwargs)
                if file_info.get("success"):
                    sha = file_info["result"].get("sha")
            except:
                sha = None  # 文件不存在
        
        # 编码内容为Base64
        content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        data = {
            "message": message,
            "content": content_base64,
            "branch": kwargs.get("branch", "main")
        }
        
        if sha:
            data["sha"] = sha
        
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        
        async with aiohttp.ClientSession() as session:
            async with session.put(
                url,
                headers=self._get_headers(token),
                json=data
            ) as response:
                if response.status in [200, 201]:
                    result_data = await response.json()
                    
                    return {
                        "file_updated": True,
                        "path": path,
                        "sha": result_data.get("content", {}).get("sha"),
                        "html_url": result_data.get("content", {}).get("html_url"),
                        "commit": result_data.get("commit", {}).get("sha")
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"更新文件失败: {error_data.get('message', '未知错误')}")
    
    async def _get_file(self, token: Optional[str], owner: str, repo: str, path: str, **kwargs) -> Dict[str, Any]:
        """获取文件内容"""
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        
        params = {}
        if "branch" in kwargs:
            params["ref"] = kwargs["branch"]
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._get_headers(token),
                params=params
            ) as response:
                if response.status == 200:
                    file_data = await response.json()
                    
                    # 解码Base64内容
                    content = ""
                    if file_data.get("encoding") == "base64":
                        content = base64.b64decode(file_data.get("content", "")).decode('utf-8')
                    
                    return {
                        "path": file_data.get("path"),
                        "sha": file_data.get("sha"),
                        "size": file_data.get("size"),
                        "html_url": file_data.get("html_url"),
                        "download_url": file_data.get("download_url"),
                        "type": file_data.get("type"),
                        "content": content,
                        "encoding": file_data.get("encoding")
                    }
                elif response.status == 404:
                    return {
                        "path": path,
                        "exists": False,
                        "error": "文件不存在"
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"获取文件失败: {error_data.get('message', '未知错误')}")
    
    async def _list_branches(self, token: Optional[str], owner: str, repo: str, **kwargs) -> Dict[str, Any]:
        """列出仓库的分支"""
        page = kwargs.get("page", 1)
        per_page = kwargs.get("per_page", 30)
        
        url = f"{self.base_url}/repos/{owner}/{repo}/branches"
        
        params = {
            "page": page,
            "per_page": min(per_page, 100),
            "protected": kwargs.get("protected")
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._get_headers(token),
                params=params
            ) as response:
                if response.status == 200:
                    branches = await response.json()
                    
                    # 简化分支信息
                    simplified_branches = []
                    for branch in branches:
                        simplified_branches.append({
                            "name": branch.get("name"),
                            "protected": branch.get("protected"),
                            "commit": {
                                "sha": branch.get("commit", {}).get("sha"),
                                "url": branch.get("commit", {}).get("url")
                            }
                        })
                    
                    return {
                        "branches": simplified_branches,
                        "total_count": len(branches),
                        "page": page,
                        "per_page": per_page
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"获取分支列表失败: {error_data.get('message', '未知错误')}")
    
    async def _list_commits(self, token: Optional[str], owner: str, repo: str, **kwargs) -> Dict[str, Any]:
        """列出仓库的提交"""
        page = kwargs.get("page", 1)
        per_page = kwargs.get("per_page", 30)
        
        url = f"{self.base_url}/repos/{owner}/{repo}/commits"
        
        params = {
            "page": page,
            "per_page": min(per_page, 100),
            "sha": kwargs.get("branch", "main"),
            "since": kwargs.get("since"),
            "until": kwargs.get("until"),
            "author": kwargs.get("author")
        }
        
        # 移除None值
        params = {k: v for k, v in params.items() if v is not None}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self._get_headers(token),
                params=params
            ) as response:
                if response.status == 200:
                    commits = await response.json()
                    
                    # 简化提交信息
                    simplified_commits = []
                    for commit in commits:
                        simplified_commits.append({
                            "sha": commit.get("sha"),
                            "message": commit.get("commit", {}).get("message"),
                            "author": {
                                "name": commit.get("commit", {}).get("author", {}).get("name"),
                                "email": commit.get("commit", {}).get("author", {}).get("email"),
                                "date": commit.get("commit", {}).get("author", {}).get("date")
                            },
                            "committer": {
                                "name": commit.get("commit", {}).get("committer", {}).get("name"),
                                "email": commit.get("commit", {}).get("committer", {}).get("email"),
                                "date": commit.get("commit", {}).get("committer", {}).get("date")
                            },
                            "html_url": commit.get("html_url"),
                            "parents": [parent.get("sha") for parent in commit.get("parents", [])]
                        })
                    
                    return {
                        "commits": simplified_commits,
                        "total_count": len(commits),
                        "page": page,
                        "per_page": per_page
                    }
                else:
                    error_data = await response.json()
                    raise ValueError(f"获取提交列表失败: {error_data.get('message', '未知错误')}")
    
    async def _record_hook_event(self, **kwargs):
        """记录Hook事件（简化实现）"""
        # 实际应用中应该调用Hook系统
        operation = kwargs.get("operation", "unknown")
        success = kwargs.get("success", False)
        
        if not success:
            self.logger.warning(f"GitHub操作失败: {operation}")


# 创建默认实例
github_hand = GitHubHand()