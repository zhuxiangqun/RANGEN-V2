#!/usr/bin/env python3
"""
Git集成模块
处理自进化系统的代码提交、版本管理和回滚机制
"""

import asyncio
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime


class GitIntegration:
    """Git集成管理"""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.logger = logging.getLogger(__name__)
        
        # 验证Git仓库
        self._verify_git_repo()
        
        self.logger.info(f"Git集成初始化完成，仓库: {self.repo_path}")
    
    def _verify_git_repo(self):
        """验证Git仓库状态"""
        try:
            # 检查是否在Git仓库中
            result = self._run_git_command(["rev-parse", "--git-dir"])
            if result.returncode != 0:
                raise RuntimeError(f"路径不是Git仓库: {self.repo_path}")
            
            # 检查是否有未提交的更改
            status_result = self._run_git_command(["status", "--porcelain"])
            if status_result.stdout.strip():
                self.logger.warning(f"Git仓库有未提交的更改: {status_result.stdout.strip()}")
            
            # 获取当前分支
            branch_result = self._run_git_command(["branch", "--show-current"])
            self.current_branch = branch_result.stdout.strip()
            self.logger.info(f"当前分支: {self.current_branch}")
            
        except Exception as e:
            self.logger.error(f"Git仓库验证失败: {e}")
            raise
    
    def _run_git_command(self, args: List[str], capture_output: bool = True) -> subprocess.CompletedProcess:
        """运行Git命令"""
        full_args = ["git"] + args
        self.logger.debug(f"运行Git命令: {' '.join(full_args)}")
        
        try:
            if capture_output:
                result = subprocess.run(
                    full_args,
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )
            else:
                result = subprocess.run(
                    full_args,
                    cwd=self.repo_path,
                    text=True,
                    encoding='utf-8'
                )
            
            if result.returncode != 0:
                self.logger.error(f"Git命令失败: {result.stderr}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"执行Git命令异常: {e}")
            raise
    
    async def commit_changes(
        self, 
        changes: List[Dict[str, Any]], 
        message: str,
        author: str = "RANGEN自进化系统"
    ) -> Optional[str]:
        """提交更改到Git"""
        self.logger.info(f"准备提交更改: {len(changes)}个修改")
        
        try:
            # 1. 检查是否有更改需要提交
            changed_files = []
            for change in changes:
                if "file_path" in change:
                    file_path = Path(change["file_path"])
                    if file_path.exists():
                        changed_files.append(str(file_path.relative_to(self.repo_path)))
            
            if not changed_files:
                self.logger.warning("没有需要提交的文件更改")
                return None
            
            # 2. 添加文件到暂存区
            add_result = self._run_git_command(["add"] + changed_files)
            if add_result.returncode != 0:
                self.logger.error(f"添加文件到暂存区失败: {add_result.stderr}")
                return None
            
            # 3. 创建提交
            commit_message = f"{message}\n\n提交者: {author}\n时间: {datetime.now().isoformat()}\n修改数: {len(changes)}"
            
            commit_result = self._run_git_command([
                "commit", 
                "-m", commit_message,
                "--author", f"{author} <evolution@rangen.ai>"
            ])
            
            if commit_result.returncode != 0:
                self.logger.error(f"提交失败: {commit_result.stderr}")
                return None
            
            # 4. 获取提交哈希
            hash_result = self._run_git_command(["rev-parse", "HEAD"])
            commit_hash = hash_result.stdout.strip()
            
            self.logger.info(f"✅ 成功提交更改，提交哈希: {commit_hash[:8]}")
            
            # 5. 记录提交信息
            await self._record_commit_info(commit_hash, changes, message)
            
            return commit_hash
            
        except Exception as e:
            self.logger.error(f"提交更改异常: {e}")
            return None
    
    async def _record_commit_info(
        self, 
        commit_hash: str, 
        changes: List[Dict[str, Any]], 
        message: str
    ):
        """记录提交信息到进化日志"""
        log_entry = {
            "commit_hash": commit_hash,
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "changes_count": len(changes),
            "changed_files": [],
            "change_types": {}
        }
        
        # 分析更改类型
        for change in changes:
            if "file_path" in change:
                rel_path = Path(change["file_path"]).relative_to(self.repo_path)
                log_entry["changed_files"].append(str(rel_path))
            
            if "change_type" in change:
                change_type = change["change_type"]
                log_entry["change_types"][change_type] = log_entry["change_types"].get(change_type, 0) + 1
        
        # 保存到日志文件
        log_file = self.repo_path / "evolution_logs" / "git_commits.json"
        log_file.parent.mkdir(exist_ok=True)
        
        import json
        log_data = []
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        
        log_data.append(log_entry)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
    
    async def rollback_last_commit(self) -> bool:
        """回滚最后一次提交"""
        self.logger.info("准备回滚最后一次提交")
        
        try:
            # 1. 获取当前提交信息
            log_result = self._run_git_command(["log", "-1", "--oneline"])
            if log_result.returncode != 0:
                self.logger.error(f"获取提交日志失败: {log_result.stderr}")
                return False
            
            last_commit = log_result.stdout.strip()
            self.logger.info(f"最后提交: {last_commit}")
            
            # 2. 执行回滚（soft reset）
            reset_result = self._run_git_command(["reset", "--soft", "HEAD~1"])
            if reset_result.returncode != 0:
                self.logger.error(f"回滚提交失败: {reset_result.stderr}")
                
                # 尝试hard reset作为备选
                self.logger.warning("尝试hard reset...")
                hard_reset_result = self._run_git_command(["reset", "--hard", "HEAD~1"])
                if hard_reset_result.returncode != 0:
                    self.logger.error(f"Hard reset也失败: {hard_reset_result.stderr}")
                    return False
            
            self.logger.info(f"✅ 成功回滚提交: {last_commit}")
            
            # 3. 记录回滚操作
            await self._record_rollback_info(last_commit)
            
            return True
            
        except Exception as e:
            self.logger.error(f"回滚提交异常: {e}")
            return False
    
    async def _record_rollback_info(self, rolled_back_commit: str):
        """记录回滚信息"""
        rollback_log = {
            "rolled_back_commit": rolled_back_commit,
            "timestamp": datetime.now().isoformat(),
            "reason": "自进化系统检测到问题或错误"
        }
        
        rollback_file = self.repo_path / "evolution_logs" / "rollbacks.json"
        rollback_file.parent.mkdir(exist_ok=True)
        
        import json
        rollback_data = []
        if rollback_file.exists():
            with open(rollback_file, 'r', encoding='utf-8') as f:
                rollback_data = json.load(f)
        
        rollback_data.append(rollback_log)
        
        with open(rollback_file, 'w', encoding='utf-8') as f:
            json.dump(rollback_data, f, indent=2, ensure_ascii=False)
    
    async def create_branch(self, branch_name: str) -> bool:
        """创建新分支用于进化实验"""
        self.logger.info(f"创建进化实验分支: {branch_name}")
        
        try:
            # 检查分支是否已存在
            check_result = self._run_git_command(["show-ref", "--verify", f"refs/heads/{branch_name}"])
            if check_result.returncode == 0:
                self.logger.warning(f"分支已存在: {branch_name}")
                return True
            
            # 创建新分支
            create_result = self._run_git_command(["checkout", "-b", branch_name])
            if create_result.returncode != 0:
                self.logger.error(f"创建分支失败: {create_result.stderr}")
                return False
            
            self.logger.info(f"✅ 成功创建分支: {branch_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"创建分支异常: {e}")
            return False
    
    async def merge_branch(self, source_branch: str, target_branch: str = "main") -> Dict[str, Any]:
        """合并分支"""
        self.logger.info(f"合并分支: {source_branch} -> {target_branch}")
        
        try:
            # 1. 切换到目标分支
            checkout_result = self._run_git_command(["checkout", target_branch])
            if checkout_result.returncode != 0:
                return {
                    "success": False,
                    "error": f"切换到目标分支失败: {checkout_result.stderr}"
                }
            
            # 2. 合并源分支
            merge_result = self._run_git_command(["merge", "--no-ff", source_branch])
            
            if merge_result.returncode == 0:
                self.logger.info(f"✅ 成功合并分支: {source_branch} -> {target_branch}")
                return {
                    "success": True,
                    "merge_commit_hash": self._run_git_command(["rev-parse", "HEAD"]).stdout.strip()
                }
            else:
                self.logger.error(f"合并冲突: {merge_result.stderr}")
                
                # 处理合并冲突
                conflict_resolution = await self._handle_merge_conflict()
                
                if conflict_resolution["resolved"]:
                    # 提交冲突解决
                    commit_result = self._run_git_command(["commit", "-m", f"合并 {source_branch} 并解决冲突"])
                    if commit_result.returncode == 0:
                        return {
                            "success": True,
                            "had_conflicts": True,
                            "merge_commit_hash": self._run_git_command(["rev-parse", "HEAD"]).stdout.strip()
                        }
                
                return {
                    "success": False,
                    "error": "合并冲突未解决",
                    "conflict_details": conflict_resolution
                }
            
        except Exception as e:
            self.logger.error(f"合并分支异常: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_merge_conflict(self) -> Dict[str, Any]:
        """处理合并冲突"""
        self.logger.warning("检测到合并冲突，尝试自动解决...")
        
        # 获取冲突文件
        status_result = self._run_git_command(["status", "--porcelain"])
        conflict_files = []
        
        for line in status_result.stdout.strip().split('\n'):
            if line and line.startswith('UU'):  # 冲突文件
                conflict_files.append(line[3:].strip())
        
        if not conflict_files:
            return {"resolved": False, "message": "未检测到冲突文件"}
        
        self.logger.info(f"冲突文件: {conflict_files}")
        
        # TODO: 实现智能冲突解决
        # 目前先中止合并，由开发者手动解决
        abort_result = self._run_git_command(["merge", "--abort"])
        
        return {
            "resolved": False,
            "message": "需要人工解决冲突",
            "conflict_files": conflict_files,
            "aborted": abort_result.returncode == 0
        }
    
    async def get_commit_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取提交历史"""
        try:
            # 使用自定义格式获取提交历史
            format_str = "%H|%an|%ad|%s"
            log_result = self._run_git_command([
                "log", 
                f"-{limit}",
                f"--pretty=format:{format_str}",
                "--date=iso"
            ])
            
            if log_result.returncode != 0:
                return []
            
            commits = []
            for line in log_result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('|', 3)
                if len(parts) == 4:
                    commits.append({
                        "hash": parts[0],
                        "author": parts[1],
                        "date": parts[2],
                        "message": parts[3]
                    })
            
            return commits
            
        except Exception as e:
            self.logger.error(f"获取提交历史异常: {e}")
            return []
    
    async def get_file_history(self, file_path: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取文件修改历史"""
        try:
            rel_path = Path(file_path).relative_to(self.repo_path)
            
            log_result = self._run_git_command([
                "log",
                f"-{limit}",
                "--pretty=format:%H|%an|%ad|%s",
                "--date=iso",
                "--follow",
                str(rel_path)
            ])
            
            if log_result.returncode != 0:
                return []
            
            history = []
            for line in log_result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('|', 3)
                if len(parts) == 4:
                    history.append({
                        "hash": parts[0],
                        "author": parts[1],
                        "date": parts[2],
                        "message": parts[3]
                    })
            
            return history
            
        except Exception as e:
            self.logger.error(f"获取文件历史异常: {e}")
            return []
    
    async def get_diff(self, commit_hash1: str, commit_hash2: str = "HEAD") -> str:
        """获取两次提交之间的差异"""
        try:
            diff_result = self._run_git_command(["diff", f"{commit_hash1}..{commit_hash2}"])
            
            if diff_result.returncode == 0:
                return diff_result.stdout
            else:
                return ""
                
        except Exception as e:
            self.logger.error(f"获取差异异常: {e}")
            return ""
    
    async def tag_release(self, version: str, message: str = "") -> bool:
        """标记发布版本"""
        self.logger.info(f"标记发布版本: {version}")
        
        try:
            tag_message = f"版本 {version}\n\n{message}\n\n标记时间: {datetime.now().isoformat()}"
            
            tag_result = self._run_git_command([
                "tag",
                "-a", version,
                "-m", tag_message
            ])
            
            if tag_result.returncode == 0:
                self.logger.info(f"✅ 成功标记版本: {version}")
                return True
            else:
                self.logger.error(f"标记版本失败: {tag_result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"标记版本异常: {e}")
            return False
    
    async def get_repo_status(self) -> Dict[str, Any]:
        """获取仓库状态"""
        try:
            # 获取当前分支
            branch_result = self._run_git_command(["branch", "--show-current"])
            current_branch = branch_result.stdout.strip()
            
            # 获取未提交的更改
            status_result = self._run_git_command(["status", "--porcelain"])
            unstaged_changes = [line for line in status_result.stdout.strip().split('\n') if line]
            
            # 获取最近提交
            recent_commits = await self.get_commit_history(5)
            
            return {
                "current_branch": current_branch,
                "unstaged_changes_count": len(unstaged_changes),
                "unstaged_changes": unstaged_changes[:5],  # 只显示前5个
                "recent_commits": recent_commits,
                "repo_path": str(self.repo_path),
                "is_clean": len(unstaged_changes) == 0
            }
            
        except Exception as e:
            self.logger.error(f"获取仓库状态异常: {e}")
            return {"error": str(e)}


if __name__ == "__main__":
    # 测试Git集成
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        print("🧪 测试Git集成")
        print("=" * 60)
        
        git = GitIntegration(Path.cwd())
        
        # 获取仓库状态
        status = await git.get_repo_status()
        print(f"仓库状态: {status}")
        
        # 获取提交历史
        history = await git.get_commit_history(5)
        print(f"\n最近5次提交:")
        for commit in history:
            print(f"  {commit['hash'][:8]} {commit['author']}: {commit['message']}")
        
        # 测试文件历史（示例文件）
        example_file = "src/evolution/git_integration.py"
        if Path(example_file).exists():
            file_history = await git.get_file_history(example_file, 3)
            print(f"\n文件历史 ({example_file}):")
            for hist in file_history:
                print(f"  {hist['hash'][:8]} {hist['date']}: {hist['message']}")
    
    asyncio.run(test())