# RANGEN V2 - Multi-Agent Research System

RANGEN is a highly intelligent multi-agent research system designed with a modular architecture. V2 introduces a production-ready **API Layer**, **Chat UI**, and robust **ReAct Reasoning Agents** powered by LangGraph.

The system is designed with strict separation of concerns, ensuring scalability and maintainability.

---

## ⚠️ Architecture Note

This document describes the actual implementation based on **source code analysis**. The system has evolved significantly:

- **19+ Workflow implementations** exist (evolutionary legacy)
- **BUT only 1 is used in production**: `ExecutionCoordinator` (5 nodes, 241 lines)
- **30+ Agent types** (core + market-specific)
- **19 ML components** in the reasoning optimization framework
- **4 different state definitions** exist (need consolidation)
- **Multi-channel Gateway** (Slack/Telegram/WhatsApp/WebChat)
- **4 Self-Learning modules** (2026新增)
- **7 Hook intercept points** (2026新增)

> ⚡ **For developers**: See [AGENTS.md](./AGENTS.md) Section 11 for detailed production architecture analysis.

This document describes the actual implementation based on **source code analysis**. The system is significantly more complex than typical documentation suggests:

- **19+ Workflow implementations** (not a single workflow)
- **30+ Agent types** (core + market-specific)
- **19 ML components** in the reasoning optimization framework
- **3 layers of state management**
- **Multi-channel Gateway** (Slack/Telegram/WhatsApp/WebChat)

---

## 🌟 What's New in V2

- **ReAct Reasoning Engine**: Implements "Reasoning + Acting" loops for complex problem solving using LangGraph.
- **FastAPI Backend**: High-performance REST API for agent interaction.
- **Streamlit Chat UI**: User-friendly web interface for real-time interaction and trace visualization.
- **Unified LLM Integration**: Support for DeepSeek (external LLM only), local models (Llama/Qwen/Phi-3), and Mock providers with robust error handling.
- **Configuration Management**: Standardized `.env` and YAML configuration.
- **Multi-Channel Gateway**: Connect via Slack, Telegram, WhatsApp, or WebChat.
- **Dual Training Frameworks**: Both inference ML optimization and LLM fine-tuning.

---

## 🏗️ System Architecture

```
RANGEN Architecture
├── 🏭 Core System (src/)
│   ├── agents/          # 30+ Agents (Reasoning, Validation, Citation, RAG, Market-specific...)
│   ├── core/            # Workflow Engine (LangGraph - 19+ variants), Coordinator, Router
│   ├── api/             # FastAPI Server Implementation
│   ├── ui/              # Streamlit Chat Interface
│   └── services/        # 40+ Services (LLM routing, caching, security, monitoring, training)
│
├── 🌐 Gateway (src/gateway/)
│   ├── gateway.py       # Control plane (484 lines)
│   ├── channels/        # Multi-channel adapters (Slack, Telegram, WhatsApp, WebChat)
│   ├── events/          # Event bus for pub/sub
│   └── memory/          # Session memory management
│
├── 📚 Knowledge Management (knowledge_management_system/)
│   └── Vector Store & Retrieval Logic
│
└── 📊 Evaluation System (evaluation/)
    └── Performance & Quality Metrics
```

### Multi-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Entry Layer (Ports)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ :8000    │  │ :8501    │  │ :8502    │  │ :8080    │       │
│  │ API      │  │ Chat UI  │  │  Management│ │ Visualize│       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
└───────┼─────────────┼─────────────┼─────────────┼──────────────┘
        │             │             │             │
        ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Gateway Layer (Control Plane)              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  - Connection Management (Multi-channel)                 │    │
