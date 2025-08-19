"""Tests for configuration loader."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from src.lead_agent.config_loader import ConfigLoader, ConfigurationError
from src.lead_agent.models import AgentType, WorkflowConfig, AgentConfig, TaskConfig


class TestConfigLoader:
    """Test ConfigLoader class."""
    
    def test_load_from_dict_valid(self):
        """Test loading valid configuration from dictionary."""
        config_data = {
            "name": "test_workflow",
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
        
        config = ConfigLoader.load_from_dict(config_data)
        
        assert isinstance(config, WorkflowConfig)
        assert config.name == "test_workflow"
        assert config.version == "1.0.0"
        assert len(config.agents) == 1
        assert len(config.tasks) == 1
        assert config.agents[0].name == "test_agent"
        assert config.agents[0].type == AgentType.AI_AGENT
        assert config.tasks[0].name == "test_task"
        assert config.tasks[0].agent_name == "test_agent"
    
    def test_load_from_dict_invalid(self):
        """Test loading invalid configuration from dictionary."""
        config_data = {
            "name": "test_workflow",
            # Missing required fields
        }
        
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigLoader.load_from_dict(config_data)
        
        assert "Configuration validation failed" in str(exc_info.value)
    
    def test_load_from_yaml_file(self):
        """Test loading configuration from YAML file."""
        config_data = {
            "name": "test_workflow",
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
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = ConfigLoader.load_from_file(temp_path)
            
            assert isinstance(config, WorkflowConfig)
            assert config.name == "test_workflow"
            assert len(config.agents) == 1
            assert len(config.tasks) == 1
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_load_from_json_file(self):
        """Test loading configuration from JSON file."""
        config_data = {
            "name": "test_workflow",
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
            temp_path = f.name
        
        try:
            config = ConfigLoader.load_from_file(temp_path)
            
            assert isinstance(config, WorkflowConfig)
            assert config.name == "test_workflow"
            assert len(config.agents) == 1
            assert len(config.tasks) == 1
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_load_from_nonexistent_file(self):
        """Test loading from non-existent file."""
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigLoader.load_from_file("/nonexistent/file.yaml")
        
        assert "Configuration file not found" in str(exc_info.value)
    
    def test_load_from_unsupported_format(self):
        """Test loading from unsupported file format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("some text")
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                ConfigLoader.load_from_file(temp_path)
            
            assert "Unsupported file format" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_load_from_invalid_yaml(self):
        """Test loading from invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                ConfigLoader.load_from_file(temp_path)
            
            assert "Failed to parse configuration file" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_load_from_invalid_json(self):
        """Test loading from invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json content}')
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                ConfigLoader.load_from_file(temp_path)
            
            assert "Failed to parse configuration file" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_validate_configuration_valid(self):
        """Test validation of valid configuration."""
        config = WorkflowConfig(
            name="test_workflow",
            agents=[
                AgentConfig(name="agent1", type=AgentType.AI_AGENT),
                AgentConfig(name="agent2", type=AgentType.HTTP_API)
            ],
            tasks=[
                TaskConfig(name="task1", agent_name="agent1", action="action1"),
                TaskConfig(name="task2", agent_name="agent2", action="action2", depends_on=["task1"])
            ]
        )
        
        # Should not raise any exception
        ConfigLoader.validate_configuration(config)
    
    def test_validate_configuration_undefined_agent(self):
        """Test validation with undefined agent reference."""
        config = WorkflowConfig(
            name="test_workflow",
            agents=[
                AgentConfig(name="agent1", type=AgentType.AI_AGENT)
            ],
            tasks=[
                TaskConfig(name="task1", agent_name="undefined_agent", action="action1")
            ]
        )
        
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigLoader.validate_configuration(config)
        
        assert "references undefined agent" in str(exc_info.value)
    
    def test_validate_configuration_undefined_dependency(self):
        """Test validation with undefined task dependency."""
        config = WorkflowConfig(
            name="test_workflow",
            agents=[
                AgentConfig(name="agent1", type=AgentType.AI_AGENT)
            ],
            tasks=[
                TaskConfig(name="task1", agent_name="agent1", action="action1", depends_on=["undefined_task"])
            ]
        )
        
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigLoader.validate_configuration(config)
        
        assert "depends on undefined task" in str(exc_info.value)
    
    def test_validate_configuration_circular_dependency(self):
        """Test validation with circular dependencies."""
        config = WorkflowConfig(
            name="test_workflow",
            agents=[
                AgentConfig(name="agent1", type=AgentType.AI_AGENT)
            ],
            tasks=[
                TaskConfig(name="task1", agent_name="agent1", action="action1", depends_on=["task2"]),
                TaskConfig(name="task2", agent_name="agent1", action="action2", depends_on=["task1"])
            ]
        )
        
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigLoader.validate_configuration(config)
        
        assert "Circular dependency detected" in str(exc_info.value)
    
    def test_check_circular_dependencies_complex(self):
        """Test circular dependency detection with complex graph."""
        tasks = [
            TaskConfig(name="A", agent_name="agent1", action="action", depends_on=["B"]),
            TaskConfig(name="B", agent_name="agent1", action="action", depends_on=["C"]),
            TaskConfig(name="C", agent_name="agent1", action="action", depends_on=["D"]),
            TaskConfig(name="D", agent_name="agent1", action="action", depends_on=["A"])  # Creates cycle
        ]
        
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigLoader._check_circular_dependencies(tasks)
        
        assert "Circular dependency detected" in str(exc_info.value)
    
    def test_check_circular_dependencies_no_cycle(self):
        """Test circular dependency detection with valid graph."""
        tasks = [
            TaskConfig(name="A", agent_name="agent1", action="action", depends_on=[]),
            TaskConfig(name="B", agent_name="agent1", action="action", depends_on=["A"]),
            TaskConfig(name="C", agent_name="agent1", action="action", depends_on=["A"]),
            TaskConfig(name="D", agent_name="agent1", action="action", depends_on=["B", "C"])
        ]
        
        # Should not raise any exception
        ConfigLoader._check_circular_dependencies(tasks)
