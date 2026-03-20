"""
动态配置系统 - 完整的配置管理解决方案

提供配置持久化、验证、版本管理、监控和热更新的完整功能
"""

import os
import json
import hashlib
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

# 导入枚举类型（如果可用）
try:
    from enum import Enum
    ENUM_AVAILABLE = True
except ImportError:
    ENUM_AVAILABLE = False

class ConfigStore(ABC):
    """配置存储抽象基类"""

    @abstractmethod
    def save_config(self, config: Dict[str, Any]) -> str:
        """保存配置，返回版本ID"""
        pass

    @abstractmethod
    def load_config(self) -> Optional[Dict[str, Any]]:
        """加载最新配置"""
        pass

    @abstractmethod
    def get_config_versions(self) -> List[str]:
        """获取所有配置版本"""
        pass

    @abstractmethod
    def rollback_to_version(self, version: str) -> Optional[Dict[str, Any]]:
        """回滚到指定版本"""
        pass

class FileConfigStore(ConfigStore):
    """增强的文件配置存储 - 支持分支和标签"""

    def __init__(self, config_file: str, max_versions: int = 20):
        self.config_file = Path(config_file)
        self.versions_dir = self.config_file.parent / f"{self.config_file.stem}_versions"
        self.branches_dir = self.config_file.parent / f"{self.config_file.stem}_branches"
        self.tags_dir = self.config_file.parent / f"{self.config_file.stem}_tags"

        # 创建目录
        for dir_path in [self.versions_dir, self.branches_dir, self.tags_dir]:
            dir_path.mkdir(exist_ok=True)

        self.max_versions = max_versions
        self.current_branch = "main"
        self.tags: Dict[str, str] = self._load_tags()

    def save_config(self, config: Dict[str, Any], message: str = "") -> str:
        """保存配置到文件 - 支持分支"""
        # 生成版本ID
        config_str = json.dumps(config, sort_keys=True, ensure_ascii=False)
        version_id = hashlib.md5(config_str.encode('utf-8')).hexdigest()[:8]

        # 添加版本元数据
        version_data = {
            'config': config,
            'version_id': version_id,
            'branch': self.current_branch,
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'parent_version': self._get_current_version()
        }

        # 保存当前配置
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        # 保存版本
        version_file = self.versions_dir / f"{version_id}.json"
        with open(version_file, 'w', encoding='utf-8') as f:
            json.dump(version_data, f, ensure_ascii=False, indent=2)

        # 保存到当前分支
        branch_file = self.branches_dir / f"{self.current_branch}.json"
        with open(branch_file, 'w', encoding='utf-8') as f:
            json.dump(version_data, f, ensure_ascii=False, indent=2)

        # 清理旧版本
        self._cleanup_old_versions()

        return version_id

    def load_config(self) -> Optional[Dict[str, Any]]:
        """从文件加载配置"""
        if not self.config_file.exists():
            return None

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def get_config_versions(self) -> List[str]:
        """获取所有配置版本"""
        if not self.versions_dir.exists():
            return []

        versions = []
        for version_file in self.versions_dir.glob("*.json"):
            versions.append(version_file.stem)

        return sorted(versions, reverse=True)

    def rollback_to_version(self, version: str) -> Optional[Dict[str, Any]]:
        """回滚到指定版本"""
        version_file = self.versions_dir / f"{version}.json"
        if not version_file.exists():
            return None

        try:
            with open(version_file, 'r', encoding='utf-8') as f:
                version_data = json.load(f)

            config = version_data.get('config', version_data)  # 兼容旧格式

            # 恢复当前配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            return config
        except Exception:
            return None

    def create_branch(self, branch_name: str, from_version: Optional[str] = None) -> bool:
        """创建新分支"""
        if branch_name in ['main', 'master']:
            return False  # 保留分支名

        from_version = from_version or self._get_current_version()
        if not from_version:
            return False

        version_file = self.versions_dir / f"{from_version}.json"
        if not version_file.exists():
            return False

        try:
            with open(version_file, 'r', encoding='utf-8') as f:
                version_data = json.load(f)

            # 创建分支文件
            branch_file = self.branches_dir / f"{branch_name}.json"
            version_data['branch'] = branch_name
            with open(branch_file, 'w', encoding='utf-8') as f:
                json.dump(version_data, f, ensure_ascii=False, indent=2)

            return True
        except Exception:
            return False

    def switch_branch(self, branch_name: str) -> bool:
        """切换分支"""
        branch_file = self.branches_dir / f"{branch_name}.json"
        if not branch_file.exists():
            return False

        try:
            with open(branch_file, 'r', encoding='utf-8') as f:
                version_data = json.load(f)

            config = version_data.get('config', version_data)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            self.current_branch = branch_name
            return True
        except Exception:
            return False

    def merge_branch(self, source_branch: str, target_branch: str = "main",
                    strategy: str = "overwrite") -> bool:
        """合并分支"""
        source_file = self.branches_dir / f"{source_branch}.json"
        target_file = self.branches_dir / f"{target_branch}.json"

        if not source_file.exists() or not target_file.exists():
            return False

        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                source_data = json.load(f)
            with open(target_file, 'r', encoding='utf-8') as f:
                target_data = json.load(f)

            source_config = source_data.get('config', source_data)
            target_config = target_data.get('config', target_data)

            # 执行合并策略
            if strategy == "overwrite":
                merged_config = source_config
            elif strategy == "merge":
                merged_config = self._deep_merge(target_config, source_config)
            else:
                return False

            # 保存合并结果
            merged_data = source_data.copy()
            merged_data['config'] = merged_config
            merged_data['branch'] = target_branch
            merged_data['merge_source'] = source_branch
            merged_data['merge_strategy'] = strategy

            with open(target_file, 'w', encoding='utf-8') as f:
                json.dump(merged_data, f, ensure_ascii=False, indent=2)

            return True
        except Exception:
            return False

    def create_tag(self, tag_name: str, version: Optional[str] = None, description: str = ""):
        """创建标签"""
        version = version or self._get_current_version()
        if not version:
            return False

        tag_data = {
            'version': version,
            'name': tag_name,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'branch': self.current_branch
        }

        try:
            tag_file = self.tags_dir / f"{tag_name}.json"
            with open(tag_file, 'w', encoding='utf-8') as f:
                json.dump(tag_data, f, ensure_ascii=False, indent=2)

            self.tags[tag_name] = version
            return True
        except Exception:
            return False

    def get_tags(self) -> Dict[str, str]:
        """获取所有标签"""
        return self.tags.copy()

    def checkout_tag(self, tag_name: str) -> bool:
        """检出标签"""
        if tag_name not in self.tags:
            return False

        version = self.tags[tag_name]
        return self.rollback_to_version(version) is not None

    def _load_tags(self) -> Dict[str, str]:
        """加载标签"""
        tags = {}
        if self.tags_dir.exists():
            for tag_file in self.tags_dir.glob("*.json"):
                try:
                    with open(tag_file, 'r', encoding='utf-8') as f:
                        tag_data = json.load(f)
                        tags[tag_data['name']] = tag_data['version']
                except Exception:
                    continue
        return tags

    def _get_current_version(self) -> Optional[str]:
        """获取当前版本"""
        if not self.config_file.exists():
            return None

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            config_str = json.dumps(config, sort_keys=True, ensure_ascii=False)
            return hashlib.md5(config_str.encode('utf-8')).hexdigest()[:8]
        except Exception:
            return None

    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并字典"""
        result = base.copy()

        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _cleanup_old_versions(self):
        """清理旧版本文件"""
        version_files = list(self.versions_dir.glob("*.json"))
        if len(version_files) > self.max_versions:
            # 按修改时间排序，删除最旧的
            version_files.sort(key=lambda x: x.stat().st_mtime)
            for old_file in version_files[:-self.max_versions]:
                old_file.unlink()

class DatabaseConfigStore(ConfigStore):
    """基于数据库的配置存储"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        # 这里实现数据库连接逻辑
        # 假设使用SQLite作为示例

    def save_config(self, config: Dict[str, Any]) -> str:
        """保存配置到数据库"""
        # 实现数据库保存逻辑
        version_id = f"db_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        # 保存到数据库表: routing_configs
        return version_id

    def load_config(self) -> Optional[Dict[str, Any]]:
        """从数据库加载配置"""
        # 从数据库加载最新配置
        return None

    def get_config_versions(self) -> List[str]:
        """获取所有配置版本"""
        return []

    def rollback_to_version(self, version: str) -> Optional[Dict[str, Any]]:
        """回滚到指定版本"""
        return None

