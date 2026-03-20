"""
Swarm Git Worktree 隔离

为每个 Agent 创建独立的 Git Worktree，实现:
- 工作区完全隔离
- 零冲突并行开发
- 分支独立管理
- 完成后合并回主分支
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass


@dataclass
class WorktreeInfo:
    """Worktree 信息"""
    path: str
    branch: str
    agent_name: str
    team: str
    clean: bool = True


class GitWorktreeManager:
    """
    Git Worktree 管理器
    
    为每个 Agent 创建独立的工作区:
    - 创建 Worktree: git worktree add <path> <branch>
    - 列出 Worktree: git worktree list
    - 删除 Worktree: git worktree remove <path>
    - 合并分支: git merge
    """
    
    def __init__(self, base_dir: str = ".swarm", repo_path: str = "."):
        self.base_dir = Path(base_dir)
        self.repo_path = Path(repo_path)
    
    def _run_git(self, *args, capture: bool = True) -> Optional[str]:
        """运行 git 命令"""
        try:
            cmd = ["git", "-C", str(self.repo_path)] + list(args)
            result = subprocess.run(
                cmd,
                capture_output=capture,
                text=True,
                check=True,
            )
            return result.stdout.strip() if capture else None
        except subprocess.CalledProcessError as e:
            print(f"Git error: {e}")
            return None
    
    def create_worktree(
        self,
        team: str,
        agent_name: str,
        branch: Optional[str] = None,
    ) -> Optional[WorktreeInfo]:
        """
        为 Agent 创建 Worktree
        
        Args:
            team: 团队名
            agent_name: Agent 名
            branch: 分支名 (默认自动生成)
            
        Returns:
            Worktree 信息
        """
        # 生成分支名
        if not branch:
            branch = f"clawteam/{team}/{agent_name}"
        
        # 工作区路径
        worktree_path = self.base_dir / team / "worktrees" / agent_name
        
        # 检查是否已存在
        if worktree_path.exists():
            return WorktreeInfo(
                path=str(worktree_path),
                branch=branch,
                agent_name=agent_name,
                team=team,
                clean=self._is_clean(worktree_path),
            )
        
        # 确保目录存在
        worktree_path.mkdir(parents=True, exist_ok=True)
        
        # 创建分支
        self._run_git("checkout", "-b", branch, raise_on_error=False)
        
        # 创建 worktree
        result = self._run_git("worktree", "add", str(worktree_path), branch)
        
        if result is None:
            return None
        
        return WorktreeInfo(
            path=str(worktree_path),
            branch=branch,
            agent_name=agent_name,
            team=team,
            clean=True,
        )
    
    def list_worktrees(self, team: Optional[str] = None) -> List[WorktreeInfo]:
        """列出 Worktree"""
        output = self._run_git("worktree", "list", "--porcelain")
        
        if not output:
            return []
        
        worktrees = []
        current = {}
        
        for line in output.split("\n"):
            if not line:
                continue
            
            if line.startswith("worktree "):
                if current:
                    worktrees.append(WorktreeInfo(**current))
                parts = line.split(" ", 2)
                current = {"path": parts[1] if len(parts) > 1 else ""}
            elif line.startswith("branch "):
                branch = line.split(" ", 1)[1]
                # 解析 clawteam/team/agent 格式
                if branch.startswith("clawteam/"):
                    parts = branch.split("/")
                    if len(parts) >= 3:
                        current["team"] = parts[1]
                        current["agent_name"] = parts[2]
                    current["branch"] = branch
                else:
                    current["branch"] = branch
                    current["team"] = ""
                    current["agent_name"] = ""
        
        if current:
            worktrees.append(WorktreeInfo(**current))
        
        # 过滤团队
        if team:
            worktrees = [w for w in worktrees if w.team == team]
        
        return worktrees
    
    def remove_worktree(
        self,
        team: str,
        agent_name: str,
        force: bool = False,
    ) -> bool:
        """删除 Worktree"""
        worktree_path = self.base_dir / team / "worktrees" / agent_name
        
        if not worktree_path.exists():
            return True
        
        # 获取分支
        worktrees = self.list_worktrees(team)
        target = None
        for w in worktrees:
            if w.agent_name == agent_name:
                target = w
                break
        
        # 删除 worktree
        cmd = ["worktree", "remove", str(worktree_path)]
        if force:
            cmd.append("--force")
        
        result = self._run_git(*cmd)
        
        # 删除分支
        if target and target.branch:
            self._run_git("branch", "-D", target.branch, raise_on_error=False)
        
        return result is not None or worktree_path.exists() is False
    
    def merge_to_main(
        self,
        team: str,
        agent_name: str,
        message: Optional[str] = None,
    ) -> bool:
        """将 Agent 分支合并到主分支"""
        worktrees = self.list_worktrees(team)
        target = None
        for w in worktrees:
            if w.agent_name == agent_name:
                target = w
                break
        
        if not target:
            return False
        
        # 切换到主分支
        self._run_git("checkout", "main")
        self._run_git("checkout", "master", raise_on_error=False)
        
        # 合并
        merge_msg = message or f"Merge {target.branch} from {team}/{agent_name}"
        result = self._run_git("merge", "--no-ff", "-m", merge_msg, target.branch)
        
        return result is not None
    
    def get_status(self, worktree_path: Path) -> Dict[str, Any]:
        """获取 Worktree 状态"""
        try:
            result = subprocess.run(
                ["git", "-C", str(worktree_path), "status", "--porcelain"],
                capture_output=True,
                text=True,
            )
            
            lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
            
            return {
                "clean": len(lines) == 0,
                "changed_files": len(lines),
                "changes": lines[:10],  # 只返回前10个
            }
        except Exception as e:
            return {"clean": True, "error": str(e)}
    
    def _is_clean(self, worktree_path: Path) -> bool:
        """检查 Worktree 是否干净"""
        status = self.get_status(worktree_path)
        return status.get("clean", True)
    
    def cleanup_team(self, team: str) -> Dict[str, bool]:
        """清理团队所有 Worktree"""
        worktrees = self.list_worktrees(team)
        results = {}
        
        for w in worktrees:
            results[w.agent_name] = self.remove_worktree(team, w.agent_name, force=True)
        
        return results


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    # 注意: 需要在 git 仓库中运行
    print("GitWorktreeManager 示例")
    print("=" * 50)
    
    # 检查是否在 git 仓库中
    import subprocess
    try:
        subprocess.run(["git", "rev-parse", "--git-dir"], check=True, capture_output=True)
        print("✓ 当前目录是 Git 仓库")
    except:
        print("✗ 当前目录不是 Git 仓库，无法演示 Worktree 功能")
        print("\n在 Git 仓库中运行时，可以执行以下操作:")
        print("  manager = GitWorktreeManager()")
        print("  manager.create_worktree('my-team', 'worker1')")
        print("  manager.list_worktrees('my-team')")
        print("  manager.merge_to_main('my-team', 'worker1')")
