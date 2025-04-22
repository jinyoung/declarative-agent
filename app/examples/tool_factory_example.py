#!/usr/bin/env python
"""
Example script demonstrating how to use the ToolFactory.

This script creates various tool configurations and uses the ToolFactory
to create LangChain tools based on these configurations.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any

from app.core.tool_factory import ToolFactory
from app.core.schema import ToolConfig, AgentDefinition
from app.core.agent_manager import AgentManager


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def load_agent_tools(agent_id: str) -> List[Any]:
    """Load an agent definition and create its tools."""
    # Use AgentManager to load the agent configuration
    manager = AgentManager()
    
    try:
        # Load the agent configuration
        agent_config = await manager.load_agent_config(agent_id)
        logger.info(f"Loaded agent '{agent_id}' with {len(agent_config.tools)} tools")
        
        # Create the tools using ToolFactory
        factory = ToolFactory()
        tools = factory.create_tools(agent_config.tools)
        
        logger.info(f"Created {len(tools)} tools for agent '{agent_id}'")
        return tools
    
    except ValueError as e:
        logger.error(f"Error loading agent '{agent_id}': {str(e)}")
        return []


def create_tool_examples() -> None:
    """Create and demonstrate various tool examples."""
    factory = ToolFactory()
    
    # Example 1: Calculator tool
    calc_config = ToolConfig(
        name="calculator",
        type="builtin",
        description="Performs mathematical calculations"
    )
    calculator_tool = factory._create_calculator_tool(calc_config)
    
    if calculator_tool:
        logger.info("Calculator tool example:")
        result = calculator_tool.run("2 * (3 + 4) / 2")
        logger.info(f"  2 * (3 + 4) / 2 = {result}")
    
    # Example 2: Search tool
    search_config = ToolConfig(
        name="search",
        type="builtin",
        description="Searches the web for information"
    )
    search_tool = factory._create_search_tool(search_config)
    
    if search_tool:
        logger.info("Search tool example:")
        logger.info("  Would search the web (not executing to avoid actual API calls)")
    
    # Example 3: MCP tool (would require an actual endpoint)
    mcp_config = ToolConfig(
        name="mcp_example",
        type="mcp",
        description="Connects to an external MCP endpoint",
        endpoint="http://example.com/api/tool",
        api_key="demo_key"
    )
    logger.info("MCP tool example:")
    logger.info("  Would connect to MCP endpoint (not executing to avoid actual API calls)")
    
    # Example 4: Creating multiple tools at once
    configs = [calc_config, search_config, mcp_config]
    tools = factory.create_tools(configs)
    
    logger.info(f"Created {len(tools)} tools with valid configurations")
    
    # Example 5: Custom tool registration
    logger.info("Registering a custom tool:")
    
    def custom_tool_creator(config: ToolConfig):
        return {
            "name": config.name,
            "description": config.description,
            "execute": lambda query: f"Custom result for: {query}"
        }
    
    factory.register_tool("custom", custom_tool_creator)
    logger.info("  Custom tool registered successfully")


async def main():
    """Main entry point for the example script."""
    logger.info("ToolFactory Example Script")
    logger.info("========================")
    
    # Create example tools
    create_tool_examples()
    
    # Load tools from an agent definition
    logger.info("\nLoading tools from agent definitions:")
    
    for agent_id in ["math_assistant", "knowledge_agent", "multi_tool_agent"]:
        tools = await load_agent_tools(agent_id)
        
        if tools:
            logger.info(f"Tools for {agent_id}:")
            for tool in tools:
                logger.info(f"  - {tool.name}: {tool.description}")
        
        logger.info("")


if __name__ == "__main__":
    asyncio.run(main()) 