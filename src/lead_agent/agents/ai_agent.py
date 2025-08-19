"""AI Agent implementation."""

import json
from typing import Any, Dict

import aiohttp

from ..models import AgentConfig, AgentResponse, AgentType
from .base import BaseAgent, AgentFactory


class AIAgent(BaseAgent):
    """Agent for communicating with AI services."""
    
    async def execute(self, action: str, parameters: Dict[str, Any]) -> AgentResponse:
        """Execute an action with the AI agent.
        
        Args:
            action: Action to execute
            parameters: Parameters for the action
            
        Returns:
            AgentResponse: Response from the AI agent
        """
        try:
            # Prepare the request payload
            payload = {
                "action": action,
                "parameters": parameters,
                **self.config.custom_params
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
            
            # Make HTTP request to AI service
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.endpoint,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        return AgentResponse(
                            success=True,
                            result=result,
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
AgentFactory.register_agent_type(AgentType.AI_AGENT, AIAgent)
