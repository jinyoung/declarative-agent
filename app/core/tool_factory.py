"""
ToolFactory module for creating LangChain tools from configurations.

This module provides functionality for creating LangChain tools based on
configuration in agent definitions, supporting both built-in tools and MCP tools.
"""
from typing import List, Dict, Any, Optional, Callable
import math
import logging
import requests

from langchain.tools import Tool
from langchain_community.tools import DuckDuckGoSearchRun

# Try to import MCPTool, but don't fail if it's not available
try:
    from langchain_mcp_adapters import MCPTool
    HAS_MCP_ADAPTERS = True
except ImportError:
    HAS_MCP_ADAPTERS = False
    # Create a placeholder for testing purposes
    class MCPTool:
        def __init__(self, name, description, endpoint, headers=None):
            self.name = name
            self.description = description
            self.endpoint = endpoint
            self.headers = headers or {}
            
        def __call__(self, *args, **kwargs):
            return f"MCP Tool: {self.name} - {args[0] if args else ''}"

from app.core.schema import ToolConfig

# Configure logging
logger = logging.getLogger(__name__)


class ToolFactory:
    """
    Factory for creating LangChain tools from tool configurations.
    
    The ToolFactory is responsible for creating appropriate LangChain Tool objects
    based on the configuration specified in the agent definition.
    """
    
    def __init__(self):
        """Initialize the ToolFactory with registered tool creators."""
        # Register built-in tools creators
        self.builtin_tools: Dict[str, Callable[[ToolConfig], Optional[Tool]]] = {
            "calculator": self._create_calculator_tool,
            "search": self._create_search_tool,
            # More built-in tools can be registered here
        }
    
    def create_tools(self, tool_configs: List[ToolConfig]) -> List[Tool]:
        """
        Create LangChain tools from tool configurations.
        
        Args:
            tool_configs: List of tool configurations from the agent definition
            
        Returns:
            List of LangChain Tool objects
        """
        tools = []
        
        for config in tool_configs:
            try:
                if config.type == "builtin":
                    tool_creator = self.builtin_tools.get(config.name.lower())
                    if tool_creator:
                        tool = tool_creator(config)
                        if tool:
                            tools.append(tool)
                    else:
                        logger.warning(f"Unknown built-in tool: '{config.name}'")
                
                elif config.type == "mcp":
                    if not config.endpoint:
                        logger.warning(f"MCP tool '{config.name}' missing endpoint")
                        continue
                        
                    tool = self._create_mcp_tool(config)
                    if tool:
                        tools.append(tool)
            except Exception as e:
                logger.error(f"Error creating tool '{config.name}': {str(e)}")
        
        return tools
    
    def _create_mcp_tool(self, config: ToolConfig) -> Optional[Tool]:
        """
        Create a tool that connects to an MCP endpoint.
        
        Args:
            config: Tool configuration
            
        Returns:
            LangChain Tool object, or None if creation fails
        """
        try:
            # If MCP adapters are not available, log a warning
            if not HAS_MCP_ADAPTERS:
                logger.warning(f"langchain_mcp_adapters module not found, using placeholder implementation for {config.name}")
            
            # Create headers if API key is provided
            headers = {}
            if config.api_key:
                headers["Authorization"] = f"Bearer {config.api_key}"
                
            # Use langchain-mcp-adapters to create an MCP tool
            mcp_tool = MCPTool(
                name=config.name,
                description=config.description or f"Tool for {config.name}",
                endpoint=config.endpoint,
                headers=headers
            )
            
            # Wrap MCPTool in a standard LangChain Tool
            return Tool(
                name=config.name,
                description=config.description or f"Tool for {config.name}",
                func=mcp_tool if callable(mcp_tool) else lambda x: f"Calling {config.name} with: {x}"
            )
            
        except Exception as e:
            logger.error(f"Error creating MCP tool '{config.name}': {str(e)}")
            return None
    
    def _create_calculator_tool(self, config: ToolConfig) -> Optional[Tool]:
        """
        Create a calculator tool for performing mathematical calculations.
        
        Args:
            config: Tool configuration
            
        Returns:
            LangChain Tool object for calculator functionality
        """
        try:
            # Create our own calculator implementation
            def calculator_func(expression: str) -> str:
                """
                Evaluate a mathematical expression.
                
                Args:
                    expression: The expression to evaluate
                    
                Returns:
                    Result of the calculation as a string
                """
                try:
                    # Make the expression safe by limiting what can be evaluated
                    # This is a simplified version and should be enhanced for production
                    allowed_names = {
                        'abs': abs, 'max': max, 'min': min,
                        'pow': pow, 'round': round, 
                        'sum': sum, 'len': len,
                        'math': math,
                    }
                    
                    # Evaluate the expression in a restricted environment
                    result = eval(expression, {"__builtins__": {}}, allowed_names)
                    return str(result)
                except Exception as e:
                    return f"Error calculating result: {str(e)}"
            
            # Create a LangChain Tool with our calculator function
            return Tool(
                name=config.name,
                description=config.description or "Useful for performing mathematical calculations",
                func=calculator_func
            )
        except Exception as e:
            logger.error(f"Error creating calculator tool: {str(e)}")
            return None
    
    def _create_search_tool(self, config: ToolConfig) -> Optional[Tool]:
        """
        Create a search tool for searching the web.
        
        Args:
            config: Tool configuration
            
        Returns:
            LangChain Tool object for web search functionality
        """
        try:
            # Use DuckDuckGo search as a default search engine
            search = DuckDuckGoSearchRun()
            
            # Override name and description from the configuration
            return Tool(
                name=config.name,
                description=config.description or "Useful for searching the web for information",
                func=search.run
            )
        except Exception as e:
            logger.error(f"Error creating search tool: {str(e)}")
            return None

    def register_tool(self, tool_name: str, tool_creator_func: Callable[[ToolConfig], Optional[Tool]]) -> None:
        """
        Register a new built-in tool creator function.
        
        Args:
            tool_name: Name of the tool to register
            tool_creator_func: Function that creates the tool
        """
        self.builtin_tools[tool_name.lower()] = tool_creator_func 