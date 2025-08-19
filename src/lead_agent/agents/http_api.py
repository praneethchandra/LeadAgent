"""HTTP API Agent implementation."""

import json
from typing import Any, Dict
from urllib.parse import urljoin

import aiohttp

from ..models import AgentConfig, AgentResponse, AgentType
from .base import BaseAgent, AgentFactory


class HTTPAPIAgent(BaseAgent):
    """Agent for communicating with HTTP APIs."""
    
    async def execute(self, action: str, parameters: Dict[str, Any]) -> AgentResponse:
        """Execute an action with the HTTP API.
        
        Args:
            action: Action to execute (HTTP method or endpoint)
            parameters: Parameters for the action
            
        Returns:
            AgentResponse: Response from the HTTP API
        """
        try:
            # Extract HTTP method and endpoint from action or parameters
            method = parameters.get("method", "POST").upper()
            endpoint = parameters.get("endpoint", action)
            
            # Build full URL
            if endpoint.startswith("http"):
                url = endpoint
            else:
                url = urljoin(self.config.endpoint or "", endpoint)
            
            # Prepare request data
            request_data = parameters.get("data", {})
            query_params = parameters.get("params", {})
            
            headers = {
                "Content-Type": "application/json"
            }
            
            # Add custom headers
            custom_headers = parameters.get("headers", {})
            headers.update(custom_headers)
            
            # Add authentication if configured
            if self.config.authentication:
                auth_type = self.config.authentication.get("type")
                if auth_type == "bearer":
                    token = self.config.authentication.get("token")
                    headers["Authorization"] = f"Bearer {token}"
                elif auth_type == "api_key":
                    key = self.config.authentication.get("key")
                    key_header = self.config.authentication.get("header", "X-API-Key")
                    headers[key_header] = key
                elif auth_type == "basic":
                    username = self.config.authentication.get("username")
                    password = self.config.authentication.get("password")
                    auth = aiohttp.BasicAuth(username, password)
                else:
                    auth = None
            else:
                auth = None
            
            # Make HTTP request
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    json=request_data if method in ["POST", "PUT", "PATCH"] else None,
                    params=query_params,
                    headers=headers,
                    auth=auth,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    
                    # Try to parse JSON response, fallback to text
                    try:
                        result = await response.json()
                    except (json.JSONDecodeError, aiohttp.ContentTypeError):
                        result = await response.text()
                    
                    success = 200 <= response.status < 300
                    
                    return AgentResponse(
                        success=success,
                        result=result if success else None,
                        error=None if success else f"HTTP {response.status}: {result}",
                        metadata={
                            "status_code": response.status,
                            "method": method,
                            "url": str(response.url),
                            "headers": dict(response.headers)
                        }
                    )
                        
        except aiohttp.ClientTimeout:
            return AgentResponse(
                success=False,
                error="Request timeout"
            )
        except aiohttp.ClientError as e:
            return AgentResponse(
                success=False,
                error=f"HTTP client error: {str(e)}"
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


# Register the agent type
AgentFactory.register_agent_type(AgentType.HTTP_API, HTTPAPIAgent)
