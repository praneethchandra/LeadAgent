"""Tests for workflow components."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from src.lead_agent.models import (
    TaskExecution, TaskStatus, WorkflowExecution, WorkflowStatus,
    AgentResponse, AgentConfig, AgentType
)
from src.lead_agent.workflow.state_machine import WorkflowStateMachine
from src.lead_agent.workflow.executor import TaskExecutor
from src.lead_agent.workflow.engine import WorkflowEngine
from src.lead_agent.agents.base import BaseAgent


class MockAgent(BaseAgent):
    """Mock agent for testing."""
    
    def __init__(self, config: AgentConfig, responses: list = None):
        super().__init__(config)
        self.responses = responses or [AgentResponse(success=True, result="mock_result")]
        self.call_count = 0
    
    async def execute(self, action: str, parameters: dict) -> AgentResponse:
        """Mock execution with predefined responses."""
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
        else:
            response = AgentResponse(success=True, result=f"mock_result_{self.call_count}")
        
        self.call_count += 1
        return response


class TestWorkflowStateMachine:
    """Test WorkflowStateMachine class."""
    
    def test_initial_state(self):
        """Test initial state machine state."""
        workflow = WorkflowExecution(name="test_workflow")
        sm = WorkflowStateMachine(workflow)
        
        assert sm.workflow_execution is workflow
        assert workflow.status == WorkflowStatus.PENDING
    
    def test_start_workflow(self):
        """Test starting workflow execution."""
        workflow = WorkflowExecution(name="test_workflow")
        sm = WorkflowStateMachine(workflow)
        
        asyncio.run(sm.start_workflow())
        
        assert workflow.status == WorkflowStatus.RUNNING
        assert workflow.start_time is not None
    
    def test_start_workflow_invalid_state(self):
        """Test starting workflow in invalid state."""
        workflow = WorkflowExecution(name="test_workflow", status=WorkflowStatus.RUNNING)
        sm = WorkflowStateMachine(workflow)
        
        with pytest.raises(ValueError) as exc_info:
            asyncio.run(sm.start_workflow())
        
        assert "not in pending state" in str(exc_info.value)
    
    def test_start_task(self):
        """Test starting task execution."""
        workflow = WorkflowExecution(name="test_workflow")
        task = TaskExecution(name="test_task", agent_name="test_agent", action="test_action")
        workflow.tasks.append(task)
        
        sm = WorkflowStateMachine(workflow)
        
        asyncio.run(sm.start_task(task))
        
        assert task.status == TaskStatus.RUNNING
        assert task.start_time is not None
        assert task.attempts == 1
    
    def test_start_task_invalid_state(self):
        """Test starting task in invalid state."""
        workflow = WorkflowExecution(name="test_workflow")
        task = TaskExecution(
            name="test_task", 
            agent_name="test_agent", 
            action="test_action",
            status=TaskStatus.RUNNING
        )
        
        sm = WorkflowStateMachine(workflow)
        
        with pytest.raises(ValueError) as exc_info:
            asyncio.run(sm.start_task(task))
        
        assert "not in pending state" in str(exc_info.value)
    
    def test_complete_task(self):
        """Test completing task execution."""
        workflow = WorkflowExecution(name="test_workflow", total_tasks=1)
        task = TaskExecution(
            name="test_task",
            agent_name="test_agent",
            action="test_action",
            status=TaskStatus.RUNNING
        )
        workflow.tasks.append(task)
        
        sm = WorkflowStateMachine(workflow)
        asyncio.run(sm.start_workflow())
        
        asyncio.run(sm.complete_task(task, "test_result"))
        
        assert task.status == TaskStatus.COMPLETED
        assert task.end_time is not None
        assert task.result == "test_result"
        assert workflow.status == WorkflowStatus.COMPLETED
        assert workflow.completed_tasks == 1
    
    def test_fail_task_with_retries(self):
        """Test failing task with retry attempts remaining."""
        workflow = WorkflowExecution(name="test_workflow")
        task = TaskExecution(
            name="test_task",
            agent_name="test_agent",
            action="test_action",
            status=TaskStatus.RUNNING,
            attempts=1,
            max_attempts=3
        )
        workflow.tasks.append(task)
        
        sm = WorkflowStateMachine(workflow)
        
        asyncio.run(sm.fail_task(task, "test_error"))
        
        assert task.status == TaskStatus.RETRYING
        assert task.error == "test_error"
        assert task.end_time is not None
    
    def test_fail_task_exhausted_retries(self):
        """Test failing task with no retry attempts remaining."""
        workflow = WorkflowExecution(name="test_workflow", total_tasks=1)
        task = TaskExecution(
            name="test_task",
            agent_name="test_agent",
            action="test_action",
            status=TaskStatus.RUNNING,
            attempts=3,
            max_attempts=3
        )
        workflow.tasks.append(task)
        
        sm = WorkflowStateMachine(workflow)
        asyncio.run(sm.start_workflow())
        
        asyncio.run(sm.fail_task(task, "test_error"))
        
        assert task.status == TaskStatus.FAILED
        assert task.error == "test_error"
        assert workflow.status == WorkflowStatus.FAILED
    
    def test_get_ready_tasks(self):
        """Test getting ready tasks."""
        workflow = WorkflowExecution(name="test_workflow")
        
        task1 = TaskExecution(name="task1", agent_name="agent1", action="action1")
        task2 = TaskExecution(name="task2", agent_name="agent2", action="action2")
        task3 = TaskExecution(name="task3", agent_name="agent3", action="action3", status=TaskStatus.RUNNING)
        
        workflow.tasks.extend([task1, task2, task3])
        
        sm = WorkflowStateMachine(workflow)
        ready_tasks = sm.get_ready_tasks()
        
        # Only pending tasks with satisfied dependencies should be ready
        assert len(ready_tasks) == 2
        assert task1 in ready_tasks
        assert task2 in ready_tasks
        assert task3 not in ready_tasks
    
    def test_get_retryable_tasks(self):
        """Test getting retryable tasks."""
        workflow = WorkflowExecution(name="test_workflow")
        
        task1 = TaskExecution(name="task1", agent_name="agent1", action="action1", status=TaskStatus.PENDING)
        task2 = TaskExecution(name="task2", agent_name="agent2", action="action2", status=TaskStatus.RETRYING)
        task3 = TaskExecution(name="task3", agent_name="agent3", action="action3", status=TaskStatus.FAILED)
        
        workflow.tasks.extend([task1, task2, task3])
        
        sm = WorkflowStateMachine(workflow)
        retryable_tasks = sm.get_retryable_tasks()
        
        assert len(retryable_tasks) == 1
        assert task2 in retryable_tasks
    
    def test_complete_workflow_all_completed(self):
        """Test completing workflow when all tasks are completed."""
        workflow = WorkflowExecution(name="test_workflow", total_tasks=2, status=WorkflowStatus.RUNNING)
        
        task1 = TaskExecution(name="task1", agent_name="agent1", action="action1", status=TaskStatus.COMPLETED)
        task2 = TaskExecution(name="task2", agent_name="agent2", action="action2", status=TaskStatus.COMPLETED)
        
        workflow.tasks.extend([task1, task2])
        
        sm = WorkflowStateMachine(workflow)
        asyncio.run(sm.complete_workflow())
        
        assert workflow.status == WorkflowStatus.COMPLETED
        assert workflow.end_time is not None
        assert workflow.completed_tasks == 2
        assert workflow.failed_tasks == 0
    
    def test_complete_workflow_partial_completion(self):
        """Test completing workflow with partial completion allowed."""
        workflow = WorkflowExecution(
            name="test_workflow",
            total_tasks=3,
            status=WorkflowStatus.RUNNING,
            partial_completion_allowed=True
        )
        
        task1 = TaskExecution(name="task1", agent_name="agent1", action="action1", status=TaskStatus.COMPLETED)
        task2 = TaskExecution(name="task2", agent_name="agent2", action="action2", status=TaskStatus.FAILED)
        task3 = TaskExecution(name="task3", agent_name="agent3", action="action3", status=TaskStatus.COMPLETED)
        
        workflow.tasks.extend([task1, task2, task3])
        
        sm = WorkflowStateMachine(workflow)
        asyncio.run(sm.complete_workflow())
        
        assert workflow.status == WorkflowStatus.PARTIALLY_COMPLETED
        assert workflow.completed_tasks == 2
        assert workflow.failed_tasks == 1


class TestTaskExecutor:
    """Test TaskExecutor class."""
    
    def test_execute_task_success(self):
        """Test successful task execution."""
        agent_config = AgentConfig(name="test_agent", type=AgentType.AI_AGENT)
        agent = MockAgent(agent_config, [AgentResponse(success=True, result="success_result")])
        
        executor = TaskExecutor({"test_agent": agent})
        
        task = TaskExecution(
            name="test_task",
            agent_name="test_agent",
            action="test_action",
            parameters={"param": "value"}
        )
        
        response = asyncio.run(executor.execute_task(task))
        
        assert response.success is True
        assert response.result == "success_result"
        assert agent.call_count == 1
    
    def test_execute_task_agent_not_found(self):
        """Test task execution with missing agent."""
        executor = TaskExecutor({})
        
        task = TaskExecution(
            name="test_task",
            agent_name="missing_agent",
            action="test_action"
        )
        
        response = asyncio.run(executor.execute_task(task))
        
        assert response.success is False
        assert "Agent 'missing_agent' not found" in response.error
    
    def test_execute_task_agent_failure(self):
        """Test task execution with agent failure."""
        agent_config = AgentConfig(name="test_agent", type=AgentType.AI_AGENT)
        agent = MockAgent(agent_config, [AgentResponse(success=False, error="agent_error")])
        
        executor = TaskExecutor({"test_agent": agent})
        
        task = TaskExecution(
            name="test_task",
            agent_name="test_agent",
            action="test_action"
        )
        
        response = asyncio.run(executor.execute_task(task))
        
        assert response.success is False
        assert response.error == "agent_error"
    
    def test_execute_task_exception(self):
        """Test task execution with exception."""
        agent_config = AgentConfig(name="test_agent", type=AgentType.AI_AGENT)
        
        class FailingAgent(MockAgent):
            async def execute_with_resilience(self, action: str, parameters: dict) -> AgentResponse:
                raise Exception("execution_exception")
        
        agent = FailingAgent(agent_config)
        executor = TaskExecutor({"test_agent": agent})
        
        task = TaskExecution(
            name="test_task",
            agent_name="test_agent",
            action="test_action"
        )
        
        response = asyncio.run(executor.execute_task(task))
        
        assert response.success is False
        assert "Task execution failed: execution_exception" in response.error


class TestWorkflowEngine:
    """Test WorkflowEngine class."""
    
    def test_initial_state(self):
        """Test initial engine state."""
        engine = WorkflowEngine()
        
        assert engine.agents == {}
        assert engine.task_executor is None
        assert engine.state_machine is None
        assert engine.workflow_config is None
        assert engine.workflow_execution is None
    
    @pytest.mark.asyncio
    async def test_execute_workflow_not_loaded(self):
        """Test executing workflow without loading configuration."""
        engine = WorkflowEngine()
        
        with pytest.raises(ValueError) as exc_info:
            await engine.execute_workflow()
        
        assert "No workflow configuration loaded" in str(exc_info.value)
    
    def test_observer_update(self):
        """Test observer update method."""
        engine = WorkflowEngine()
        
        # Should not raise any exceptions
        asyncio.run(engine.update(None, "test_event", "test_data"))
