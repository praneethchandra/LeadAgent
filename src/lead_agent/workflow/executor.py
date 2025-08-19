"""Task executor for workflow tasks."""

import asyncio
import time
from typing import Dict

from ..agents.base import BaseAgent
from ..models import AgentResponse, TaskExecution
from ..patterns.observer import Observer, Subject


class TaskExecutor(Observer):
    """Executes individual tasks using appropriate agents."""
    
    def __init__(self, agents: Dict[str, BaseAgent]):
        """Initialize task executor.
        
        Args:
            agents: Dictionary of agent instances by name
        """
        self.agents = agents
    
    async def execute_task(self, task: TaskExecution) -> AgentResponse:
        """Execute a single task.
        
        Args:
            task: Task to execute
            
        Returns:
            AgentResponse: Response from agent execution
        """
        agent = self.agents.get(task.agent_name)
        if not agent:
            return AgentResponse(
                success=False,
                error=f"Agent '{task.agent_name}' not found"
            )
        
        try:
            # Execute task with the agent
            response = await agent.execute_with_resilience(
                task.action,
                task.parameters
            )
            
            return response
            
        except Exception as e:
            return AgentResponse(
                success=False,
                error=f"Task execution failed: {str(e)}"
            )
    
    async def update(self, subject: Subject, event_type: str, data: any) -> None:
        """Handle notifications from workflow state machine.
        
        Args:
            subject: Subject that sent the notification
            event_type: Type of event
            data: Event data
        """
        # This can be used to implement task-specific logic
        # based on workflow events
        pass
