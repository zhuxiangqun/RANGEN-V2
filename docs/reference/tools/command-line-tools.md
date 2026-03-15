# 🛠️ 命令行工具参考指南

> RANGEN 系统的完整命令行工具集合和使用指南

## 📋 概述

RANGEN 系统提供了丰富的命令行工具，涵盖系统管理、性能测试、数据处理、监控诊断等多个方面。本文档详细介绍了每个工具的功能、参数和使用方法。

### 1.1 文档目标
- 提供所有命令行工具的完整参考
- 解释每个工具的用途和适用场景
- 提供详细的使用示例和最佳实践
- 帮助用户高效使用系统功能

### 1.2 目标读者
- 系统管理员和运维工程师
- 开发者和测试工程师
- 数据科学家和研究人员
- 系统集成商和合作伙伴

## 🚀 安装和配置

### 2.1 环境要求
- Python 3.9+
- 已安装的 RANGEN 系统
- 必要的环境变量配置

### 2.2 安装方式
#### 2.2.1 从源代码安装
```bash
# 克隆仓库
git clone https://github.com/your-repo/RANGEN.git
cd RANGEN

# 安装依赖
pip install -r requirements.txt

# 安装开发版本
pip install -e .
```

#### 2.2.2 配置环境变量
```bash
# 复制环境模板
cp .env.example .env

# 编辑环境变量
vim .env

# 重要环境变量
export DEEPSEEK_API_KEY="your-api-key"
export STEPSFLASH_API_KEY="your-step-flash-key"
export OPENAI_API_KEY="your-openai-key"
export LLM_PROVIDER="deepseek"  # 默认LLM提供商
```

### 2.3 验证安装
```bash
# 检查Python环境
python --version

# 检查RANGEN安装
python -c "import src; print('RANGEN 安装成功')"

# 运行简单测试
python scripts/quick_start.py --help
```

## 🗂️ 工具分类

RANGEN 的命令行工具可分为以下六大类：

| 类别 | 工具数量 | 主要用途 | 关键工具 |
|------|----------|----------|----------|
| 系统启动与管理 | 8 | 启动、停止、监控系统服务 | `start_unified_server.py`, `stop_all_services.sh` |
| 性能测试与监控 | 12 | 性能基准测试、监控指标 | `run_performance_benchmark.py`, `run_quality_benchmark.py` |
| 数据管理与知识库 | 10 | 数据导入导出、向量数据库管理 | `import_knowledge_base.py`, `export_data.py` |
| 迁移与部署 | 6 | 版本迁移、环境部署 | `migrate_database.py`, `deploy_to_production.sh` |
| 测试与验证 | 15 | 单元测试、集成测试、端到端测试 | `run_tests.py`, `validate_configuration.py` |
| 诊断与调试 | 8 | 日志分析、错误诊断、性能调试 | `analyze_logs.py`, `debug_agent.py` |

### 3.1 工具位置
所有命令行工具主要位于以下位置：

```
scripts/                    # 主要脚本目录
  ├── quick_start.py        # 快速启动工具
  ├── start_unified_server.py  # 统一服务器启动
  ├── run_performance_benchmark.py  # 性能基准测试
  ├── run_quality_benchmark.py      # 质量基准测试
  ├── import_knowledge_base.py      # 知识库导入
  ├── export_data.py                # 数据导出
  ├── migrate_database.py           # 数据库迁移
  ├── run_tests.py                  # 运行测试
  └── analyze_logs.py               # 日志分析

knowledge_management_system/scripts/  # 知识管理脚本
  ├── build_vector_store.py          # 构建向量存储
  ├── query_vector_store.py          # 查询向量存储
  └── manage_embeddings.py           # 管理嵌入

tests/                      # 测试相关脚本
  ├── run_integration_tests.py      # 集成测试
  └── run_e2e_tests.py              # 端到端测试
```

## 📖 详细工具参考

### 4.1 系统启动与管理工具

#### 4.1.1 `quick_start.py` - 快速启动工具
快速启动 RANGEN 系统的完整服务栈。

**基本用法:**
```bash
python scripts/quick_start.py [选项]
```

**选项:**
| 选项 | 简写 | 默认值 | 描述 |
|------|------|--------|------|
| `--mode` | `-m` | `development` | 启动模式: `development`, `production`, `test` |
| `--services` | `-s` | `all` | 启动的服务: `all`, `api`, `ui`, `monitoring` |
| `--port` | `-p` | 8000 | API 服务器端口 |
| `--ui-port` | `-u` | 8501 | Streamlit UI 端口 |
| `--verbose` | `-v` | `False` | 详细输出模式 |
| `--skip-deps` | 无 | `False` | 跳过依赖检查 |
| `--help` | `-h` | 无 | 显示帮助信息 |

**示例:**
```bash
# 启动开发环境所有服务
python scripts/quick_start.py --mode development

# 只启动 API 服务
python scripts/quick_start.py --services api --port 8080

# 启动生产环境，详细输出
python scripts/quick_start.py --mode production --verbose
```

**高级用法:**
```bash
# 自定义配置文件
python scripts/quick_start.py --config custom_config.yaml

# 指定日志级别
python scripts/quick_start.py --log-level debug

# 后台运行
python scripts/quick_start.py --daemon
```

#### 4.1.2 `start_unified_server.py` - 统一服务器启动
启动包含所有核心组件的统一服务器。

**基本用法:**
```bash
python scripts/start_unified_server.py [选项]
```

