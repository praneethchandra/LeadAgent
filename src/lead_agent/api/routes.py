"""API routes for the Lead Agent REST API."""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import JSONResponse

from ..lead_agent import LeadAgent
from ..models import WorkflowResult
from .models import (
    AgentTestRequest,
    AgentTestResponse,
    ErrorResponse,
    HealthResponse,
    WorkflowListResponse,
    WorkflowRequest,
    WorkflowResponse,
    WorkflowStatusResponse,
)

logger = structlog.get_logger(__name__)

# Global storage for workflow executions (in production, use a database)
workflow_executions: Dict[UUID, WorkflowResponse] = {}
execution_results: Dict[UUID, WorkflowResult] = {}

# Create API router
router = APIRouter()

# Service start time for uptime calculation
start_time = time.time()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime=time.time() - start_time,
        timestamp=datetime.utcnow()
    )


@router.post("/workflows", response_model=WorkflowResponse)
async def create_workflow(
    workflow: WorkflowRequest,
    background_tasks: BackgroundTasks
):
    """Create and execute a new workflow."""
    execution_id = uuid4()
    
    # Create workflow response
    workflow_response = WorkflowResponse(
        execution_id=execution_id,
        name=workflow.name,
        status="queued",
        created_at=datetime.utcnow(),
        total_tasks=len(workflow.tasks)
    )
    
    # Store workflow execution
    workflow_executions[execution_id] = workflow_response
    
    # Execute workflow in background
    background_tasks.add_task(execute_workflow_background, execution_id, workflow)
    
    logger.info("Workflow queued for execution", execution_id=str(execution_id), name=workflow.name)
    
    return workflow_response


@router.get("/workflows", response_model=WorkflowListResponse)
async def list_workflows(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """List all workflow executions."""
    workflows = list(workflow_executions.values())
    
    # Filter by status if provided
    if status:
        workflows = [w for w in workflows if w.status == status]
    
    # Sort by creation time (newest first)
    workflows.sort(key=lambda w: w.created_at, reverse=True)
    
    # Paginate
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_workflows = workflows[start_idx:end_idx]
    
    return WorkflowListResponse(
        workflows=paginated_workflows,
        total=len(workflows),
        page=page,
        page_size=page_size
    )


@router.get("/workflows/{execution_id}", response_model=WorkflowResponse)
async def get_workflow(execution_id: UUID):
    """Get workflow execution details."""
    if execution_id not in workflow_executions:
        raise HTTPException(status_code=404, detail="Workflow execution not found")
    
    return workflow_executions[execution_id]


@router.get("/workflows/{execution_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status(execution_id: UUID):
    """Get workflow execution status."""
    if execution_id not in workflow_executions:
        raise HTTPException(status_code=404, detail="Workflow execution not found")
    
    workflow = workflow_executions[execution_id]
    
    # Calculate progress
    progress = 0.0
    if workflow.total_tasks > 0:
        progress = (workflow.completed_tasks / workflow.total_tasks) * 100
    
    # Determine current task
    current_task = None
    if workflow.status == "running" and execution_id in execution_results:
        # This would require more sophisticated tracking in a real implementation
        current_task = "In progress..."
    
    return WorkflowStatusResponse(
        execution_id=execution_id,
        status=workflow.status,
        progress=progress,
        current_task=current_task,
        message=f"Workflow {workflow.status}"
    )


@router.delete("/workflows/{execution_id}")
async def cancel_workflow(execution_id: UUID):
    """Cancel a workflow execution (if still running)."""
    if execution_id not in workflow_executions:
        raise HTTPException(status_code=404, detail="Workflow execution not found")
    
    workflow = workflow_executions[execution_id]
    
    if workflow.status in ["completed", "failed", "cancelled"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel workflow with status: {workflow.status}"
        )
    
    # Update status to cancelled
    workflow.status = "cancelled"
    workflow.completed_at = datetime.utcnow()
    
    logger.info("Workflow cancelled", execution_id=str(execution_id))
    
    return {"message": "Workflow cancelled successfully"}


@router.post("/agents/test", response_model=AgentTestResponse)
async def test_agent(agent_test: AgentTestRequest):
    """Test agent connectivity and configuration."""
    start_time = time.time()
    
    try:
        # Create a temporary agent for testing
        from ..agents.base import AgentFactory
        from ..models import AgentConfig
        
        # Convert dict to AgentConfig
        agent_config = AgentConfig(**agent_test.agent_config)
        agent = AgentFactory.create_agent(agent_config)
        
        # Execute test action
        result = await agent.execute(
            agent_test.test_action, 
            agent_test.test_parameters
        )
        
        response_time = time.time() - start_time
        
        return AgentTestResponse(
            agent_name=agent_config.name,
            success=result.success,
            response_time=response_time,
            result=result.result if result.success else None,
            error=result.error if not result.success else None
        )
        
    except Exception as e:
        response_time = time.time() - start_time
        
        return AgentTestResponse(
            agent_name=agent_test.agent_config.get("name", "unknown"),
            success=False,
            response_time=response_time,
            result=None,
            error=str(e)
        )


async def execute_workflow_background(execution_id: UUID, workflow_request: WorkflowRequest):
    """Execute workflow in the background."""
    try:
        # Update status to running
        workflow_executions[execution_id].status = "running"
        workflow_executions[execution_id].started_at = datetime.utcnow()
        
        logger.info("Starting workflow execution", execution_id=str(execution_id))
        
        # Convert workflow request to dict
        workflow_dict = {
            "name": workflow_request.name,
            "description": workflow_request.description,
            "version": workflow_request.version,
            "parallel_execution": workflow_request.parallel_execution,
            "failure_strategy": workflow_request.failure_strategy,
            "global_timeout": workflow_request.global_timeout,
            "agents": workflow_request.agents,
            "tasks": workflow_request.tasks
        }
        
        # Execute workflow
        lead_agent = LeadAgent()
        result = await lead_agent.execute_workflow_from_dict(workflow_dict)
        
        # Store result
        execution_results[execution_id] = result
        
        # Update workflow response
        workflow_response = workflow_executions[execution_id]
        workflow_response.status = result.status
        workflow_response.completed_at = datetime.utcnow()
        workflow_response.execution_time = result.execution_time
        workflow_response.completed_tasks = result.completed_tasks
        workflow_response.results = result.results
        workflow_response.errors = result.errors
        
        logger.info(
            "Workflow execution completed", 
            execution_id=str(execution_id),
            status=result.status,
            execution_time=result.execution_time
        )
        
    except Exception as e:
        logger.error(
            "Workflow execution failed", 
            execution_id=str(execution_id),
            error=str(e)
        )
        
        # Update status to failed
        workflow_response = workflow_executions[execution_id]
        workflow_response.status = "failed"
        workflow_response.completed_at = datetime.utcnow()
        workflow_response.errors = {"execution_error": str(e)}
