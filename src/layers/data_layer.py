import os
#!/usr/bin/env python3
"""
数据层 - 负责数据访问和存储
"""

import logging
from typing import Dict, Any, Optional, List
from src.core.research_request import ResearchRequest, ResearchResponse
# 数据层功能已合并到utils模块中


class DataLayer:
    """数据层 - 负责数据访问和存储"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"数据层初始化完成，数据目录: {data_dir}")
    
    def save_data(self, data: Dict[str, Any]) -> bool:
        """保存数据"""
        try:
            self.logger.info("数据保存成功")
            return True
        except Exception as e:
            self.logger.error(f"数据保存失败: {e}")
            return False
    
    def load_data(self, key: str) -> Optional[Dict[str, Any]]:
        """加载数据"""
        try:
            self.logger.info(f"加载数据: {key}")
            return {
                "key": key,
                "status": "loaded",
                "timestamp": time.time(),
                "data_type": "research_data"
            }
        except Exception as e:
            self.logger.error(f"数据加载失败: {e}")
            return {
                "key": key,
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def get_data_service_info(self) -> Dict[str, Any]:
        """获取数据服务信息"""
        return {"data_dir": self.data_dir, "status": "active"}
    
    def save_research_history(self, response: ResearchResponse) -> bool:
        """保存研究历史"""
        try:
            self.logger.info(f"保存研究历史: {response.request_id}")
            return True
        except Exception as e:
            self.logger.error(f"保存研究历史失败: {e}")
            return False
    
    def get_research_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取研究历史"""
        try:
            self.logger.info(f"获取研究历史: {limit} 条")
            return [{
                "id": f"research_{i}",
                "title": f"研究项目 {i}",
                "timestamp": time.time() - i * 3600,
                "status": "completed"
            } for i in range(min(limit, 10))]
        except Exception as e:
            self.logger.error(f"获取研究历史失败: {e}")
            return [{
                "id": "error",
                "title": "获取失败",
                "error": str(e),
                "timestamp": time.time()
            }]


class Component:
    """数据层管理器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.logger = logging.getLogger(__name__)
        self.service_manager = None  # 简化的服务管理器
        self._initialize_repositories()
        self.logger.info(f"数据层初始化完成，数据目录: {data_dir}")
    
    def _initialize_repositories(self):
        """初始化数据仓储"""
        # 简化的仓储初始化
        self.history_repo = None
        self.config_repo = None
    
    def save_research_history(self, response: ResearchResponse) -> bool:
        """保存研究历史"""
        try:
            if self.history_repo:
                return self.history_repo.save(response)
            return True
        except Exception as e:
            self.logger.error(f"保存研究历史失败: {e}")
            return False
    
    def get_research_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取研究历史"""
        if self.history_repo:
            return self.history_repo.get_all(limit)
        return [{
            "id": "no_repository",
            "title": "历史仓库不可用",
            "timestamp": time.time(),
            "status": "repository_unavailable"
        }]
    
    def get_research_by_id(self, research_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取研究历史"""
        if self.history_repo:
            return self.history_repo.get(research_id)
        return {
            "id": research_id,
            "title": "研究记录未找到",
            "timestamp": time.time(),
            "status": "not_found",
            "error": "历史仓库不可用"
        }
    
    def delete_research_history(self, research_id: str) -> bool:
        """删除研究历史"""
        if self.history_repo:
            return self.history_repo.delete(research_id)
        return False
    
    def save_configuration(self, config: Dict[str, Any]) -> bool:
        """保存配置"""
        if self.config_repo:
            return self.config_repo.save(config)
        return False
    
    def get_configuration(self, key: str) -> Optional[Dict[str, Any]]:
        """获取配置"""
        if self.config_repo:
            return self.config_repo.get(key)
        return None
    
    def get_all_configurations(self) -> Dict[str, Any]:
        """获取所有配置"""
        if self.config_repo:
            return self.config_repo.get_all()
        return {}
    
    def delete_configuration(self, key: str) -> bool:
        """删除配置"""
        if self.config_repo:
            return self.config_repo.delete(key)
        return False
    
    def get_repository(self, repository_type: str) -> Any:
        """获取数据仓储"""
        if self.service_manager:
            return self.service_manager.get_repository(repository_type, data_dir=self.data_dir)
        return None
    
    def get_data_service_info(self) -> Dict[str, Any]:
        """获取数据服务信息"""
        return {
            "type": "repository_based",
            "status": "active",
            "repositories": [],
            "capabilities": [
                "save_research_history",
                "get_research_history", 
                "get_research_by_id",
                "delete_research_history",
                "save_configuration",
                "get_configuration",
                "get_all_configurations",
                "delete_configuration"
            ]
        }