#!/usr/bin/env python3
"""
模型迁移管理器 - 管理模型版本迁移和部署
"""
import os
import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ModelVersion:
    """模型版本"""
    version_id: str
    model_name: str
    version: str
    file_path: str
    checksum: str
    created_at: float
    metadata: Dict[str, Any]


@dataclass
class MigrationPlan:
    """迁移计划"""
    plan_id: str
    source_version: str
    target_version: str
    migration_steps: List[Dict[str, Any]]
    estimated_time: int
    status: str


class ModelMigrationManager:
    """模型迁移管理器"""
    
    def __init__(self, models_dir: str = "models"):
        """初始化模型迁移管理器"""
        self.logger = logging.getLogger(__name__)
        self.models_dir = Path(models_dir)
        self.model_versions: Dict[str, ModelVersion] = {}
        self.migration_plans: Dict[str, MigrationPlan] = {}
        
        # 确保模型目录存在
        self.models_dir.mkdir(exist_ok=True)
        
        self._load_model_versions()
    
    def register_model_version(self, model_name: str, version: str, 
                             file_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """注册模型版本"""
        try:
            # 验证输入
            if not self._validate_model_input(model_name, version, file_path):
                return ""
            
            # 计算文件校验和
            checksum = self._calculate_checksum(file_path)
            
            # 创建版本ID
            version_id = f"{model_name}_{version}_{int(datetime.now().timestamp())}"
            
            # 创建模型版本
            model_version = ModelVersion(
                version_id=version_id,
                model_name=model_name,
                version=version,
                file_path=file_path,
                checksum=checksum,
                created_at=datetime.now().timestamp(),
                metadata=metadata or {}
            )
            
            # 保存到内存
            self.model_versions[version_id] = model_version
            
            # 保存到文件
            self._save_model_version_to_file(model_version)
            
            self.logger.info(f"注册模型版本成功: {version_id}")
            return version_id
            
        except Exception as e:
            self.logger.error(f"注册模型版本失败: {e}")
            return ""
    
    def _validate_model_input(self, model_name: str, version: str, file_path: str) -> bool:
        """验证模型输入"""
        if not model_name or not model_name.strip():
            return False
        
        if not version or not version.strip():
            return False
        
        if not file_path or not os.path.exists(file_path):
            return False
        
        return True
    
    def _save_model_version_to_file(self, model_version: ModelVersion):
        """保存模型版本到文件"""
        try:
            versions_dir = self.models_dir / "versions"
            versions_dir.mkdir(exist_ok=True)
            
            version_file = versions_dir / f"{model_version.version_id}.json"
            version_data = {
                "version_id": model_version.version_id,
                "model_name": model_version.model_name,
                "version": model_version.version,
                "file_path": model_version.file_path,
                "checksum": model_version.checksum,
                "created_at": model_version.created_at,
                "metadata": model_version.metadata
            }
            
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(version_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"保存模型版本文件失败: {e}")
    
    def create_migration_plan(self, from_version: str, to_version: str, 
                            migration_type: MigrationType = MigrationType.UPGRADE) -> str:
        """创建迁移计划"""
        try:
            # 验证版本
            if from_version not in self.model_versions or to_version not in self.model_versions:
                self.logger.error("源版本或目标版本不存在")
                return ""
            
            # 生成计划ID
            plan_id = f"migration_{from_version}_to_{to_version}_{int(datetime.now().timestamp())}"
            
            # 创建迁移计划
            migration_plan = MigrationPlan(
                plan_id=plan_id,
                from_version=from_version,
                to_version=to_version,
                migration_type=migration_type,
                status=MigrationStatus.PENDING,
                created_at=datetime.now().timestamp(),
                steps=self._generate_migration_steps(from_version, to_version),
                metadata={}
            )
            
            # 保存计划
            self.migration_plans[plan_id] = migration_plan
            self._save_migration_plan_to_file(migration_plan)
            
            self.logger.info(f"创建迁移计划成功: {plan_id}")
            return plan_id
            
        except Exception as e:
            self.logger.error(f"创建迁移计划失败: {e}")
            return ""
    
    def _generate_migration_steps(self, from_version: str, to_version: str) -> List[Dict[str, Any]]:
        """生成迁移步骤"""
        steps = []
        
        # 备份当前版本
        steps.append({
            "step_id": "backup_current",
            "description": "备份当前版本",
            "action": "backup",
            "parameters": {"version": from_version}
        })
        
        # 下载目标版本
        steps.append({
            "step_id": "download_target",
            "description": "下载目标版本",
            "action": "download",
            "parameters": {"version": to_version}
        })
        
        # 验证目标版本
        steps.append({
            "step_id": "verify_target",
            "description": "验证目标版本",
            "action": "verify",
            "parameters": {"version": to_version}
        })
        
        # 执行迁移
        steps.append({
            "step_id": "execute_migration",
            "description": "执行迁移",
            "action": "migrate",
            "parameters": {"from_version": from_version, "to_version": to_version}
        })
        
        return steps
    
    def _save_migration_plan_to_file(self, migration_plan: MigrationPlan):
        """保存迁移计划到文件"""
        try:
            plans_dir = self.models_dir / "migration_plans"
            plans_dir.mkdir(exist_ok=True)
            
            plan_file = plans_dir / f"{migration_plan.plan_id}.json"
            plan_data = {
                "plan_id": migration_plan.plan_id,
                "from_version": migration_plan.from_version,
                "to_version": migration_plan.to_version,
                "migration_type": migration_plan.migration_type.value,
                "status": migration_plan.status.value,
                "created_at": migration_plan.created_at,
                "steps": migration_plan.steps,
                "metadata": migration_plan.metadata
            }
            
            with open(plan_file, 'w', encoding='utf-8') as f:
                json.dump(plan_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"保存迁移计划文件失败: {e}")
    
    def create_migration_plan(self, source_version: str, target_version: str, 
                            migration_steps: List[Dict[str, Any]]) -> str:
        """创建迁移计划"""
        try:
            plan_id = f"migration_{int(datetime.now().timestamp())}"
            
            # 估算迁移时间
            estimated_time = len(migration_steps) * 30  # 每个步骤30秒
            
            migration_plan = MigrationPlan(
                plan_id=plan_id,
                source_version=source_version,
                target_version=target_version,
                migration_steps=migration_steps,
                estimated_time=estimated_time,
                status="pending"
            )
            
            self.migration_plans[plan_id] = migration_plan
            
            self.logger.info(f"迁移计划创建成功: {plan_id}")
            return plan_id
            
        except Exception as e:
            self.logger.error(f"创建迁移计划失败: {e}")
            raise
    
    def execute_migration(self, plan_id: str) -> bool:
        """执行迁移"""
        try:
            if plan_id not in self.migration_plans:
                raise ValueError(f"迁移计划不存在: {plan_id}")
            
            plan = self.migration_plans[plan_id]
            plan.status = "running"
            
            self.logger.info(f"开始执行迁移: {plan_id}")
            
            # 执行迁移步骤
            for step in plan.migration_steps:
                self._execute_migration_step(step)
            
            plan.status = "completed"
            self.logger.info(f"迁移执行完成: {plan_id}")
            return True
            
        except Exception as e:
            if plan_id in self.migration_plans:
                self.migration_plans[plan_id].status = "failed"
            self.logger.error(f"迁移执行失败: {e}")
            return False
    
    def rollback_migration(self, plan_id: str) -> bool:
        """回滚迁移"""
        try:
            if plan_id not in self.migration_plans:
                raise ValueError(f"迁移计划不存在: {plan_id}")
            
            plan = self.migration_plans[plan_id]
            
            if plan.status != "completed":
                raise ValueError("只能回滚已完成的迁移")
            
            self.logger.info(f"开始回滚迁移: {plan_id}")
            
            # 反向执行迁移步骤
            for step in reversed(plan.migration_steps):
                self._execute_rollback_step(step)
            
            plan.status = "rolled_back"
            self.logger.info(f"迁移回滚完成: {plan_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"迁移回滚失败: {e}")
            return False
    
    def get_model_versions(self, model_name: Optional[str] = None) -> List[ModelVersion]:
        """获取模型版本列表"""
        if model_name:
            return [v for v in self.model_versions.values() if v.model_name == model_name]
        return list(self.model_versions.values())
    
    def get_migration_plans(self, status: Optional[str] = None) -> List[MigrationPlan]:
        """获取迁移计划列表"""
        if status:
            return [p for p in self.migration_plans.values() if p.status == status]
        return list(self.migration_plans.values())
    
    def _calculate_checksum(self, file_path: str) -> str:
        """计算文件校验和"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _load_model_versions(self):
        """加载模型版本"""
        try:
            versions_file = self.models_dir / "versions.json"
            if versions_file.exists():
                with open(versions_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for version_data in data.get("versions", []):
                        version = ModelVersion(**version_data)
                        self.model_versions[version.version_id] = version
        except Exception as e:
            self.logger.error(f"加载模型版本失败: {e}")
    
    def _save_model_versions(self):
        """保存模型版本"""
        try:
            versions_file = self.models_dir / "versions.json"
            data = {
                "versions": [
                    {
                        "version_id": v.version_id,
                        "model_name": v.model_name,
                        "version": v.version,
                        "file_path": v.file_path,
                        "checksum": v.checksum,
                        "created_at": v.created_at,
                        "metadata": v.metadata
                    }
                    for v in self.model_versions.values()
                ]
            }
            
            with open(versions_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"保存模型版本失败: {e}")
    
    def _execute_migration_step(self, step: Dict[str, Any]):
        """执行迁移步骤"""
        step_type = step.get("type")
        
        if step_type == "copy_file":
            source = step["source"]
            target = step["target"]
            # 复制文件逻辑
            self.logger.info(f"复制文件: {source} -> {target}")
            
        elif step_type == "update_config":
            config_path = step["config_path"]
            updates = step["updates"]
            # 更新配置逻辑
            self.logger.info(f"更新配置: {config_path}")
            
        elif step_type == "restart_service":
            service_name = step["service_name"]
            # 重启服务逻辑
            self.logger.info(f"重启服务: {service_name}")
            
        else:
            self.logger.warning(f"未知的迁移步骤类型: {step_type}")
    
    def _execute_rollback_step(self, step: Dict[str, Any]):
        """执行回滚步骤"""
        step_type = step.get("type")
        
        if step_type == "copy_file":
            # 反向复制文件
            source = step["target"]
            target = step["source"]
            self.logger.info(f"回滚复制文件: {source} -> {target}")
            
        elif step_type == "update_config":
            # 恢复配置
            config_path = step["config_path"]
            self.logger.info(f"恢复配置: {config_path}")
            
        elif step_type == "restart_service":
            # 重启服务
            service_name = step["service_name"]
            self.logger.info(f"重启服务: {service_name}")
    
    def get_migration_status(self) -> Dict[str, Any]:
        """获取迁移状态"""
        return {
            "total_versions": len(self.model_versions),
            "total_plans": len(self.migration_plans),
            "pending_plans": len([p for p in self.migration_plans.values() if p.status == "pending"]),
            "running_plans": len([p for p in self.migration_plans.values() if p.status == "running"]),
            "completed_plans": len([p for p in self.migration_plans.values() if p.status == "completed"]),
            "failed_plans": len([p for p in self.migration_plans.values() if p.status == "failed"])
        }


def get_model_migration_manager(models_dir: str = "models") -> ModelMigrationManager:
    """获取模型迁移管理器实例"""
    return ModelMigrationManager(models_dir)


if __name__ == "__main__":
    # 测试模型迁移管理器
    manager = ModelMigrationManager()
    
    # 注册模型版本
    version_id = manager.register_model_version(
        "test_model",
        "v1.0",
        "test_model_v1.pkl",
        {"description": "测试模型版本1.0"}
    )
    print(f"注册模型版本: {version_id}")
    
    # 创建迁移计划
    migration_steps = [
        {"type": "copy_file", "source": "old_model.pkl", "target": "new_model.pkl"},
        {"type": "update_config", "config_path": "config.json", "updates": {"model_path": "new_model.pkl"}},
        {"type": "restart_service", "service_name": "model_service"}
    ]
    
    plan_id = manager.create_migration_plan("v1.0", "v2.0", migration_steps)
    print(f"创建迁移计划: {plan_id}")
    
    # 获取状态
    status = manager.get_migration_status()
    print(f"迁移状态: {status}")