@dataclass
class ConfigValidationResult:
    """配置验证结果"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

class ConfigValidator:
    """增强的配置验证器"""

    def __init__(self):
        self.validation_rules = self._load_validation_rules()
        self.custom_validators: List[Callable[[Dict[str, Any]], ConfigValidationResult]] = []

    def add_custom_validator(self, validator: Callable[[Dict[str, Any]], ConfigValidationResult]):
        """添加自定义验证器"""
        self.custom_validators.append(validator)

    def _load_validation_rules(self) -> Dict[str, Any]:
        """加载增强的验证规则"""
        return {
            'thresholds': {
                'simple_max_complexity': {'type': 'float', 'range': [0.0, 1.0], 'required': True},
                'medium_min_complexity': {'type': 'float', 'range': [0.0, 1.0], 'required': True},
                'medium_max_complexity': {'type': 'float', 'range': [0.0, 1.0], 'required': True},
                'complex_min_complexity': {'type': 'float', 'range': [0.0, 1.0], 'required': True},
                'simple_max_words': {'type': 'int', 'range': [1, 100], 'required': True},
                'medium_min_words': {'type': 'int', 'range': [1, 100], 'required': True},
                'medium_max_words': {'type': 'int', 'range': [1, 100], 'required': True},
                'complex_min_words': {'type': 'int', 'range': [1, 100], 'required': True},
            },
            'keywords': {
                'question_words': {'type': 'list', 'item_type': 'str', 'max_length': 50},
                'complexity_indicators': {'type': 'list', 'item_type': 'str', 'max_length': 30},
                'domain_keywords': {'type': 'dict', 'value_type': 'list', 'max_keys': 10},
            },
            'routing_rules': {
                'rules': {'type': 'list', 'item_type': 'dict', 'max_length': 20}
            },
            # 依赖关系验证
            'dependencies': {
                'thresholds': [
                    # 复杂度阈值必须递增
                    ['simple_max_complexity', '<', 'medium_min_complexity'],
                    ['medium_min_complexity', '<=', 'medium_max_complexity'],
                    ['medium_max_complexity', '<', 'complex_min_complexity'],
                ],
                'words': [
                    # 词数阈值必须递增
                    ['simple_max_words', '<=', 'medium_min_words'],
                    ['medium_min_words', '<=', 'medium_max_words'],
                    ['medium_max_words', '<=', 'complex_min_words'],
                ]
            }
        }

    def validate(self, config: Dict[str, Any]) -> ConfigValidationResult:
        """增强的配置验证"""
        errors = []
        warnings = []

        # 1. 基础验证
        self._validate_basic_structure(config, errors, warnings)

        # 2. 依赖关系验证
        self._validate_dependencies(config, errors, warnings)

        # 3. 业务逻辑验证
        self._validate_business_logic(config, errors, warnings)

        # 4. 性能影响评估
        self._validate_performance_impact(config, warnings)

        # 5. 自定义验证器
        for validator in self.custom_validators:
            try:
                result = validator(config)
                errors.extend(result.errors)
                warnings.extend(result.warnings)
            except Exception as e:
                errors.append(f"自定义验证器错误: {e}")

        return ConfigValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _validate_basic_structure(self, config: Dict[str, Any], errors: List[str], warnings: List[str]):
        """验证基础结构"""
        # 验证必需字段
        required_sections = ['thresholds']
        for section in required_sections:
            if section not in config:
                errors.append(f"缺少必需的配置部分: {section}")

        # 验证阈值
        thresholds = config.get('thresholds', {})
        threshold_rules = self.validation_rules.get('thresholds', {})

        for key, rule in threshold_rules.items():
            if rule.get('required', False) and key not in thresholds:
                errors.append(f"缺少必需的阈值: {key}")
            elif key in thresholds:
                value = thresholds[key]
                if not self._validate_value(value, rule):
                    errors.append(f"阈值 {key} = {value} 无效")

        # 验证关键词结构
        keywords = config.get('keywords', {})
        keyword_rules = self.validation_rules.get('keywords', {})

        for key, rule in keyword_rules.items():
            if key in keywords:
                value = keywords[key]
                if not self._validate_keyword_structure(value, rule):
                    errors.append(f"关键词 {key} 结构无效")
                else:
                    # 检查长度限制
                    max_length = rule.get('max_length')
                    if max_length and isinstance(value, list) and len(value) > max_length:
                        warnings.append(f"关键词 {key} 数量过多 ({len(value)}), 建议不超过 {max_length}")

    def _validate_dependencies(self, config: Dict[str, Any], errors: List[str], warnings: List[str]):
        """验证依赖关系"""
        dependencies = self.validation_rules.get('dependencies', {})

        # 验证阈值依赖关系
        thresholds = config.get('thresholds', {})
        for dep_list in dependencies.get('thresholds', []):
            if len(dep_list) == 3:
                left, op, right = dep_list
                if left in thresholds and right in thresholds:
                    left_val = thresholds[left]
                    right_val = thresholds[right]
                    if not self._check_dependency(left_val, op, right_val):
                        errors.append(f"阈值依赖关系错误: {left}({left_val}) {op} {right}({right_val}) 不成立")

        # 验证词数依赖关系
        for dep_list in dependencies.get('words', []):
            if len(dep_list) == 3:
                left, op, right = dep_list
                if left in thresholds and right in thresholds:
                    left_val = thresholds[left]
                    right_val = thresholds[right]
                    if not self._check_dependency(left_val, op, right_val):
                        errors.append(f"词数依赖关系错误: {left}({left_val}) {op} {right}({right_val}) 不成立")

    def _check_dependency(self, left: Any, op: str, right: Any) -> bool:
        """检查依赖关系"""
        if op == '<':
            return left < right
        elif op == '<=':
            return left <= right
        elif op == '>':
            return left > right
        elif op == '>=':
            return left >= right
        elif op == '==':
            return left == right
        return False

    def _validate_business_logic(self, config: Dict[str, Any], errors: List[str], warnings: List[str]):
        """验证业务逻辑"""
        thresholds = config.get('thresholds', {})

        # 检查阈值范围合理性
        complexity_range = thresholds.get('complex_min_complexity', 0) - thresholds.get('simple_max_complexity', 0)
        if complexity_range < 0.1:
            warnings.append("复杂度阈值范围过小，可能导致路由过于敏感")

        word_range = thresholds.get('complex_min_words', 0) - thresholds.get('simple_max_words', 0)
        if word_range < 5:
            warnings.append("词数阈值范围过小，可能导致路由过于敏感")

        # 检查关键词冲突
        keywords = config.get('keywords', {})
        all_keywords = []
        for kw_list in keywords.values():
            if isinstance(kw_list, list):
                all_keywords.extend(kw_list)

        duplicates = set([x for x in all_keywords if all_keywords.count(x) > 1])
        if duplicates:
            warnings.append(f"发现重复关键词: {', '.join(duplicates)}")

    def _validate_performance_impact(self, config: Dict[str, Any], warnings: List[str]):
        """评估性能影响"""
        keywords = config.get('keywords', {})
        total_keywords = sum(len(kw_list) for kw_list in keywords.values() if isinstance(kw_list, list))

        if total_keywords > 100:
            warnings.append(f"关键词总数过多 ({total_keywords})，可能影响匹配性能")

        routing_rules = config.get('routing_rules', [])
        if len(routing_rules) > 10:
            warnings.append(f"路由规则数量过多 ({len(routing_rules)})，可能影响决策性能")

    def _validate_value(self, value: Any, rule: Dict[str, Any]) -> bool:
        """验证单个值"""
        expected_type = rule['type']
        value_range = rule.get('range')

        # 类型检查
        if expected_type == 'float' and not isinstance(value, (int, float)):
            return False
        if expected_type == 'int' and not isinstance(value, int):
            return False

        # 范围检查
        if value_range and isinstance(value, (int, float)):
            if not (value_range[0] <= value <= value_range[1]):
                return False

        return True

    def _validate_keyword_structure(self, value: Any, rule: Dict[str, Any]) -> bool:
        """验证关键词结构"""
        if rule['type'] == 'list':
            if not isinstance(value, list):
                return False
            if rule.get('item_type') == 'str':
                return all(isinstance(item, str) for item in value)
        elif rule['type'] == 'dict':
            if not isinstance(value, dict):
                return False
            if rule.get('value_type') == 'list':
                return all(isinstance(v, list) for v in value.values())

        return True

    def _validate_threshold_consistency(self, thresholds: Dict[str, float],
                                       errors: List[str], warnings: List[str]):
        """验证阈值逻辑一致性"""
        # 检查复杂度阈值顺序
        complexity_thresholds = [
            ('simple_max_complexity', thresholds.get('simple_max_complexity', 0.05)),
            ('medium_min_complexity', thresholds.get('medium_min_complexity', 0.05)),
            ('medium_max_complexity', thresholds.get('medium_max_complexity', 0.15)),
            ('complex_min_complexity', thresholds.get('complex_min_complexity', 0.15)),
        ]

        for i in range(len(complexity_thresholds) - 1):
            current_name, current_value = complexity_thresholds[i]
            next_name, next_value = complexity_thresholds[i + 1]
            if current_value > next_value:
                errors.append(f"复杂度阈值顺序错误: {current_name}({current_value}) > {next_name}({next_value})")

        # 检查词数阈值顺序
        word_thresholds = [
            ('simple_max_words', thresholds.get('simple_max_words', 3)),
            ('medium_min_words', thresholds.get('medium_min_words', 3)),
            ('medium_max_words', thresholds.get('medium_max_words', 10)),
            ('complex_min_words', thresholds.get('complex_min_words', 10)),
        ]

        for i in range(len(word_thresholds) - 1):
            current_name, current_value = word_thresholds[i]
            next_name, next_value = word_thresholds[i + 1]
            if current_value > next_value:
                errors.append(f"词数阈值顺序错误: {current_name}({current_value}) > {next_name}({next_value})")

@dataclass
class ConfigChangeRecord:
    """配置变更记录"""
    timestamp: datetime
    version: str
    changes: Dict[str, Any]
    author: str = "system"
    description: str = ""

class ConfigMonitor:
    """增强的配置监控器"""

    def __init__(self, log_file: str = "config_changes.log"):
        self.log_file = Path(log_file)
        self.change_history: List[ConfigChangeRecord] = []
        self.alert_rules: List[Dict[str, Any]] = []
        self._load_change_history()

    def record_config_change(self, new_config: Dict[str, Any],
                           author: str = "system", description: str = "",
                           change_type: str = "manual"):
        """记录配置变更"""
        version = self._calculate_config_version(new_config)
        record = ConfigChangeRecord(
            timestamp=datetime.now(),
            version=version,
            changes=new_config,
            author=author,
            description=description
        )

        self.change_history.append(record)
        self._save_change_record(record)

        # 检查告警规则
        self._check_alert_rules(record)

        # 保留最近200条记录
        if len(self.change_history) > 200:
            self.change_history = self.change_history[-200:]

    def add_alert_rule(self, rule: Dict[str, Any]):
        """添加告警规则"""
        self.alert_rules.append(rule)

    def _check_alert_rules(self, record: ConfigChangeRecord):
        """检查告警规则"""
        for rule in self.alert_rules:
            if self._matches_rule(record, rule):
                self._trigger_alert(record, rule)

    def _matches_rule(self, record: ConfigChangeRecord, rule: Dict[str, Any]) -> bool:
        """检查记录是否匹配规则"""
        # 时间范围检查
        if 'time_window_minutes' in rule:
            time_diff = (datetime.now() - record.timestamp).total_seconds() / 60
            if time_diff > rule['time_window_minutes']:
                return False

        # 作者检查
        if 'authors' in rule and record.author not in rule['authors']:
            return False

        # 变更类型检查
        if 'change_types' in rule and record.change_type not in rule['change_types']:
            return False

        # 频率检查
        if 'max_changes_per_hour' in rule:
            recent_changes = [r for r in self.change_history[-50:]
                            if (datetime.now() - r.timestamp).total_seconds() < 3600]
            if len(recent_changes) >= rule['max_changes_per_hour']:
                return True

        return False

    def _trigger_alert(self, record: ConfigChangeRecord, rule: Dict[str, Any]):
        """触发告警"""
        alert_message = f"配置告警: {rule.get('name', '未命名规则')} - {record.description}"
        print(f"🚨 {alert_message}")

        # 这里可以集成邮件、Slack等通知系统
        # send_notification(alert_message, rule.get('channels', []))

    def query_changes(self, filters: Dict[str, Any] = None, limit: int = 20) -> List[ConfigChangeRecord]:
        """查询变更记录"""
        results = self.change_history

        if filters:
            # 作者过滤
            if 'author' in filters:
                results = [r for r in results if r.author == filters['author']]

            # 时间范围过滤
            if 'start_time' in filters:
                start_time = datetime.fromisoformat(filters['start_time'])
                results = [r for r in results if r.timestamp >= start_time]

            if 'end_time' in filters:
                end_time = datetime.fromisoformat(filters['end_time'])
                results = [r for r in results if r.timestamp <= end_time]

            # 变更类型过滤
            if 'change_type' in filters:
                results = [r for r in results if r.change_type == filters['change_type']]

            # 描述关键词过滤
            if 'description_contains' in filters:
                keyword = filters['description_contains']
                results = [r for r in results if keyword in r.description]

        return results[-limit:]

    def get_change_history(self, limit: int = 10) -> List[ConfigChangeRecord]:
        """获取变更历史"""
        return self.change_history[-limit:]

    def get_config_metrics(self) -> Dict[str, Any]:
        """获取配置指标"""
        if not self.change_history:
            return {}

        total_changes = len(self.change_history)
        recent_changes = [r for r in self.change_history
                         if (datetime.now() - r.timestamp).days <= 7]

        # 计算变更频率
        change_freq = self._calculate_change_frequency()

        # 计算作者统计
        author_stats = self._calculate_author_stats()

        # 计算变更类型分布
        type_distribution = self._calculate_type_distribution()

        return {
            'total_changes': total_changes,
            'recent_changes_7d': len(recent_changes),
            'change_frequency_per_day': change_freq,
            'author_stats': author_stats,
            'type_distribution': type_distribution,
            'health_score': self._calculate_health_score()
        }

    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        if not self.change_history:
            return {}

        # 时间趋势分析
        time_trends = self._analyze_time_trends()

        # 变更影响分析
        impact_analysis = self._analyze_change_impact()

        # 预测分析
        predictions = self._predict_future_changes()

        return {
            'time_trends': time_trends,
            'impact_analysis': impact_analysis,
            'predictions': predictions,
            'recommendations': self._generate_recommendations()
        }

    def _calculate_config_version(self, config: Dict[str, Any]) -> str:
        """计算配置版本"""
        config_str = json.dumps(config, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(config_str.encode('utf-8')).hexdigest()[:8]

    def _save_change_record(self, record: ConfigChangeRecord):
        """保存变更记录"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                log_entry = {
                    'timestamp': record.timestamp.isoformat(),
                    'version': record.version,
                    'author': record.author,
                    'description': record.description,
                    'change_summary': self._summarize_changes(record.changes)
                }
                json.dump(log_entry, f, ensure_ascii=False)
                f.write('\n')
        except Exception as e:
            print(f"保存配置变更记录失败: {e}")

    def _load_change_history(self):
        """加载变更历史"""
        if not self.log_file.exists():
            return

        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line.strip())
                        record = ConfigChangeRecord(
                            timestamp=datetime.fromisoformat(data['timestamp']),
                            version=data['version'],
                            changes={},  # 不加载完整变更数据以节省内存
                            author=data['author'],
                            description=data['description']
                        )
                        self.change_history.append(record)
        except Exception as e:
            print(f"加载配置变更历史失败: {e}")

    def _summarize_changes(self, config: Dict[str, Any]) -> Dict[str, int]:
        """总结配置变更"""
        return {
            'thresholds_count': len(config.get('thresholds', {})),
            'keywords_count': len(config.get('keywords', {})),
            'rules_count': len(config.get('routing_rules', []))
        }

    def _calculate_change_frequency(self) -> float:
        """计算变更频率（次/天）"""
        if len(self.change_history) < 2:
            return 0.0

        # 计算时间跨度
        earliest = min(r.timestamp for r in self.change_history)
        latest = max(r.timestamp for r in self.change_history)
        days_span = (latest - earliest).days or 1

        return len(self.change_history) / days_span

    def _calculate_author_stats(self) -> Dict[str, int]:
        """计算作者统计"""
        author_counts = {}
        for record in self.change_history:
            author_counts[record.author] = author_counts.get(record.author, 0) + 1

        return dict(sorted(author_counts.items(), key=lambda x: x[1], reverse=True))

    def _calculate_type_distribution(self) -> Dict[str, int]:
        """计算变更类型分布"""
        type_counts = {}
        for record in self.change_history:
            change_type = getattr(record, 'change_type', 'unknown')
            type_counts[change_type] = type_counts.get(change_type, 0) + 1

        return type_counts

    def _calculate_health_score(self) -> float:
        """计算健康分数 (0-100)"""
        if not self.change_history:
            return 100.0

        score = 100.0

        # 频繁变更扣分
        changes_per_day = self._calculate_change_frequency()
        if changes_per_day > 10:
            score -= 20
        elif changes_per_day > 5:
            score -= 10

        # 单一作者过多扣分
        author_stats = self._calculate_author_stats()
        if author_stats:
            max_author_ratio = max(author_stats.values()) / sum(author_stats.values())
            if max_author_ratio > 0.8:
                score -= 15

        return max(0.0, min(100.0, score))

    def _analyze_time_trends(self) -> Dict[str, Any]:
        """分析时间趋势"""
        if not self.change_history:
            return {}

        # 按小时分组
        hourly_stats = {}
        for record in self.change_history:
            hour = record.timestamp.strftime('%Y-%m-%d %H')
            hourly_stats[hour] = hourly_stats.get(hour, 0) + 1

        # 按日期分组
        daily_stats = {}
        for record in self.change_history:
            day = record.timestamp.strftime('%Y-%m-%d')
            daily_stats[day] = daily_stats.get(day, 0) + 1

        return {
            'hourly_distribution': hourly_stats,
            'daily_distribution': daily_stats,
            'peak_hours': sorted(hourly_stats.items(), key=lambda x: x[1], reverse=True)[:3]
        }

    def _analyze_change_impact(self) -> Dict[str, Any]:
        """分析变更影响"""
        return {
            'threshold_changes': len([r for r in self.change_history if 'threshold' in r.description.lower()]),
            'keyword_changes': len([r for r in self.change_history if 'keyword' in r.description.lower()]),
            'rule_changes': len([r for r in self.change_history if 'rule' in r.description.lower()])
        }

    def _predict_future_changes(self) -> Dict[str, Any]:
        """预测未来变更"""
        if len(self.change_history) < 5:
            return {'prediction': '数据不足'}

        recent_changes = self.change_history[-10:]
        avg_interval = sum(
            (recent_changes[i+1].timestamp - recent_changes[i].timestamp).total_seconds()
            for i in range(len(recent_changes)-1)
        ) / (len(recent_changes) - 1) if len(recent_changes) > 1 else 86400

        next_change_prediction = datetime.now().timestamp() + avg_interval

        return {
            'next_change_expected': datetime.fromtimestamp(next_change_prediction).isoformat(),
            'avg_interval_hours': avg_interval / 3600,
            'trend': 'increasing' if len(recent_changes) > 5 else 'stable'
        }

    def _generate_recommendations(self) -> List[str]:
        """生成建议"""
        recommendations = []

        metrics = self.get_config_metrics()

        if metrics.get('change_frequency_per_day', 0) > 10:
            recommendations.append("变更频率过高，建议增加测试覆盖率")

        if metrics.get('health_score', 100) < 70:
            recommendations.append("配置健康分数较低，建议增加审核流程")

        author_stats = metrics.get('author_stats', {})
        if author_stats and len(author_stats) == 1:
            recommendations.append("配置变更过于集中，建议增加多人审核")

        return recommendations


