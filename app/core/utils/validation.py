"""Validation utilities for agent definitions."""
import json
import os
from typing import List, Dict, Optional, Union
import aiofiles
from pydantic import ValidationError

from app.core.schema import AgentDefinition, validate_agent_json


async def validate_agent_file(file_path: str) -> AgentDefinition:
    """
    Load and validate an agent definition from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing the agent definition
        
    Returns:
        AgentDefinition: Validated agent definition object
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file contains invalid JSON or doesn't conform to the schema
    """
    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file {file_path}: {str(e)}")
        
        return validate_agent_json(data)
    except FileNotFoundError:
        raise FileNotFoundError(f"Agent definition file not found: {file_path}")


async def list_available_agents(agents_dir: str) -> List[Dict[str, str]]:
    """
    List all available agent definitions in the specified directory.
    
    Args:
        agents_dir: Directory containing agent definition JSON files
        
    Returns:
        List of dictionaries containing agent ID and validation status
    """
    agents = []
    
    if not os.path.exists(agents_dir):
        return agents
    
    for filename in os.listdir(agents_dir):
        if filename.endswith('.json'):
            agent_id = os.path.splitext(filename)[0]
            file_path = os.path.join(agents_dir, filename)
            
            # Check if the agent definition is valid
            try:
                await validate_agent_file(file_path)
                status = "valid"
            except (ValueError, FileNotFoundError) as e:
                status = f"invalid: {str(e)}"
            
            agents.append({
                "id": agent_id,
                "status": status,
                "file_path": file_path
            })
    
    return agents


async def validate_all_agents(agents_dir: str) -> Dict[str, Union[List[str], List[Dict[str, str]]]]:
    """
    Validate all agent definitions in the specified directory.
    
    Args:
        agents_dir: Directory containing agent definition JSON files
        
    Returns:
        Dictionary containing lists of valid and invalid agent definitions
    """
    valid_agents = []
    invalid_agents = []
    
    agents = await list_available_agents(agents_dir)
    
    for agent in agents:
        if agent["status"] == "valid":
            valid_agents.append(agent)
        else:
            invalid_agents.append(agent)
    
    return {
        "valid": valid_agents,
        "invalid": invalid_agents
    } 