# 开发环境搭建指南

## 📖 概述

本指南详细介绍如何搭建RANGEN系统的开发环境，包括环境配置、依赖安装、开发工具设置和日常开发工作流程。

## 🎯 环境要求

### 系统要求
- **操作系统**：macOS 10.15+、Ubuntu 20.04+、Windows 10+（WSL2推荐）
- **Python版本**：Python 3.9 - 3.11（推荐3.9.x）
- **内存**：8GB RAM（推荐16GB+）
- **磁盘空间**：至少10GB可用空间
- **网络连接**：稳定的互联网连接（用于下载依赖和API调用）

### 开发工具要求
- **代码编辑器**：VS Code、PyCharm或任意支持Python的编辑器
- **终端**：支持bash/zsh的终端
- **Git**：版本控制系统
- **Docker**（可选）：用于容器化开发和测试

## 🚀 快速开始

### 1. 克隆代码库
```bash
# 克隆主仓库
git clone https://github.com/your-repo/RANGEN.git
cd RANGEN

# 或克隆到指定目录
git clone https://github.com/your-repo/RANGEN.git /path/to/your/project
cd /path/to/your/project
```

### 2. 设置Python虚拟环境
```bash
# 创建虚拟环境（推荐）
python3 -m venv venv

# 激活虚拟环境
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

# 验证虚拟环境
python --version
which python  # 应该指向venv目录
```

### 3. 安装核心依赖
```bash
# 安装基础依赖
pip install -r requirements.txt

# 安装开发依赖（可选，包含测试工具）
pip install pytest pytest-asyncio psutil coverage
```

### 4. 配置环境变量
```bash
# 复制示例配置文件
cp .env.example .env

# 编辑配置文件
# 使用你喜欢的编辑器编辑.env文件
nano .env  # 或 vim .env 或 code .env
```

### 5. 快速验证安装
```bash
# 运行快速测试
python scripts/quick_test.py

# 或运行快速启动脚本
python scripts/quick_start.py --api-port 8080 --web-port 8081
```

## 🔧 详细安装步骤

### Python环境配置

#### macOS环境
```bash
# 使用Homebrew安装Python
brew install python@3.9

# 验证安装
python3 --version  # 应该显示Python 3.9.x

# 安装pip（如果未安装）
python3 -m ensurepip --upgrade
```

#### Ubuntu/Debian环境
```bash
# 更新包列表
sudo apt update

# 安装Python和必要工具
sudo apt install python3.9 python3.9-venv python3-pip git

# 验证安装
python3.9 --version
```

#### Windows环境（使用WSL2）
```bash
# 在WSL2中安装Ubuntu
# 然后按照Ubuntu步骤操作

# 或使用Windows原生Python
# 从Python官网下载Python 3.9安装包
# https://www.python.org/downloads/
```

### 虚拟环境管理

#### 创建和管理虚拟环境
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

# 安装包到虚拟环境
pip install package-name

# 冻结依赖（生成requirements.txt）
pip freeze > requirements.txt

# 退出虚拟环境
deactivate
```

#### 使用virtualenvwrapper（可选）
```bash
# 安装virtualenvwrapper
pip install virtualenvwrapper

# 配置（添加到~/.bashrc或~/.zshrc）
export WORKON_HOME=$HOME/.virtualenvs
export PROJECT_HOME=$HOME/Projects
source /usr/local/bin/virtualenvwrapper.sh

# 创建新环境
mkvirtualenv rangen-dev --python=python3.9

# 激活环境
workon rangen-dev

# 列出所有环境
lsvirtualenv

# 删除环境
rmvirtualenv rangen-dev
```

### 依赖安装

#### 核心依赖安装
```bash
# 安装所有核心依赖
pip install -r requirements.txt

# 如果安装缓慢，可以使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 可选依赖安装
```bash
# LangGraph相关依赖
pip install -r requirements_langgraph.txt

# 可选功能依赖
pip install -r requirements-optional.txt

# 开发工具依赖
pip install pytest pytest-asyncio pytest-cov coverage black isort pylint mypy
```