@dataclass(frozen=True)
class RouteTypeDefinition:
    """动态路由类型定义"""
    name: str
    description: str
    priority: int = 0
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def value(self) -> str:
        return self.name


class DynamicRouteTypeRegistry:
    """动态路由类型注册表"""

    def __init__(self):
        self._route_types: Dict[str, RouteTypeDefinition] = {}
        self._load_default_types()

    def _load_default_types(self):
        """加载默认路由类型"""
        default_types = [
            RouteTypeDefinition(
                name="simple",
                description="简单查询",
                priority=1
            ),
            RouteTypeDefinition(
                name="medium",
                description="中等复杂度查询",
                priority=2
            ),
            RouteTypeDefinition(
                name="complex",
                description="复杂查询",
                priority=3
            ),
            RouteTypeDefinition(
                name="reasoning",
                description="推理密集查询",
                priority=4
            ),
            RouteTypeDefinition(
                name="multi_agent",
                description="多智能体协作查询",
                priority=5
            )
        ]

        for route_type in default_types:
            self._route_types[route_type.name] = route_type

    def register_route_type(self, route_type: RouteTypeDefinition):
        """注册新的路由类型"""
        self._route_types[route_type.name] = route_type

    def get_route_type(self, name: str) -> Optional[RouteTypeDefinition]:
        """获取路由类型"""
        return self._route_types.get(name)

    def get_all_route_types(self) -> List[RouteTypeDefinition]:
        """获取所有路由类型"""
        return list(self._route_types.values())

    def remove_route_type(self, name: str) -> bool:
        """移除路由类型"""
        if name in self._route_types:
            del self._route_types[name]
            return True
        return False


