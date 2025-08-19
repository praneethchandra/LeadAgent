#!/usr/bin/env python3
"""
Simple demo showing Lead Agent system components without network calls.
"""

import asyncio
from lead_agent.models import (
    AgentConfig, AgentType, TaskConfig, WorkflowConfig, 
    RetryConfig, CircuitBreakerConfig
)
from lead_agent.config_loader import ConfigLoader
from lead_agent.agents.base import AgentFactory
from lead_agent.patterns.circuit_breaker import CircuitBreaker, CircuitBreakerState
from lead_agent.patterns.retry import RetryHandler


def demo_models():
    """Demonstrate the core data models."""
    print("🏗️  Core Models Demo")
    print("=" * 30)
    
    # Create retry configuration
    retry_config = RetryConfig(
        max_attempts=3,
        initial_delay=1.0,
        max_delay=10.0,
        exponential_base=2.0,
        jitter=True
    )
    print(f"✅ Retry Config: {retry_config.max_attempts} attempts, {retry_config.initial_delay}s initial delay")
    
    # Create circuit breaker configuration
    cb_config = CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=60.0
    )
    print(f"✅ Circuit Breaker: {cb_config.failure_threshold} failure threshold, {cb_config.recovery_timeout}s recovery")
    
    # Create agent configuration
    agent_config = AgentConfig(
        name="demo_agent",
        type=AgentType.AI_AGENT,
        endpoint="https://api.example.com",
        timeout=30.0,
        retry_config=retry_config,
        circuit_breaker=cb_config
    )
    print(f"✅ Agent Config: {agent_config.name} ({agent_config.type})")
    
    # Create task configuration
    task_config = TaskConfig(
        name="demo_task",
        description="A demo task",
        agent_name="demo_agent",
        action="demo_action",
        parameters={"param1": "value1"},
        timeout=30.0,
        depends_on=[]
    )
    print(f"✅ Task Config: {task_config.name} -> {task_config.agent_name}")
    
    # Create workflow configuration
    workflow_config = WorkflowConfig(
        name="demo_workflow",
        description="A demo workflow",
        version="1.0.0",
        tasks=[task_config],
        agents=[agent_config],
        parallel_execution=False,
        failure_strategy="stop_on_first_failure"
    )
    print(f"✅ Workflow Config: {workflow_config.name} v{workflow_config.version}")
    print(f"   - Tasks: {len(workflow_config.tasks)}")
    print(f"   - Agents: {len(workflow_config.agents)}")
    print(f"   - Strategy: {workflow_config.failure_strategy}")


def demo_patterns():
    """Demonstrate design patterns."""
    print("\n🎯 Design Patterns Demo")
    print("=" * 30)
    
    # Circuit Breaker Pattern
    cb_config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=1.0)
    circuit_breaker = CircuitBreaker(cb_config)
    
    print(f"🔵 Circuit Breaker State: {circuit_breaker.state}")
    print(f"   Can execute: {circuit_breaker.can_execute()}")
    
    # Simulate failures
    circuit_breaker.record_failure()
    circuit_breaker.record_failure()  # Should open circuit
    
    print(f"🔴 After 2 failures: {circuit_breaker.state}")
    print(f"   Can execute: {circuit_breaker.can_execute()}")
    
    # Retry Pattern
    retry_config = RetryConfig(max_attempts=3, initial_delay=0.1, jitter=False)
    retry_handler = RetryHandler(retry_config)
    
    print(f"🔄 Retry Handler: {retry_config.max_attempts} max attempts")
    print(f"   Delay calculation (attempt 0): {retry_handler._calculate_delay(0):.1f}s")
    print(f"   Delay calculation (attempt 1): {retry_handler._calculate_delay(1):.1f}s")
    print(f"   Delay calculation (attempt 2): {retry_handler._calculate_delay(2):.1f}s")


def demo_configuration():
    """Demonstrate configuration loading and validation."""
    print("\n📋 Configuration Demo")
    print("=" * 30)
    
    # Create a sample configuration
    config_dict = {
        "name": "validation_demo",
        "version": "1.0.0",
        "agents": [
            {
                "name": "test_agent",
                "type": "ai_agent",
                "endpoint": "https://api.example.com"
            }
        ],
        "tasks": [
            {
                "name": "test_task",
                "agent_name": "test_agent",
                "action": "test_action"
            }
        ]
    }
    
    try:
        # Load and validate configuration
        workflow_config = ConfigLoader.load_from_dict(config_dict)
        ConfigLoader.validate_configuration(workflow_config)
        
        print("✅ Configuration loaded and validated successfully")
        print(f"   Workflow: {workflow_config.name}")
        print(f"   Agents: {[agent.name for agent in workflow_config.agents]}")
        print(f"   Tasks: {[task.name for task in workflow_config.tasks]}")
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")


def demo_agent_factory():
    """Demonstrate agent factory pattern."""
    print("\n🏭 Agent Factory Demo")
    print("=" * 30)
    
    # Show registered agent types
    registered_types = AgentFactory.get_registered_types()
    print(f"🤖 Registered agent types: {len(registered_types)}")
    for agent_type in registered_types:
        print(f"   - {agent_type}")
    
    # Create an agent configuration
    config = AgentConfig(
        name="factory_demo_agent",
        type=AgentType.AI_AGENT,
        endpoint="https://api.example.com"
    )
    
    try:
        # Create agent using factory
        agent = AgentFactory.create_agent(config)
        print(f"✅ Created agent: {agent.name} (type: {agent.type})")
        print(f"   Agent class: {agent.__class__.__name__}")
        
    except Exception as e:
        print(f"❌ Agent creation error: {e}")


def demo_system_overview():
    """Show system overview."""
    print("\n🎯 Lead Agent System Overview")
    print("=" * 50)
    
    components = [
        "📋 Configuration Management (YAML/JSON)",
        "🤖 Multi-Agent Communication (AI/MCP/HTTP)",
        "🔄 Workflow Orchestration (Sequential/Parallel)",
        "🛡️  Resilience Patterns (Circuit Breaker, Retry)",
        "📊 State Management (Workflow/Task States)",
        "🔍 Event Monitoring (Observer Pattern)",
        "⚡ Error Handling (Partial Failures, Recovery)",
        "🧪 Comprehensive Testing (100% Coverage Goal)"
    ]
    
    for component in components:
        print(f"  {component}")
    
    print(f"\n📈 Design Patterns Implemented: 10+")
    print(f"🏗️  Architecture: Modular, Event-Driven, Resilient")
    print(f"🔧 Configuration: Declarative YAML/JSON")


def main():
    """Main demo function."""
    print("🚀 Lead Agent System - Component Demo")
    print("=" * 60)
    
    demo_models()
    demo_patterns()
    demo_configuration()
    demo_agent_factory()
    demo_system_overview()
    
    print("\n" + "=" * 60)
    print("✨ Component demo completed!")
    print("📖 Check README.md for complete documentation")
    print("🧪 Run tests: python -m pytest tests/")
    print("📁 Example configs: examples/*.yaml")
    print("=" * 60)


if __name__ == "__main__":
    main()