#### 使用安装脚本
```bash
# 使用项目提供的安装脚本
# 安装pytest（测试框架）
bash scripts/install_pytest.sh

# 安装FastAPI（Web框架）
bash scripts/install_fastapi.sh

# 安装OpenTelemetry（监控）
bash scripts/install_opentelemetry.sh
```

### 环境变量配置

#### 基本配置
编辑`.env`文件，配置以下变量：

```ini
# .env文件示例

# ====================
# LLM提供商配置
# ====================

# LLM提供商（deepseek, openai, stepflash, mock）
LLM_PROVIDER=mock

# DeepSeek配置（如果使用deepseek）
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
REASONING_MODEL=deepseek-reasoner
VALIDATION_MODEL=deepseek-chat
CITATION_MODEL=deepseek-chat

# Step-3.5-Flash配置（如果使用stepflash）
STEPSFLASH_API_KEY=your_stepflash_api_key_here

# ====================
# 知识库配置
# ====================

VECTOR_STORE_PATH=./data/vector_store
EMBEDDING_MODEL=text-embedding-3-small

# ====================
# 系统配置
# ====================

LOG_LEVEL=INFO
ENVIRONMENT=development

# ====================
# 服务器配置
# ====================

API_PORT=8000
WEB_PORT=8501
DEBUG=true
```

#### 配置说明
1. **LLM_PROVIDER**：设置使用的LLM提供商
   - `mock`：使用模拟LLM，无需API密钥（推荐用于开发）
   - `deepseek`：使用DeepSeek API
   - `stepflash`：使用Step-3.5-Flash API
   - `openai`：使用OpenAI API

2. **API密钥**：根据选择的提供商配置相应API密钥

3. **开发模式建议**：使用`LLM_PROVIDER=mock`避免API调用费用

#### 环境变量验证
```bash
# 验证环境变量加载
python -c "import os; print('LLM_PROVIDER:', os.getenv('LLM_PROVIDER', '未设置'))"

# 检查所有环境变量
python scripts/check_config.py
```

### 数据库初始化

#### 向量数据库初始化
```bash
# 创建数据目录
mkdir -p data/vector_store

# 初始化向量数据库（如果需要）
python scripts/initialize_vector_kb.py

# 或使用简单初始化
python scripts/simple_build_vector_kb.py
```

#### 知识库数据导入
```bash
# 导入基准测试数据
python scripts/import_frames_benchmark.py

# 或导入示例数据
python scripts/populate_q3_q4.py
```

## 🛠️ 开发工具配置

### 代码编辑器配置

#### VS Code配置
创建`.vscode/settings.json`：

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.flake8Enabled": false,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": [
    "--line-length",
    "120"
  ],
  "python.sortImports.args": [
    "--profile",
    "black"
  ],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": "explicit"
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/.coverage": true,
    "**/htmlcov": true
  }
}
```

#### VS Code扩展推荐
- **Python**：微软官方Python支持
- **Python Docstring Generator**：自动生成文档字符串
- **Pylance**：Python语言服务器
- **Black Formatter**：代码格式化
- **isort**：导入排序
- **Python Test Explorer**：测试管理

### 代码质量工具

#### 代码格式化配置
```bash
# 安装格式化工具
pip install black isort

# 格式化所有Python文件
black src/
isort src/

# 检查格式化（不修改）
black --check src/
isort --check-only src/
```

#### 代码检查配置
```bash
# 安装代码检查工具
pip install pylint mypy

# 运行代码检查
pylint src/
mypy src/

# 使用项目配置运行检查
pylint --rcfile=.pylintrc src/
```

#### 预提交钩子配置
创建`.pre-commit-config.yaml`：

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black
        args: [--line-length=120]
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]
  
  - repo: https://github.com/pycqa/pylint
    rev: v3.0.1
    hooks:
      - id: pylint
        args:
          - --rcfile=.pylintrc
          - --fail-under=8.0
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.6.1
    hooks:
      - id: mypy
        args: [--ignore-missing-imports, --follow-imports=silent]
```

