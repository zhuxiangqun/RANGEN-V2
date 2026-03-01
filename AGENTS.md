# AGENTS.md

## Project Overview

RANGEN V2 is a sophisticated Multi-Agent Research System built with Python, designed for intelligent research and knowledge retrieval using AI agents. The system features a unified center architecture with LangGraph workflow orchestration, FastAPI REST API, and modular agent-based design.

## Repository Structure

```
RANGEN-main(syu-python)/
├── src/                    # Core source code
│   ├── agents/            # AI agent implementations
│   ├── api/               # FastAPI server and models
│   ├── core/              # Workflow engine and coordinator
│   ├── services/          # Business logic services
│   ├── interfaces/        # Abstract interfaces
│   ├── monitoring/        # System monitoring
│   └── ui/                # Streamlit web interface
├── knowledge_management_system/  # Vector store and retrieval
├── frontend_monitor/      # Vue.js frontend monitoring
├── tests/                 # Test suites
├── config/               # Configuration files
└── scripts/              # Utility and deployment scripts
```

## Build, Lint, and Test Commands

### Environment Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies (if working with frontend_monitor)
cd frontend_monitor && npm install

# Configure environment
cp .env.example .env
# Edit .env with API keys and configuration
```

### Development Commands
```bash
# Start API server
python src/api/server.py

# Start Streamlit web UI
streamlit run src/ui/app.py

# Run linting
pylint src/

# Run type checking (if pyright is installed)
pyright src/
```

### Testing Commands
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_specific_file.py

# Run single test function
pytest tests/test_file.py::test_function_name

# Run tests by marker
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m slow          # Slow tests only

# Run tests with verbose output
pytest -v

# Run tests with coverage (if pytest-cov is installed)
pytest --cov=src --cov-report=html
```

### Quality Assurance
```bash
# Validate LangGraph node docstrings
python scripts/check_node_docstrings.py

# Run comprehensive quality checks
pylint src/ && pytest && python scripts/check_node_docstrings.py
```

## Code Style Guidelines

### Python Code Style

