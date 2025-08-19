"""Main Lead Agent class."""

import asyncio
from pathlib import Path
from typing import Optional

import structlog

from .models import WorkflowResult
from .workflow.engine import WorkflowEngine

logger = structlog.get_logger(__name__)


class LeadAgent:
    """Main Lead Agent class for orchestrating workflows."""
    
    def __init__(self):
        """Initialize Lead Agent."""
        self.workflow_engine = WorkflowEngine()
    
    async def execute_workflow_from_file(self, config_path: str) -> WorkflowResult:
        """Execute a workflow from configuration file.
        
        Args:
            config_path: Path to workflow configuration file
            
        Returns:
            WorkflowResult: Result of workflow execution
        """
        logger.info("Starting workflow execution", config_path=config_path)
        
        try:
            # Load workflow configuration
            await self.workflow_engine.load_workflow(config_path)
            
            # Execute workflow
            result = await self.workflow_engine.execute_workflow()
            
            logger.info(
                "Workflow execution completed",
                workflow_id=result.workflow_id,
                status=result.status,
                completed_tasks=result.completed_tasks,
                failed_tasks=result.failed_tasks,
                execution_time=result.execution_time
            )
            
            return result
            
        except Exception as e:
            logger.error("Workflow execution failed", error=str(e))
            raise
    
    async def execute_workflow_from_dict(self, config_dict: dict) -> WorkflowResult:
        """Execute a workflow from configuration dictionary.
        
        Args:
            config_dict: Workflow configuration as dictionary
            
        Returns:
            WorkflowResult: Result of workflow execution
        """
        # Save config to temporary file and use file-based execution
        # In a production system, you might want to extend the engine
        # to accept dict directly
        import tempfile
        import json
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_dict, f, indent=2)
            temp_path = f.name
        
        try:
            return await self.execute_workflow_from_file(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)


async def main() -> None:
    """Main entry point for CLI usage."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python -m lead_agent.lead_agent <config_file>")
        sys.exit(1)
    
    config_path = sys.argv[1]
    
    # Configure logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Execute workflow
    lead_agent = LeadAgent()
    try:
        result = await lead_agent.execute_workflow_from_file(config_path)
        print(f"Workflow completed with status: {result.status}")
        print(f"Completed tasks: {result.completed_tasks}/{result.total_tasks}")
        print(f"Execution time: {result.execution_time:.2f}s")
        
        if result.results:
            print("\nResults:")
            for task_name, result_data in result.results.items():
                print(f"  {task_name}: {result_data}")
        
        if result.errors:
            print("\nErrors:")
            for task_name, error in result.errors.items():
                print(f"  {task_name}: {error}")
                
    except Exception as e:
        print(f"Workflow execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