**选项:**
| 选项 | 简写 | 默认值 | 描述 |
|------|------|--------|------|
| `--host` | `-H` | `0.0.0.0` | 服务器监听地址 |
| `--port` | `-p` | 8000 | 服务器端口 |
| `--workers` | `-w` | 4 | 工作进程数量 |
| `--reload` | 无 | `False` | 开发模式热重载 |
| `--log-level` | `-l` | `info` | 日志级别: `debug`, `info`, `warning`, `error` |
| `--config` | `-c` | `config/server_config.yaml` | 配置文件路径 |
| `--help` | `-h` | 无 | 显示帮助信息 |

**示例:**
```bash
# 启动生产服务器
python scripts/start_unified_server.py --host 0.0.0.0 --port 8000 --workers 8

# 启动开发服务器（带热重载）
python scripts/start_unified_server.py --reload --log-level debug

# 使用自定义配置
python scripts/start_unified_server.py --config /path/to/config.yaml
```

#### 4.1.3 `stop_all_services.sh` - 停止所有服务
停止所有正在运行的 RANGEN 服务。

**基本用法:**
```bash
./scripts/stop_all_services.sh [选项]
```

**选项:**
| 选项 | 简写 | 默认值 | 描述 |
|------|------|--------|------|
| `--force` | `-f` | `False` | 强制停止进程 |
| `--verbose` | `-v` | `False` | 详细输出模式 |
| `--pid-file` | `-p` | `var/run/pids.txt` | PID 文件路径 |

**示例:**
```bash
# 正常停止服务
./scripts/stop_all_services.sh

# 强制停止所有相关进程
./scripts/stop_all_services.sh --force

# 详细输出停止过程
./scripts/stop_all_services.sh --verbose
```

#### 4.1.4 `check_services.py` - 服务状态检查
检查所有服务的运行状态和健康状况。

**基本用法:**
```bash
python scripts/check_services.py [选项]
```

**选项:**
| 选项 | 简写 | 默认值 | 描述 |
|------|------|--------|------|
| `--services` | `-s` | `all` | 检查的服务列表 |
| `--format` | `-f` | `table` | 输出格式: `table`, `json`, `yaml` |
| `--timeout` | `-t` | 5 | 检查超时时间（秒） |
| `--retries` | `-r` | 3 | 重试次数 |

**示例:**
```bash
# 检查所有服务状态
python scripts/check_services.py

# 检查特定服务（JSON格式输出）
python scripts/check_services.py --services api,ui,monitoring --format json

# 检查数据库连接
python scripts/check_services.py --services database
```

### 4.2 性能测试与监控工具

#### 4.2.1 `run_performance_benchmark.py` - 性能基准测试
运行全面的性能基准测试，评估系统性能。

**基本用法:**
```bash
python scripts/run_performance_benchmark.py [选项]
```

**选项:**
| 选项 | 简写 | 默认值 | 描述 |
|------|------|--------|------|
| `--scenario` | `-s` | `medium_load` | 测试场景: `light_load`, `medium_load`, `heavy_load`, `spike_load` |
| `--duration` | `-d` | 300 | 测试持续时间（秒） |
| `--users` | `-u` | 20 | 并发用户数 |
| `--requests` | `-r` | 500 | 总请求数 |
| `--output` | `-o` | `performance_report.json` | 输出文件路径 |
| `--format` | `-f` | `json` | 输出格式: `json`, `html`, `csv` |
| `--verbose` | `-v` | `False` | 详细输出模式 |
| `--help` | `-h` | 无 | 显示帮助信息 |

**示例:**
```bash
# 运行中等负载测试
python scripts/run_performance_benchmark.py --scenario medium_load

# 自定义负载测试
python scripts/run_performance_benchmark.py --users 50 --requests 1000 --duration 600

# 生成 HTML 报告
python scripts/run_performance_benchmark.py --output report.html --format html
```

**测试场景说明:**
- `light_load`: 5 并发用户，100 请求，5 分钟 - 模拟正常使用
- `medium_load`: 20 并发用户，500 请求，10 分钟 - 模拟高峰期
- `heavy_load`: 50 并发用户，1000 请求，15 分钟 - 压力测试
- `spike_load`: 100 并发用户，2000 请求，20 分钟 - 突发高负载

#### 4.2.2 `run_quality_benchmark.py` - 质量基准测试
测试系统的回答质量和推理能力。

**基本用法:**
```bash
python run_quality_benchmark.py [选项]
```

**选项:**
| 选项 | 简写 | 默认值 | 描述 |
|------|------|--------|------|
| `--real` | `-r` | `False` | 使用真实 LLM (否则使用模拟) |
| `--queries` | `-q` | 5 | 测试查询数量 |
| `--output` | `-o` | `quality_report.json` | 输出文件路径 |
| `--verbose` | `-v` | `False` | 详细输出模式 |

**示例:**
```bash
# 使用模拟 LLM 运行测试
python run_quality_benchmark.py

# 使用真实 LLM 运行测试
python run_quality_benchmark.py --real

# 运行更多查询
python run_quality_benchmark.py --queries 20 --output detailed_report.json
```

#### 4.2.3 `monitor_system.py` - 实时系统监控
实时监控系统性能和资源使用情况。

**基本用法:**
```bash
python scripts/monitor_system.py [选项]
```

