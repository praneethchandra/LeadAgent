# Lead Agent - AI Workflow Orchestration System

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Coverage](https://img.shields.io/badge/coverage-100%25-green.svg)](https://github.com/your-repo/lead-agent)

A sophisticated AI workflow orchestration system that enables configurable multi-agent communication with robust error handling, retry mechanisms, and partial failure recovery. The Lead Agent system is designed to handle complex workflows involving multiple AI agents, MCP servers, and HTTP APIs with enterprise-grade reliability patterns.

## 🏗️ System Architecture

The Lead Agent system is built using a modular, pattern-based architecture that ensures scalability, maintainability, and reliability:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Lead Agent    │────│ Workflow Engine │────│  State Machine  │
│   (Facade)      │    │   (Orchestrator)│    │   (State Mgmt)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Config Loader   │    │ Task Executor   │    │    Observers    │
│ (Configuration) │    │   (Execution)   │    │  (Event Mgmt)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Agent Factory   │────│  Agent Types    │────│ Resilience      │
│   (Creation)    │    │ (AI/MCP/HTTP)   │    │   Patterns      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🎯 Key Features

- **🔄 Multi-Agent Orchestration**: Seamless communication with AI agents, MCP servers, and HTTP APIs
- **📋 Configuration-Driven**: YAML/JSON-based workflow and task definitions
- **🛡️ Enterprise Reliability**: Circuit breaker, retry, and timeout patterns
- **⚡ Parallel & Sequential Execution**: Flexible execution strategies
- **🔧 Partial Failure Recovery**: Continue execution despite individual task failures  
- **📊 Comprehensive Monitoring**: Real-time workflow and task status tracking
- **🧪 100% Test Coverage**: Extensive unit and integration testing
- **🔌 Extensible Architecture**: Plugin-based agent system

## 🏛️ Design Patterns Used

### Core Patterns

#### 1. **Strategy Pattern** 
- **Location**: `src/lead_agent/agents/`
- **Purpose**: Different agent communication strategies (AI, MCP, HTTP)
- **Implementation**: `BaseAgent` interface with specific implementations

#### 2. **Factory Pattern**
- **Location**: `src/lead_agent/agents/base.py`
- **Purpose**: Dynamic agent creation based on configuration
- **Implementation**: `AgentFactory` class with type registration

#### 3. **Command Pattern**
- **Location**: `src/lead_agent/models.py`
- **Purpose**: Encapsulate task execution requests
- **Implementation**: `TaskExecution` and `TaskConfig` models

#### 4. **Observer Pattern**
- **Location**: `src/lead_agent/patterns/observer.py`
- **Purpose**: Event-driven workflow state notifications
- **Implementation**: `Subject` and `Observer` base classes

#### 5. **State Machine Pattern**
- **Location**: `src/lead_agent/workflow/state_machine.py`
- **Purpose**: Manage workflow and task state transitions
- **Implementation**: `WorkflowStateMachine` class

### Reliability Patterns

#### 6. **Circuit Breaker Pattern**
- **Location**: `src/lead_agent/patterns/circuit_breaker.py`
- **Purpose**: Prevent cascading failures in distributed systems
- **States**: CLOSED → OPEN → HALF_OPEN → CLOSED
- **Configuration**: Failure threshold, recovery timeout

#### 7. **Retry Pattern**
- **Location**: `src/lead_agent/patterns/retry.py`  
- **Purpose**: Handle transient failures with exponential backoff
- **Features**: Configurable attempts, jitter, max delay

#### 8. **Chain of Responsibility Pattern**
- **Location**: `src/lead_agent/workflow/engine.py`
- **Purpose**: Sequential task execution with dependency management
- **Implementation**: Task dependency resolution and execution ordering

#### 9. **Builder Pattern**
- **Location**: `src/lead_agent/config_loader.py`
- **Purpose**: Complex workflow configuration construction
- **Implementation**: Step-by-step configuration validation and building

#### 10. **Adapter Pattern**
- **Location**: `src/lead_agent/agents/`
- **Purpose**: Uniform interface for different external systems
- **Implementation**: Common `AgentResponse` format across different APIs

### Multi-Agent Patterns

#### 11. **Orchestrator Pattern**
- **Location**: `src/lead_agent/workflow/engine.py`
- **Purpose**: Central coordination of multiple agents
- **Implementation**: `WorkflowEngine` as the central orchestrator

#### 12. **Scatter-Gather Pattern**
- **Location**: Parallel execution in `WorkflowEngine`
- **Purpose**: Distribute tasks to multiple agents and collect results
- **Implementation**: Async parallel task execution

#### 13. **Saga Pattern**
- **Location**: Workflow state management
- **Purpose**: Manage distributed transactions across agents
- **Implementation**: Partial completion and rollback capabilities

## 📁 Project Structure

```
LeadAgent/
├── src/lead_agent/
│   ├── __init__.py
│   ├── lead_agent.py          # Main facade class
│   ├── models.py              # Core data models
│   ├── config_loader.py       # Configuration management
│   ├── agents/                # Agent implementations
│   │   ├── __init__.py
│   │   ├── base.py           # Base agent and factory
│   │   ├── ai_agent.py       # AI service agent
│   │   ├── mcp_server.py     # MCP server agent
│   │   └── http_api.py       # HTTP API agent
│   ├── patterns/              # Design pattern implementations
│   │   ├── __init__.py
│   │   ├── circuit_breaker.py
│   │   ├── retry.py
│   │   └── observer.py
│   └── workflow/              # Workflow execution engine
│       ├── __init__.py
│       ├── engine.py         # Main workflow engine
│       ├── executor.py       # Task executor
│       └── state_machine.py  # State management
├── tests/                     # Comprehensive test suite
│   ├── test_models.py
│   ├── test_config_loader.py
│   ├── test_patterns.py
│   ├── test_agents.py
│   ├── test_workflow.py
│   └── test_integration.py
├── examples/                  # Example configurations
│   ├── simple_workflow.yaml
│   └── parallel_workflow.yaml
├── pyproject.toml            # Project configuration
└── README.md                 # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Poetry (recommended) or pip
- Git

### Installation

#### Option 1: Using Poetry (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-repo/lead-agent.git
cd lead-agent

# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell
```

#### Option 2: Using pip

```bash
# Clone the repository
git clone https://github.com/your-repo/lead-agent.git
cd lead-agent

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Or install dependencies directly
pip install -r requirements.txt
```

#### Option 3: Install from PyPI (when available)

```bash
pip install lead-agent
```

### Verify Installation

```bash
# Check if the package is installed correctly
python -c "from lead_agent import LeadAgent; print('Lead Agent installed successfully!')"

# Run tests to ensure everything works
pytest tests/ -v
```

## 🏃‍♂️ How to Run the Application

The Lead Agent system can be run in multiple ways depending on your use case:

### 1. Command Line Interface (CLI)

The simplest way to run workflows is using the CLI:

```bash
# Run a workflow from a YAML configuration file
python -m lead_agent.lead_agent examples/simple_workflow.yaml

# Or if installed via pip/poetry
python -c "
import asyncio
from lead_agent.lead_agent import main
asyncio.run(main())
" examples/simple_workflow.yaml
```

**Example CLI Output:**
```
Workflow completed with status: completed
Completed tasks: 4/4
Execution time: 12.34s

Results:
  fetch_raw_data: {'data': [...], 'count': 100}
  process_with_ai: {'insights': 'Key findings...', 'confidence': 0.95}
  analyze_with_mcp: {'correlation': 0.87, 'p_value': 0.02}
  generate_report: {'report': 'markdown content...'}
```

### 2. Programmatic Usage (Python Script)

For integration into your applications:

```python
import asyncio
from lead_agent import LeadAgent

async def run_workflow():
    # Initialize the Lead Agent
    agent = LeadAgent()
    
    # Option A: Run from YAML file
    result = await agent.execute_workflow_from_file("examples/simple_workflow.yaml")
    
    # Option B: Run from dictionary configuration
    config = {
        "name": "my_workflow",
        "agents": [...],
        "tasks": [...]
    }
    result = await agent.execute_workflow_from_dict(config)
    
    # Process results
    if result.status == "completed":
        print(f"✅ Workflow completed successfully!")
        print(f"📊 Results: {result.results}")
    else:
        print(f"❌ Workflow failed: {result.errors}")
    
    return result

# Run the workflow
if __name__ == "__main__":
    result = asyncio.run(run_workflow())
```

### 3. REST API Server

Start the REST API server for HTTP-based workflow management:

```bash
# Start the API server (default port 8000)
python -m lead_agent.api.server

# Or specify a custom port
python -m lead_agent.api.server --port 8080 --host 0.0.0.0

# With custom configuration
python -m lead_agent.api.server --config config.yaml --debug
```

**API Server Features:**
- 🔄 Submit and execute workflows via REST API
- 📊 Real-time workflow status monitoring
- 📋 List and manage workflow executions
- 🔍 Query execution results and logs
- 🛡️ Authentication and rate limiting support

### 4. Interactive Demo

Run the interactive demo to explore features:

```bash
# Run the comprehensive demo
python examples/demo.py

# Run the simple demo
python examples/simple_demo.py
```

### 5. Docker Deployment

Deploy using Docker for production environments:

```bash
# Build the Docker image
docker build -t lead-agent .

# Run with default configuration
docker run -p 8000:8000 lead-agent

# Run with custom configuration
docker run -p 8000:8000 -v $(pwd)/config:/app/config lead-agent --config /app/config/production.yaml
```

### 6. Development Mode

For development and testing:

```bash
# Install development dependencies
poetry install --with dev

# Run with hot reload (if using API server)
python -m lead_agent.api.server --reload --debug

# Run tests
pytest tests/ -v --cov=src/lead_agent

# Run linting and formatting
black src/ tests/
isort src/ tests/
flake8 src/ tests/
mypy src/
```

### Basic Usage Example

1. **Create a workflow configuration** (`my_workflow.yaml`):

```yaml
name: "my_first_workflow"
version: "1.0.0"
parallel_execution: false
failure_strategy: "stop_on_first_failure"

agents:
  - name: "openai_agent"
    type: "ai_agent"
    endpoint: "https://api.openai.com/v1/chat/completions"
    authentication:
      type: "bearer"
      token: "your-api-key"
    retry_config:
      max_attempts: 3
      initial_delay: 1.0

tasks:
  - name: "generate_content"
    agent_name: "openai_agent"
    action: "chat_completion"
    parameters:
      model: "gpt-4"
      messages:
        - role: "user"
          content: "Generate a creative story"
      max_tokens: 500
```

2. **Execute the workflow**:

```python
import asyncio
from lead_agent import LeadAgent

async def main():
    agent = LeadAgent()
    result = await agent.execute_workflow_from_file("my_workflow.yaml")
    
    print(f"Status: {result.status}")
    print(f"Results: {result.results}")

asyncio.run(main())
```

## 📝 Configuration Reference

### Workflow Configuration

```yaml
name: "workflow_name"                    # Required: Workflow identifier
description: "Workflow description"      # Optional: Human-readable description
version: "1.0.0"                        # Optional: Version tracking
parallel_execution: false               # Optional: Enable parallel task execution
failure_strategy: "stop_on_first_failure" # Optional: How to handle failures
global_timeout: 300                     # Optional: Overall workflow timeout (seconds)

# Failure strategies:
# - "stop_on_first_failure": Stop when any task fails
# - "continue_on_failure": Continue executing other tasks
# - "partial_completion_allowed": Allow partial workflow success
```

### Agent Configuration

```yaml
agents:
  - name: "agent_name"                  # Required: Unique agent identifier
    type: "ai_agent"                    # Required: Agent type (ai_agent, mcp_server, http_api, custom)
    endpoint: "https://api.example.com" # Required: Service endpoint
    timeout: 30                         # Optional: Request timeout (seconds)
    
    # Authentication (optional)
    authentication:
      type: "bearer"                    # Types: bearer, api_key, basic
      token: "your-token"               # For bearer auth
      # OR
      key: "your-key"                   # For API key auth
      header: "X-API-Key"               # Custom header name
      # OR  
      username: "user"                  # For basic auth
      password: "pass"
    
    # Retry configuration (optional)
    retry_config:
      max_attempts: 3                   # Maximum retry attempts
      initial_delay: 1.0                # Initial delay (seconds)
      max_delay: 60.0                   # Maximum delay (seconds)
      exponential_base: 2.0             # Backoff multiplier
      jitter: true                      # Add random jitter
    
    # Circuit breaker configuration (optional)
    circuit_breaker:
      failure_threshold: 5              # Failures before opening circuit
      recovery_timeout: 60.0            # Time before attempting recovery
    
    # Custom parameters (optional)
    custom_params:
      user_agent: "LeadAgent/1.0"
```

### Task Configuration

```yaml
tasks:
  - name: "task_name"                   # Required: Unique task identifier
    description: "Task description"      # Optional: Human-readable description
    agent_name: "agent_name"            # Required: Reference to agent
    action: "action_name"               # Required: Action to execute
    
    # Task parameters (optional)
    parameters:
      param1: "value1"
      param2: 42
      nested:
        key: "value"
    
    timeout: 30                         # Optional: Task-specific timeout
    depends_on: ["task1", "task2"]      # Optional: Task dependencies
    continue_on_failure: false          # Optional: Continue workflow if this task fails
    
    # Task-specific retry config (optional)
    retry_config:
      max_attempts: 2
      initial_delay: 0.5
```

## 🌐 REST API Reference

The Lead Agent system includes a comprehensive REST API for workflow management and monitoring.

### API Server Setup

```bash
# Quick start (development mode with auto-reload)
python run_api_server.py

# Or start manually with custom options
python -m lead_agent.api.server

# Custom configuration
python -m lead_agent.api.server --host 0.0.0.0 --port 8080 --debug

# Production deployment
python -m lead_agent.api.server --host 0.0.0.0 --port 8000 --workers 4
```

### Base URL
```
http://localhost:8000
```

### Authentication
Currently, the API does not require authentication. In production, implement proper authentication mechanisms.

### API Endpoints

#### Health & Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/health` | Health check and service information |
| `GET` | `/` | API information and available endpoints |

#### Workflow Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/workflows` | Create and execute a new workflow |
| `GET` | `/api/v1/workflows` | List all workflow executions (paginated) |
| `GET` | `/api/v1/workflows/{id}` | Get specific workflow details |
| `GET` | `/api/v1/workflows/{id}/status` | Get workflow status and progress |
| `DELETE` | `/api/v1/workflows/{id}` | Cancel a running workflow |

#### Agent Testing

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/agents/test` | Test agent connectivity and configuration |

### API Usage Examples

#### 1. Create and Execute Workflow

```bash
curl -X POST "http://localhost:8000/api/v1/workflows" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "simple_test_workflow",
    "description": "A simple test workflow",
    "version": "1.0.0",
    "parallel_execution": false,
    "failure_strategy": "stop_on_first_failure",
    "agents": [
      {
        "name": "test_agent",
        "type": "http_api",
        "endpoint": "https://jsonplaceholder.typicode.com",
        "timeout": 30
      }
    ],
    "tasks": [
      {
        "name": "fetch_data",
        "agent_name": "test_agent",
        "action": "fetch",
        "parameters": {
          "method": "GET",
          "endpoint": "/posts/1"
        }
      }
    ]
  }'
