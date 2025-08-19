"""Tests for core models."""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from src.lead_agent.models import (
    TaskStatus, WorkflowStatus, AgentType, RetryConfig, CircuitBreakerConfig,
    AgentConfig, TaskConfig, WorkflowConfig, TaskExecution, WorkflowExecution,
    AgentResponse, WorkflowResult
)


class TestRetryConfig:
    """Test RetryConfig model."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = RetryConfig(
            max_attempts=5,
            initial_delay=0.5,
            max_delay=30.0,
            exponential_base=1.5,
            jitter=False
        )
        assert config.max_attempts == 5
        assert config.initial_delay == 0.5
        assert config.max_delay == 30.0
        assert config.exponential_base == 1.5
        assert config.jitter is False
    
    def test_validation_constraints(self):
        """Test validation constraints."""
        # max_attempts must be >= 1 and <= 10
        with pytest.raises(ValidationError):
            RetryConfig(max_attempts=0)
        
        with pytest.raises(ValidationError):
            RetryConfig(max_attempts=11)
        
        # initial_delay must be >= 0.1
        with pytest.raises(ValidationError):
            RetryConfig(initial_delay=0.05)
        
        # max_delay must be >= 1.0
        with pytest.raises(ValidationError):
            RetryConfig(max_delay=0.5)
        
        # exponential_base must be >= 1.1
        with pytest.raises(ValidationError):
            RetryConfig(exponential_base=1.0)


class TestCircuitBreakerConfig:
    """Test CircuitBreakerConfig model."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.recovery_timeout == 60.0
        assert config.expected_exception is None
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30.0,
            expected_exception="TimeoutError"
        )
        assert config.failure_threshold == 3
        assert config.recovery_timeout == 30.0
        assert config.expected_exception == "TimeoutError"
    
    def test_validation_constraints(self):
        """Test validation constraints."""
        # failure_threshold must be >= 1
        with pytest.raises(ValidationError):
            CircuitBreakerConfig(failure_threshold=0)
        
        # recovery_timeout must be >= 1.0
        with pytest.raises(ValidationError):
            CircuitBreakerConfig(recovery_timeout=0.5)


class TestAgentConfig:
    """Test AgentConfig model."""
    
    def test_minimal_config(self):
        """Test minimal agent configuration."""
        config = AgentConfig(name="test_agent", type=AgentType.AI_AGENT)
        assert config.name == "test_agent"
        assert config.type == AgentType.AI_AGENT
        assert config.endpoint is None
        assert config.authentication is None
        assert config.timeout == 30.0
        assert isinstance(config.retry_config, RetryConfig)
        assert isinstance(config.circuit_breaker, CircuitBreakerConfig)
        assert config.custom_params == {}
    
    def test_full_config(self):
        """Test full agent configuration."""
        config = AgentConfig(
            name="test_agent",
            type=AgentType.HTTP_API,
            endpoint="https://api.example.com",
            authentication={"type": "bearer", "token": "secret"},
            timeout=60.0,
            retry_config=RetryConfig(max_attempts=5),
            circuit_breaker=CircuitBreakerConfig(failure_threshold=3),
            custom_params={"version": "v1"}
        )
        assert config.name == "test_agent"
        assert config.type == AgentType.HTTP_API
        assert config.endpoint == "https://api.example.com"
        assert config.authentication == {"type": "bearer", "token": "secret"}
        assert config.timeout == 60.0
        assert config.retry_config.max_attempts == 5
        assert config.circuit_breaker.failure_threshold == 3
        assert config.custom_params == {"version": "v1"}


