"""Integration tests for the Lead Agent system."""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import yaml

from src.lead_agent.lead_agent import LeadAgent
from src.lead_agent.workflow.engine import WorkflowEngine
from src.lead_agent.models import WorkflowStatus, AgentResponse


class TestLeadAgentIntegration:
    """Integration tests for LeadAgent."""
    
    def create_test_workflow_config(self) -> dict:
        """Create a test workflow configuration."""
        return {
            "name": "integration_test_workflow",
            "version": "1.0.0",
            "parallel_execution": False,
            "failure_strategy": "stop_on_first_failure",
            "global_timeout": 60,
            "agents": [
                {
                    "name": "mock_ai_agent",
                    "type": "ai_agent",
                    "endpoint": "https://api.example.com/chat",
                    "timeout": 30,
                    "retry_config": {
                        "max_attempts": 2,
                        "initial_delay": 0.1,
                        "max_delay": 5.0
                    },
                    "circuit_breaker": {
                        "failure_threshold": 3,
                        "recovery_timeout": 30
                    }
                },
                {
                    "name": "mock_http_agent",
                    "type": "http_api",
                    "endpoint": "https://api.example.com",
                    "timeout": 20,
                    "authentication": {
                        "type": "api_key",
                        "key": "test_key",
                        "header": "X-API-Key"
                    }
                }
            ],
            "tasks": [
                {
                    "name": "fetch_data",
                    "description": "Fetch initial data",
                    "agent_name": "mock_http_agent",
                    "action": "/api/data",
                    "parameters": {
                        "method": "GET",
                        "params": {"limit": 100}
                    },
                    "timeout": 20,
                    "depends_on": [],
                    "continue_on_failure": False
                },
                {
                    "name": "process_data",
                    "description": "Process fetched data with AI",
                    "agent_name": "mock_ai_agent",
                    "action": "analyze",
                    "parameters": {
                        "model": "gpt-4",
                        "prompt": "Analyze this data: {{fetch_data.result}}"
                    },
                    "timeout": 30,
                    "depends_on": ["fetch_data"],
                    "continue_on_failure": False
                }
            ]
        }
    
    @patch('aiohttp.ClientSession.request')
    @patch('aiohttp.ClientSession.post')
    def test_successful_workflow_execution(self, mock_post, mock_request):
        """Test successful end-to-end workflow execution."""
        # Mock HTTP responses
        http_response = AsyncMock()
        http_response.status = 200
        http_response.json = AsyncMock(return_value={"data": ["item1", "item2", "item3"]})
        http_response.url = "https://api.example.com/api/data"
        http_response.headers = {"Content-Type": "application/json"}
        mock_request.return_value.__aenter__.return_value = http_response
        
        ai_response = AsyncMock()
        ai_response.status = 200
        ai_response.json = AsyncMock(return_value={"analysis": "Data contains 3 items"})
        mock_post.return_value.__aenter__.return_value = ai_response
        
        # Create workflow configuration file
        config_data = self.create_test_workflow_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            # Execute workflow
            lead_agent = LeadAgent()
            result = asyncio.run(lead_agent.execute_workflow_from_file(config_path))
            
            # Verify results
            assert result.status == WorkflowStatus.COMPLETED
            assert result.completed_tasks == 2
            assert result.failed_tasks == 0
            assert result.total_tasks == 2
            assert result.execution_time > 0
            
            # Verify task results
            assert "fetch_data" in result.results
            assert "process_data" in result.results
            assert result.results["fetch_data"] == {"data": ["item1", "item2", "item3"]}
            assert result.results["process_data"] == {"analysis": "Data contains 3 items"}
            
            # Verify no errors
            assert len(result.errors) == 0
            
            # Verify agents were called correctly
            assert mock_request.call_count == 1
            assert mock_post.call_count == 1
            
        finally:
            Path(config_path).unlink(missing_ok=True)
    
    @patch('aiohttp.ClientSession.request')
    def test_workflow_with_task_failure(self, mock_request):
        """Test workflow execution with task failure."""
        # Mock HTTP failure
        http_response = AsyncMock()
        http_response.status = 500
        http_response.text = AsyncMock(return_value="Internal Server Error")
        http_response.url = "https://api.example.com/api/data"
        http_response.headers = {}
        mock_request.return_value.__aenter__.return_value = http_response
        
        # Create workflow configuration
        config_data = self.create_test_workflow_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            # Execute workflow
            lead_agent = LeadAgent()
            result = asyncio.run(lead_agent.execute_workflow_from_file(config_path))
            
            # Verify failure results
            assert result.status == WorkflowStatus.FAILED
            assert result.completed_tasks == 0
            assert result.failed_tasks == 1  # Only first task failed
            assert result.total_tasks == 2
            
            # Verify error information
            assert "fetch_data" in result.errors
            assert "HTTP 500" in result.errors["fetch_data"]
            
            # Second task should not have run
            assert "process_data" not in result.results
            assert "process_data" not in result.errors
            
        finally:
            Path(config_path).unlink(missing_ok=True)
    
    def test_workflow_from_dict(self):
        """Test executing workflow from dictionary configuration."""
        config_data = {
            "name": "dict_workflow",
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
                    "name": "simple_task",
                    "agent_name": "test_agent",
                    "action": "test_action",
                    "parameters": {"test": "value"}
                }
            ]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock successful AI response
            ai_response = AsyncMock()
            ai_response.status = 200
            ai_response.json = AsyncMock(return_value={"result": "success"})
            mock_post.return_value.__aenter__.return_value = ai_response
            
            # Execute workflow
            lead_agent = LeadAgent()
            result = asyncio.run(lead_agent.execute_workflow_from_dict(config_data))
            
            # Verify results
            assert result.status == WorkflowStatus.COMPLETED
            assert result.completed_tasks == 1
            assert result.failed_tasks == 0
    
    @patch('aiohttp.ClientSession.request')
    @patch('aiohttp.ClientSession.post')
    def test_parallel_workflow_execution(self, mock_post, mock_request):
        """Test parallel workflow execution."""
        # Create parallel workflow configuration
        config_data = {
            "name": "parallel_workflow",
            "version": "1.0.0",
            "parallel_execution": True,
            "failure_strategy": "partial_completion_allowed",
            "agents": [
                {
                    "name": "http_agent",
                    "type": "http_api",
                    "endpoint": "https://api.example.com"
                },
                {
                    "name": "ai_agent",
                    "type": "ai_agent",
                    "endpoint": "https://ai.example.com"
                }
            ],
            "tasks": [
                {
                    "name": "fetch_task",
                    "agent_name": "http_agent",
                    "action": "/data",
                    "parameters": {"method": "GET"},
                    "continue_on_failure": True
                },
                {
                    "name": "ai_task",
                    "agent_name": "ai_agent",
                    "action": "generate",
                    "parameters": {"prompt": "Hello"},
                    "continue_on_failure": True
                }
            ]
        }
        
        # Mock responses
        http_response = AsyncMock()
        http_response.status = 200
        http_response.json = AsyncMock(return_value={"data": "http_data"})
        http_response.url = "https://api.example.com/data"
        http_response.headers = {}
        mock_request.return_value.__aenter__.return_value = http_response
        
        ai_response = AsyncMock()
        ai_response.status = 200
        ai_response.json = AsyncMock(return_value={"text": "Hello world"})
        mock_post.return_value.__aenter__.return_value = ai_response
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            # Execute workflow
            lead_agent = LeadAgent()
            result = asyncio.run(lead_agent.execute_workflow_from_file(config_path))
            
            # Verify parallel execution results
            assert result.status == WorkflowStatus.COMPLETED
            assert result.completed_tasks == 2
            assert result.failed_tasks == 0
            assert result.total_tasks == 2
            
            # Both tasks should have results
            assert "fetch_task" in result.results
            assert "ai_task" in result.results
            
            # Both agents should have been called
            assert mock_request.call_count >= 1
            assert mock_post.call_count >= 1
            
        finally:
            Path(config_path).unlink(missing_ok=True)
    
    def test_invalid_configuration_handling(self):
        """Test handling of invalid workflow configuration."""
        # Invalid configuration missing required fields
        invalid_config = {
            "name": "invalid_workflow",
            # Missing agents and tasks
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_config, f)
            config_path = f.name
        
        try:
            lead_agent = LeadAgent()
            
            # Should raise an exception during loading
            with pytest.raises(Exception):
                asyncio.run(lead_agent.execute_workflow_from_file(config_path))
                
        finally:
            Path(config_path).unlink(missing_ok=True)
    
    def test_nonexistent_configuration_file(self):
        """Test handling of non-existent configuration file."""
        lead_agent = LeadAgent()
        
        with pytest.raises(Exception):
            asyncio.run(lead_agent.execute_workflow_from_file("/nonexistent/file.yaml"))
    
    @patch('aiohttp.ClientSession.request')
    def test_retry_mechanism_integration(self, mock_request):
        """Test retry mechanism in integration scenario."""
        # Mock responses: first call fails, second succeeds
        failure_response = AsyncMock()
        failure_response.status = 500
        failure_response.text = AsyncMock(return_value="Server Error")
        failure_response.url = "https://api.example.com/data"
        failure_response.headers = {}
        
        success_response = AsyncMock()
        success_response.status = 200
        success_response.json = AsyncMock(return_value={"data": "retry_success"})
        success_response.url = "https://api.example.com/data"
        success_response.headers = {}
        
        mock_request.return_value.__aenter__.side_effect = [failure_response, success_response]
        
        # Create workflow with retry configuration
        config_data = {
            "name": "retry_workflow",
            "version": "1.0.0",
            "agents": [
                {
                    "name": "retry_agent",
                    "type": "http_api",
                    "endpoint": "https://api.example.com",
                    "retry_config": {
                        "max_attempts": 2,
                        "initial_delay": 0.1,
                        "max_delay": 1.0
                    }
                }
            ],
            "tasks": [
                {
                    "name": "retry_task",
                    "agent_name": "retry_agent",
                    "action": "/data",
                    "parameters": {"method": "GET"}
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            # Execute workflow
            lead_agent = LeadAgent()
            result = asyncio.run(lead_agent.execute_workflow_from_file(config_path))
            
            # Should succeed after retry
            assert result.status == WorkflowStatus.COMPLETED
            assert result.completed_tasks == 1
            assert result.failed_tasks == 0
            assert result.results["retry_task"] == {"data": "retry_success"}
            
            # Should have been called twice (original + retry)
            assert mock_request.call_count == 2
            
        finally:
            Path(config_path).unlink(missing_ok=True)


class TestWorkflowEngineIntegration:
    """Integration tests for WorkflowEngine specifically."""
    
    def test_engine_lifecycle(self):
        """Test complete engine lifecycle."""
        engine = WorkflowEngine()
        
        # Initial state
        assert engine.workflow_config is None
        assert engine.workflow_execution is None
        
        # Create test configuration file
        config_data = {
            "name": "lifecycle_test",
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
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            # Load workflow
            asyncio.run(engine.load_workflow(config_path))
            
            # Verify loading
            assert engine.workflow_config is not None
            assert engine.workflow_config.name == "lifecycle_test"
            assert len(engine.agents) == 1
            assert "test_agent" in engine.agents
            assert engine.task_executor is not None
            
            # Mock the agent execution
            with patch.object(engine.agents["test_agent"], 'execute_with_resilience') as mock_execute:
                mock_execute.return_value = AgentResponse(success=True, result="test_result")
                
                # Execute workflow
                result = asyncio.run(engine.execute_workflow())
                
                # Verify execution
                assert result.status == WorkflowStatus.COMPLETED
                assert result.completed_tasks == 1
                assert result.failed_tasks == 0
                assert result.results["test_task"] == "test_result"
                
                # Verify agent was called
                mock_execute.assert_called_once_with("test_action", {})
                
        finally:
            Path(config_path).unlink(missing_ok=True)