class DynamicRoutingConfig:
    """动态路由配置 - 简化的配置管理"""

    def __init__(self, config_store: Optional['ConfigStore'] = None):
        self.thresholds: Dict[str, float] = {}
        self.keywords: Dict[str, Any] = {}
        self.routing_rules: List[Dict[str, Any]] = []
        self._config_sources: List['ConfigSource'] = []
        self._last_updated = None
        self._auto_refresh_interval = 300  # 5分钟自动刷新

        # 配置存储和验证
        self.config_store = config_store
        self.config_validator = ConfigValidator() if 'ConfigValidator' in globals() else None
        self.config_monitor = ConfigMonitor() if 'ConfigMonitor' in globals() else None

        # 初始化默认配置
        self._load_default_config()

    def _load_default_config(self):
        """加载默认配置"""
        self.thresholds = {
            'simple_max_complexity': 0.05,
            'medium_min_complexity': 0.05,
            'medium_max_complexity': 0.15,
            'complex_min_complexity': 0.15,
            'simple_max_words': 3,
            'medium_min_words': 3,
            'medium_max_words': 10,
            'complex_min_words': 10,
            'multi_agent_min_questions': 2,
            'multi_agent_min_complexity': 0.4
        }

        self.keywords = {
            'question_words': ['what', 'who', 'when', 'where', 'how', 'why'],
            'reasoning_keywords': ['explain', 'analyze', 'compare', 'evaluate'],
            'complex_keywords': ['design', 'architecture', 'system', 'implementation']
        }

    def load_config(self, config_store: 'ConfigStore'):
        """从存储加载配置"""
        try:
            saved_config = config_store.load_config()
            if saved_config:
                self.thresholds.update(saved_config.get('thresholds', {}))
                self.keywords.update(saved_config.get('keywords', {}))
                self.routing_rules = saved_config.get('routing_rules', [])
        except Exception as e:
            print(f"加载配置失败，使用默认配置: {e}")

    def save_config(self, config_store: 'ConfigStore'):
        """保存配置到存储"""
        try:
            config_data = {
                'thresholds': self.thresholds,
                'keywords': self.keywords,
                'routing_rules': self.routing_rules
            }
            config_store.save_config(config_data)
        except Exception as e:
            print(f"保存配置失败: {e}")

    def add_config_source(self, source: 'ConfigSource'):
        """添加配置源"""
        self._config_sources.append(source)
        self._refresh_config()

    def update_threshold(self, key: str, value: float):
        """更新单个阈值"""
        self.thresholds[key] = value

    def add_keyword(self, category: str, keyword: str):
        """添加关键词"""
        if category not in self.keywords:
            self.keywords[category] = []

        if isinstance(self.keywords[category], list):
            if keyword not in self.keywords[category]:
                self.keywords[category].append(keyword)

    def get_routing_config(self) -> Dict[str, Any]:
        """获取完整的路由配置"""
        return {
            'thresholds': self.thresholds,
            'keywords': self.keywords,
            'routing_rules': self.routing_rules
        }

    def _refresh_config(self):
        """刷新配置"""
        pass  # 简化实现


