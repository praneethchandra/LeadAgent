"""Core data models for the Lead Agent system."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIALLY_COMPLETED = "partially_completed"


class AgentType(str, Enum):
    """Types of agents that can be communicated with."""
    AI_AGENT = "ai_agent"
    MCP_SERVER = "mcp_server"
    HTTP_API = "http_api"
    CUSTOM = "custom"


class RetryConfig(BaseModel):
    """Configuration for retry logic."""
    max_attempts: int = Field(default=3, ge=1, le=10)
    initial_delay: float = Field(default=1.0, ge=0.1)
    max_delay: float = Field(default=60.0, ge=1.0)
    exponential_base: float = Field(default=2.0, ge=1.1)
    jitter: bool = Field(default=True)


class CircuitBreakerConfig(BaseModel):
    """Configuration for circuit breaker pattern."""
    failure_threshold: int = Field(default=5, ge=1)
    recovery_timeout: float = Field(default=60.0, ge=1.0)
    expected_exception: Optional[str] = None


class AgentConfig(BaseModel):
    """Configuration for an agent."""
    name: str
    type: AgentType
    endpoint: Optional[str] = None
    authentication: Optional[Dict[str, Any]] = None
    timeout: float = Field(default=30.0, ge=1.0)
    retry_config: RetryConfig = Field(default_factory=RetryConfig)
    circuit_breaker: CircuitBreakerConfig = Field(default_factory=CircuitBreakerConfig)
    custom_params: Dict[str, Any] = Field(default_factory=dict)


class TaskConfig(BaseModel):
    """Configuration for a task."""
    name: str
    description: Optional[str] = None
    agent_name: str
    action: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    timeout: float = Field(default=30.0, ge=1.0)
    retry_config: RetryConfig = Field(default_factory=RetryConfig)
    depends_on: List[str] = Field(default_factory=list)
    continue_on_failure: bool = Field(default=False)


class WorkflowConfig(BaseModel):
    """Configuration for a workflow."""
    name: str
    description: Optional[str] = None
    version: str = Field(default="1.0.0")
    tasks: List[TaskConfig]
    agents: List[AgentConfig]
    global_timeout: Optional[float] = None
    parallel_execution: bool = Field(default=False)
    failure_strategy: str = Field(default="stop_on_first_failure")

    @field_validator("failure_strategy")
    @classmethod
    def validate_failure_strategy(cls, v: str) -> str:
        """Validate failure strategy."""
        valid_strategies = [
            "stop_on_first_failure",
            "continue_on_failure",
            "partial_completion_allowed"
        ]
        if v not in valid_strategies:
            raise ValueError(f"Invalid failure strategy: {v}")
        return v


class TaskExecution(BaseModel):
    """Runtime task execution state."""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    attempts: int = 0
    max_attempts: int = 3
    result: Optional[Any] = None
    error: Optional[str] = None
    dependencies_completed: bool = False
    agent_name: str
    action: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class WorkflowExecution(BaseModel):
    """Runtime workflow execution state."""
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    tasks: List[TaskExecution] = Field(default_factory=list)
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_tasks: int = 0
    partial_completion_allowed: bool = False


class AgentResponse(BaseModel):
    """Response from an agent."""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowResult(BaseModel):
    """Final result of workflow execution."""
    workflow_id: str
    status: WorkflowStatus
    completed_tasks: int
    failed_tasks: int
    total_tasks: int
    execution_time: float
    results: Dict[str, Any] = Field(default_factory=dict)
    errors: Dict[str, str] = Field(default_factory=dict)
