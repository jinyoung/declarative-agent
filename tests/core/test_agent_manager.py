"""Tests for the AgentManager class."""
import os
import json
import pytest
import tempfile
import shutil
from typing import Dict, Any

from app.core.agent_manager import AgentManager
from app.core.schema import AgentDefinition


@pytest.fixture
def test_agents_dir():
    """Create a temporary directory for agent definitions."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def agent_manager(test_agents_dir):
    """Create an AgentManager instance with a test agents directory."""
    return AgentManager(agents_dir=test_agents_dir)


@pytest.fixture
def valid_agent_config() -> Dict[str, Any]:
    """Return a valid agent configuration."""
    return {
        "persona": "You are a helpful assistant that specializes in mathematics.",
        "tools": [
            {
                "name": "calculator",
                "type": "builtin",
                "description": "Performs calculations"
            }
        ],
        "model": "gpt-4"
    }


@pytest.fixture
def invalid_agent_config() -> Dict[str, Any]:
    """Return an invalid agent configuration (missing persona)."""
    return {
        "tools": [
            {
                "name": "calculator",
                "type": "builtin",
                "description": "Performs calculations"
            }
        ],
        "model": "gpt-4"
    }


@pytest.fixture
async def sample_agent_file(test_agents_dir, valid_agent_config):
    """Create a sample agent file in the test directory."""
    agent_id = "test-agent"
    file_path = os.path.join(test_agents_dir, f"{agent_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(valid_agent_config, f)
    return agent_id, file_path


class TestAgentManager:
    """Tests for the AgentManager class."""

    @pytest.mark.asyncio
    async def test_load_agent_config(self, agent_manager, sample_agent_file):
        """Test loading a valid agent configuration."""
        agent_id, _ = sample_agent_file
        agent_config = await agent_manager.load_agent_config(agent_id)
        
        assert isinstance(agent_config, AgentDefinition)
        assert agent_config.persona == "You are a helpful assistant that specializes in mathematics."
        assert len(agent_config.tools) == 1
        assert agent_config.tools[0].name == "calculator"
        assert agent_config.model == "gpt-4"

    @pytest.mark.asyncio
    async def test_load_agent_config_not_found(self, agent_manager):
        """Test loading a non-existent agent configuration."""
        with pytest.raises(ValueError) as excinfo:
            await agent_manager.load_agent_config("non-existent-agent")
        assert "not found" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_load_agent_config_invalid_json(self, agent_manager, test_agents_dir):
        """Test loading an agent configuration with invalid JSON."""
        agent_id = "invalid-json"
        file_path = os.path.join(test_agents_dir, f"{agent_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("This is not valid JSON")
        
        with pytest.raises(ValueError) as excinfo:
            await agent_manager.load_agent_config(agent_id)
        assert "Invalid JSON" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_caching(self, agent_manager, sample_agent_file):
        """Test that agent configurations are cached."""
        agent_id, file_path = sample_agent_file
        
        # Load the config first time (should read from file)
        agent_config1 = await agent_manager.load_agent_config(agent_id)
        
        # Modify the file to verify cache is used
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({"persona": "Modified persona", "model": "gpt-3.5-turbo"}, f)
        
        # Load again without force_reload (should use cache)
        agent_config2 = await agent_manager.load_agent_config(agent_id)
        
        # Should be the same object from cache
        assert agent_config1 is agent_config2
        assert agent_config2.persona == "You are a helpful assistant that specializes in mathematics."
        
        # Now force reload (should read from file)
        agent_config3 = await agent_manager.load_agent_config(agent_id, force_reload=True)
        
        # Should be a different object with updated data
        assert agent_config1 is not agent_config3
        assert agent_config3.persona == "Modified persona"
        assert agent_config3.model == "gpt-3.5-turbo"

    @pytest.mark.asyncio
    async def test_clear_cache(self, agent_manager, sample_agent_file):
        """Test clearing the cache."""
        agent_id, file_path = sample_agent_file
        
        # Load the config to populate the cache
        await agent_manager.load_agent_config(agent_id)
        
        # Verify it's in the cache
        assert agent_id in agent_manager.cache
        
        # Clear the cache for this agent
        agent_manager.clear_cache(agent_id)
        
        # Verify it's not in the cache
        assert agent_id not in agent_manager.cache
        
        # Load the config again to populate the cache
        await agent_manager.load_agent_config(agent_id)
        
        # Verify it's in the cache
        assert agent_id in agent_manager.cache
        
        # Clear the entire cache
        agent_manager.clear_cache()
        
        # Verify the cache is empty
        assert not agent_manager.cache

    @pytest.mark.asyncio
    async def test_list_agents(self, agent_manager, test_agents_dir, valid_agent_config):
        """Test listing available agents."""
        # Create multiple agent files
        agent_ids = ["agent1", "agent2", "agent3"]
        for agent_id in agent_ids:
            file_path = os.path.join(test_agents_dir, f"{agent_id}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(valid_agent_config, f)
        
        # Create an invalid agent file
        invalid_agent_id = "invalid-agent"
        file_path = os.path.join(test_agents_dir, f"{invalid_agent_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("Invalid JSON")
        
        # List agents
        agents = await agent_manager.list_agents()
        
        # Verify all agents are listed
        assert len(agents) == 4
        
        # Get valid agent IDs
        valid_ids = await agent_manager.get_agent_ids()
        
        # Verify only valid agents are included
        assert len(valid_ids) == 3
        for agent_id in agent_ids:
            assert agent_id in valid_ids
        assert invalid_agent_id not in valid_ids

    @pytest.mark.asyncio
    async def test_save_agent_config(self, agent_manager, test_agents_dir, valid_agent_config):
        """Test saving an agent configuration."""
        agent_id = "new-agent"
        
        # Save the configuration
        agent_config = await agent_manager.save_agent_config(agent_id, valid_agent_config)
        
        # Verify the file was created
        file_path = os.path.join(test_agents_dir, f"{agent_id}.json")
        assert os.path.exists(file_path)
        
        # Verify the configuration was cached
        assert agent_id in agent_manager.cache
        
        # Verify the file contents
        with open(file_path, "r", encoding="utf-8") as f:
            saved_config = json.load(f)
        assert saved_config["persona"] == valid_agent_config["persona"]
        assert saved_config["tools"] == valid_agent_config["tools"]
        assert saved_config["model"] == valid_agent_config["model"]

    @pytest.mark.asyncio
    async def test_save_invalid_agent_config(self, agent_manager, invalid_agent_config):
        """Test saving an invalid agent configuration."""
        with pytest.raises(ValueError) as excinfo:
            await agent_manager.save_agent_config("invalid-agent", invalid_agent_config)
        assert "Invalid agent configuration" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_delete_agent(self, agent_manager, sample_agent_file):
        """Test deleting an agent."""
        agent_id, file_path = sample_agent_file
        
        # Load the agent to populate the cache
        await agent_manager.load_agent_config(agent_id)
        
        # Verify it's in the cache
        assert agent_id in agent_manager.cache
        
        # Delete the agent
        result = await agent_manager.delete_agent(agent_id)
        
        # Verify the operation was successful
        assert result is True
        
        # Verify the file was deleted
        assert not os.path.exists(file_path)
        
        # Verify it was removed from the cache
        assert agent_id not in agent_manager.cache
        
        # Try to delete a non-existent agent
        result = await agent_manager.delete_agent("non-existent-agent")
        
        # Verify the operation failed (but didn't raise an exception)
        assert result is False 