"""Tests for agent implementations."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest
import aiohttp

from src.lead_agent.models import AgentConfig, AgentResponse, AgentType
from src.lead_agent.agents.base import BaseAgent, AgentFactory
from src.lead_agent.agents.ai_agent import AIAgent
from src.lead_agent.agents.mcp_server import MCPServerAgent
from src.lead_agent.agents.http_api import HTTPAPIAgent


class MockAgent(BaseAgent):
    """Mock agent for testing base functionality."""
    
    def __init__(self, config: AgentConfig, should_fail: bool = False):
        super().__init__(config)
        self.should_fail = should_fail
        self.execution_count = 0
    
    async def execute(self, action: str, parameters: dict) -> AgentResponse:
        """Mock execution."""
        self.execution_count += 1
        
        if self.should_fail:
            raise Exception("Mock agent failure")
        
        return AgentResponse(
            success=True,
            result={"action": action, "parameters": parameters},
            execution_time=0.1
        )


class TestBaseAgent:
    """Test BaseAgent functionality."""
    
    def test_agent_properties(self):
        """Test agent properties."""
        config = AgentConfig(name="test_agent", type=AgentType.AI_AGENT)
        agent = MockAgent(config)
        
        assert agent.name == "test_agent"
        assert agent.type == AgentType.AI_AGENT
        assert agent.config is config
    
    def test_successful_execution_with_resilience(self):
        """Test successful execution with resilience patterns."""
        config = AgentConfig(name="test_agent", type=AgentType.AI_AGENT)
        agent = MockAgent(config)
        
        response = asyncio.run(agent.execute_with_resilience("test_action", {"param": "value"}))
        
        assert response.success is True
        assert response.result == {"action": "test_action", "parameters": {"param": "value"}}
        assert response.error is None
        assert response.execution_time > 0
        assert agent.execution_count == 1
    
    def test_execution_with_retry(self):
        """Test execution with retry on failure."""
        config = AgentConfig(
            name="test_agent", 
            type=AgentType.AI_AGENT,
            retry_config={"max_attempts": 3, "initial_delay": 0.1}
        )
        agent = MockAgent(config, should_fail=True)
        
        response = asyncio.run(agent.execute_with_resilience("test_action", {}))
        
        assert response.success is False
        assert "Mock agent failure" in response.error
        assert response.execution_time > 0
        # Should have attempted multiple times due to retry
        assert agent.execution_count == 3
    
    def test_circuit_breaker_blocks_execution(self):
        """Test that circuit breaker blocks execution after failures."""
        config = AgentConfig(
            name="test_agent",
            type=AgentType.AI_AGENT,
            circuit_breaker={"failure_threshold": 2, "recovery_timeout": 60}
        )
        agent = MockAgent(config, should_fail=True)
        
        # First two executions should fail and open circuit breaker
        response1 = asyncio.run(agent.execute_with_resilience("action1", {}))
        response2 = asyncio.run(agent.execute_with_resilience("action2", {}))
        
        assert response1.success is False
        assert response2.success is False
        
        # Third execution should be blocked by circuit breaker
        response3 = asyncio.run(agent.execute_with_resilience("action3", {}))
        
        assert response3.success is False
        assert "Circuit breaker is open" in response3.error
    
    def test_timeout_handling(self):
        """Test timeout handling in execution."""
        config = AgentConfig(
            name="test_agent",
            type=AgentType.AI_AGENT,
            timeout=0.01  # Very short timeout
        )
        
        class SlowAgent(MockAgent):
            async def execute(self, action: str, parameters: dict) -> AgentResponse:
                await asyncio.sleep(0.1)  # Longer than timeout
                return AgentResponse(success=True, result="slow_result")
        
        agent = SlowAgent(config)
        response = asyncio.run(agent.execute_with_resilience("slow_action", {}))
        
        assert response.success is False
        assert "timeout" in response.error.lower()


class TestAgentFactory:
    """Test AgentFactory functionality."""
    
    def test_register_and_create_agent(self):
        """Test registering and creating agent types."""
        # Register mock agent type
        AgentFactory.register_agent_type(AgentType.CUSTOM, MockAgent)
        
        config = AgentConfig(name="custom_agent", type=AgentType.CUSTOM)
        agent = AgentFactory.create_agent(config)
        
        assert isinstance(agent, MockAgent)
        assert agent.name == "custom_agent"
        assert agent.type == AgentType.CUSTOM
    
    def test_create_unknown_agent_type(self):
        """Test creating unknown agent type raises error."""
        # Create a new enum value for testing
        config = AgentConfig(name="unknown_agent", type="unknown_type")  # type: ignore
        
        with pytest.raises(ValueError) as exc_info:
            AgentFactory.create_agent(config)
        
        assert "Unknown agent type" in str(exc_info.value)
    
    def test_get_registered_types(self):
        """Test getting registered agent types."""
        # Should include at least the types registered by default
        registered_types = AgentFactory.get_registered_types()
        
        assert AgentType.AI_AGENT in registered_types
        assert AgentType.MCP_SERVER in registered_types
        assert AgentType.HTTP_API in registered_types


class TestAIAgent:
    """Test AIAgent implementation."""
    
    @patch('aiohttp.ClientSession.post')
    def test_successful_execution(self, mock_post):
        """Test successful AI agent execution."""
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"result": "ai_response"})
        mock_post.return_value.__aenter__.return_value = mock_response
        
        config = AgentConfig(
            name="ai_agent",
            type=AgentType.AI_AGENT,
            endpoint="https://api.example.com/chat"
        )
        agent = AIAgent(config)
        
        response = asyncio.run(agent.execute("generate", {"prompt": "Hello"}))
        
        assert response.success is True
        assert response.result == {"result": "ai_response"}
        assert response.error is None
        assert response.metadata["status_code"] == 200
        
        # Verify request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"]["action"] == "generate"
        assert call_args[1]["json"]["parameters"] == {"prompt": "Hello"}
    
    @patch('aiohttp.ClientSession.post')
    def test_execution_with_authentication(self, mock_post):
        """Test AI agent execution with authentication."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"result": "authenticated_response"})
        mock_post.return_value.__aenter__.return_value = mock_response
        
        config = AgentConfig(
            name="ai_agent",
            type=AgentType.AI_AGENT,
            endpoint="https://api.example.com/chat",
            authentication={
                "type": "bearer",
                "token": "secret_token"
            }
        )
        agent = AIAgent(config)
        
        response = asyncio.run(agent.execute("generate", {"prompt": "Hello"}))
        
        assert response.success is True
        
        # Verify authentication header was added
        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer secret_token"
    
    @patch('aiohttp.ClientSession.post')
    def test_execution_with_api_key(self, mock_post):
        """Test AI agent execution with API key authentication."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"result": "api_key_response"})
        mock_post.return_value.__aenter__.return_value = mock_response
        
        config = AgentConfig(
            name="ai_agent",
            type=AgentType.AI_AGENT,
            endpoint="https://api.example.com/chat",
            authentication={
                "type": "api_key",
                "key": "api_key_123",
                "header": "X-API-Key"
            }
        )
        agent = AIAgent(config)
        
        response = asyncio.run(agent.execute("generate", {}))
        
        assert response.success is True
        
        # Verify API key header was added
        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        assert headers["X-API-Key"] == "api_key_123"
    
    @patch('aiohttp.ClientSession.post')
    def test_http_error_handling(self, mock_post):
        """Test AI agent HTTP error handling."""
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value="Bad Request")
        mock_post.return_value.__aenter__.return_value = mock_response
        
        config = AgentConfig(name="ai_agent", type=AgentType.AI_AGENT, endpoint="https://api.example.com")
        agent = AIAgent(config)
        
        response = asyncio.run(agent.execute("generate", {}))
        
        assert response.success is False
        assert "HTTP 400: Bad Request" in response.error
        assert response.metadata["status_code"] == 400
    
    @patch('aiohttp.ClientSession.post')
    def test_timeout_handling(self, mock_post):
        """Test AI agent timeout handling."""
        mock_post.side_effect = aiohttp.ClientTimeout()
        
        config = AgentConfig(name="ai_agent", type=AgentType.AI_AGENT, endpoint="https://api.example.com")
        agent = AIAgent(config)
        
        response = asyncio.run(agent.execute("generate", {}))
        
        assert response.success is False
        assert "Request timeout" in response.error


class TestMCPServerAgent:
    """Test MCPServerAgent implementation."""
    
    @patch('aiohttp.ClientSession.post')
    def test_successful_execution(self, mock_post):
        """Test successful MCP server execution."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"data": "mcp_result"}
        })
        mock_post.return_value.__aenter__.return_value = mock_response
        
        config = AgentConfig(
            name="mcp_agent",
            type=AgentType.MCP_SERVER,
            endpoint="http://localhost:8080/mcp"
        )
        agent = MCPServerAgent(config)
        
        response = asyncio.run(agent.execute("tool_name", {"param": "value"}))
        
        assert response.success is True
        assert response.result == {"data": "mcp_result"}
        assert response.metadata["jsonrpc_id"] == 1
        
        # Verify JSON-RPC format
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["jsonrpc"] == "2.0"
        assert payload["method"] == "tools/call"
        assert payload["params"]["name"] == "tool_name"
        assert payload["params"]["arguments"] == {"param": "value"}
    
    @patch('aiohttp.ClientSession.post')
    def test_mcp_error_handling(self, mock_post):
        """Test MCP server error handling."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -32601,
                "message": "Method not found"
            }
        })
        mock_post.return_value.__aenter__.return_value = mock_response
        
        config = AgentConfig(name="mcp_agent", type=AgentType.MCP_SERVER, endpoint="http://localhost:8080")
        agent = MCPServerAgent(config)
        
        response = asyncio.run(agent.execute("unknown_tool", {}))
        
        assert response.success is False
        assert "MCP Error -32601: Method not found" in response.error
        assert response.metadata["error_code"] == -32601


class TestHTTPAPIAgent:
    """Test HTTPAPIAgent implementation."""
    
    @patch('aiohttp.ClientSession.request')
    def test_successful_get_request(self, mock_request):
        """Test successful GET request."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"data": "get_result"})
        mock_response.url = "https://api.example.com/endpoint"
        mock_response.headers = {"Content-Type": "application/json"}
        mock_request.return_value.__aenter__.return_value = mock_response
        
        config = AgentConfig(
            name="http_agent",
            type=AgentType.HTTP_API,
            endpoint="https://api.example.com"
        )
        agent = HTTPAPIAgent(config)
        
        response = asyncio.run(agent.execute("endpoint", {
            "method": "GET",
            "params": {"limit": 10}
        }))
        
        assert response.success is True
        assert response.result == {"data": "get_result"}
        assert response.metadata["method"] == "GET"
        assert response.metadata["status_code"] == 200
        
        # Verify request parameters
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[1]["method"] == "GET"
        assert call_args[1]["params"] == {"limit": 10}
    
    @patch('aiohttp.ClientSession.request')
    def test_successful_post_request(self, mock_request):
        """Test successful POST request."""
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.json = AsyncMock(return_value={"id": 123, "status": "created"})
        mock_response.url = "https://api.example.com/create"
        mock_response.headers = {"Content-Type": "application/json"}
        mock_request.return_value.__aenter__.return_value = mock_response
        
        config = AgentConfig(
            name="http_agent",
            type=AgentType.HTTP_API,
            endpoint="https://api.example.com"
        )
        agent = HTTPAPIAgent(config)
        
        response = asyncio.run(agent.execute("create", {
            "method": "POST",
            "data": {"name": "test", "value": 42}
        }))
        
        assert response.success is True
        assert response.result == {"id": 123, "status": "created"}
        
        # Verify JSON data was sent
        call_args = mock_request.call_args
        assert call_args[1]["method"] == "POST"
        assert call_args[1]["json"] == {"name": "test", "value": 42}
    
    @patch('aiohttp.ClientSession.request')
    def test_basic_authentication(self, mock_request):
        """Test HTTP agent with basic authentication."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"authenticated": True})
        mock_response.url = "https://api.example.com/secure"
        mock_response.headers = {}
        mock_request.return_value.__aenter__.return_value = mock_response
        
        config = AgentConfig(
            name="http_agent",
            type=AgentType.HTTP_API,
            endpoint="https://api.example.com",
            authentication={
                "type": "basic",
                "username": "user",
                "password": "pass"
            }
        )
        agent = HTTPAPIAgent(config)
        
        response = asyncio.run(agent.execute("secure", {"method": "GET"}))
        
        assert response.success is True
        
        # Verify basic auth was used
        call_args = mock_request.call_args
        auth = call_args[1]["auth"]
        assert auth.login == "user"
        assert auth.password == "pass"
    
    @patch('aiohttp.ClientSession.request')
    def test_text_response_handling(self, mock_request):
        """Test handling of non-JSON text responses."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(side_effect=aiohttp.ContentTypeError(None, None))
        mock_response.text = AsyncMock(return_value="plain text response")
        mock_response.url = "https://api.example.com/text"
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_request.return_value.__aenter__.return_value = mock_response
        
        config = AgentConfig(name="http_agent", type=AgentType.HTTP_API, endpoint="https://api.example.com")
        agent = HTTPAPIAgent(config)
        
        response = asyncio.run(agent.execute("text", {"method": "GET"}))
        
        assert response.success is True
        assert response.result == "plain text response"
    
    @patch('aiohttp.ClientSession.request')
    def test_error_response_handling(self, mock_request):
        """Test handling of HTTP error responses."""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.json = AsyncMock(side_effect=aiohttp.ContentTypeError(None, None))
        mock_response.text = AsyncMock(return_value="Not Found")
        mock_response.url = "https://api.example.com/missing"
        mock_response.headers = {}
        mock_request.return_value.__aenter__.return_value = mock_response
        
        config = AgentConfig(name="http_agent", type=AgentType.HTTP_API, endpoint="https://api.example.com")
        agent = HTTPAPIAgent(config)
        
        response = asyncio.run(agent.execute("missing", {"method": "GET"}))
        
        assert response.success is False
        assert "HTTP 404: Not Found" in response.error
        assert response.metadata["status_code"] == 404
