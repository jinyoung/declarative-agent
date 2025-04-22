"""
AgentManager module for loading and managing agent configurations.

This module provides functionality for loading agent definitions from JSON files,
validating them against the schema, and caching them for efficient access.
"""
import json
import os
from typing import Dict, Any, Optional, List
import aiofiles
from pydantic import ValidationError

from app.core.schema import AgentDefinition, validate_agent_json
from app.core.utils.validation import validate_agent_file, list_available_agents


class AgentManager:
    """
    Manages the lifecycle and configuration of agents in the system.
    
    The AgentManager is responsible for loading agent definition files, 
    validating them against the schema, and caching them for efficient access.
    """
    
    def __init__(self, agents_dir: str = "app/agents"):
        """
        Initialize the AgentManager with the directory containing agent definitions.
        
        Args:
            agents_dir: Path to the directory containing agent JSON files (default: "app/agents")
        """
        self.agents_dir = agents_dir
        self.cache: Dict[str, AgentDefinition] = {}
    
    async def load_agent_config(self, agent_id: str, force_reload: bool = False) -> AgentDefinition:
        """
        Load agent configuration from JSON file.
        
        Args:
            agent_id: ID of the agent to load
            force_reload: If True, force reload from file even if cached
            
        Returns:
            AgentDefinition: The validated agent configuration
            
        Raises:
            ValueError: If the agent definition file is not found, contains invalid JSON,
                        or fails schema validation
        """
        # Return cached config if available and not forcing reload
        if agent_id in self.cache and not force_reload:
            return self.cache[agent_id]
            
        file_path = os.path.join(self.agents_dir, f"{agent_id}.json")
        
        try:
            # Read and parse the JSON file
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                config_dict = json.loads(content)
                
            # Validate against schema
            agent_config = AgentDefinition.model_validate(config_dict)
            
            # Cache the validated config
            self.cache[agent_id] = agent_config
            return agent_config
            
        except FileNotFoundError:
            raise ValueError(f"Agent definition not found for ID: {agent_id}")
        except ValidationError as e:
            raise ValueError(f"Invalid agent definition: {str(e)}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in agent definition file: {file_path}")
    
    async def list_agents(self) -> List[Dict[str, str]]:
        """
        List all available agents in the agents directory.
        
        Returns:
            List of dictionaries containing agent ID and validation status
        """
        return await list_available_agents(self.agents_dir)
    
    async def get_agent_ids(self) -> List[str]:
        """
        Get a list of all valid agent IDs.
        
        Returns:
            List of valid agent IDs
        """
        agents = await self.list_agents()
        return [agent["id"] for agent in agents if agent["status"] == "valid"]
    
    def clear_cache(self, agent_id: Optional[str] = None) -> None:
        """
        Clear the agent configuration cache.
        
        Args:
            agent_id: If provided, clear only the cache for this agent; otherwise, clear all
        """
        if agent_id:
            if agent_id in self.cache:
                del self.cache[agent_id]
        else:
            self.cache.clear()
    
    async def save_agent_config(self, agent_id: str, config: Dict[str, Any]) -> AgentDefinition:
        """
        Save an agent configuration to a JSON file and update the cache.
        
        Args:
            agent_id: ID of the agent to save
            config: Agent configuration dictionary
            
        Returns:
            AgentDefinition: The validated agent configuration
            
        Raises:
            ValueError: If the agent configuration is invalid
        """
        # Create agents directory if it doesn't exist
        os.makedirs(self.agents_dir, exist_ok=True)
        
        file_path = os.path.join(self.agents_dir, f"{agent_id}.json")
        
        # Validate the configuration
        try:
            agent_config = validate_agent_json(config)
        except ValueError as e:
            raise ValueError(f"Invalid agent configuration: {str(e)}")
        
        # Write to file
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(config, indent=2))
        
        # Update cache
        self.cache[agent_id] = agent_config
        
        return agent_config
    
    async def delete_agent(self, agent_id: str) -> bool:
        """
        Delete an agent definition file and remove it from the cache.
        
        Args:
            agent_id: ID of the agent to delete
            
        Returns:
            bool: True if the agent was deleted, False if it didn't exist
        """
        file_path = os.path.join(self.agents_dir, f"{agent_id}.json")
        
        # Check if file exists
        if not os.path.exists(file_path):
            return False
        
        # Delete file
        os.remove(file_path)
        
        # Remove from cache
        if agent_id in self.cache:
            del self.cache[agent_id]
        
        return True 