class TestTaskConfig:
    """Test TaskConfig model."""
    
    def test_minimal_config(self):
        """Test minimal task configuration."""
        config = TaskConfig(name="test_task", agent_name="test_agent", action="test_action")
        assert config.name == "test_task"
        assert config.description is None
        assert config.agent_name == "test_agent"
        assert config.action == "test_action"
        assert config.parameters == {}
        assert config.timeout == 30.0
        assert isinstance(config.retry_config, RetryConfig)
        assert config.depends_on == []
        assert config.continue_on_failure is False
    
    def test_full_config(self):
        """Test full task configuration."""
        config = TaskConfig(
            name="test_task",
            description="A test task",
            agent_name="test_agent",
            action="test_action",
            parameters={"param1": "value1"},
            timeout=45.0,
            retry_config=RetryConfig(max_attempts=2),
            depends_on=["task1", "task2"],
            continue_on_failure=True
        )
        assert config.name == "test_task"
        assert config.description == "A test task"
        assert config.agent_name == "test_agent"
        assert config.action == "test_action"
        assert config.parameters == {"param1": "value1"}
        assert config.timeout == 45.0
        assert config.retry_config.max_attempts == 2
        assert config.depends_on == ["task1", "task2"]
        assert config.continue_on_failure is True


class TestWorkflowConfig:
    """Test WorkflowConfig model."""
    
    def test_minimal_config(self):
        """Test minimal workflow configuration."""
        task = TaskConfig(name="task1", agent_name="agent1", action="action1")
        agent = AgentConfig(name="agent1", type=AgentType.AI_AGENT)
        
        config = WorkflowConfig(
            name="test_workflow",
            tasks=[task],
            agents=[agent]
        )
        assert config.name == "test_workflow"
        assert config.description is None
        assert config.version == "1.0.0"
        assert len(config.tasks) == 1
        assert len(config.agents) == 1
        assert config.global_timeout is None
        assert config.parallel_execution is False
        assert config.failure_strategy == "stop_on_first_failure"
    
    def test_full_config(self):
        """Test full workflow configuration."""
        task = TaskConfig(name="task1", agent_name="agent1", action="action1")
        agent = AgentConfig(name="agent1", type=AgentType.AI_AGENT)
        
        config = WorkflowConfig(
            name="test_workflow",
            description="A test workflow",
            version="2.0.0",
            tasks=[task],
            agents=[agent],
            global_timeout=300.0,
            parallel_execution=True,
            failure_strategy="continue_on_failure"
        )
        assert config.name == "test_workflow"
        assert config.description == "A test workflow"
        assert config.version == "2.0.0"
        assert config.global_timeout == 300.0
        assert config.parallel_execution is True
        assert config.failure_strategy == "continue_on_failure"
    
    def test_invalid_failure_strategy(self):
        """Test invalid failure strategy validation."""
        task = TaskConfig(name="task1", agent_name="agent1", action="action1")
        agent = AgentConfig(name="agent1", type=AgentType.AI_AGENT)
        
        with pytest.raises(ValidationError):
            WorkflowConfig(
                name="test_workflow",
                tasks=[task],
                agents=[agent],
                failure_strategy="invalid_strategy"
            )


class TestTaskExecution:
    """Test TaskExecution model."""
    
    def test_default_values(self):
        """Test default execution values."""
        execution = TaskExecution(
            name="test_task",
            agent_name="test_agent",
            action="test_action"
        )
        assert execution.name == "test_task"
        assert execution.status == TaskStatus.PENDING
        assert execution.start_time is None
        assert execution.end_time is None
        assert execution.attempts == 0
        assert execution.max_attempts == 3
        assert execution.result is None
        assert execution.error is None
        assert execution.dependencies_completed is False
        assert execution.agent_name == "test_agent"
        assert execution.action == "test_action"
        assert execution.parameters == {}
        # task_id should be auto-generated UUID
        assert len(execution.task_id) == 36  # UUID length
    
    def test_custom_values(self):
        """Test custom execution values."""
        now = datetime.now(timezone.utc)
        execution = TaskExecution(
            task_id="custom-id",
            name="test_task",
            status=TaskStatus.RUNNING,
            start_time=now,
            attempts=1,
            max_attempts=5,
            result={"success": True},
            error="test error",
            dependencies_completed=True,
            agent_name="test_agent",
            action="test_action",
            parameters={"param": "value"}
        )
        assert execution.task_id == "custom-id"
        assert execution.status == TaskStatus.RUNNING
        assert execution.start_time == now
        assert execution.attempts == 1
        assert execution.max_attempts == 5
        assert execution.result == {"success": True}
        assert execution.error == "test error"
        assert execution.dependencies_completed is True
        assert execution.parameters == {"param": "value"}


