"""Configuration loader for workflows and agents."""

import json
from pathlib import Path
from typing import Dict, Any, Union

import yaml
from pydantic import ValidationError

from .models import WorkflowConfig


class ConfigurationError(Exception):
    """Raised when configuration loading fails."""
    pass


class ConfigLoader:
    """Loads and validates workflow configurations."""

    @staticmethod
    def load_from_file(file_path: Union[str, Path]) -> WorkflowConfig:
        """Load workflow configuration from a file.
        
        Args:
            file_path: Path to the configuration file (YAML or JSON)
            
        Returns:
            WorkflowConfig: Validated workflow configuration
            
        Raises:
            ConfigurationError: If loading or validation fails
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ConfigurationError(f"Configuration file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    config_data = yaml.safe_load(f)
                elif file_path.suffix.lower() == '.json':
                    config_data = json.load(f)
                else:
                    raise ConfigurationError(
                        f"Unsupported file format: {file_path.suffix}"
                    )
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ConfigurationError(f"Failed to parse configuration file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to read configuration file: {e}")
        
        return ConfigLoader.load_from_dict(config_data)
    
    @staticmethod
    def load_from_dict(config_data: Dict[str, Any]) -> WorkflowConfig:
        """Load workflow configuration from a dictionary.
        
        Args:
            config_data: Configuration data as dictionary
            
        Returns:
            WorkflowConfig: Validated workflow configuration
            
        Raises:
            ConfigurationError: If validation fails
        """
        try:
            return WorkflowConfig(**config_data)
        except ValidationError as e:
            raise ConfigurationError(f"Configuration validation failed: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")
    
    @staticmethod
    def validate_configuration(config: WorkflowConfig) -> None:
        """Validate workflow configuration for consistency.
        
        Args:
            config: Workflow configuration to validate
            
        Raises:
            ConfigurationError: If validation fails
        """
        # Check that all task agents are defined
        agent_names = {agent.name for agent in config.agents}
        for task in config.tasks:
            if task.agent_name not in agent_names:
                raise ConfigurationError(
                    f"Task '{task.name}' references undefined agent '{task.agent_name}'"
                )
        
        # Check task dependencies
        task_names = {task.name for task in config.tasks}
        for task in config.tasks:
            for dependency in task.depends_on:
                if dependency not in task_names:
                    raise ConfigurationError(
                        f"Task '{task.name}' depends on undefined task '{dependency}'"
                    )
        
        # Check for circular dependencies
        ConfigLoader._check_circular_dependencies(config.tasks)
    
    @staticmethod
    def _check_circular_dependencies(tasks: list) -> None:
        """Check for circular dependencies in tasks.
        
        Args:
            tasks: List of task configurations
            
        Raises:
            ConfigurationError: If circular dependencies are found
        """
        task_deps = {task.name: set(task.depends_on) for task in tasks}
        
        def has_cycle(task_name: str, visited: set, rec_stack: set) -> bool:
            visited.add(task_name)
            rec_stack.add(task_name)
            
            for dep in task_deps.get(task_name, set()):
                if dep not in visited:
                    if has_cycle(dep, visited, rec_stack):
                        return True
                elif dep in rec_stack:
                    return True
            
            rec_stack.remove(task_name)
            return False
        
        visited = set()
        for task in tasks:
            if task.name not in visited:
                if has_cycle(task.name, visited, set()):
                    raise ConfigurationError("Circular dependency detected in tasks")
