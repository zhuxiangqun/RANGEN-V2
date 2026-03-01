# RANGEN V2 - Multi-Agent Research System

RANGEN is a highly intelligent multi-agent research system designed with a modular architecture. V2 introduces a production-ready **API Layer**, **Chat UI**, and robust **ReAct Reasoning Agents** powered by LangGraph.

## 📋 Project Overview

The system is designed with strict separation of concerns, ensuring scalability and maintainability.

### 🌟 New in V2
- **ReAct Reasoning Engine**: Implements "Reasoning + Acting" loops for complex problem solving using LangGraph.
- **FastAPI Backend**: High-performance REST API for agent interaction.
- **Streamlit Chat UI**: User-friendly web interface for real-time interaction and trace visualization.
- **Unified LLM Integration**: Support for DeepSeek, OpenAI, and Mock providers with robust error handling.
- **Configuration Management**: Standardized `.env` and YAML configuration.

## 🏗️ System Architecture

```
RANGEN Architecture
├── 🏭 Core System (src/)
│   ├── agents/          # Reasoning, Validation, Citation Agents
│   ├── core/            # Workflow Engine (LangGraph), Coordinator, Router
│   ├── api/             # FastAPI Server Implementation
│   ├── ui/              # Streamlit Chat Interface
│   └── services/        # Config, Logging, Error Handling
│
├── 📚 Knowledge Management (knowledge_management_system/)
│   └── Vector Store & Retrieval Logic
│
├── 📊 Evaluation System (evaluation/)
│   └── Performance & Quality Metrics
```

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

Edit `.env` to configure your LLM provider (e.g., DeepSeek) and API Key.

```ini
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-xxxxxxxx
```

*Note: You can use `LLM_PROVIDER=mock` to run the system without an API key.*

### 3. Running the System

#### Option A: Start API Server
The core backend service that handles agent coordination.

```bash
python src/api/server.py
# Server will start at http://localhost:8000
```

#### Option B: Start Chat UI
A web-based interface to interact with the agents.

```bash
streamlit run src/ui/app.py
# UI will open at http://localhost:8501
```

#### Option C: Run End-to-End Test
Verify the system integrity via command line.

```bash
python scripts/test_end_to_end.py
```

### 4. Evaluation
Run the batch evaluation script to test performance on a dataset.

```bash
python scripts/evaluate.py data/frames-benchmark/queries.json
```

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

## 🤝 Contribution

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

MIT License