class TestWorkflowExecution:
    """Test WorkflowExecution model."""
    
    def test_default_values(self):
        """Test default execution values."""
        execution = WorkflowExecution(name="test_workflow")
        assert execution.name == "test_workflow"
        assert execution.status == WorkflowStatus.PENDING
        assert execution.start_time is None
        assert execution.end_time is None
        assert execution.tasks == []
        assert execution.completed_tasks == 0
        assert execution.failed_tasks == 0
        assert execution.total_tasks == 0
        assert execution.partial_completion_allowed is False
        # workflow_id should be auto-generated UUID
        assert len(execution.workflow_id) == 36  # UUID length
    
    def test_custom_values(self):
        """Test custom execution values."""
        now = datetime.now(timezone.utc)
        task = TaskExecution(name="task1", agent_name="agent1", action="action1")
        
        execution = WorkflowExecution(
            workflow_id="custom-id",
            name="test_workflow",
            status=WorkflowStatus.RUNNING,
            start_time=now,
            tasks=[task],
            completed_tasks=1,
            failed_tasks=0,
            total_tasks=1,
            partial_completion_allowed=True
        )
        assert execution.workflow_id == "custom-id"
        assert execution.status == WorkflowStatus.RUNNING
        assert execution.start_time == now
        assert len(execution.tasks) == 1
        assert execution.completed_tasks == 1
        assert execution.failed_tasks == 0
        assert execution.total_tasks == 1
        assert execution.partial_completion_allowed is True


class TestAgentResponse:
    """Test AgentResponse model."""
    
    def test_success_response(self):
        """Test successful response."""
        response = AgentResponse(
            success=True,
            result={"data": "test"},
            execution_time=1.5,
            metadata={"status": "ok"}
        )
        assert response.success is True
        assert response.result == {"data": "test"}
        assert response.error is None
        assert response.execution_time == 1.5
        assert response.metadata == {"status": "ok"}
    
    def test_error_response(self):
        """Test error response."""
        response = AgentResponse(
            success=False,
            error="Test error",
            execution_time=0.5
        )
        assert response.success is False
        assert response.result is None
        assert response.error == "Test error"
        assert response.execution_time == 0.5
        assert response.metadata == {}


class TestWorkflowResult:
    """Test WorkflowResult model."""
    
    def test_complete_result(self):
        """Test complete workflow result."""
        result = WorkflowResult(
            workflow_id="test-id",
            status=WorkflowStatus.COMPLETED,
            completed_tasks=3,
            failed_tasks=0,
            total_tasks=3,
            execution_time=45.2,
            results={"task1": "result1", "task2": "result2"},
            errors={}
        )
        assert result.workflow_id == "test-id"
        assert result.status == WorkflowStatus.COMPLETED
        assert result.completed_tasks == 3
        assert result.failed_tasks == 0
        assert result.total_tasks == 3
        assert result.execution_time == 45.2
        assert result.results == {"task1": "result1", "task2": "result2"}
        assert result.errors == {}
    
    def test_failed_result(self):
        """Test failed workflow result."""
        result = WorkflowResult(
            workflow_id="test-id",
            status=WorkflowStatus.FAILED,
            completed_tasks=1,
            failed_tasks=2,
            total_tasks=3,
            execution_time=30.1,
            results={"task1": "result1"},
            errors={"task2": "error2", "task3": "error3"}
        )
        assert result.status == WorkflowStatus.FAILED
        assert result.completed_tasks == 1
        assert result.failed_tasks == 2
        assert result.results == {"task1": "result1"}
        assert result.errors == {"task2": "error2", "task3": "error3"}