**选项:**
| 选项 | 简写 | 默认值 | 描述 |
|------|------|--------|------|
| `--interval` | `-i` | 5 | 监控间隔（秒） |
| `--duration` | `-d` | 300 | 监控持续时间（秒） |
| `--metrics` | `-m` | `all` | 监控指标: `cpu`, `memory`, `disk`, `network`, `response_time` |
| `--output` | `-o` | 无 | 输出文件路径（如指定则保存） |
| `--dashboard` | 无 | `False` | 启动 Web 仪表板 |

**示例:**
```bash
# 实时监控系统
python scripts/monitor_system.py

# 监控特定指标，每秒更新
python scripts/monitor_system.py --interval 1 --metrics cpu,memory

# 启动 Web 仪表板
python scripts/monitor_system.py --dashboard --port 8888
```

#### 4.2.4 `analyze_performance_logs.py` - 性能日志分析
分析性能日志文件，生成性能报告。

**基本用法:**
```bash
python scripts/analyze_performance_logs.py [选项] <日志文件>
```

**选项:**
| 选项 | 简写 | 默认值 | 描述 |
|------|------|--------|------|
| `--time-range` | `-t` | `all` | 时间范围: `today`, `yesterday`, `last_week`, 或自定义格式 |
| `--aggregate` | `-a` | `hour` | 聚合粒度: `minute`, `hour`, `day` |
| `--output` | `-o` | `performance_analysis.html` | 输出文件路径 |
| `--format` | `-f` | `html` | 输出格式: `html`, `json`, `csv` |
| `--help` | `-h` | 无 | 显示帮助信息 |

**示例:**
```bash
# 分析今天的日志
python scripts/analyze_performance_logs.py logs/performance.log --time-range today

# 分析上周日志，按小时聚合
python scripts/analyze_performance_logs.py logs/performance.log --time-range last_week --aggregate hour

# 生成 JSON 报告
python scripts/analyze_performance_logs.py logs/performance.log --format json --output report.json
```

### 4.3 数据管理与知识库工具

#### 4.3.1 `import_knowledge_base.py` - 知识库导入
导入文档、网页或其他数据源到知识库。

**基本用法:**
```bash
python scripts/import_knowledge_base.py [选项] <数据源>
```

**选项:**
| 选项 | 简写 | 默认值 | 描述 |
|------|------|--------|------|
| `--format` | `-f` | `auto` | 数据格式: `pdf`, `html`, `txt`, `md`, `csv`, `json` |
| `--collection` | `-c` | `default` | 向量存储集合名称 |
| `--chunk-size` | `-s` | 1000 | 文本分块大小 |
| `--overlap` | `-o` | 200 | 分块重叠大小 |
| `--parallel` | `-p` | 4 | 并行处理数量 |
| `--verbose` | `-v` | `False` | 详细输出模式 |

**数据源支持:**
- 单个文件: `document.pdf`, `data.csv`
- 目录: `documents/`, `data/`
- URL: `https://example.com/document.html`
- 通配符: `documents/*.pdf`

**示例:**
```bash
# 导入单个 PDF 文件
python scripts/import_knowledge_base.py document.pdf --format pdf

# 导入整个目录
python scripts/import_knowledge_base.py data/ --format auto --parallel 8

# 导入网页内容
python scripts/import_knowledge_base.py https://example.com --format html

# 自定义分块参数
python scripts/import_knowledge_base.py documents/ --chunk-size 2000 --overlap 500
```

#### 4.3.2 `export_data.py` - 数据导出工具
导出系统数据到各种格式。

**基本用法:**
```bash
python scripts/export_data.py [选项] <数据类型>
```

**选项:**
| 选项 | 简写 | 默认值 | 描述 |
|------|------|--------|------|
| `--format` | `-f` | `json` | 导出格式: `json`, `csv`, `sql`, `parquet` |
| `--output` | `-o` | 无 | 输出文件路径（默认基于类型和时间） |
| `--limit` | `-l` | 无 | 限制导出记录数 |
| `--since` | `-s` | `2024-01-01` | 导出从此日期之后的数据 |
| `--until` | `-u` | 当前时间 | 导出到此日期之前的数据 |

**支持的数据类型:**
- `conversations`: 对话记录
- `queries`: 查询日志
- `agents`: 智能体配置和状态
- `knowledge`: 知识库内容
- `metrics`: 性能指标
- `all`: 所有数据类型

**示例:**
```bash
# 导出对话记录到 JSON
python scripts/export_data.py conversations --format json --output conversations.json

# 导出最近7天的查询日志
python scripts/export_data.py queries --since 7d --format csv

# 导出所有数据到 SQLite
python scripts/export_data.py all --format sql --output backup.db
```

#### 4.3.3 `build_vector_store.py` - 构建向量存储
从原始数据构建向量数据库。

**基本用法:**
```bash
python knowledge_management_system/scripts/build_vector_store.py [选项]
```

**选项:**
| 选项 | 简写 | 默认值 | 描述 |
|------|------|--------|------|
| `--input` | `-i` | `data/documents/` | 输入数据目录 |
| `--output` | `-o` | `data/vector_store/` | 输出向量存储目录 |
| `--model` | `-m` | `text-embedding-ada-002` | 嵌入模型名称 |
| `--batch-size` | `-b` | 100 | 批处理大小 |
| `--dimension` | `-d` | 1536 | 向量维度 |
| `--recreate` | `-r` | `False` | 重新创建向量存储 |

**示例:**
```bash
# 构建向量存储
python knowledge_management_system/scripts/build_vector_store.py

# 使用自定义模型和参数
python knowledge_management_system/scripts/build_vector_store.py --model all-MiniLM-L6-v2 --dimension 384

# 重新构建向量存储
python knowledge_management_system/scripts/build_vector_store.py --recreate --input new_data/
```