class ConfigTemplateManager:
    """增强的配置模板管理器 - 支持继承和条件模板"""

    def __init__(self):
        self.templates: Dict[str, Dict[str, Any]] = {}
        self.template_inheritance: Dict[str, str] = {}  # 子模板 -> 父模板
        self.conditional_templates: Dict[str, Dict[str, Any]] = {}
        self._load_builtin_templates()

    def _load_builtin_templates(self):
        """加载内置模板"""
        self.templates = {
            'base': {
                'name': '基础模板',
                'description': '所有模板的基础配置',
                'thresholds': {
                    'simple_max_complexity': 0.1,
                    'medium_min_complexity': 0.1,
                    'medium_max_complexity': 0.25,
                    'complex_min_complexity': 0.25,
                    'simple_max_words': 5,
                    'medium_min_words': 5,
                    'medium_max_words': 15,
                    'complex_min_words': 15,
                },
                'keywords': {
                    'question_words': ['what', 'why', 'how', 'when', 'where', 'who'],
                    'complexity_indicators': ['explain', 'analyze', 'compare', 'evaluate']
                }
            },
            'conservative': {
                'name': '保守配置',
                'description': '适用于生产环境的保守配置',
                'extends': 'base',  # 继承基础模板
                'thresholds': {
                    'simple_max_complexity': 0.08,  # 覆盖基础配置
                    'medium_max_complexity': 0.3,
                    'complex_min_complexity': 0.3,
                },
                'environment': ['production', 'staging']
            },
            'aggressive': {
                'name': '激进配置',
                'description': '适用于测试环境的激进配置',
                'extends': 'base',
                'thresholds': {
                    'simple_max_complexity': 0.05,
                    'medium_max_complexity': 0.2,
                    'complex_min_complexity': 0.2,
                    'simple_max_words': 3,
                    'medium_min_words': 3,
                    'medium_max_words': 10,
                    'complex_min_words': 10,
                },
                'environment': ['development', 'testing']
            },
            'balanced': {
                'name': '平衡配置',
                'description': '平衡性能和准确率的配置',
                'extends': 'base',
                'thresholds': {
                    'simple_max_complexity': 0.08,
                    'medium_max_complexity': 0.25,
                    'complex_min_complexity': 0.25,
                    'simple_max_words': 4,
                    'medium_min_words': 4,
                    'medium_max_words': 12,
                    'complex_min_words': 12,
                },
                'environment': ['production', 'staging']
            },
            'high_precision': {
                'name': '高精度配置',
                'description': '追求最高准确率的配置',
                'extends': 'conservative',
                'thresholds': {
                    'simple_max_complexity': 0.05,
                    'medium_max_complexity': 0.15,
                    'complex_min_complexity': 0.15,
                },
                'keywords': {
                    'question_words': ['what', 'why', 'how', 'when', 'where', 'who', 'which', 'whose',
                                     'explain', 'describe', 'compare', 'analyze', 'evaluate', 'discuss',
                                     '请问', '如何', '为什么', '什么是'],
                    'complexity_indicators': ['explain', 'analyze', 'compare', 'evaluate', 'discuss',
                                            'describe', 'why', 'how', 'relationship', 'difference',
                                            'similarity', 'impact', '优化', '性能', '架构']
                }
            }
        }

        # 设置继承关系
        for name, template in self.templates.items():
            if 'extends' in template:
                self.template_inheritance[name] = template['extends']

        # 加载条件模板
        self.conditional_templates = {
            'auto_scale': {
                'condition': 'system_load > 0.8',
                'template': 'aggressive',
                'description': '系统负载高时自动切换到激进配置'
            },
            'maintenance_mode': {
                'condition': 'maintenance_window',
                'template': 'conservative',
                'description': '维护窗口期间使用保守配置'
            },
            'peak_hours': {
                'condition': 'business_hours_peak',
                'template': 'high_precision',
                'description': '高峰期使用高精度配置'
            }
        }

    def get_template(self, name: str, resolve_inheritance: bool = True) -> Optional[Dict[str, Any]]:
        """获取配置模板（支持继承解析）"""
        template = self.templates.get(name)
        if not template or not resolve_inheritance:
            return template

        # 解析继承关系
        if 'extends' in template:
            parent_name = template['extends']
            parent_template = self.get_template(parent_name, resolve_inheritance=True)

            if parent_template:
                # 深度合并父模板
                resolved_template = self._deep_merge(parent_template.copy(), template.copy())
                resolved_template['resolved_from'] = [name]
                resolved_template['inheritance_chain'] = self._get_inheritance_chain(name)
                return resolved_template

        return template

    def _get_inheritance_chain(self, template_name: str) -> List[str]:
        """获取模板继承链"""
        chain = [template_name]
        current = template_name

        while current in self.template_inheritance:
            parent = self.template_inheritance[current]
            if parent in chain:  # 防止循环继承
                break
            chain.insert(0, parent)
            current = parent

        return chain

    def list_templates(self, include_inheritance: bool = True) -> List[Dict[str, Any]]:
        """列出所有模板"""
        templates = []
        for name, template in self.templates.items():
            template_info = {
                'name': name,
                'display_name': template['name'],
                'description': template['description'],
                'extends': template.get('extends'),
                'environment': template.get('environment', []),
                'inheritance_chain': self._get_inheritance_chain(name) if include_inheritance else None
            }
            templates.append(template_info)

        return templates

    def apply_template(self, config_manager, template_name: str, context: Dict[str, Any] = None):
        """应用配置模板（支持条件和继承）"""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"模板 {template_name} 不存在")

        # 检查环境条件
        if 'environment' in template and context and 'environment' in context:
            current_env = context['environment']
            allowed_envs = template['environment']
            if current_env not in allowed_envs:
                raise ValueError(f"模板 {template_name} 不适用于环境 {current_env}")

        # 应用阈值配置
        if 'thresholds' in template:
            for key, value in template['thresholds'].items():
                config_manager.update_threshold(key, value)

        # 应用关键词配置
        if 'keywords' in template:
            for category, keywords in template['keywords'].items():
                if isinstance(keywords, list):
                    for keyword in keywords:
                        config_manager.add_keyword(category, keyword)
                elif isinstance(keywords, dict):
                    # 处理嵌套关键词结构
                    for sub_category, sub_keywords in keywords.items():
                        if isinstance(sub_keywords, list):
                            for keyword in sub_keywords:
                                config_manager.add_keyword(f"{category}.{sub_category}", keyword)

        inheritance_info = ""
        if 'inheritance_chain' in template and len(template['inheritance_chain']) > 1:
            inheritance_info = f" (继承自: {' -> '.join(template['inheritance_chain'][:-1])})"

        print(f"✅ 已应用配置模板: {template['name']}{inheritance_info}")

    def get_recommended_template(self, context: Dict[str, Any]) -> str:
        """根据上下文推荐模板"""
        # 检查条件模板
        for condition_name, condition_config in self.conditional_templates.items():
            if self._evaluate_condition(condition_config['condition'], context):
                return condition_config['template']

        # 基于环境推荐
        environment = context.get('environment', 'development')
        load_level = context.get('system_load', 0.5)
        accuracy_requirement = context.get('accuracy_requirement', 'medium')

        if environment == 'production':
            if accuracy_requirement == 'high':
                return 'high_precision'
            elif load_level > 0.8:
                return 'conservative'
            else:
                return 'balanced'
        elif environment in ['development', 'testing']:
            return 'aggressive'
        else:
            return 'balanced'

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """评估条件表达式"""
        try:
            # 简单条件评估器（可以扩展为更复杂的表达式）
            if '>' in condition:
                parts = condition.split('>')
                var_name = parts[0].strip()
                threshold = float(parts[1].strip())
                return context.get(var_name, 0) > threshold
            elif 'business_hours_peak' in condition:
                # 检查是否为业务高峰期
                return self._is_business_peak_hour(context)
            elif 'maintenance_window' in condition:
                # 检查是否在维护窗口
                return context.get('maintenance_mode', False)

            return False
        except Exception:
            return False

    def _is_business_peak_hour(self, context: Dict[str, Any]) -> bool:
        """检查是否为业务高峰期"""
        # 简单的业务高峰期判断（9:00-18:00工作日）
        from datetime import datetime
        now = datetime.now()
        is_weekday = now.weekday() < 5  # 周一到周五
        is_business_hour = 9 <= now.hour <= 18
        return is_weekday and is_business_hour

    def create_custom_template(self, name: str, base_template: str,
                             customizations: Dict[str, Any],
                             description: str = "") -> bool:
        """创建自定义模板"""
        if name in self.templates:
            return False

        if base_template not in self.templates:
            return False

        # 基于基础模板创建
        base = self.templates[base_template]
        custom_template = {
            'name': name,
            'description': description or f"基于 {base['name']} 的自定义模板",
            'extends': base_template,
            **customizations
        }

        self.templates[name] = custom_template
        self.template_inheritance[name] = base_template

        print(f"✅ 已创建自定义模板: {name}")
        return True

    def export_template(self, template_name: str, file_path: str):
        """导出模板"""
        template = self.get_template(template_name, resolve_inheritance=True)
        if not template:
            raise ValueError(f"模板 {template_name} 不存在")

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(template, f, ensure_ascii=False, indent=2)
            print(f"✅ 模板已导出到: {file_path}")
        except Exception as e:
            print(f"❌ 模板导出失败: {e}")

    def import_template(self, file_path: str, template_name: str = None) -> str:
        """导入模板"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)

            name = template_name or template_data.get('name', f"imported_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            self.templates[name] = template_data

            if 'extends' in template_data:
                self.template_inheritance[name] = template_data['extends']

            print(f"✅ 模板已导入: {name}")
            return name
        except Exception as e:
            print(f"❌ 模板导入失败: {e}")
            return ""

    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并字典"""
        result = base.copy()

        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

