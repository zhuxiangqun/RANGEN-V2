"""
LangGraph 状态版本管理模块

实现状态版本控制、回滚和差异分析
"""
import logging
import json
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from src.core.langgraph_unified_workflow import ResearchSystemState

logger = logging.getLogger(__name__)


class StateVersionManager:
    """状态版本管理器"""
    
    def __init__(self, max_versions: int = 10):
        """初始化状态版本管理器
        
        Args:
            max_versions: 每个状态的最大版本数
        """
        self.max_versions = max_versions
        self.versions: Dict[str, List[Dict[str, Any]]] = {}  # thread_id -> versions
        self.logger = logging.getLogger(__name__)
    
    def save_version(self, thread_id: str, state: ResearchSystemState, metadata: Optional[Dict[str, Any]] = None) -> str:
        """保存状态版本
        
        Args:
            thread_id: 线程ID
            state: 状态字典
            metadata: 可选的元数据
        
        Returns:
            版本ID（hash）
        """
        # 计算状态hash作为版本ID
        state_str = json.dumps(state, sort_keys=True, default=str)
        version_id = hashlib.sha256(state_str.encode()).hexdigest()[:16]
        
        version = {
            "version_id": version_id,
            "state": state.copy(),
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        if thread_id not in self.versions:
            self.versions[thread_id] = []
        
        self.versions[thread_id].append(version)
        
        # 限制版本数量
        if len(self.versions[thread_id]) > self.max_versions:
            self.versions[thread_id] = self.versions[thread_id][-self.max_versions:]
        
        self.logger.debug(f"✅ [状态版本] 保存版本: thread_id={thread_id}, version_id={version_id}")
        return version_id
    
    def get_version(self, thread_id: str, version_id: str) -> Optional[Dict[str, Any]]:
        """获取指定版本的状态
        
        Args:
            thread_id: 线程ID
            version_id: 版本ID
        
        Returns:
            版本信息，如果不存在则返回 None
        """
        if thread_id not in self.versions:
            return None
        
        for version in self.versions[thread_id]:
            if version["version_id"] == version_id:
                return version
        
        return None
    
    def list_versions(self, thread_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出所有版本
        
        Args:
            thread_id: 线程ID
            limit: 返回的最大版本数
        
        Returns:
            版本列表（按时间倒序）
        """
        if thread_id not in self.versions:
            return []
        
        versions = self.versions[thread_id]
        if limit:
            versions = versions[-limit:]
        
        # 返回版本摘要（不包含完整状态）
        return [
            {
                "version_id": v["version_id"],
                "timestamp": v["timestamp"],
                "metadata": v["metadata"]
            }
            for v in versions
        ]
    
    def get_latest_version(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取最新版本
        
        Args:
            thread_id: 线程ID
        
        Returns:
            最新版本信息
        """
        if thread_id not in self.versions or not self.versions[thread_id]:
            return None
        
        return self.versions[thread_id][-1]
    
    def rollback_to_version(self, thread_id: str, version_id: str) -> Optional[ResearchSystemState]:
        """回滚到指定版本
        
        Args:
            thread_id: 线程ID
            version_id: 版本ID
        
        Returns:
            回滚后的状态，如果版本不存在则返回 None
        """
        version = self.get_version(thread_id, version_id)
        if not version:
            self.logger.warning(f"⚠️ [状态版本] 版本不存在: thread_id={thread_id}, version_id={version_id}")
            return None
        
        # 创建新版本（回滚后的状态）
        rolled_back_state = version["state"].copy()
        self.save_version(
            thread_id,
            rolled_back_state,
            metadata={
                "rollback_from": version_id,
                "rollback_timestamp": datetime.now().isoformat()
            }
        )
        
        self.logger.info(f"✅ [状态版本] 回滚到版本: thread_id={thread_id}, version_id={version_id}")
        return rolled_back_state
    
    def compare_versions(
        self,
        thread_id: str,
        version_id1: str,
        version_id2: str
    ) -> Dict[str, Any]:
        """比较两个版本的差异
        
        Args:
            thread_id: 线程ID
            version_id1: 第一个版本ID
            version_id2: 第二个版本ID
        
        Returns:
            差异分析结果
        """
        version1 = self.get_version(thread_id, version_id1)
        version2 = self.get_version(thread_id, version_id2)
        
        if not version1 or not version2:
            return {
                "error": "版本不存在",
                "version1_exists": version1 is not None,
                "version2_exists": version2 is not None
            }
        
        state1 = version1["state"]
        state2 = version2["state"]
        
        # 比较差异
        differences = {}
        all_keys = set(state1.keys()) | set(state2.keys())
        
        for key in all_keys:
            val1 = state1.get(key)
            val2 = state2.get(key)
            
            if val1 != val2:
                differences[key] = {
                    "old": val1,
                    "new": val2,
                    "type": type(val1).__name__ if val1 is not None else type(val2).__name__
                }
        
        return {
            "version1": version_id1,
            "version2": version_id2,
            "timestamp1": version1["timestamp"],
            "timestamp2": version2["timestamp"],
            "differences": differences,
            "difference_count": len(differences)
        }
    
    def get_version_history(self, thread_id: str) -> List[Dict[str, Any]]:
        """获取版本历史
        
        Args:
            thread_id: 线程ID
        
        Returns:
            版本历史列表
        """
        return self.list_versions(thread_id)
    
    def cleanup_old_versions(self, thread_id: Optional[str] = None, keep_latest: int = 5):
        """清理旧版本
        
        Args:
            thread_id: 线程ID（如果为 None，清理所有线程）
            keep_latest: 保留的最新版本数
        """
        if thread_id:
            if thread_id in self.versions:
                self.versions[thread_id] = self.versions[thread_id][-keep_latest:]
                self.logger.info(f"✅ [状态版本] 清理旧版本: thread_id={thread_id}, 保留 {keep_latest} 个版本")
        else:
            for tid in list(self.versions.keys()):
                self.versions[tid] = self.versions[tid][-keep_latest:]
            self.logger.info(f"✅ [状态版本] 清理所有线程的旧版本，每个线程保留 {keep_latest} 个版本")