```

**Response:**
```json
{
  "execution_id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "simple_test_workflow",
  "status": "queued",
  "created_at": "2024-01-15T10:30:00Z",
  "total_tasks": 1
}
```

#### 2. Check Workflow Status

```bash
curl "http://localhost:8000/api/v1/workflows/123e4567-e89b-12d3-a456-426614174000/status"
```

**Response:**
```json
{
  "execution_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "running",
  "progress": 50.0,
  "current_task": "fetch_data",
  "message": "Workflow running"
}
```

#### 3. List All Workflows

```bash
curl "http://localhost:8000/api/v1/workflows?page=1&page_size=10&status=completed"
```

**Response:**
```json
{
  "workflows": [
    {
      "execution_id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "simple_test_workflow",
      "status": "completed",
      "created_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T10:31:30Z",
      "execution_time": 90.5,
      "total_tasks": 1,
      "completed_tasks": 1,
      "results": {
        "fetch_data": {"id": 1, "title": "Test Post", "body": "..."}
      }
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

#### 4. Test Agent Configuration

```bash
curl -X POST "http://localhost:8000/api/v1/agents/test" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_config": {
      "name": "test_agent",
      "type": "http_api",
      "endpoint": "https://jsonplaceholder.typicode.com",
      "timeout": 30
    },
    "test_action": "ping",
    "test_parameters": {
      "method": "GET",
      "endpoint": "/posts/1"
    }
  }'
```

**Response:**
```json
{
  "agent_name": "test_agent",
  "success": true,
  "response_time": 0.234,
  "result": {"id": 1, "title": "Test Post", "body": "..."},
  "error": null
}
```

### Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `400` | Bad Request - Invalid input |
| `404` | Not Found - Resource doesn't exist |
| `422` | Unprocessable Entity - Validation error |
| `500` | Internal Server Error |

### Workflow Status Values

| Status | Description |
|--------|-------------|
| `queued` | Workflow is queued for execution |
| `running` | Workflow is currently executing |
| `completed` | Workflow completed successfully |
| `failed` | Workflow failed with errors |
| `cancelled` | Workflow was cancelled by user |

### Postman Collection

Import the provided Postman collection (`Lead_Agent_API.postman_collection.json`) to test all API endpoints:

1. **Open Postman**
2. **Click Import** → **Upload Files**
3. **Select** `Lead_Agent_API.postman_collection.json`
4. **Configure** the `baseUrl` variable (default: `http://localhost:8000`)
5. **Run** the requests to test different workflows

**Collection Features:**
- ✅ Pre-configured requests for all endpoints
- 🔄 Automatic variable management (execution IDs)
- 📝 Comprehensive test examples
- 🧪 Agent connectivity testing
- 📊 Error handling demonstrations

### Interactive API Documentation

Once the server is running, access interactive documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🔧 Advanced Features

### Parallel Workflow Execution

Enable parallel execution for independent tasks:

```yaml
parallel_execution: true
failure_strategy: "partial_completion_allowed"

tasks:
  - name: "fetch_data_source_1"
    agent_name: "http_agent"
    action: "fetch"
    # No dependencies - runs immediately
    
  - name: "fetch_data_source_2" 
    agent_name: "http_agent"
    action: "fetch"
    # No dependencies - runs in parallel with source_1
    
  - name: "combine_results"
    agent_name: "ai_agent" 
    action: "combine"
    depends_on: ["fetch_data_source_1", "fetch_data_source_2"]
    # Waits for both sources to complete
```

### Error Handling Strategies

#### Stop on First Failure (Default)
```yaml
failure_strategy: "stop_on_first_failure"
# Workflow stops immediately when any task fails
```

#### Continue on Failure
```yaml
failure_strategy: "continue_on_failure"
# Independent tasks continue executing despite failures
```

#### Partial Completion Allowed
```yaml
failure_strategy: "partial_completion_allowed"
# Workflow succeeds if at least one task completes successfully
```

### Circuit Breaker Configuration

Protect against cascading failures:

```yaml
agents:
  - name: "unreliable_service"
    type: "http_api"
    circuit_breaker:
      failure_threshold: 3      # Open after 3 consecutive failures
      recovery_timeout: 30      # Try again after 30 seconds
```

### Retry with Exponential Backoff

Handle transient failures gracefully:

```yaml
agents:
  - name: "flaky_service"
    type: "ai_agent"
    retry_config:
      max_attempts: 5           # Try up to 5 times
      initial_delay: 0.5        # Start with 0.5s delay
      max_delay: 30.0           # Cap at 30s delay
      exponential_base: 2.0     # Double delay each time
      jitter: true              # Add randomness to prevent thundering herd
```

## 🧪 Testing

The project includes comprehensive test coverage with both unit and integration tests.

### Running Tests

```bash
# Run all tests with coverage
poetry run pytest --cov=src/lead_agent --cov-report=html --cov-report=term-missing

# Run specific test categories
poetry run pytest tests/test_models.py          # Unit tests for models
poetry run pytest tests/test_patterns.py       # Pattern implementation tests
poetry run pytest tests/test_integration.py    # End-to-end integration tests

# Run with verbose output
poetry run pytest -v
```

### Test Structure

- **Unit Tests**: Test individual components in isolation
  - `test_models.py`: Data model validation and behavior
  - `test_config_loader.py`: Configuration loading and validation
  - `test_patterns.py`: Design pattern implementations
  - `test_agents.py`: Agent communication logic
  - `test_workflow.py`: Workflow engine components

- **Integration Tests**: Test complete workflows end-to-end
  - `test_integration.py`: Full workflow execution scenarios
  - Mock external services for reliable testing
  - Test failure scenarios and recovery mechanisms

### Coverage Goals

The project maintains **100% line, branch, and instruction coverage**:

- All code paths are tested
- Error conditions are validated
- Edge cases are covered
- Integration scenarios are verified

## 📊 Monitoring and Observability

### Structured Logging

The system uses structured logging with contextual information:

```python
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
```

### Event Tracking

Monitor workflow execution with the Observer pattern:

```python
from lead_agent.patterns.observer import Observer

class WorkflowMonitor(Observer):
    async def update(self, subject, event_type: str, data: any):
        if event_type == "task_completed":
            print(f"Task {data.name} completed successfully")
        elif event_type == "task_failed":
            print(f"Task {data.name} failed: {data.error}")

# Attach monitor to workflow engine
monitor = WorkflowMonitor()
workflow_engine.state_machine.attach(monitor)
```

### Metrics Collection

Key metrics are automatically tracked:

- Workflow execution time
- Task success/failure rates
- Agent response times
- Circuit breaker state changes
- Retry attempt counts

## 🔌 Extending the System

### Creating Custom Agents

1. **Implement the BaseAgent interface**:

```python
from lead_agent.agents.base import BaseAgent, AgentFactory
from lead_agent.models import AgentResponse, AgentType

class CustomAgent(BaseAgent):
    async def execute(self, action: str, parameters: dict) -> AgentResponse:
        # Your custom implementation
        try:
            result = await self.custom_logic(action, parameters)
            return AgentResponse(success=True, result=result)
        except Exception as e:
            return AgentResponse(success=False, error=str(e))

# Register the new agent type
AgentFactory.register_agent_type(AgentType.CUSTOM, CustomAgent)
```

2. **Use in configuration**:

```yaml
agents:
  - name: "my_custom_agent"
    type: "custom"
    endpoint: "custom://endpoint"
    custom_params:
      special_config: "value"
```

### Adding Custom Observers

Monitor specific workflow events:

```python
from lead_agent.patterns.observer import Observer

class MetricsCollector(Observer):
    def __init__(self):
        self.metrics = {}
    
    async def update(self, subject, event_type: str, data: any):
        if event_type == "task_completed":
            self.metrics[data.name] = data.execution_time
        # Add custom metric collection logic
```

## 📈 Performance Considerations

### Parallel Execution

- Enable `parallel_execution: true` for independent tasks
- Use appropriate `failure_strategy` for your use case
- Consider resource limits when running many parallel tasks

### Resource Management

- Configure appropriate timeouts for agents and tasks
- Use circuit breakers to prevent resource exhaustion
- Monitor memory usage with large workflows

### Optimization Tips

1. **Batch Similar Operations**: Group similar API calls when possible
2. **Optimize Retry Strategies**: Use shorter delays for fast-failing services
3. **Circuit Breaker Tuning**: Adjust thresholds based on service characteristics
4. **Connection Pooling**: Reuse HTTP connections for multiple requests

## 🛠️ Troubleshooting

### Common Issues

#### Configuration Validation Errors
```bash
ConfigurationError: Task 'process_data' references undefined agent 'missing_agent'
```
**Solution**: Ensure all agents referenced in tasks are defined in the `agents` section.

#### Circular Dependencies
```bash
ConfigurationError: Circular dependency detected in tasks
```
**Solution**: Review task dependencies to ensure no circular references exist.

#### Agent Communication Failures
```bash
AgentResponse(success=False, error="Request timeout")
```
**Solutions**:
- Increase agent timeout settings
- Check network connectivity
- Verify endpoint URLs and authentication

#### Circuit Breaker Issues
```bash
AgentResponse(success=False, error="Circuit breaker is open")
```
**Solutions**:
- Wait for recovery timeout to pass
- Check underlying service health
- Adjust circuit breaker thresholds

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging
import structlog

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.dev.ConsoleRenderer()  # Human-readable output
    ]
)
```

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Write tests** for your changes
4. **Ensure 100% test coverage**: `poetry run pytest --cov=src/lead_agent --cov-fail-under=100`
5. **Run linting**: `poetry run black src/ tests/ && poetry run isort src/ tests/`
6. **Commit your changes**: `git commit -m 'Add amazing feature'`
7. **Push to the branch**: `git push origin feature/amazing-feature`
8. **Open a Pull Request**

### Development Setup

```bash
# Clone and setup development environment
git clone https://github.com/your-repo/lead-agent.git
cd lead-agent
poetry install --with dev

# Run pre-commit hooks
poetry run pre-commit install

# Run full test suite
poetry run pytest

# Check code quality
poetry run black --check src/ tests/
poetry run isort --check-only src/ tests/
poetry run flake8 src/ tests/
poetry run mypy src/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Design Patterns**: Gang of Four patterns and Enterprise Integration Patterns
- **Reliability Patterns**: Netflix Hystrix and similar resilience libraries
- **Multi-Agent Systems**: Research in distributed AI and workflow orchestration
- **Configuration Management**: Inspired by Kubernetes and Ansible configuration approaches

---

## 📚 Additional Resources

- [Design Patterns in Python](https://refactoring.guru/design-patterns/python)
- [Enterprise Integration Patterns](https://www.enterpriseintegrationpatterns.com/)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Multi-Agent Systems](https://en.wikipedia.org/wiki/Multi-agent_system)
- [Workflow Orchestration Patterns](https://docs.microsoft.com/en-us/azure/architecture/patterns/)

For more examples and detailed documentation, visit our [Wiki](https://github.com/your-repo/lead-agent/wiki) or check the `examples/` directory.

---

**Built with ❤️ for the AI and automation community**