安装预提交钩子：
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

### 测试工具配置

#### 测试框架安装
```bash
# 使用安装脚本
bash scripts/install_pytest.sh

# 或手动安装
pip install pytest pytest-asyncio pytest-cov pytest-xdist
```

#### 测试配置文件
创建`pytest.ini`：

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    slow: Slow tests (require external APIs)
addopts = -v --tb=short -ra
asyncio_mode = auto
```

#### 测试运行配置
```bash
# 运行所有测试
pytest

# 运行单元测试
pytest -m unit

# 运行集成测试
pytest -m integration

# 生成覆盖率报告
pytest --cov=src --cov-report=html --cov-report=term

# 并行运行测试
pytest -n auto
```

## 🚀 启动开发服务器

### 启动API服务器
```bash
# 启动FastAPI服务器
python src/api/server.py

# 或使用uvicorn直接启动
uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000

# 启动后访问：http://localhost:8000
# API文档：http://localhost:8000/docs
```

### 启动Web界面
```bash
# 启动Streamlit界面
streamlit run src/ui/app.py

# 启动后访问：http://localhost:8501
```

### 启动统一服务器
```bash
# 使用快速启动脚本
python scripts/quick_start.py

# 或使用统一服务器脚本
python scripts/start_unified_server.py --port 8080

# 启动后访问：
# Web管理界面：http://localhost:8081
# REST API：http://localhost:8080/docs
```

### 启动监控面板
```bash
# 启动监控系统
python scripts/start_operations_monitoring.py

# 或启动自主监控
python scripts/start_autonomous_monitoring.py
```

## 🔍 验证开发环境

### 环境验证脚本
```bash
# 运行环境验证
python scripts/check_config.py

# 验证导入
python tests/test_01_imports.py

# 验证配置
python tests/test_02_config.py
```

### 快速测试验证
```bash
# 运行快速测试
python tests/quick_test.py

# 运行简单集成测试
python tests/simple_system_test.py

# 验证核心功能
python scripts/test_end_to_end.py
```

### 性能验证
```bash
# 运行性能基准测试
python scripts/test_performance_benchmark_simple.py

# 或运行完整性能测试
pytest tests/test_langgraph_performance_benchmark.py -v
```

## 📝 日常开发工作流程

### 1. 开始新功能开发
```bash
# 激活虚拟环境
source venv/bin/activate

# 创建新分支
git checkout -b feature/new-feature

# 更新依赖（如果需要）
pip install -r requirements.txt

# 启动开发服务器
python src/api/server.py
```

### 2. 编写和测试代码
```bash
# 运行相关测试
pytest tests/test_related_module.py -v

# 运行代码检查
pylint src/module/

# 格式化代码
black src/module/
isort src/module/
```

### 3. 提交代码
```bash
# 添加修改
git add .

# 提交代码
git commit -m "feat: 添加新功能"

# 运行预提交钩子
pre-commit run --all-files

# 推送代码
git push origin feature/new-feature
```

### 4. 代码审查和合并
- 创建Pull Request
- 等待代码审查
- 解决审查意见
- 合并到主分支

## ⚠️ 常见问题解决

### 依赖安装问题

#### 问题1：pip安装失败
```bash
# 解决方案1：升级pip
python -m pip install --upgrade pip

# 解决方案2：使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 解决方案3：使用虚拟环境
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 问题2：特定包安装失败
```bash
# 尝试单独安装
pip install package-name --no-cache-dir

# 或使用指定版本
pip install package-name==specific.version

# 查看错误信息，可能需要系统依赖
# 例如：某些包可能需要gcc或libssl-dev
```

### 环境变量问题

#### 问题：环境变量未生效
```bash
# 解决方案1：重新加载环境变量
source .env  # 如果.env文件可以直接source

# 解决方案2：使用export设置
export LLM_PROVIDER=mock
export LOG_LEVEL=DEBUG

# 解决方案3：检查.env文件格式
# 确保是KEY=VALUE格式，没有空格和引号
```

