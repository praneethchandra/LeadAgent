"""Main workflow execution engine."""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional

import structlog

from ..agents.base import AgentFactory, BaseAgent
from ..config_loader import ConfigLoader
from ..models import (
    TaskConfig, TaskExecution, WorkflowConfig, WorkflowExecution, 
    WorkflowResult, WorkflowStatus, TaskStatus
)
from ..patterns.observer import Observer
from .executor import TaskExecutor
from .state_machine import WorkflowStateMachine

logger = structlog.get_logger(__name__)


class WorkflowEngine(Observer):
    """Main engine for executing workflows."""
    
    def __init__(self):
        """Initialize workflow engine."""
        self.agents: Dict[str, BaseAgent] = {}
        self.task_executor: Optional[TaskExecutor] = None
        self.state_machine: Optional[WorkflowStateMachine] = None
        self.workflow_config: Optional[WorkflowConfig] = None
        self.workflow_execution: Optional[WorkflowExecution] = None
    
    async def load_workflow(self, config_path: str) -> None:
        """Load workflow configuration from file.
        
        Args:
            config_path: Path to workflow configuration file
        """
        try:
            # Load and validate configuration
            self.workflow_config = ConfigLoader.load_from_file(config_path)
            ConfigLoader.validate_configuration(self.workflow_config)
            
            # Create agents
            self.agents = {}
            for agent_config in self.workflow_config.agents:
                agent = AgentFactory.create_agent(agent_config)
                self.agents[agent_config.name] = agent
            
            # Create task executor
            self.task_executor = TaskExecutor(self.agents)
            
            logger.info("Workflow loaded successfully", workflow=self.workflow_config.name)
            
        except Exception as e:
            logger.error("Failed to load workflow", error=str(e))
            raise
    
    async def execute_workflow(self) -> WorkflowResult:
        """Execute the loaded workflow.
        
        Returns:
            WorkflowResult: Result of workflow execution
        """
        if not self.workflow_config:
            raise ValueError("No workflow configuration loaded")
        
        start_time = time.time()
        
        try:
            # Create workflow execution instance
            self.workflow_execution = WorkflowExecution(
                name=self.workflow_config.name,
                total_tasks=len(self.workflow_config.tasks),
                partial_completion_allowed=(
                    self.workflow_config.failure_strategy == "partial_completion_allowed"
                )
            )
            
            # Create task executions
            for task_config in self.workflow_config.tasks:
                task_execution = TaskExecution(
                    name=task_config.name,
                    agent_name=task_config.agent_name,
                    action=task_config.action,
                    parameters=task_config.parameters,
                    max_attempts=task_config.retry_config.max_attempts
                )
                self.workflow_execution.tasks.append(task_execution)
            
            # Create state machine and attach observers
            self.state_machine = WorkflowStateMachine(self.workflow_execution)
            self.state_machine.attach(self)
            
            # Start workflow execution
            await self.state_machine.start_workflow()
            
            # Execute workflow based on strategy
            if self.workflow_config.parallel_execution:
                await self._execute_parallel()
            else:
                await self._execute_sequential()
            
            # Wait for completion or timeout
            await self._wait_for_completion()
            
            execution_time = time.time() - start_time
            
            return WorkflowResult(
                workflow_id=self.workflow_execution.workflow_id,
                status=self.workflow_execution.status,
                completed_tasks=self.workflow_execution.completed_tasks,
                failed_tasks=self.workflow_execution.failed_tasks,
                total_tasks=self.workflow_execution.total_tasks,
                execution_time=execution_time,
                results=self._collect_results(),
                errors=self._collect_errors()
            )
            
        except Exception as e:
            logger.error("Workflow execution failed", error=str(e))
            if self.state_machine:
                await self.state_machine.fail_workflow(str(e))
            raise
    
    async def _execute_parallel(self) -> None:
        """Execute tasks in parallel where possible."""
        logger.info("Starting parallel workflow execution")
        
        while True:
            # Get ready tasks
            ready_tasks = self.state_machine.get_ready_tasks()
            retryable_tasks = self.state_machine.get_retryable_tasks()
            
            all_tasks = ready_tasks + retryable_tasks
            
            if not all_tasks:
                # No more tasks to execute
                break
            
            # Execute all ready tasks concurrently
            tasks = [self._execute_single_task(task) for task in all_tasks]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Small delay to prevent busy waiting
            await asyncio.sleep(0.1)
    
    async def _execute_sequential(self) -> None:
        """Execute tasks sequentially based on dependencies."""
        logger.info("Starting sequential workflow execution")
        
        while True:
            # Get ready tasks (should be one at a time for sequential)
            ready_tasks = self.state_machine.get_ready_tasks()
            retryable_tasks = self.state_machine.get_retryable_tasks()
            
            all_tasks = ready_tasks + retryable_tasks
            
            if not all_tasks:
                # No more tasks to execute
                break
            
            # Execute one task at a time
            for task in all_tasks[:1]:  # Take only first task for sequential
                await self._execute_single_task(task)
            
            # Small delay to prevent busy waiting
            await asyncio.sleep(0.1)
    
    async def _execute_single_task(self, task: TaskExecution) -> None:
        """Execute a single task.
        
        Args:
            task: Task to execute
        """
        try:
            # Start task execution
            await self.state_machine.start_task(task)
            
            # Execute task
            response = await self.task_executor.execute_task(task)
            
            if response.success:
                await self.state_machine.complete_task(task, response.result)
            else:
                await self.state_machine.fail_task(task, response.error or "Unknown error")
                
        except Exception as e:
            await self.state_machine.fail_task(task, str(e))
    
    async def _wait_for_completion(self) -> None:
        """Wait for workflow completion or timeout."""
        timeout = self.workflow_config.global_timeout
        start_time = time.time()
        
        while self.workflow_execution.status == WorkflowStatus.RUNNING:
            if timeout and (time.time() - start_time) > timeout:
                await self.state_machine.fail_workflow("Workflow timeout")
                break
            
            await asyncio.sleep(0.5)
    
    def _collect_results(self) -> Dict[str, any]:
        """Collect results from completed tasks.
        
        Returns:
            Dictionary of task results
        """
        results = {}
        for task in self.workflow_execution.tasks:
            if task.status == TaskStatus.COMPLETED and task.result is not None:
                results[task.name] = task.result
        return results
    
    def _collect_errors(self) -> Dict[str, str]:
        """Collect errors from failed tasks.
        
        Returns:
            Dictionary of task errors
        """
        errors = {}
        for task in self.workflow_execution.tasks:
            if task.status == TaskStatus.FAILED and task.error:
                errors[task.name] = task.error
        return errors
    
    async def update(self, subject, event_type: str, data: any) -> None:
        """Handle notifications from state machine.
        
        Args:
            subject: Subject that sent the notification
            event_type: Type of event
            data: Event data
        """
        logger.info("Workflow event", event=event_type, data=data)
