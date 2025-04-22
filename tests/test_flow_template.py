"""
Tests for the LangGraph flow template functionality.

These tests verify that flow templates can be correctly created and executed.
"""
import os
import json
import pytest
from unittest.mock import MagicMock, patch

from app.core.schema import AgentDefinition
from app.core.flow_template_manager import FlowTemplateManager
from app.core.runtime_engine import RuntimeEngine


@pytest.fixture
def mock_llm():
    """Create a mock LLM that returns predefined responses."""
    mock = MagicMock()
    
    # Set up predict method to return different responses based on input
    def predict_side_effect(prompt):
        if "Extract the name of the city" in prompt:
            return "Paris"
        elif "Based on the following information" in prompt:
            return "Here are some attractions in Paris: Eiffel Tower, Louvre Museum, Notre Dame Cathedral"
        elif "primary intent" in prompt:
            return "order"
        elif "friendly customer service response" in prompt:
            return "Thank you for contacting TechGadgets customer service. Your order information is available. Please let us know if you have any other questions."
        return "Generic LLM response"
    
    mock.predict.side_effect = predict_side_effect
    return mock


@pytest.fixture
def mock_tools():
    """Create mock tools for testing."""
    weather_tool = MagicMock()
    weather_tool.name = "WeatherTool"
    weather_tool.invoke.return_value = "Weather in Paris: 22°C, Partly Cloudy"
    
    order_tool = MagicMock()
    order_tool.name = "OrderLookup"
    order_tool.invoke.return_value = "Order #12345: Shipped on 2024-06-01, estimated delivery on 2024-06-05"
    
    product_tool = MagicMock()
    product_tool.name = "ProductSearch"
    product_tool.invoke.return_value = "Product: Smartphone X-2000, Price: $899, In Stock: Yes"
    
    shipping_tool = MagicMock()
    shipping_tool.name = "ShippingStatus"
    shipping_tool.invoke.return_value = "Shipping Status: In Transit, Current Location: Distribution Center"
    
    return_tool = MagicMock()
    return_tool.name = "ReturnPolicy"
    return_tool.invoke.return_value = "Returns accepted within 30 days of purchase with original receipt"
    
    return [weather_tool, order_tool, product_tool, shipping_tool, return_tool]


@pytest.fixture
def sequential_flow_config():
    """Load a sequential flow configuration for testing."""
    with open("app/agents/travel_agent_flow.json", "r") as f:
        config = json.load(f)
    return AgentDefinition.model_validate(config).flow_template


@pytest.fixture
def branching_flow_config():
    """Load a branching flow configuration for testing."""
    with open("app/agents/customer_service_flow.json", "r") as f:
        config = json.load(f)
    return AgentDefinition.model_validate(config).flow_template


class TestFlowTemplateManager:
    """Test the FlowTemplateManager class."""
    
    def test_create_sequential_flow(self, sequential_flow_config, mock_tools, mock_llm):
        """Test creating a sequential flow."""
        # Initialize the flow template manager
        flow_manager = FlowTemplateManager()
        
        # Create a sequential flow
        flow = flow_manager.create_flow(sequential_flow_config, mock_tools, mock_llm)
        
        # Verify the flow is created and callable
        assert flow is not None
        assert callable(flow)


    def test_create_branching_flow(self, branching_flow_config, mock_tools, mock_llm):
        """Test creating a branching flow."""
        # Initialize the flow template manager
        flow_manager = FlowTemplateManager()
        
        # Create a branching flow
        flow = flow_manager.create_flow(branching_flow_config, mock_tools, mock_llm)
        
        # Verify the flow is created and callable
        assert flow is not None
        assert callable(flow)
    
    
    @pytest.mark.asyncio
    async def test_sequential_flow_execution(self, sequential_flow_config, mock_tools, mock_llm):
        """Test executing a sequential flow."""
        # Initialize the flow template manager
        flow_manager = FlowTemplateManager()
        
        # Create a sequential flow
        flow = flow_manager.create_flow(sequential_flow_config, mock_tools, mock_llm)
        
        # Execute the flow
        result = await flow.ainvoke({
            "input": "What should I visit in Paris this weekend?",
            "steps": []
        })
        
        # Verify the flow execution result
        assert "output" in result
        assert isinstance(result["output"], str)
        assert "steps" in result
        assert len(result["steps"]) >= 3  # Should have at least 3 steps


class TestRuntimeEngineWithFlows:
    """Test the RuntimeEngine with flow templates."""
    
    @pytest.mark.asyncio
    @patch("app.core.runtime_engine.ToolFactory")
    @patch("app.core.runtime_engine.KnowledgeBaseLoader")
    async def test_create_flow_agent(self, mock_kb_loader, mock_tool_factory, mock_tools, mock_llm):
        """Test creating an agent with a flow template."""
        # Set up mocks
        mock_tool_factory.return_value.create_tools.return_value = mock_tools
        mock_kb_loader.return_value.create_knowledge_tool.return_value = None
        
        # Initialize the runtime engine
        runtime_engine = RuntimeEngine()
        runtime_engine._initialize_llm = MagicMock(return_value=mock_llm)
        
        # Load a test agent configuration
        with open("app/agents/travel_agent_flow.json", "r") as f:
            config = json.load(f)
        agent_config = AgentDefinition.model_validate(config)
        
        # Create an agent with a flow template
        agent = await runtime_engine.create_agent(agent_config)
        
        # Verify the agent is created and has the correct interface
        assert agent is not None
        assert hasattr(agent, "arun")
        
        # Test running the agent
        result = await agent.arun("What should I visit in Paris this weekend?")
        
        # Verify the result
        assert isinstance(result, str)
        assert len(result) > 0 