"""
命名空间管理器 - 纯新增，不影响现有系统

功能:
- 命名空间创建与管理
- 应用与命名空间绑定
- 访问权限控制
- 资源配额 (向量维度、文档数、图谱节点数)

使用单例模式，确保全局唯一实例
"""

import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Namespace:
    """命名空间"""
    namespace_id: str
    app_id: str
    name: str
    description: str
    vector_dim: int = 1536
    max_documents: int = 10000
    max_graph_nodes: int = 50000
    created_at: str = ""  # ISO format datetime string
    document_count: int = 0
    graph_node_count: int = 0


class NamespaceManager:
    """
    命名空间管理器 - 单例模式
    
    功能:
    - 创建应用专属的命名空间
    - 管理命名空间与应用的绑定
    - 访问权限验证
    - 资源配额追踪
    
    使用内存存储，Phase 1 不涉及数据库
    """
    
    _instance: Optional['NamespaceManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._namespaces: Dict[str, Namespace] = {}  # namespace_id -> Namespace
        self._app_namespaces: Dict[str, List[str]] = {}  # app_id -> [namespace_ids]
        self._default_namespaces: Dict[str, str] = {}  # app_id -> default namespace_id
        self._namespace_by_name: Dict[str, str] = {}  # "{app_id}:{name}" -> namespace_id
        self._initialized = True
    
    def create(
        self,
        app_id: str,
        name: str,
        description: str = "",
        vector_dim: int = 1536,
        max_documents: int = 10000,
        max_graph_nodes: int = 50000
    ) -> Namespace:
        """
        创建命名空间
        
        Args:
            app_id: 应用ID
            name: 命名空间名称
            description: 描述
            vector_dim: 向量维度
            max_documents: 最大文档数
            max_graph_nodes: 最大图谱节点数
            
        Returns:
            Namespace: 创建的命名空间
        """
        # 生成唯一 ID
        namespace_id = f"ns_{uuid.uuid4().hex[:12]}"
        
        # 创建命名空间
        namespace = Namespace(
            namespace_id=namespace_id,
            app_id=app_id,
            name=name,
            description=description,
            vector_dim=vector_dim,
            max_documents=max_documents,
            max_graph_nodes=max_graph_nodes
        )
        
        # 存储
        self._namespaces[namespace_id] = namespace
        
        if app_id not in self._app_namespaces:
            self._app_namespaces[app_id] = []
        self._app_namespaces[app_id].append(namespace_id)
        
        # 按名称索引
        self._namespace_by_name[f"{app_id}:{name}"] = namespace_id
        
        # 第一个命名空间设为默认
        if app_id not in self._default_namespaces:
            self._default_namespaces[app_id] = namespace_id
        
        return namespace
    
    def create_default(self, app_id: str) -> Namespace:
        """
        为应用创建默认命名空间
        
        Args:
            app_id: 应用ID
            
        Returns:
            Namespace: 默认命名空间
        """
        return self.create(
            app_id=app_id,
            name="default",
            description="系统自动创建的默认命名空间"
        )
    
    def get_default(self, app_id: str) -> Optional[str]:
        """
        获取应用的默认命名空间ID
        
        Args:
            app_id: 应用ID
            
        Returns:
            Optional[str]: 默认命名空间ID
        """
        return self._default_namespaces.get(app_id)
    
    def get_default_namespace(self, app_id: str) -> Optional[Namespace]:
        """
        获取应用的默认命名空间
        
        Args:
            app_id: 应用ID
            
        Returns:
            Optional[Namespace]: 默认命名空间
        """
        ns_id = self.get_default(app_id)
        if not ns_id:
            return None
        return self._namespaces.get(ns_id)
    
    def get_by_app(self, app_id: str) -> List[Namespace]:
        """
        获取应用的所有命名空间
        
        Args:
            app_id: 应用ID
            
        Returns:
            List[Namespace]: 命名空间列表
        """
        namespace_ids = self._app_namespaces.get(app_id, [])
        return [
            self._namespaces[nid]
            for nid in namespace_ids
            if nid in self._namespaces
        ]
    
    def get_by_id(self, namespace_id: str) -> Optional[Namespace]:
        """通过ID获取命名空间"""
        return self._namespaces.get(namespace_id)
    
    def get_by_name(self, app_id: str, name: str) -> Optional[Namespace]:
        """通过应用ID和名称获取命名空间"""
        ns_id = self._namespace_by_name.get(f"{app_id}:{name}")
        if not ns_id:
            return None
        return self._namespaces.get(ns_id)
    
    def check_access(self, namespace_id: str, app_id: str) -> bool:
        """
        检查应用是否有权访问命名空间
        
        Args:
            namespace_id: 命名空间ID
            app_id: 应用ID
            
        Returns:
            bool: 是否有权访问
        """
        namespace = self._namespaces.get(namespace_id)
        if not namespace:
            return False
        return namespace.app_id == app_id
    
    def set_default(self, app_id: str, namespace_id: str) -> bool:
        """
        设置应用的默认命名空间
        
        Args:
            app_id: 应用ID
            namespace_id: 命名空间ID
            
        Returns:
            bool: 是否设置成功
        """
        # 验证命名空间属于该应用
        if not self.check_access(namespace_id, app_id):
            return False
        
        self._default_namespaces[app_id] = namespace_id
        return True
    
    def delete(self, namespace_id: str) -> bool:
        """
        删除命名空间
        
        Args:
            namespace_id: 命名空间ID
            
        Returns:
            bool: 是否删除成功
        """
        namespace = self._namespaces.get(namespace_id)
        if not namespace:
            return False
        
        app_id = namespace.app_id
        
        # 从索引中移除
        del self._namespaces[namespace_id]
        
        if app_id in self._app_namespaces:
            if namespace_id in self._app_namespaces[app_id]:
                self._app_namespaces[app_id].remove(namespace_id)
        
        # 移除名称索引
        key = f"{app_id}:{namespace.name}"
        if key in self._namespace_by_name:
            del self._namespace_by_name[key]
        
        # 如果是默认命名空间，重置
        if self._default_namespaces.get(app_id) == namespace_id:
            del self._default_namespaces[app_id]
        
        return True
    
    def update_resource_counts(
        self,
        namespace_id: str,
        document_count: Optional[int] = None,
        graph_node_count: Optional[int] = None
    ) -> bool:
        """
        更新资源计数
        
        Args:
            namespace_id: 命名空间ID
            document_count: 文档数
            graph_node_count: 图谱节点数
            
        Returns:
            bool: 是否更新成功
        """
        namespace = self._namespaces.get(namespace_id)
        if not namespace:
            return False
        
        if document_count is not None:
            namespace.document_count = document_count
        if graph_node_count is not None:
            namespace.graph_node_count = graph_node_count
        
        return True
    
    def check_resource_limits(self, namespace_id: str) -> Dict[str, bool]:
        """
        检查资源配额
        
        Args:
            namespace_id: 命名空间ID
            
        Returns:
            Dict[str, bool]: 各资源是否超限
        """
        namespace = self._namespaces.get(namespace_id)
        if not namespace:
            return {}
        
        return {
            'document_limit_reached': namespace.document_count >= namespace.max_documents,
            'graph_limit_reached': namespace.graph_node_count >= namespace.max_graph_nodes
        }
    
    def list_all(self) -> List[Namespace]:
        """获取所有命名空间"""
        return list(self._namespaces.values())
    
    def __len__(self) -> int:
        """获取命名空间数量"""
        return len(self._namespaces)


# 全局单例
_namespace_manager: Optional[NamespaceManager] = None


def get_namespace_manager() -> NamespaceManager:
    """获取命名空间管理器实例"""
    global _namespace_manager
    if _namespace_manager is None:
        _namespace_manager = NamespaceManager()
    return _namespace_manager
