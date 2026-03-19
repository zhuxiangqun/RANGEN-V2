#!/usr/bin/env python3
"""
Linear Integration - Linear/Jira 集成

基于 Open SWE 的 PR 创建流程:

流程:
1. 获取 Linear Issue
2. 创建 GitHub Branch
3. 创建 Pull Request
4. 关联 PR 到 Issue
5. 更新 Issue 状态
"""

import os
import logging
import requests
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)

# Linear API 配置
LINEAR_API_URL = "https://api.linear.app/graphql"
GITHUB_API_URL = "https://api.github.com"


class IssueState(Enum):
    """Issue 状态"""
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"


@dataclass
class LinearIssue:
    """Linear Issue"""
    id: str
    identifier: str  # 如 "PROJ-123"
    title: str
    description: str
    state: str
    priority: int
    assignee: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    url: str = ""


@dataclass
class PullRequest:
    """GitHub Pull Request"""
    number: int
    title: str
    body: str
    head: str  # branch name
    base: str  # target branch
    html_url: str
    state: str


class LinearIntegration:
    """
    Linear/Jira 集成器
    
    实现:
    - Linear Issue 获取和创建
    - GitHub PR 创建
    - Issue → Branch → PR 工作流
    
    环境变量:
    - LINEAR_API_KEY: Linear API Key
    - GITHUB_TOKEN: GitHub Personal Access Token
    - GITHUB_OWNER: GitHub 仓库所有者
    - GITHUB_REPO: GitHub 仓库名
    """
    
    def __init__(
        self,
        linear_api_key: str = None,
        github_token: str = None,
        github_owner: str = None,
        github_repo: str = None
    ):
        self.linear_api_key = linear_api_key or os.getenv("LINEAR_API_KEY")
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.github_owner = github_owner or os.getenv("GITHUB_OWNER")
        self.github_repo = github_repo or os.getenv("GITHUB_REPO")
        
        self._linear_headers = {
            "Authorization": f"Bearer {self.linear_api_key}",
            "Content-Type": "application/json",
        }
        self._github_headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        
        logger.info(f"LinearIntegration 初始化: {self.github_owner}/{self.github_repo}")
    
    def _linear_graphql(self, query: str, variables: Dict = None) -> Dict:
        """执行 Linear GraphQL 查询"""
        if not self.linear_api_key:
            raise ValueError("LINEAR_API_KEY 未设置")
        
        response = requests.post(
            LINEAR_API_URL,
            headers=self._linear_headers,
            json={"query": query, "variables": variables or {}},
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
        if "errors" in result:
            raise Exception(f"GraphQL Error: {result['errors']}")
        
        return result.get("data", {})
    
    # ==================== Linear Issue 操作 ====================
    
    def get_issue(self, issue_id: str) -> LinearIssue:
        """
        获取 Linear Issue
        
        Args:
            issue_id: Issue ID 或 Identifier (如 "PROJ-123")
            
        Returns:
            LinearIssue 对象
        """
        # 如果是 Identifier 格式，需要先查询 ID
        if "-" in issue_id and not issue_id.startswith("lin"):
            # 查询 issue by identifier
            query = """
            query GetIssue($identifier: String!) {
                issue(identifier: $identifier) {
                    id
                    identifier
                    title
                    description
                    state {
                        name
                    }
                    priority
                    assignee {
                        name
                    }
                    labels {
                        nodes {
                            name
                        }
                    }
                    url
                }
            }
            """
            variables = {"identifier": issue_id}
        else:
            # 直接用 ID 查询
            query = """
            query GetIssue($id: String!) {
                issue(id: $id) {
                    id
                    identifier
                    title
                    description
                    state {
                        name
                    }
                    priority
                    assignee {
                        name
                    }
                    labels {
                        nodes {
                            name
                        }
                    }
                    url
                }
            }
            """
            variables = {"id": issue_id}
        
        data = self._linear_graphql(query, variables)
        issue_data = data.get("issue")
        
        if not issue_data:
            raise ValueError(f"Issue 未找到: {issue_id}")
        
        return LinearIssue(
            id=issue_data["id"],
            identifier=issue_data["identifier"],
            title=issue_data["title"],
            description=issue_data.get("description", ""),
            state=issue_data["state"]["name"],
            priority=issue_data["priority"],
            assignee=issue_data.get("assignee", {}).get("name") if issue_data.get("assignee") else None,
            labels=[label["name"] for label in issue_data.get("labels", {}).get("nodes", [])],
            url=issue_data.get("url", "")
        )
    
    def create_issue(
        self,
        title: str,
        description: str = "",
        team_id: str = None,
        priority: int = 2
    ) -> LinearIssue:
        """
        创建 Linear Issue
        
        Args:
            title: Issue 标题
            description: Issue 描述
            team_id: Team ID
            priority: 优先级 (0-4)
            
        Returns:
            创建的 LinearIssue
        """
        mutation = """
        mutation CreateIssue($title: String!, $description: String, $teamId: String!, $priority: Int!) {
            issueCreate(input: {
                title: $title
                description: $description
                teamId: $teamId
                priority: $priority
            }) {
                success
                issue {
                    id
                    identifier
                    title
                    description
                    state {
                        name
                    }
                    priority
                    url
                }
            }
        }
        """
        variables = {
            "title": title,
            "description": description,
            "teamId": team_id,
            "priority": priority
        }
        
        data = self._linear_graphql(mutation, variables)
        result = data.get("issueCreate", {})
        
        if not result.get("success"):
            raise Exception("创建 Issue 失败")
        
        issue_data = result["issue"]
        return LinearIssue(
            id=issue_data["id"],
            identifier=issue_data["identifier"],
            title=issue_data["title"],
            description=issue_data.get("description", ""),
            state=issue_data["state"]["name"],
            priority=issue_data["priority"],
            url=issue_data.get("url", "")
        )
    
    def update_issue_status(self, issue_id: str, state: str) -> bool:
        """
        更新 Issue 状态
        
        Args:
            issue_id: Issue ID
            state: 新状态 (如 "In Progress", "Done")
            
        Returns:
            是否成功
        """
        # 先获取 state 的 ID
        state_query = """
        query GetState($name: String!) {
            workflowStates(filter: {name: {eq: $name}}) {
                nodes {
                    id
                    name
                }
            }
        }
        """
        state_data = self._linear_graphql(state_query, {"name": state})
        states = state_data.get("workflowStates", {}).get("nodes", [])
        
        if not states:
            raise ValueError(f"状态未找到: {state}")
        
        state_id = states[0]["id"]
        
        # 更新 Issue
        mutation = """
        mutation UpdateIssue($id: String!, $stateId: String!) {
            issueUpdate(id: $id, input: {stateId: $stateId}) {
                success
            }
        }
        """
        variables = {"id": issue_id, "stateId": state_id}
        
        data = self._linear_graphql(mutation, variables)
        return data.get("issueUpdate", {}).get("success", False)
    
    # ==================== GitHub PR 操作 ====================
    
    def create_branch(self, branch_name: str, base_branch: str = "main") -> bool:
        """
        创建 Git Branch
        
        Args:
            branch_name: 新分支名
            base_branch: 基础分支
            
        Returns:
            是否成功
        """
        if not all([self.github_token, self.github_owner, self.github_repo]):
            raise ValueError("GitHub 配置不完整")
        
        # 获取 base branch 的 SHA
        ref_url = f"{GITHUB_API_URL}/repos/{self.github_owner}/{self.github_repo}/git/ref"
        response = requests.get(
            f"{GITHUB_API_URL}/repos/{self.github_owner}/{self.github_repo}/git/ref/heads/{base_branch}",
            headers=self._github_headers,
            timeout=30
        )
        response.raise_for_status()
        base_sha = response.json()["object"]["sha"]
        
        # 创建分支
        response = requests.post(
            ref_url,
            headers=self._github_headers,
            json={
                "ref": f"refs/heads/{branch_name}",
                "sha": base_sha
            },
            timeout=30
        )
        
        if response.status_code == 201:
            logger.info(f"分支创建成功: {branch_name}")
            return True
        else:
            logger.error(f"分支创建失败: {response.text}")
            return False
    
    def create_pr(
        self,
        title: str,
        body: str,
        head: str,
        base: str = "main",
        draft: bool = False
    ) -> PullRequest:
        """
        创建 Pull Request
        
        Args:
            title: PR 标题
            body: PR 描述
            head: 源分支
            base: 目标分支
            draft: 是否为草稿 PR
            
        Returns:
            PullRequest 对象
        """
        if not all([self.github_token, self.github_owner, self.github_repo]):
            raise ValueError("GitHub 配置不完整")
        
        url = f"{GITHUB_API_URL}/repos/{self.github_owner}/{self.github_repo}/pulls"
        response = requests.post(
            url,
            headers=self._github_headers,
            json={
                "title": title,
                "body": body,
                "head": head,
                "base": base,
                "draft": draft
            },
            timeout=30
        )
        response.raise_for_status()
        pr_data = response.json()
        
        return PullRequest(
            number=pr_data["number"],
            title=pr_data["title"],
            body=pr_data["body"] or "",
            head=pr_data["head"]["ref"],
            base=pr_data["base"]["ref"],
            html_url=pr_data["html_url"],
            state=pr_data["state"]
        )
    
    def get_pr(self, pr_number: int) -> PullRequest:
        """
        获取 Pull Request
        
        Args:
            pr_number: PR 编号
            
        Returns:
            PullRequest 对象
        """
        url = f"{GITHUB_API_URL}/repos/{self.github_owner}/{self.github_repo}/pulls/{pr_number}"
        response = requests.get(url, headers=self._github_headers, timeout=30)
        response.raise_for_status()
        pr_data = response.json()
        
        return PullRequest(
            number=pr_data["number"],
            title=pr_data["title"],
            body=pr_data["body"] or "",
            head=pr_data["head"]["ref"],
            base=pr_data["base"]["ref"],
            html_url=pr_data["html_url"],
            state=pr_data["state"]
        )
    
    # ==================== Issue → PR 工作流 ====================
    
    def create_pr_from_issue(
        self,
        issue_id: str,
        branch_prefix: str = None,
        base_branch: str = "main",
        pr_body_template: str = None
    ) -> Dict[str, Any]:
        """
        从 Linear Issue 创建 PR
        
        完整流程:
        1. 获取 Issue 信息
        2. 创建分支
        3. 创建 PR
        4. 更新 Issue 状态
        
        Args:
            issue_id: Linear Issue ID 或 Identifier
            branch_prefix: 分支前缀，默认使用 issue identifier
            base_branch: 基础分支
            pr_body_template: PR 描述模板，{title}, {body}, {url} 占位符
            
        Returns:
            包含所有操作结果的字典
        """
        result = {
            "issue": None,
            "branch": None,
            "pr": None,
            "success": False,
            "errors": []
        }
        
        try:
            # 1. 获取 Issue
            issue = self.get_issue(issue_id)
            result["issue"] = {
                "id": issue.id,
                "identifier": issue.identifier,
                "title": issue.title,
                "url": issue.url
            }
            logger.info(f"获取 Issue: {issue.identifier}")
            
            # 2. 创建分支
            branch_name = branch_prefix or f"{issue.identifier.lower().replace('-', '/')}"
            # 将 - 替换为 / 以符合 Linear 分支命名约定
            branch_name = f"feat/{issue.identifier.lower()}-{issue.title.lower().replace(' ', '-')[:30]}"
            
            if self.create_branch(branch_name, base_branch):
                result["branch"] = {
                    "name": branch_name,
                    "base": base_branch
                }
                logger.info(f"创建分支: {branch_name}")
            else:
                result["errors"].append("分支创建失败")
                return result
            
            # 3. 创建 PR
            pr_body = pr_body_template or """## {title}

{body}

---
**Linear Issue**: {identifier}
**Issue URL**: {url}
**Created by**: RANGEN Agent
"""
            pr_body = pr_body.format(
                title=issue.title,
                body=issue.description or "无描述",
                identifier=issue.identifier,
                url=issue.url
            )
            
            pr = self.create_pr(
                title=f"[{issue.identifier}] {issue.title}",
                body=pr_body,
                head=branch_name,
                base=base_branch
            )
            result["pr"] = {
                "number": pr.number,
                "title": pr.title,
                "url": pr.html_url
            }
            logger.info(f"创建 PR: #{pr.number}")
            
            result["success"] = True
            
        except Exception as e:
            logger.error(f"创建 PR 失败: {e}")
            result["errors"].append(str(e))
        
        return result
    
    def link_pr_to_issue(self, pr_url: str, issue_id: str) -> bool:
        """
        关联 PR 到 Linear Issue
        
        通过在 PR body 中添加 Linear Issue 链接实现自动关联
        """
        # Linear 会自动识别 PR body 中的 issue identifier
        # 只需要确保 PR body 包含 issue identifier 即可
        return True
    
    def update_issue_on_pr_merge(self, issue_id: str) -> bool:
        """
        在 PR 合并后更新 Issue 状态
        
        Args:
            issue_id: Issue ID
            
        Returns:
            是否成功
        """
        try:
            return self.update_issue_status(issue_id, "Done")
        except Exception as e:
            logger.error(f"更新 Issue 状态失败: {e}")
            return False


# ==================== Jira 适配器 (可选) ====================

class JiraIntegration:
    """
    Jira 集成器 (简化版)
    
    与 LinearIntegration 接口兼容
    """
    
    def __init__(
        self,
        jira_url: str = None,
        jira_email: str = None,
        jira_api_token: str = None,
        project_key: str = None
    ):
        self.jira_url = jira_url or os.getenv("JIRA_URL")
        self.jira_email = jira_email or os.getenv("JIRA_EMAIL")
        self.jira_api_token = jira_api_token or os.getenv("JIRA_API_TOKEN")
        self.project_key = project_key or os.getenv("JIRA_PROJECT_KEY")
        
        self._auth = (self.jira_email, self.jira_api_token)
        
        logger.info(f"JiraIntegration 初始化: {self.jira_url}")
    
    def get_issue(self, issue_id: str) -> Dict:
        """获取 Jira Issue"""
        url = f"{self.jira_url}/rest/api/3/issue/{issue_id}"
        response = requests.get(url, auth=self._auth, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        return {
            "id": data["id"],
            "key": data["key"],
            "title": data["fields"]["summary"],
            "description": data["fields"].get("description", {}).get("content", ""),
            "status": data["fields"]["status"]["name"],
            "priority": data["fields"]["priority"]["name"],
        }
    
    def create_branch(self, branch_name: str, base_branch: str = "main") -> bool:
        """创建 Git Branch (需要额外配置)"""
        # Jira 本身不创建分支，需要调用 GitHub/GitLab API
        raise NotImplementedError("请使用 LinearIntegration 或直接调用 GitHub API")


# 全局单例
_linear_integration: Optional[LinearIntegration] = None


def get_linear_integration() -> LinearIntegration:
    """获取全局 Linear 集成器"""
    global _linear_integration
    if _linear_integration is None:
        _linear_integration = LinearIntegration()
    return _linear_integration