#### 4.3.4 `query_vector_store.py` - 向量存储查询
查询向量数据库，查找相关内容。

**基本用法:**
```bash
python knowledge_management_system/scripts/query_vector_store.py [选项] <查询文本>
```

**选项:**
| 选项 | 简写 | 默认值 | 描述 |
|------|------|--------|------|
| `--collection` | `-c` | `default` | 集合名称 |
| `--limit` | `-l` | 5 | 返回结果数量 |
| `--threshold` | `-t` | 0.7 | 相似度阈值 |
| `--format` | `-f` | `table` | 输出格式: `table`, `json`, `text` |
| `--store` | `-s` | `data/vector_store/` | 向量存储路径 |

**示例:**
```bash
# 查询向量存储
python knowledge_management_system/scripts/query_vector_store.py "机器学习的基本概念"

# 返回更多结果
python knowledge_management_system/scripts/query_vector_store.py "深度学习" --limit 10 --threshold 0.8

# JSON 格式输出
python knowledge_management_system/scripts/query_vector_store.py "神经网络" --format json
```

### 4.4 迁移与部署工具

#### 4.4.1 `migrate_database.py` - 数据库迁移
执行数据库架构迁移和数据迁移。

**基本用法:**
```bash
python scripts/migrate_database.py [选项] <迁移命令>
```

**选项:**
| 选项 | 简写 | 默认值 | 描述 |
|------|------|--------|------|
| `--database` | `-d` | `sqlite:///data/rangen.db` | 数据库连接字符串 |
| `--target` | `-t` | `head` | 目标迁移版本 |
| `--revision` | `-r` | 无 | 特定修订版本 |
| `--dry-run` | 无 | `False` | 试运行，不实际执行 |
| `--verbose` | `-v` | `False` | 详细输出模式 |

**迁移命令:**
- `upgrade`: 升级到最新版本
- `downgrade`: 降级到指定版本
- `current`: 显示当前版本
- `history`: 显示迁移历史
- `revision`: 创建新的迁移版本

**示例:**
```bash
# 升级到最新版本
python scripts/migrate_database.py upgrade

# 降级到特定版本
python scripts/migrate_database.py downgrade --revision abc123

# 显示迁移历史
python scripts/migrate_database.py history

# 创建新迁移
python scripts/migrate_database.py revision --message "添加用户表"
```

#### 4.4.2 `deploy_to_production.sh` - 生产环境部署
自动化部署脚本，用于生产环境。

**基本用法:**
```bash
./scripts/deploy_to_production.sh [选项]
```

**选项:**
| 选项 | 简写 | 默认值 | 描述 |
|------|------|--------|------|
| `--environment` | `-e` | `production` | 目标环境: `staging`, `production` |
| `--version` | `-v` | `latest` | 部署版本 |
| `--config` | `-c` | `config/production.yaml` | 配置文件 |
| `--skip-tests` | 无 | `False` | 跳过测试 |
| `--force` | `-f` | `False` | 强制部署 |

**示例:**
```bash
# 部署最新版本到生产环境
./scripts/deploy_to_production.sh

# 部署特定版本到预发布环境
./scripts/deploy_to_production.sh --environment staging --version v1.2.3

# 跳过测试的强制部署
./scripts/deploy_to_production.sh --force --skip-tests
```

#### 4.4.3 `setup_environment.py` - 环境设置
设置和配置系统环境。

**基本用法:**
```bash
python scripts/setup_environment.py [选项]
```

**选项:**
| 选项 | 简写 | 默认值 | 描述 |
|------|------|--------|------|
| `--environment` | `-e` | `development` | 环境类型: `development`, `staging`, `production` |
| `--components` | `-c` | `all` | 设置组件: `database`, `vector_store`, `cache`, `monitoring` |
| `--interactive` | `-i` | `True` | 交互式设置 |
| `--force` | `-f` | `False` | 强制重新设置 |

**示例:**
```bash
# 交互式设置开发环境
python scripts/setup_environment.py

# 设置生产环境所有组件
python scripts/setup_environment.py --environment production --components all

# 非交互式设置数据库和缓存
python scripts/setup_environment.py --environment staging --components database,cache --interactive false
```

### 4.5 测试与验证工具

#### 4.5.1 `run_tests.py` - 运行测试套件
运行完整的测试套件。

**基本用法:**
```bash
python scripts/run_tests.py [选项]
```

**选项:**
| 选项 | 简写 | 默认值 | 描述 |
|------|------|--------|------|
| `--type` | `-t` | `all` | 测试类型: `unit`, `integration`, `e2e`, `performance`, `all` |
| `--pattern` | `-p` | `*` | 测试文件模式 |
| `--coverage` | `-c` | `False` | 生成覆盖率报告 |
| `--parallel` | 无 | `False` | 并行运行测试 |
| `--verbose` | `-v` | `False` | 详细输出模式 |
| `--fail-fast` | `-f` | `False` | 快速失败模式 |

**示例:**
```bash
# 运行所有测试
python scripts/run_tests.py

# 只运行单元测试
python scripts/run_tests.py --type unit

# 运行特定测试文件
python scripts/run_tests.py --pattern test_agent*.py

# 生成覆盖率报告
python scripts/run_tests.py --coverage --output coverage.html
```

#### 4.5.2 `run_integration_tests.py` - 集成测试
运行系统集成测试。

**基本用法:**
```bash
python tests/run_integration_tests.py [选项]
```

