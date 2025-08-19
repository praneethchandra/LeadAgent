"""State machine for workflow execution."""

from datetime import datetime, timezone
from typing import Dict, List, Set

from ..models import TaskExecution, TaskStatus, WorkflowExecution, WorkflowStatus
from ..patterns.observer import Subject


class WorkflowStateMachine(Subject):
    """State machine for managing workflow execution state."""
    
    def __init__(self, workflow_execution: WorkflowExecution):
        """Initialize state machine.
        
        Args:
            workflow_execution: Workflow execution instance to manage
        """
        super().__init__()
        self.workflow_execution = workflow_execution
        self._task_dependencies: Dict[str, Set[str]] = {}
        self._build_dependency_graph()
    
    def _build_dependency_graph(self) -> None:
        """Build task dependency graph."""
        for task in self.workflow_execution.tasks:
            # For now, we'll assume dependencies are stored in task metadata
            # In a real implementation, this would come from the task configuration
            self._task_dependencies[task.name] = set()
    
    async def start_workflow(self) -> None:
        """Start workflow execution."""
        if self.workflow_execution.status != WorkflowStatus.PENDING:
            raise ValueError("Workflow is not in pending state")
        
        self.workflow_execution.status = WorkflowStatus.RUNNING
        self.workflow_execution.start_time = datetime.now(timezone.utc)
        
        await self.notify("workflow_started", self.workflow_execution)
    
    async def complete_workflow(self) -> None:
        """Complete workflow execution."""
        if self.workflow_execution.status != WorkflowStatus.RUNNING:
            return
        
        # Determine final status based on task results
        failed_tasks = sum(1 for task in self.workflow_execution.tasks 
                          if task.status == TaskStatus.FAILED)
        completed_tasks = sum(1 for task in self.workflow_execution.tasks 
                             if task.status == TaskStatus.COMPLETED)
        
        if failed_tasks == 0:
            self.workflow_execution.status = WorkflowStatus.COMPLETED
        elif completed_tasks > 0 and self.workflow_execution.partial_completion_allowed:
            self.workflow_execution.status = WorkflowStatus.PARTIALLY_COMPLETED
        else:
            self.workflow_execution.status = WorkflowStatus.FAILED
        
        self.workflow_execution.end_time = datetime.now(timezone.utc)
        self.workflow_execution.completed_tasks = completed_tasks
        self.workflow_execution.failed_tasks = failed_tasks
        
        await self.notify("workflow_completed", self.workflow_execution)
    
    async def fail_workflow(self, error: str) -> None:
        """Fail workflow execution."""
        self.workflow_execution.status = WorkflowStatus.FAILED
        self.workflow_execution.end_time = datetime.now(timezone.utc)
        
        await self.notify("workflow_failed", {"workflow": self.workflow_execution, "error": error})
    
    async def start_task(self, task: TaskExecution) -> None:
        """Start task execution."""
        if task.status != TaskStatus.PENDING:
            raise ValueError(f"Task {task.name} is not in pending state")
        
        task.status = TaskStatus.RUNNING
        task.start_time = datetime.now(timezone.utc)
        task.attempts += 1
        
        await self.notify("task_started", task)
    
    async def complete_task(self, task: TaskExecution, result: any = None) -> None:
        """Complete task execution."""
        if task.status not in [TaskStatus.RUNNING, TaskStatus.RETRYING]:
            return
        
        task.status = TaskStatus.COMPLETED
        task.end_time = datetime.now(timezone.utc)
        task.result = result
        
        await self.notify("task_completed", task)
        
        # Check if workflow can be completed
        if self._all_tasks_finished():
            await self.complete_workflow()
    
    async def fail_task(self, task: TaskExecution, error: str) -> None:
        """Fail task execution."""
        task.error = error
        task.end_time = datetime.now(timezone.utc)
        
        # Check if we should retry
        if task.attempts < task.max_attempts:
            task.status = TaskStatus.RETRYING
            await self.notify("task_retry", task)
        else:
            task.status = TaskStatus.FAILED
            await self.notify("task_failed", task)
            
            # Check if workflow should fail
            if not self._can_continue_after_failure(task):
                await self.fail_workflow(f"Task {task.name} failed: {error}")
            elif self._all_tasks_finished():
                await self.complete_workflow()
    
    def get_ready_tasks(self) -> List[TaskExecution]:
        """Get tasks that are ready to execute.
        
        Returns:
            List of tasks ready for execution
        """
        ready_tasks = []
        
        for task in self.workflow_execution.tasks:
            if task.status == TaskStatus.PENDING and self._dependencies_satisfied(task):
                ready_tasks.append(task)
        
        return ready_tasks
    
    def get_retryable_tasks(self) -> List[TaskExecution]:
        """Get tasks that are ready for retry.
        
        Returns:
            List of tasks ready for retry
        """
        return [task for task in self.workflow_execution.tasks 
                if task.status == TaskStatus.RETRYING]
    
    def _dependencies_satisfied(self, task: TaskExecution) -> bool:
        """Check if task dependencies are satisfied.
        
        Args:
            task: Task to check
            
        Returns:
            True if dependencies are satisfied
        """
        dependencies = self._task_dependencies.get(task.name, set())
        
        for dep_name in dependencies:
            dep_task = self._get_task_by_name(dep_name)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    def _get_task_by_name(self, name: str) -> TaskExecution:
        """Get task by name.
        
        Args:
            name: Task name
            
        Returns:
            Task execution instance or None
        """
        for task in self.workflow_execution.tasks:
            if task.name == name:
                return task
        return None
    
    def _all_tasks_finished(self) -> bool:
        """Check if all tasks are finished.
        
        Returns:
            True if all tasks are in a final state
        """
        final_states = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}
        return all(task.status in final_states for task in self.workflow_execution.tasks)
    
    def _can_continue_after_failure(self, failed_task: TaskExecution) -> bool:
        """Check if workflow can continue after task failure.
        
        Args:
            failed_task: Task that failed
            
        Returns:
            True if workflow can continue
        """
        # This would be based on the failure strategy from configuration
        # For now, we'll use a simple heuristic
        return (self.workflow_execution.partial_completion_allowed or 
                hasattr(failed_task, 'continue_on_failure') and 
                getattr(failed_task, 'continue_on_failure', False))
