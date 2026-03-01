# 模型配置管理

## 配置优先级
1. 环境变量 (最高优先级)
2. 配置文件 `model_settings.json`
3. 默认配置 (最低优先级)

## 环境变量
- `EMBEDDING_DIMENSION`: 设置embedding维度
- `EMBEDDING_MODEL`: 设置模型名称
- `MODEL_DEVICE`: 设置模型设备 (cpu/cuda/mps)

## 配置文件
复制 `model_settings.example.json` 为 `model_settings.json` 并修改配置

## 代码使用
```python
from src.utils.unified_config_center import get_embedding_dimension
dimension = get_embedding_dimension()  # 自动获取配置的维度
```