**选项:**
| 选项 | 简写 | 默认值 | 描述 |
|------|------|--------|------|
| `--modules` | `-m` | `all` | 测试模块: `agents`, `api`, `database`, `llm` |
| `--timeout` | `-t` | 60 | 测试超时时间（秒） |
| `--retry` | `-r` | 3 | 失败重试次数 |
| `--report` | 无 | `False` | 生成详细测试报告 |

**示例:**
```bash
# 运行所有集成测试
python tests/run_integration_tests.py

# 测试特定模块
python tests/run_integration_tests.py --modules agents,api

# 生成测试报告
python tests/run_integration_tests.py --report --output integration_report.html
```

#### 4.5.3 `run_e2e_tests.py` - 端到端测试
运行端到端系统测试。

**基本用法:**
```bash
python tests/run_e2e_tests.py [选项]
```

**选项:**
| 选项 | 简写 | 默认值 | 描述 |
|------|------|--------|------|
| `--scenarios` | `-s` | `all` | 测试场景: `chat`, `reasoning`, `retrieval`, `workflow` |
| `--parallel` | `-p` | `False` | 并行运行场景 |
| `--headless` | `-h` | `True` | 无头模式（无UI） |
| `--screenshots` | 无 | `False` | 失败时截屏 |

**示例:**
```bash
# 运行所有端到端测试
python tests/run_e2e_tests.py

# 测试特定场景
python tests/run_e2e_tests.py --scenarios chat,reasoning

# 启用截屏和详细输出
python tests/run_e2e_tests.py --screenshots --verbose
```

#### 4.5.4 `validate_configuration.py` - 配置验证
验证系统配置文件的有效性。

**基本用法:**
```bash
python scripts/validate_configuration.py [选项] <配置文件>
```

**选项:**
| 选项 | 简写 | 默认值 | 描述 |
|------|------|--------|------|
| `--strict` | `-s` | `False` | 严格模式（检查所有字段） |
| `--fix` | `-f` | `False` | 自动修复常见问题 |
| `--output` | `-o` | 无 | 输出验证报告 |
| `--format` | 无 | `text` | 报告格式: `text`, `json`, `yaml` |

**示例:**
```bash
# 验证主配置文件
python scripts/validate_configuration.py config/config.yaml

# 严格验证并自动修复
python scripts/validate_configuration.py config/config.yaml --strict --fix

# 生成 JSON 验证报告
python scripts/validate_configuration.py config/config.yaml --output validation.json --format json
```

### 4.6 诊断与调试工具

#### 4.6.1 `analyze_logs.py` - 日志分析
分析和聚合系统日志。

**基本用法:**
```bash
python scripts/analyze_logs.py [选项] <日志文件或目录>
```

**选项:**
| 选项 | 简写 | 默认值 | 描述 |
|------|------|--------|------|
| `--time-range` | `-t` | `today` | 时间范围: `today`, `yesterday`, `last_week`, 或自定义格式 |
| `--level` | `-l` | `all` | 日志级别: `error`, `warning`, `info`, `debug`, `all` |
| `--pattern` | `-p` | 无 | 搜索模式（正则表达式） |
| `--output` | `-o` | 无 | 输出分析结果 |
| `--format` | `-f` | `table` | 输出格式: `table`, `json`, `html` |

**示例:**
```bash
# 分析今天的错误日志
python scripts/analyze_logs.py logs/ --level error --time-range today

# 搜索特定错误模式
python scripts/analyze_logs.py logs/app.log --pattern "connection.*failed"

# 生成 HTML 报告
python scripts/analyze_logs.py logs/ --output analysis.html --format html
```

#### 4.6.2 `debug_agent.py` - 智能体调试
调试和分析智能体的行为。

**基本用法:**
```bash
python scripts/debug_agent.py [选项] <智能体ID>
```

**选项:**
| 选项 | 简写 | 默认值 | 描述 |
|------|------|--------|------|
| `--input` | `-i` | 无 | 输入文本或文件 |
| `--steps` | `-s` | `all` | 显示调试步骤: `all`, `thinking`, `actions`, `output` |
| `--verbose` | `-v` | `False` | 详细输出模式 |
| `--save` | 无 | 无 | 保存调试会话到文件 |
| `--compare` | `-c` | 无 | 与另一个智能体比较 |

**示例:**
```bash
# 调试智能体
python scripts/debug_agent.py ReasoningExpert --input "什么是机器学习？"

# 详细调试，显示所有步骤
python scripts/debug_agent.py ResearchAgent --input research_query.txt --steps all --verbose

# 保存调试会话
python scripts/debug_agent.py QA_Agent --input "问题" --save debug_session.json
```

#### 4.6.3 `profile_agent.py` - 智能体性能分析
分析智能体的性能特征。

**基本用法:**
```bash
python scripts/profile_agent.py [选项] <智能体ID>
```

**选项:**
| 选项 | 简写 | 默认值 | 描述 |
|------|------|--------|------|
| `--iterations` | `-i` | 10 | 分析迭代次数 |
| `--warmup` | `-w` | 3 | 预热迭代次数 |
| `--output` | `-o` | 无 | 输出分析报告 |
| `--format` | `-f` | `table` | 报告格式: `table`, `json`, `html` |
| `--memory` | `-m` | `False` | 分析内存使用 |

**示例:**
```bash
# 分析智能体性能
python scripts/profile_agent.py ReasoningExpert

# 多次迭代分析
python scripts/profile_agent.py ResearchAgent --iterations 100 --warmup 10

# 包含内存分析
python scripts/profile_agent.py QA_Agent --memory --output profile.json --format json
```