class DynamicConfigManager:
    """完整的动态配置管理器"""

    def __init__(self, config_store: Optional[ConfigStore] = None):
        self.config = DynamicRoutingConfig()
        self.route_type_registry = DynamicRouteTypeRegistry()
        self.config_store = config_store or FileConfigStore("routing_config.json")
        self.config_validator = ConfigValidator()
        self.config_monitor = ConfigMonitor()
        self.template_manager = ConfigTemplateManager()

        # 加载持久化配置
        self.config.load_config(self.config_store)

    def get_routing_config(self) -> Dict[str, Any]:
        """获取完整的路由配置"""
        return {
            'thresholds': self.config.thresholds,
            'keywords': self.config.keywords,
            'routing_rules': self.config.routing_rules,
            'route_types': [
                {
                    'name': rt.name,
                    'description': rt.description,
                    'priority': rt.priority,
                    'enabled': rt.enabled
                }
                for rt in self.route_type_registry.get_all_route_types()
            ]
        }

    def add_config_source(self, source: 'ConfigSource'):
        """添加配置源"""
        self.config.add_config_source(source)

    def register_route_type(self, name: str, description: str, priority: int = 0, **metadata):
        """运行时注册新的路由类型"""
        route_type = RouteTypeDefinition(
            name=name,
            description=description,
            priority=priority,
            metadata=metadata
        )
        self.route_type_registry.register_route_type(route_type)

        # 记录配置变更
        if self.config_monitor:
            self.config_monitor.record_config_change(
                {'route_types': [name]},
            author="system",
            description=f"注册路由类型: {name}"
        )

    def update_routing_threshold(self, key: str, value: float):
        """运行时更新路由阈值"""
        # 验证配置更新
        if not self.config.validate_config_update(f'thresholds.{key}', value):
            raise ValueError(f"配置更新验证失败: {key} = {value}")

        self.config.update_threshold(key, value)

        # 持久化配置
        self.config.save_config()

        # 记录变更
        self.config_monitor.record_config_change(
            {'thresholds': {key: value}},
            author="system",
            description=f"更新阈值: {key} = {value}"
        )

    def add_routing_keyword(self, category: str, keyword: str):
        """运行时添加路由关键词"""
        self.config.add_keyword(category, keyword)

        # 持久化配置
        self.config.save_config()

        # 记录变更
        self.config_monitor.record_config_change(
            {'keywords': {category: [keyword]}},
            author="system",
            description=f"添加关键词: {category} -> {keyword}"
        )

    def apply_template(self, template_name: str):
        """应用配置模板"""
        self.template_manager.apply_template(self.config, template_name)

        # 持久化配置
        self.config.save_config()

        # 记录变更
        self.config_monitor.record_config_change(
            {'template_applied': template_name},
            author="system",
            description=f"应用配置模板: {template_name}"
        )

    def rollback_config(self, version: str):
        """回滚配置"""
        self.config.rollback_config(version)

        # 记录变更
        self.config_monitor.record_config_change(
            {'rollback_to': version},
            author="system",
            description=f"回滚配置到版本: {version}"
        )

    def get_config_status(self) -> Dict[str, Any]:
        """获取配置状态"""
        return {
            'current_config': {
                'thresholds_count': len(self.config.thresholds),
                'keywords_count': len(self.config.keywords),
                'route_types_count': len(self.route_type_registry.get_all_route_types())
            },
            'config_versions': self.config_store.get_config_versions()[:5],  # 最近5个版本
            'change_metrics': self.config_monitor.get_config_metrics(),
            'available_templates': self.template_manager.list_templates(),
            'last_updated': self.config._last_updated.isoformat() if self.config._last_updated else None
        }

    def export_config_documentation(self) -> str:
        """导出配置文档"""
        doc = []
        doc.append("# 动态路由配置文档")
        doc.append("")
        doc.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc.append("")

        # 路由类型
        doc.append("## 路由类型")
        for rt in self.route_type_registry.get_all_route_types():
            doc.append(f"- **{rt.name}**: {rt.description} (优先级: {rt.priority})")
        doc.append("")

        # 阈值配置
        doc.append("## 阈值配置")
        for key, value in self.config.thresholds.items():
            doc.append(f"- **{key}**: {value}")
        doc.append("")

        # 关键词配置
        doc.append("## 关键词配置")
        for category, keywords in self.config.keywords.items():
            if isinstance(keywords, list):
                doc.append(f"- **{category}**: {', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''}")
            elif isinstance(keywords, dict):
                doc.append(f"- **{category}**: {len(keywords)} 个子类别")
        doc.append("")

        # 配置模板
        doc.append("## 可用配置模板")
        for template in self.template_manager.list_templates():
            doc.append(f"- **{template['name']}**: {template['description']}")
        doc.append("")

        return "\n".join(doc)
