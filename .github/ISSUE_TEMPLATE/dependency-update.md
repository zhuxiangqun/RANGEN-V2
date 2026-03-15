---
name: "📦 依赖更新检查报告"
about: "自动生成的依赖更新报告"
title: "📦 依赖更新检查报告"
labels: ["dependencies", "automated"]
assignees: ""
---

# 📦 依赖更新检查报告

本报告由自动化维护任务生成，列出了项目中需要更新的依赖包。

## 📋 报告摘要

- **生成时间**: {{ date | date("YYYY-MM-DD HH:mm:ss") }}
- **项目**: RANGEN V2
- **分支**: {{ github.ref }}

## 🔍 发现的问题

### ⚠️ 需要更新的依赖

以下依赖包有可用的更新版本：

```markdown
| 包名 | 当前版本 | 最新版本 | 更新类型 | 优先级 |
|------|----------|----------|----------|--------|
| TODO | TODO | TODO | TODO | TODO |
```

### 📊 依赖统计

- 总依赖数: TODO
- 需要更新的依赖数: TODO
- 安全更新数: TODO
- 主要版本更新数: TODO

## 🛠️ 建议操作

### 1. 手动更新（推荐）

```bash
# 激活虚拟环境
source .venv/bin/activate

# 查看需要更新的包
pip list --outdated

# 更新特定包
pip install --upgrade <package_name>

# 更新所有包（谨慎使用）
pip install --upgrade -r requirements.txt
```

### 2. 使用自动化工具

```bash
# 使用 pip-review
pip install pip-review
pip-review --local --auto

# 或使用 pip-tools
pip install pip-tools
pip-compile --upgrade requirements.in
```

### 3. 创建 Pull Request

1. 创建新的功能分支: `git checkout -b chore/update-dependencies`
2. 更新依赖版本: 编辑 `pyproject.toml` 文件
3. 安装更新后的依赖: `pip install .[dev]`
4. 运行测试: `pytest tests/ -v`
5. 提交更改: `git commit -m "chore: update dependencies"`
6. 推送分支: `git push origin chore/update-dependencies`
7. 创建 Pull Request

## 🧪 测试建议

更新依赖后，请运行以下测试确保兼容性：

```bash
# 运行完整测试套件
pytest tests/ -v

# 运行类型检查
mypy src/

# 运行代码质量检查
pylint src/

# 运行安全扫描
bandit -r src/
safety check
```

## ⚠️ 注意事项

1. **主要版本更新**: 主要版本更新（如 1.x.x → 2.x.x）可能包含破坏性变更，请仔细阅读变更日志
2. **依赖冲突**: 更新某个包可能导致其他依赖的冲突，请测试完整的依赖树
3. **Python 版本兼容性**: 确保新版本与项目支持的 Python 版本兼容
4. **安全更新**: 优先处理标记为安全更新的依赖

## 📚 相关资源

- [PyPI - Python Package Index](https://pypi.org/)
- [pip documentation](https://pip.pypa.io/)
- [Python Packaging User Guide](https://packaging.python.org/)
- [Semantic Versioning](https://semver.org/)

## 🔄 自动化任务

本报告由 `.github/workflows/maintenance.yml` 工作流自动生成。

要手动触发依赖更新检查，请运行：

```bash
# 在 GitHub Actions 中手动触发
gh workflow run maintenance.yml
```

或通过 GitHub Web 界面：
1. 进入 "Actions" 标签页
2. 选择 "维护任务" 工作流
3. 点击 "Run workflow"

---

**提示**: 保持依赖更新是维护项目安全性和稳定性的重要部分。建议定期（每月）检查并更新依赖。

*本 Issue 由自动化系统生成，将在依赖更新后自动关闭。*