#### 4.6.4 `trace_request.py` - 请求跟踪
跟踪单个请求的处理流程。

**基本用法:**
```bash
python scripts/trace_request.py [选项] <请求文本>
```

**选项:**
| 选项 | 简写 | 默认值 | 描述 |
|------|------|--------|------|
| `--correlation-id` | `-c` | 自动生成 | 关联 ID |
| `--detailed` | `-d` | `False` | 详细跟踪模式 |
| `--visualize` | `-v` | `False` | 生成可视化跟踪图 |
| `--output` | `-o` | 无 | 输出跟踪结果 |

**示例:**
```bash
# 跟踪请求
python scripts/trace_request.py "帮我分析一下这个文档"

# 详细跟踪并可视化
python scripts/trace_request.py "复杂查询" --detailed --visualize

# 保存跟踪结果
python scripts/trace_request.py "测试请求" --output trace.json
```

## 📝 使用示例

### 5.1 日常运维流程

#### 5.1.1 启动和监控系统
```bash
# 1. 启动系统
python scripts/quick_start.py --mode development --verbose

# 2. 检查服务状态
python scripts/check_services.py --format table

# 3. 实时监控
python scripts/monitor_system.py --dashboard --port 8888
```

#### 5.1.2 数据维护
```bash
# 1. 导入新知识
python scripts/import_knowledge_base.py new_documents/ --parallel 8

# 2. 构建向量存储
python knowledge_management_system/scripts/build_vector_store.py --recreate

# 3. 备份数据
python scripts/export_data.py all --format sql --output backup_$(date +%Y%m%d).db
```

### 5.2 性能测试流程

#### 5.2.1 定期性能测试
```bash
# 1. 运行基准测试
python scripts/run_performance_benchmark.py --scenario heavy_load --output weekly_report.json

# 2. 分析性能日志
python scripts/analyze_performance_logs.py logs/performance.log --time-range last_week

# 3. 生成报告
python scripts/generate_performance_report.py --input weekly_report.json --format html
```

#### 5.2.2 质量保证测试
```bash
# 1. 运行质量测试
python run_quality_benchmark.py --real --queries 20

# 2. 运行集成测试
python tests/run_integration_tests.py --modules agents,api

# 3. 验证配置
python scripts/validate_configuration.py config/production.yaml --strict
```

### 5.3 故障排查流程

#### 5.3.1 诊断性能问题
```bash
# 1. 检查系统资源
python scripts/monitor_system.py --metrics cpu,memory,disk --interval 1

# 2. 分析错误日志
python scripts/analyze_logs.py logs/error.log --level error --time-range today

# 3. 调试智能体
python scripts/debug_agent.py ReasoningExpert --input "问题示例" --verbose
```

#### 5.3.2 处理数据库问题
```bash
# 1. 检查数据库状态
python scripts/check_services.py --services database

# 2. 执行数据库迁移
python scripts/migrate_database.py upgrade --verbose

# 3. 备份和恢复
python scripts/export_data.py conversations --format json --output backup.json
```

## 🔧 高级用法

### 6.1 自动化脚本

#### 6.1.1 创建自动化部署脚本
```bash
#!/bin/bash
# deploy.sh - 自动化部署脚本

set -e  # 出错时退出

echo "🚀 开始部署 RANGEN 系统..."

# 1. 停止现有服务
./scripts/stop_all_services.sh --force

# 2. 更新代码
git pull origin main

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行数据库迁移
python scripts/migrate_database.py upgrade

# 5. 运行测试
python scripts/run_tests.py --type unit

# 6. 启动服务
python scripts/start_unified_server.py --daemon

echo "✅ 部署完成！"
```

#### 6.1.2 监控告警脚本
```bash
#!/bin/bash
# check_and_alert.sh - 监控和告警脚本

# 检查服务状态
STATUS=$(python scripts/check_services.py --format json)

# 解析状态
if echo "$STATUS" | grep -q '"status": "unhealthy"'; then
    # 发送告警
    curl -X POST https://hooks.slack.com/services/... \
         -H 'Content-type: application/json' \
         -d "{\"text\": \"⚠️ RANGEN 服务异常！\"}"
    
    # 尝试重启
    ./scripts/stop_all_services.sh
    python scripts/start_unified_server.py --daemon
fi
```

### 6.2 工具组合使用

#### 6.2.1 性能测试管道
```bash
#!/bin/bash
# performance_pipeline.sh - 性能测试管道

# 1. 清理旧数据
rm -f performance_*.json
rm -f logs/performance.log

# 2. 启动测试环境
python scripts/quick_start.py --mode test --services api

# 3. 运行不同负载测试
for SCENARIO in light_load medium_load heavy_load; do
    echo "测试场景: $SCENARIO"
    python scripts/run_performance_benchmark.py \
        --scenario $SCENARIO \
        --output "performance_${SCENARIO}.json"
done

# 4. 生成综合报告
python scripts/generate_performance_report.py \
    --input performance_*.json \
    --output performance_summary.html \
    --format html

echo "性能测试完成！"
```

#### 6.2.2 数据备份和恢复
```bash
#!/bin/bash
# backup_and_restore.sh - 数据备份和恢复

# 备份所有数据
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).tar.gz"

echo "开始备份..."
python scripts/export_data.py all --format json --output backup_data.json
tar -czf "$BACKUP_FILE" backup_data.json config/ logs/

# 上传到云存储
aws s3 cp "$BACKUP_FILE" s3://rangen-backups/

echo "备份完成: $BACKUP_FILE"

# 恢复数据示例
# python scripts/import_data.py --input backup_data.json --mode overwrite
```