│  │  - Authentication & Authorization                       │    │
│  │  - Task Distribution & Routing                          │    │
│  │  - Event Bus (Pub/Sub)                                 │    │
│  │  - Kill Switch                                         │    │
│  │  - Rate Limiting                                       │    │
│  └─────────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Core Orchestration Layer                     │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │ ExecutionCoord.  │  │ UnifiedWorkflow  │                   │
│  │ (Lightweight)    │  │ Facade          │                   │
│  └──────────────────┘  └──────────────────┘                   │
│                                                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           LangGraph Workflow Engine (19+ variants)      │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Agent System (30+ Agents)                    │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐      │
│  │Reasoning│ │Validation│ │Citation│ │ RAG    │ │ Expert │      │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘      │
│  ┌─────────────────────────────────────────────────────┐      │
│  │     Market-Specific Agents (Japan/China/Pro)        │      │
│  └─────────────────────────────────────────────────────┘      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Services Layer (40+)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  LLM Routing | Tool Registry | Cache | Security        │  │
│  │  Monitoring | Training (ML + LLM)                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/RANGEN.git
cd RANGEN

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy the example configuration file and set your API keys:

```bash
cp .env.example .env
```

Edit `.env` to configure your LLM provider (e.g., DeepSeek, Step-3.5-Flash) and API Key.

```ini
# For DeepSeek
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-xxxxxxxx

# For Step-3.5-Flash (via OpenRouter)
LLM_PROVIDER=stepflash
STEPSFLASH_API_KEY=your_openrouter_api_key
```

*Note: You can use `LLM_PROVIDER=mock` to run the system without an API key.*

### 3. Running the System

#### Option A: One-Click Startup (Recommended)
Start all system services with a single command:

```bash
# Start all services
./start_rangen.sh start

# Check service status
./start_rangen.sh status

# Stop all services
./start_rangen.sh stop

# Restart all services
./start_rangen.sh restart
```

**Services Started**:
- 🤖 **Chat Interface**: http://localhost:8501
- 🔧 **Management Platform**: http://localhost:8502  
- 📊 **Governance Dashboard**: http://localhost:8503
- 🏗️ **Unified Server**: http://localhost:8080 (LangGraph workflow visualization)
- 🔌 **API Documentation**: http://localhost:8000/docs

**Enhanced Features**:
- 🚀 Starts all 5 core services simultaneously
- 📊 Full process management (start, stop, restart, status)
- 📝 Logging for each service in `logs/` directory
- 🔧 Automatic port conflict resolution

#### Option B: Start API Server
The core backend service that handles agent coordination.

```bash
python src/api/server.py
# Server will start at http://localhost:8000
```

#### Option C: Start Chat UI
A web-based interface to interact with the agents.

```bash
streamlit run src/ui/app.py
# UI will open at http://localhost:8501
```

#### Option D: Run End-to-End Test
Verify the system integrity via command line.

```bash
python scripts/test_end_to_end.py
```

### 4. Evaluation
Run the batch evaluation script to test performance on a dataset.

```bash
python scripts/evaluate.py data/frames-benchmark/queries.json
```

---

## 🔧 API Documentation

Once the API server is running, visit `http://localhost:8000/docs` for the interactive Swagger UI.

### Key Endpoints

- `POST /chat`: Send a query to the agent system.
  ```json
  {
    "query": "Explain the impact of quantum computing on cryptography",
    "session_id": "optional-session-id"
  }
  ```

---

## 📚 Documentation

RANGEN provides comprehensive documentation organized by user roles and usage scenarios:

### 📖 [Documentation Center](docs/README.md)
The main entry point to all documentation, organized into 7 categories:

1. **📚 [Getting Started](docs/getting-started/README.md)** - Quick start guides, installation, and complete user manual
2. **🏗️ [Architecture Design](docs/architecture/README.md)** - System design and components
3. **🔧 [Development Guide](docs/development/README.md)** - API reference and extension development
4. **🚀 [Operations & Deployment](docs/operations/README.md)** - Deployment, monitoring, and troubleshooting
5. **📖 [Technical Reference](docs/reference/README.md)** - Configuration and technical specifications
6. **💡 [Best Practices](docs/best-practices/README.md)** - Optimization and security practices
7. **📝 [Changelog](docs/changelog/README.md)** - Version history and migration guides

---

## 🤝 Contribution

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

MIT License
