"""MCP Server Agent implementation."""

import json
from typing import Any, Dict

import aiohttp

from ..models import AgentConfig, AgentResponse, AgentType
from .base import BaseAgent, AgentFactory


class MCPServerAgent(BaseAgent):
    """Agent for communicating with MCP (Model Context Protocol) servers."""
    
    async def execute(self, action: str, parameters: Dict[str, Any]) -> AgentResponse:
        """Execute an action with the MCP server.
        
        Args:
            action: Action to execute (typically a tool name)
            parameters: Parameters for the action
            
        Returns:
            AgentResponse: Response from the MCP server
        """
        try:
            # MCP protocol typically uses JSON-RPC format
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": action,
                    "arguments": parameters
                }
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
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
            
            # Make HTTP request to MCP server
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.endpoint,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        # Handle JSON-RPC response format
                        if "result" in result:
                            return AgentResponse(
                                success=True,
                                result=result["result"],
                                metadata={
                                    "status_code": response.status,
                                    "jsonrpc_id": result.get("id")
                                }
                            )
                        elif "error" in result:
                            error_info = result["error"]
                            return AgentResponse(
                                success=False,
                                error=f"MCP Error {error_info.get('code')}: {error_info.get('message')}",
                                metadata={
                                    "status_code": response.status,
                                    "jsonrpc_id": result.get("id"),
                                    "error_code": error_info.get("code")
                                }
                            )
                        else:
                            return AgentResponse(
                                success=False,
                                error="Invalid MCP response format",
                                metadata={"status_code": response.status}
                            )
                    else:
                        error_text = await response.text()
                        return AgentResponse(
                            success=False,
                            error=f"HTTP {response.status}: {error_text}",
                            metadata={"status_code": response.status}
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
        except json.JSONDecodeError as e:
            return AgentResponse(
                success=False,
                error=f"Invalid JSON response: {str(e)}"
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


# Register the agent type
AgentFactory.register_agent_type(AgentType.MCP_SERVER, MCPServerAgent)