### 6.3 自定义工具开发

#### 6.3.1 创建自定义工具模板
```python
#!/usr/bin/env python3
"""
custom_tool.py - 自定义命令行工具模板
"""

import argparse
import sys
import logging
from pathlib import Path

def setup_logging(verbose=False):
    """设置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='自定义命令行工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  %(prog)s --input data.txt --output result.json
  %(prog)s --verbose --dry-run
        '''
    )
    
    parser.add_argument('--input', '-i', required=True,
                       help='输入文件或目录')
    parser.add_argument('--output', '-o', default='output.json',
                       help='输出文件路径')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细输出模式')
    parser.add_argument('--dry-run', action='store_true',
                       help='试运行，不实际执行')
    
    args = parser.parse_args()
    setup_logging(args.verbose)
    
    # 主逻辑
    logging.info(f"处理输入: {args.input}")
    
    if not args.dry_run:
        # 实际处理逻辑
        pass
    
    logging.info(f"结果保存到: {args.output}")

if __name__ == '__main__':
    main()
```

#### 6.3.2 集成现有工具功能
```python
#!/usr/bin/env python3
"""
enhanced_monitor.py - 增强版监控工具
"""

import subprocess
import json
import time
from datetime import datetime

class EnhancedMonitor:
    """增强版监控器"""
    
    def __init__(self):
        self.metrics = []
        
    def collect_system_metrics(self):
        """收集系统指标"""
        # 使用现有工具收集数据
        result = subprocess.run(
            ['python', 'scripts/monitor_system.py', '--format', 'json'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {}
        
    def check_service_health(self):
        """检查服务健康状态"""
        result = subprocess.run(
            ['python', 'scripts/check_services.py', '--format', 'json'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {}
        
    def run(self, interval=60):
        """运行监控"""
        while True:
            timestamp = datetime.now().isoformat()
            
            # 收集数据
            system_metrics = self.collect_system_metrics()
            service_health = self.check_service_health()
            
            # 合并数据
            data = {
                'timestamp': timestamp,
                'system': system_metrics,
                'services': service_health
            }
            
            self.metrics.append(data)
            print(f"监控数据收集完成: {timestamp}")
            
            time.sleep(interval)

if __name__ == '__main__':
    monitor = EnhancedMonitor()
    monitor.run(interval=300)  # 每5分钟收集一次
```

## ❓ 常见问题

### 7.1 安装和配置问题

#### Q1: 运行工具时出现 "ModuleNotFoundError" 错误
**A:** 确保在项目根目录运行，并已安装所有依赖：
```bash
# 在项目根目录
cd /path/to/RANGEN

# 安装依赖
pip install -r requirements.txt

# 设置 PYTHONPATH
export PYTHONPATH=$(pwd):$PYTHONPATH
```

#### Q2: 工具运行时提示 "缺少环境变量" 错误
**A:** 检查并设置必要的环境变量：
```bash
# 复制环境模板
cp .env.example .env

# 编辑环境变量（添加 API 密钥等）
vim .env

# 或者直接设置环境变量
export DEEPSEEK_API_KEY="your-api-key"
export STEPSFLASH_API_KEY="your-step-flash-key"
export OPENAI_API_KEY="your-openai-key"
```

#### Q3: 性能测试工具运行非常慢
**A:** 可能是由于网络问题或资源不足：
1. **检查网络连接**: `ping api.deepseek.com`
2. **使用模拟模式**: 添加 `--use-mock` 参数（如果支持）
3. **减少并发数**: 降低 `--users` 参数值
4. **缩短测试时间**: 减少 `--duration` 参数值

#### Q4: 数据导入工具处理大文件时内存不足
**A:** 优化处理参数：
```bash
# 减少批处理大小
python scripts/import_knowledge_base.py large_file.pdf --batch-size 10

# 增加分块大小，减少分块数量
python scripts/import_knowledge_base.py large_file.pdf --chunk-size 5000

# 使用并行处理
python scripts/import_knowledge_base.py large_file.pdf --parallel 2
```

#### Q5: 服务启动后无法访问 API
**A:** 检查以下方面：
1. **服务是否正常运行**: `python scripts/check_services.py`
2. **端口是否被占用**: `netstat -tulpn | grep :8000`
3. **防火墙设置**: 检查防火墙是否允许端口访问
4. **日志信息**: 查看 `logs/server.log` 获取详细信息

### 7.2 性能和使用问题

#### Q6: 如何提高系统响应速度？
**A:** 优化建议：
1. **启用缓存**: 确保缓存系统正常工作
2. **调整并发设置**: 根据系统资源调整工作进程数
3. **使用本地模型**: 对于简单查询使用本地 LLM 模型
4. **优化向量查询**: 调整向量存储的索引参数

#### Q7: 如何监控系统性能？
**A:** 使用内置监控工具：
```bash
# 实时监控
python scripts/monitor_system.py --dashboard

# 性能基准测试
python scripts/run_performance_benchmark.py --scenario medium_load

# 分析日志
python scripts/analyze_performance_logs.py logs/performance.log
```

#### Q8: 如何备份和恢复系统数据？
**A:** 使用数据管理工具：
```bash
# 备份所有数据
python scripts/export_data.py all --format sql --output backup.db

# 恢复数据（如果需要）
# 注意：恢复功能需根据具体需求实现
```

