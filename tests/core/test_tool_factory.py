"""Tests for the ToolFactory class."""
import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any

from langchain.tools import Tool

# Mock imports for testing
import sys
from unittest.mock import MagicMock

# Create mocks for external dependencies
mock_duckduckgo = MagicMock()
mock_mcp_tool = MagicMock()

# Add mocks to sys.modules
sys.modules['langchain_community.tools.DuckDuckGoSearchRun'] = mock_duckduckgo
sys.modules['langchain_mcp_adapters'] = MagicMock()
sys.modules['langchain_mcp_adapters.MCPTool'] = mock_mcp_tool

# Now import our module under test
from app.core.tool_factory import ToolFactory
from app.core.schema import ToolConfig


class TestToolFactory:
    """Tests for the ToolFactory class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock for DuckDuckGoSearchRun
        self.mock_search = MagicMock()
        self.mock_search.run.return_value = "Search results"
        mock_duckduckgo.DuckDuckGoSearchRun.return_value = self.mock_search

    def test_init(self):
        """Test initialization of ToolFactory."""
        factory = ToolFactory()
        assert "calculator" in factory.builtin_tools
        assert "search" in factory.builtin_tools
    
    def test_register_tool(self):
        """Test registering a custom tool."""
        factory = ToolFactory()
        
        # Create a mock tool creator function
        def mock_tool_creator(config):
            return Tool(name=config.name, func=lambda x: x, description="Mock tool")
        
        # Register the tool
        factory.register_tool("custom_tool", mock_tool_creator)
        
        # Verify it was registered
        assert "custom_tool" in factory.builtin_tools
        assert factory.builtin_tools["custom_tool"] == mock_tool_creator

    def test_create_calculator_tool(self):
        """Test creating a calculator tool."""
        factory = ToolFactory()
        
        config = ToolConfig(
            name="math_calculator",
            type="builtin",
            description="Math calculator for complex calculations"
        )
        
        tool = factory._create_calculator_tool(config)
        
        assert tool is not None
        assert tool.name == "math_calculator"
        assert tool.description == "Math calculator for complex calculations"
        assert callable(tool.func)
        
        # Test tool functionality
        result = tool.func("2 + 2")
        assert result == "4"
    
    def test_create_search_tool(self):
        """Test creating a search tool."""
        factory = ToolFactory()
        
        # Mock the DuckDuckGoSearchRun
        with patch("app.core.tool_factory.DuckDuckGoSearchRun", return_value=self.mock_search):
            config = ToolConfig(
                name="web_search",
                type="builtin",
                description="Search the web for information"
            )
            
            tool = factory._create_search_tool(config)
            
            assert tool is not None
            assert tool.name == "web_search"
            assert tool.description == "Search the web for information"
            assert callable(tool.func)
            
            # Test tool functionality
            result = tool.func("test query")
            assert result == "Search results"
            self.mock_search.run.assert_called_once_with("test query")
    
    def test_create_mcp_tool(self):
        """Test creating an MCP tool."""
        factory = ToolFactory()
        
        # Mock the MCPTool
        mock_tool = MagicMock()
        
        with patch("app.core.tool_factory.MCPTool", return_value=mock_tool):
            config = ToolConfig(
                name="mcp_tool_name",
                type="mcp",
                description="MCP tool description",
                endpoint="http://example.com/api",
                api_key="test_api_key"
            )
            
            tool = factory._create_mcp_tool(config)
            
            assert tool is not None
            assert tool.name == "mcp_tool_name"
            assert tool.description == "MCP tool description"
        
    def test_create_mcp_tool_without_endpoint(self):
        """Test attempting to create an MCP tool without an endpoint."""
        factory = ToolFactory()
        
        config = ToolConfig(
            name="invalid_mcp_tool",
            type="mcp",
            description="MCP tool without endpoint"
            # endpoint is missing
        )
        
        # This should not create a tool since endpoint is required
        with patch("app.core.tool_factory.logger") as mock_logger:
            tools = factory.create_tools([config])
            assert len(tools) == 0
            mock_logger.warning.assert_called_once()
    
    def test_create_tools_with_various_configs(self):
        """Test creating multiple tools with different configurations."""
        factory = ToolFactory()
        
        # Setup mocks
        mock_tool = MagicMock()
        
        with patch("app.core.tool_factory.DuckDuckGoSearchRun", return_value=self.mock_search), \
             patch("app.core.tool_factory.MCPTool", return_value=mock_tool):
            
            configs = [
                ToolConfig(
                    name="calculator",
                    type="builtin",
                    description="Calculator"
                ),
                ToolConfig(
                    name="search",
                    type="builtin",
                    description="Search"
                ),
                ToolConfig(
                    name="external_api",
                    type="mcp",
                    description="External API",
                    endpoint="http://example.com/api"
                ),
                ToolConfig(
                    name="invalid_tool",
                    type="builtin",
                    description="Invalid tool type"
                )
            ]
            
            with patch("app.core.tool_factory.logger") as mock_logger:
                tools = factory.create_tools(configs)
                
                # Should create 3 tools (calculator, search, and MCP)
                assert len(tools) == 3
                
                # Verify tool names are correct
                tool_names = [tool.name for tool in tools]
                assert "calculator" in tool_names
                assert "search" in tool_names
                assert "external_api" in tool_names
                
                # Verify warning was logged for the invalid tool
                mock_logger.warning.assert_called_once()
    
    def test_create_tools_handles_exceptions(self):
        """Test that create_tools handles exceptions when creating tools."""
        factory = ToolFactory()
        
        # Create a configuration that will cause an exception
        config = ToolConfig(
            name="problematic_tool",
            type="builtin",
            description="This tool will cause an exception"
        )
        
        # Patch the tool creator to raise an exception
        with patch.dict(factory.builtin_tools, {"problematic_tool": lambda x: 1/0}):
            with patch("app.core.tool_factory.logger") as mock_logger:
                # This should not raise an exception
                tools = factory.create_tools([config])
                
                # No tools should be created
                assert len(tools) == 0
                
                # Error should be logged
                mock_logger.error.assert_called_once() 