"""Base agent interface and factory."""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Type

from ..models import AgentConfig, AgentResponse, AgentType
from ..patterns.circuit_breaker import CircuitBreaker
from ..patterns.retry import RetryHandler


class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    def __init__(self, config: AgentConfig):
        """Initialize the agent.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.circuit_breaker = CircuitBreaker(config.circuit_breaker)
        self.retry_handler = RetryHandler(config.retry_config)
    
    @abstractmethod
    async def execute(self, action: str, parameters: Dict[str, Any]) -> AgentResponse:
        """Execute an action with the given parameters.
        
        Args:
            action: Action to execute
            parameters: Parameters for the action
            
        Returns:
            AgentResponse: Response from the agent
        """
        pass
    
    async def execute_with_resilience(
        self, 
        action: str, 
        parameters: Dict[str, Any]
    ) -> AgentResponse:
        """Execute an action with retry and circuit breaker patterns.
        
        Args:
            action: Action to execute
            parameters: Parameters for the action
            
        Returns:
            AgentResponse: Response from the agent
        """
        start_time = time.time()
        
        try:
            # Check circuit breaker
            if not self.circuit_breaker.can_execute():
                return AgentResponse(
                    success=False,
                    error="Circuit breaker is open",
                    execution_time=time.time() - start_time
                )
            
            # Execute with retry
            response = await self.retry_handler.execute_with_retry(
                self._execute_internal,
                action,
                parameters
            )
            
            # Record success for circuit breaker
            self.circuit_breaker.record_success()
            
            response.execution_time = time.time() - start_time
            return response
            
        except Exception as e:
            # Record failure for circuit breaker
            self.circuit_breaker.record_failure()
            
            return AgentResponse(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def _execute_internal(
        self, 
        action: str, 
        parameters: Dict[str, Any]
    ) -> AgentResponse:
        """Internal execute method with timeout.
        
        Args:
            action: Action to execute
            parameters: Parameters for the action
            
        Returns:
            AgentResponse: Response from the agent
        """
        try:
            return await asyncio.wait_for(
                self.execute(action, parameters),
                timeout=self.config.timeout
            )
        except asyncio.TimeoutError:
            raise Exception(f"Agent execution timeout after {self.config.timeout}s")
    
    @property
    def name(self) -> str:
        """Get agent name."""
        return self.config.name
    
    @property
    def type(self) -> AgentType:
        """Get agent type."""
        return self.config.type


class AgentFactory:
    """Factory for creating agents based on configuration."""
    
    _agent_types: Dict[AgentType, Type[BaseAgent]] = {}
    
    @classmethod
    def register_agent_type(cls, agent_type: AgentType, agent_class: Type[BaseAgent]) -> None:
        """Register an agent type with its implementation class.
        
        Args:
            agent_type: Type of agent
            agent_class: Agent implementation class
        """
        cls._agent_types[agent_type] = agent_class
    
    @classmethod
    def create_agent(cls, config: AgentConfig) -> BaseAgent:
        """Create an agent instance based on configuration.
        
        Args:
            config: Agent configuration
            
        Returns:
            BaseAgent: Agent instance
            
        Raises:
            ValueError: If agent type is not registered
        """
        if config.type not in cls._agent_types:
            raise ValueError(f"Unknown agent type: {config.type}")
        
        agent_class = cls._agent_types[config.type]
        return agent_class(config)
    
    @classmethod
    def get_registered_types(cls) -> list[AgentType]:
        """Get list of registered agent types.
        
        Returns:
            List of registered agent types
        """
        return list(cls._agent_types.keys())
