# Pytest 安装指南

## 📦 安装方法

### 方法1：使用安装脚本（推荐）

```bash
bash scripts/install_pytest.sh
```

### 方法2：手动安装

```bash
# 安装 pytest
python3 -m pip install pytest

# 安装 pytest-asyncio（用于异步测试）
python3 -m pip install pytest-asyncio

# 安装 psutil（用于性能测试）
python3 -m pip install psutil
```

### 方法3：使用 requirements 文件

如果项目有 `requirements.txt` 或 `requirements-test.txt`，可以添加：

```txt
pytest>=7.0.0
pytest-asyncio>=0.21.0
psutil>=5.9.0
```

然后安装：

```bash
python3 -m pip install -r requirements.txt
```

## ✅ 验证安装

安装完成后，验证安装：

```bash
python3 -m pytest --version
```

应该看到类似输出：
```
pytest 7.x.x
```

## 🧪 运行测试

安装完成后，可以运行测试：

```bash
# 运行集成测试
pytest tests/test_langgraph_integration.py -v

# 运行性能基准测试
pytest tests/test_langgraph_performance_benchmark.py -v

# 运行编排追踪验证测试
pytest tests/test_orchestration_tracking.py -v

# 运行所有测试
pytest tests/ -v
```

## 📝 注意事项

1. **Python 版本**：确保使用 Python 3.8 或更高版本
2. **虚拟环境**：建议在虚拟环境中安装
3. **权限问题**：如果遇到权限问题，可以使用 `--user` 参数：
   ```bash
   python3 -m pip install --user pytest pytest-asyncio psutil
   ```

## 🔧 故障排除

### 问题1：找不到 pytest 命令

**解决方案**：
- 使用 `python3 -m pytest` 而不是 `pytest`
- 或者确保 pytest 在 PATH 中

### 问题2：权限错误

**解决方案**：
```bash
python3 -m pip install --user pytest pytest-asyncio psutil
```

### 问题3：网络问题

**解决方案**：
- 使用国内镜像源：
  ```bash
  python3 -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pytest pytest-asyncio psutil
  ```

## 📚 相关文档

- [Pytest 官方文档](https://docs.pytest.org/)
- [Pytest-asyncio 文档](https://pytest-asyncio.readthedocs.io/)
- [测试执行指南](../implementation/test_execution_guide.md)

