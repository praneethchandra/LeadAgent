"""API models for the Lead Agent REST API."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class WorkflowRequest(BaseModel):
    """Request model for workflow execution."""
    
    name: str = Field(..., description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    version: str = Field("1.0.0", description="Workflow version")
    parallel_execution: bool = Field(False, description="Enable parallel execution")
    failure_strategy: str = Field("stop_on_first_failure", description="Failure handling strategy")
    global_timeout: Optional[int] = Field(None, description="Global timeout in seconds")
    agents: List[Dict[str, Any]] = Field(..., description="Agent configurations")
    tasks: List[Dict[str, Any]] = Field(..., description="Task definitions")


class WorkflowResponse(BaseModel):
    """Response model for workflow operations."""
    
    execution_id: UUID = Field(default_factory=uuid4, description="Unique execution ID")
    name: str = Field(..., description="Workflow name")
    status: str = Field(..., description="Execution status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")
    total_tasks: int = Field(0, description="Total number of tasks")
    completed_tasks: int = Field(0, description="Number of completed tasks")
    results: Optional[Dict[str, Any]] = Field(None, description="Task results")
    errors: Optional[Dict[str, str]] = Field(None, description="Task errors")


class WorkflowListResponse(BaseModel):
    """Response model for listing workflows."""
    
    workflows: List[WorkflowResponse] = Field(..., description="List of workflows")
    total: int = Field(..., description="Total number of workflows")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(10, description="Number of items per page")


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status."""
    
    execution_id: UUID = Field(..., description="Execution ID")
    status: str = Field(..., description="Current status")
    progress: float = Field(..., description="Progress percentage (0-100)")
    current_task: Optional[str] = Field(None, description="Currently executing task")
    message: Optional[str] = Field(None, description="Status message")


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    execution_id: Optional[UUID] = Field(None, description="Related execution ID")


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field("healthy", description="Service status")
    version: str = Field("1.0.0", description="API version")
    uptime: float = Field(..., description="Uptime in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Current timestamp")


class AgentTestRequest(BaseModel):
    """Request model for testing agent connectivity."""
    
    agent_config: Dict[str, Any] = Field(..., description="Agent configuration")
    test_action: str = Field("ping", description="Test action to perform")
    test_parameters: Dict[str, Any] = Field(default_factory=dict, description="Test parameters")


class AgentTestResponse(BaseModel):
    """Response model for agent testing."""
    
    agent_name: str = Field(..., description="Agent name")
    success: bool = Field(..., description="Test success status")
    response_time: float = Field(..., description="Response time in seconds")
    result: Optional[Any] = Field(None, description="Test result")
    error: Optional[str] = Field(None, description="Error message if test failed")