#### Naming Conventions
- **Variables and functions**: `snake_case` (e.g., `agent_config`, `process_request`)
- **Classes**: `PascalCase` (e.g., `BaseAgent`, `AgentConfig`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Private members**: Prefix with underscore (e.g., `_internal_method`, `_private_var`)

#### Import Organization
```python
# Standard library imports
import os
import sys
from typing import Dict, List, Any, Optional

# Third-party imports
import numpy as np
import pandas as pd
from fastapi import FastAPI
from langgraph import StateGraph

# Local application imports
from src.agents.base_agent import BaseAgent
from src.core.config import ConfigService
```

#### Formatting and Structure
- **Line length**: Maximum 120 characters (configured in .pylintrc)
- **Indentation**: 4 spaces (no tabs)
- **Docstrings**: Comprehensive docstrings with Chinese descriptions for user-facing code
- **Type hints**: Use `typing` module for all function signatures and class attributes

#### Error Handling
```python
# Use unified error handling service
from src.services.error_handling import ErrorHandlingService

class AgentService:
    def __init__(self):
        self.error_handler = ErrorHandlingService()
    
    def process_request(self, request: Request) -> Response:
        try:
            # Process request
            result = self._do_work(request)
            return Response(success=True, data=result)
        except Exception as e:
            # Log and handle errors consistently
            self.error_handler.handle_error(e, context="AgentService.process_request")
            return Response(success=False, error=str(e))
```

#### Logging
```python
import logging

# Use structured logging
logger = logging.getLogger(__name__)

class AgentService:
    def process_request(self, request: Request) -> Response:
        logger.info(f"Processing request {request.id}", extra={
            "request_id": request.id,
            "agent_type": self.agent_type,
            "timestamp": datetime.now().isoformat()
        })
```

### Architectural Patterns

#### Agent Development
- **BaseAgent Interface**: All agents must inherit from `BaseAgent`
- **AgentBuilder Pattern**: Use `AgentBuilder` for creating agent instances
- **Capabilities Configuration**: Configure via `capabilities_dict`
- **Singleton Services**: Use singleton pattern for shared services like `ConfigService`

#### LangGraph Nodes
```python
def node_function(state: AgentState) -> AgentState:
    """节点名称 - 功能说明"""
    # Single-line docstring format is mandatory
    # Docstring must reflect current functionality
    # Used by automated visualization system
    
    # Process state
    result = process_data(state.data)
    
    # Return updated state
    return {**state, "data": result}
```

#### Configuration Management
- **No hardcoding**: Use configuration center for all settings
- **Environment variables**: Use `.env` file for sensitive data
- **Unified config**: Prioritize existing unified center system

### Frontend (Vue.js) Style
- **Component naming**: PascalCase
- **File naming**: kebab-case
- **Code style**: Follow Vue.js 3 Composition API conventions
- **TypeScript**: Use TypeScript for type safety

## Development Principles

### Core Principles (from .cursorrules)
1. **DRY (Don't Repeat Yourself)**: Extract repeated code into functions or modules
2. **KISS (Keep It Simple, Stupid)**: Prioritize simple, clear implementations
3. **Single Responsibility**: Each function/class has one purpose
4. **Composition over Inheritance**: Prefer composition for code reuse

### Security Principles
- **Input validation**: All user input must be validated and sanitized
- **Safe functions**: Avoid `eval()`, `exec()`, `compile()` - use safe alternatives
- **No secrets in code**: Use environment variables for API keys and sensitive data

### Agent-Specific Guidelines
- **14 Agent Components**: Categorized into core, support, and specialized agents
- **Unified Center System**: Prioritize existing unified systems over new implementations
- **Core Functionality Focus**: Solve root causes, not workarounds
- **Code Quality**: Must pass pylint/pyright checks

## Testing Guidelines

### Test Structure
- **Base Test Class**: Use `RANGENTestCase` in `tests/test_framework.py`
- **Test Categories**: Unit tests, integration tests, performance benchmarks
- **Mock Support**: Use built-in mocking utilities for external dependencies

### Test Writing
```python
import pytest
from tests.test_framework import RANGENTestCase

class TestAgentService(RANGENTestCase):
    def test_agent_creation(self):
        """测试智能体创建功能"""
        agent = self.create_test_agent("test_agent")
        assert agent.agent_id == "test_agent"
        assert agent.is_enabled() is True
    
    @pytest.mark.asyncio
    async def test_async_processing(self):
        """测试异步处理功能"""
        result = await self.agent_service.process_async(test_data)
        assert result.success is True
```

## Pre-commit Checklist

Before committing changes:
- [ ] Code passes `pylint src/` without errors
- [ ] All tests pass: `pytest`
- [ ] LangGraph node docstrings are valid: `python scripts/check_node_docstrings.py`
- [ ] No hardcoded values (use configuration center)
- [ ] Error handling follows unified patterns
- [ ] Logging is structured and informative
- [ ] Type hints are complete and accurate
- [ ] Documentation is updated for new features

## Running Single Tests

### Quick Test Commands
```bash
# Run specific test class
pytest tests/test_agent_service.py

# Run specific test method
pytest tests/test_agent_service.py::TestAgentService::test_agent_creation

# Run with specific marker and verbosity
pytest -m unit -v tests/

# Run async tests only
pytest -m asyncio tests/test_async_components.py
```

### Debug Mode
```bash
# Run with debugger (breakpoint on exception)
pytest --pdb --tb=short tests/test_failing_file.py

# Run with detailed output
pytest -v -s tests/test_specific_file.py::test_function_name
```

## Key Dependencies and Frameworks

- **FastAPI**: REST API framework
- **LangGraph**: Workflow orchestration and agent coordination  
- **Streamlit**: Web UI for chat interface
- **Vue.js 3**: Frontend monitoring dashboard
- **Pytest**: Testing framework with asyncio support
- **Pylint**: Code quality and style enforcement

## License

MIT License - see [LICENSE](LICENSE) for details