#### Q9: 如何调试智能体行为？
**A:** 使用调试工具：
```bash
# 调试单个智能体
python scripts/debug_agent.py ReasoningExpert --input "测试输入"

# 性能分析
python scripts/profile_agent.py ResearchAgent --iterations 50

# 请求跟踪
python scripts/trace_request.py "复杂查询" --detailed
```

#### Q10: 如何自定义命令行工具？
**A:** 参考工具开发模板：
1. 使用 `custom_tool.py` 模板
2. 遵循现有工具的代码结构
3. 集成到 `scripts/` 目录
4. 更新文档说明

### 7.3 错误处理和故障排除

#### Q11: 遇到 "数据库连接失败" 错误怎么办？
**A:** 检查步骤：
1. **数据库服务状态**: `systemctl status postgresql`（如使用 PostgreSQL）
2. **连接字符串**: 检查 `config/database.yaml` 配置
3. **权限问题**: 确保数据库用户有足够权限
4. **网络连接**: 检查数据库服务器网络可达性

#### Q12: 向量存储查询返回空结果
**A:** 可能原因和解决方案：
1. **集合名称错误**: 检查 `--collection` 参数
2. **相似度阈值过高**: 降低 `--threshold` 参数
3. **数据未正确导入**: 重新构建向量存储
4. **嵌入模型不匹配**: 确保查询使用的嵌入模型与构建时一致

#### Q13: LLM API 调用频繁失败
**A:** 应对策略：
1. **检查 API 密钥**: 确认密钥有效且未过期
2. **查看配额限制**: 检查 API 调用配额
3. **实现重试机制**: 工具通常内置重试，可调整参数
4. **使用备用模型**: 配置备用 LLM 提供商

#### Q14: 系统日志文件过大
**A:** 日志管理方案：
1. **启用日志轮转**: 配置 logrotate
2. **调整日志级别**: 生产环境使用 `INFO` 而非 `DEBUG`
3. **定期清理旧日志**: 使用脚本自动清理
4. **使用集中式日志**: 集成 ELK 或 Loki

#### Q15: 如何升级到新版本？
**A:** 升级步骤：
1. **备份数据**: `python scripts/export_data.py all`
2. **停止服务**: `./scripts/stop_all_services.sh`
3. **更新代码**: `git pull origin main`
4. **安装依赖**: `pip install -r requirements.txt`
5. **运行迁移**: `python scripts/migrate_database.py upgrade`
6. **启动服务**: `python scripts/start_unified_server.py`
7. **运行测试**: `python scripts/run_tests.py`

## 📋 总结

RANGEN 系统提供了一套完整的命令行工具集，涵盖了系统管理、性能测试、数据处理、监控诊断等各个方面。这些工具的设计目标是：

### 8.1 核心优势
- **全面性**: 覆盖系统全生命周期管理
- **易用性**: 统一的命令行接口和详细的帮助信息
- **可扩展性**: 支持自定义工具开发和集成
- **可靠性**: 内置错误处理和故障恢复机制

### 8.2 最佳实践
1. **定期性能测试**: 每周运行基准测试，监控性能变化
2. **数据备份**: 每日备份重要数据，保留最近7天备份
3. **日志分析**: 每天检查错误日志，及时处理问题
4. **版本管理**: 使用 Git 管理配置变更，记录每次部署

### 8.3 工具选择指南
| 任务类型 | 推荐工具 | 关键参数 |
|----------|----------|----------|
| 日常启动 | `quick_start.py` | `--mode development --verbose` |
| 性能测试 | `run_performance_benchmark.py` | `--scenario medium_load --output report.json` |
| 数据导入 | `import_knowledge_base.py` | `--parallel 4 --chunk-size 1000` |
| 故障诊断 | `analyze_logs.py` + `debug_agent.py` | `--level error --time-range today` |
| 系统监控 | `monitor_system.py` | `--dashboard --port 8888` |

## 📖 版本历史

| 版本 | 日期 | 作者 | 变更描述 |
|------|------|------|----------|
| 1.0.0 | 2026-03-07 | 技术团队 | 初始版本，包含完整的命令行工具参考 |
| 1.0.1 | 2026-03-08 | 技术团队 | 修复环境变量设置示例，添加更多常见问题 |
| 1.1.0 | 2026-03-10 | 工具团队 | 新增高级用法章节，添加工具开发模板 |
| 1.2.0 | 2026-03-12 | 运维团队 | 增强故障排除指南，添加自动化脚本示例 |

## 📞 支持与反馈

- **技术问题**: [提交 Issue](https://github.com/your-repo/RANGEN/issues)
- **功能建议**: [功能请求](https://github.com/your-repo/RANGEN/discussions/categories/ideas)
- **文档反馈**: [文档改进](https://github.com/your-repo/RANGEN/discussions/categories/documentation)
- **紧急支持**: 联系运维团队或查看 [紧急处理指南](紧急处理.md)

## 🔗 相关文档

- [快速开始指南](../getting-started/quick-start-guide.md)
- [系统架构文档](../architecture/diagrams/system-architecture.md)
- [性能规格说明书](../technical-specs/performance-specs.md)
- [API 参考文档](../api-formats.md)（待完善）
- [最佳实践指南](../best-practices/)（待完善）

---

*最后更新: 2026-03-07*  
*文档版本: 1.2.0*  
*维护团队: RANGEN 工具与运维组*

> **提示**: 本文档会随着工具更新而持续完善。建议定期查看最新版本。