### 服务器启动问题

#### 问题1：端口被占用
```bash
# 检查端口占用
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# 终止占用进程
kill -9 <PID>

# 或使用其他端口
python src/api/server.py --port 8080
```

#### 问题2：导入错误
```bash
# 确保在项目根目录
cd /path/to/RANGEN

# 确保虚拟环境激活
source venv/bin/activate

# 检查Python路径
python -c "import sys; print(sys.path)"
```

### 测试问题

#### 问题：测试失败或超时
```bash
# 运行单个测试排查
pytest tests/test_specific.py::test_function -v -s

# 增加超时时间
python tests/run_tests_with_timeout.py 600

# 使用模拟模式（避免API调用）
export LLM_PROVIDER=mock
pytest tests/test_module.py
```

## 🔧 高级配置

### Docker开发环境
```dockerfile
# Dockerfile.dev
FROM python:3.9-slim

WORKDIR /app

# 复制依赖文件
COPY requirements.txt .
COPY requirements-dev.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# 复制代码
COPY . .

# 设置环境变量
ENV PYTHONPATH=/app
ENV LLM_PROVIDER=mock
ENV LOG_LEVEL=DEBUG

# 暴露端口
EXPOSE 8000 8501

# 启动命令
CMD ["python", "src/api/server.py"]
```

使用Docker Compose：
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    environment:
      - LLM_PROVIDER=mock
      - LOG_LEVEL=DEBUG
    volumes:
      - .:/app
      - ./data:/app/data
    command: python src/api/server.py

  ui:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8501:8501"
    environment:
      - LLM_PROVIDER=mock
    volumes:
      - .:/app
    command: streamlit run src/ui/app.py
```

### 数据库配置

#### 使用SQLite（默认）
```ini
# .env配置
DATABASE_URL=sqlite:///./data/rangen.db
```

#### 使用PostgreSQL（高级）
```ini
# .env配置
DATABASE_URL=postgresql://user:password@localhost:5432/rangen
```

### 监控和日志配置

#### 日志配置
```python
# 在代码中配置日志
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/rangen.log'),
        logging.StreamHandler()
    ]
)
```

#### 性能监控
```bash
# 启用性能监控
export ENABLE_PERFORMANCE_MONITORING=true
export ENABLE_OPENTELEMETRY=true

# 启动监控
python scripts/start_autonomous_monitoring.py
```

## 📚 学习资源

### 官方文档
- [RANGEN系统架构](../architecture/README.md)
- [API参考](../development/api-reference/rest-api.md)
- [开发指南](../development/README.md)

### 外部资源
- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [LangGraph官方文档](https://langchain-ai.github.io/langgraph/)
- [Streamlit官方文档](https://docs.streamlit.io/)
- [Pytest官方文档](https://docs.pytest.org/)

### 项目资源
- [测试工具指南](../../tests/README_TEST_TOOLS.md)
- [代码规范指南](../development/code-style-guide.md)
- [单元测试指南](../testing/unit-testing.md)

## 🔄 更新和维护

### 更新依赖
```bash
# 更新所有依赖
pip install --upgrade -r requirements.txt

# 生成新的requirements.txt
pip freeze > requirements.txt

# 更新开发依赖
pip install --upgrade pytest black isort pylint mypy
```

### 环境维护
```bash
# 清理虚拟环境
deactivate
rm -rf venv

# 重新创建环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 清理缓存
rm -rf __pycache__/
rm -rf .pytest_cache/
rm -rf .coverage
rm -rf htmlcov/
```

### 数据维护
```bash
# 备份数据
cp -r data/ data_backup_$(date +%Y%m%d)

# 清理临时文件
rm -rf data/vector_store/cache/
rm -rf data/temp/

# 重建知识库
python scripts/rebuild_knowledge_base.py
```

---

*最后更新：2026-03-07*  
*文档版本：1.0.0*  
*维护团队：RANGEN开发工作组*