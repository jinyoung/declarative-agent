"""Test cases for the RuntimeEngine."""
import unittest
from unittest.mock import patch, MagicMock, AsyncMock

from app.core.schema import AgentDefinition, ToolConfig, KnowledgeBaseConfig, VectorDBConfig
from app.core.runtime_engine import RuntimeEngine


class TestRuntimeEngine(unittest.TestCase):
    """Test cases for the RuntimeEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = RuntimeEngine()
        
        # Create a mock agent definition
        self.agent_config = AgentDefinition(
            persona="You are a helpful assistant",
            tools=[
                ToolConfig(
                    name="calculator",
                    type="builtin",
                    description="A calculator tool"
                )
            ],
            knowledge_base=None,
            model="gpt-3.5-turbo"
        )
        
        # Agent config with knowledge base
        self.kb_agent_config = AgentDefinition(
            persona="You are a knowledgeable assistant",
            tools=[],
            knowledge_base=KnowledgeBaseConfig(
                type="vectordb",
                config=VectorDBConfig(
                    type="vectordb",
                    uri="/path/to/vectordb",
                    k=3
                )
            ),
            model="gpt-4"
        )
        
        # Agent config with Claude model
        self.claude_agent_config = AgentDefinition(
            persona="You are Claude, a helpful AI assistant",
            tools=[],
            knowledge_base=None,
            model="claude-3-opus-20240229"
        )
    
    @patch("app.core.runtime_engine.ChatOpenAI")
    @patch("app.core.runtime_engine.initialize_agent")
    @patch("app.core.runtime_engine.ConversationBufferMemory")
    def test_create_agent_with_openai_model(self, mock_memory, mock_initialize, mock_openai):
        """Test creating an agent with an OpenAI model."""
        # Setup mocks
        mock_memory.return_value = MagicMock()
        mock_agent = MagicMock()
        mock_initialize.return_value = mock_agent
        mock_llm = MagicMock()
        mock_openai.return_value = mock_llm
        
        # Mock tool factory
        self.engine.tool_factory.create_tools = MagicMock(return_value=[MagicMock()])
        
        # Call the method
        agent = asyncio.run(self.engine.create_agent(self.agent_config))
        
        # Verify the result
        self.assertEqual(agent, mock_agent)
        
        # Verify mocks were called correctly
        mock_openai.assert_called_once()
        mock_initialize.assert_called_once()
        self.engine.tool_factory.create_tools.assert_called_once_with(self.agent_config.tools)
    
    @patch("app.core.runtime_engine.ChatAnthropic")
    @patch("app.core.runtime_engine.initialize_agent")
    @patch("app.core.runtime_engine.ConversationBufferMemory")
    def test_create_agent_with_claude_model(self, mock_memory, mock_initialize, mock_anthropic):
        """Test creating an agent with a Claude model."""
        # Setup mocks
        mock_memory.return_value = MagicMock()
        mock_agent = MagicMock()
        mock_initialize.return_value = mock_agent
        mock_llm = MagicMock()
        mock_anthropic.return_value = mock_llm
        
        # Mock tool factory
        self.engine.tool_factory.create_tools = MagicMock(return_value=[MagicMock()])
        
        # Call the method
        agent = asyncio.run(self.engine.create_agent(self.claude_agent_config))
        
        # Verify the result
        self.assertEqual(agent, mock_agent)
        
        # Verify mocks were called correctly
        mock_anthropic.assert_called_once()
        mock_initialize.assert_called_once()
    
    @patch("app.core.runtime_engine.ChatOpenAI")
    @patch("app.core.runtime_engine.initialize_agent")
    def test_create_agent_with_knowledge_base(self, mock_initialize, mock_openai):
        """Test creating an agent with a knowledge base."""
        # Setup mocks
        mock_agent = MagicMock()
        mock_initialize.return_value = mock_agent
        mock_llm = MagicMock()
        mock_openai.return_value = mock_llm
        
        # Mock tool factory and knowledge base loader
        self.engine.tool_factory.create_tools = MagicMock(return_value=[MagicMock()])
        mock_kb_tool = MagicMock()
        self.engine.kb_loader.create_knowledge_tool = MagicMock(return_value=mock_kb_tool)
        
        # Call the method
        agent = asyncio.run(self.engine.create_agent(self.kb_agent_config))
        
        # Verify the result
        self.assertEqual(agent, mock_agent)
        
        # Verify mocks were called correctly
        self.engine.kb_loader.create_knowledge_tool.assert_called_once_with(
            self.kb_agent_config.knowledge_base
        )
    
    @patch("app.core.runtime_engine.initialize_agent")
    def test_create_agent_sets_persona(self, mock_initialize):
        """Test that the agent's persona is set correctly."""
        # Setup mocks
        mock_agent = MagicMock()
        mock_agent.agent.llm_chain.prompt.messages = [MagicMock()]
        mock_agent.agent.llm_chain.prompt.messages[0].prompt = MagicMock()
        mock_initialize.return_value = mock_agent
        
        # Mock tool factory and LLM initialization
        self.engine.tool_factory.create_tools = MagicMock(return_value=[])
        self.engine._initialize_llm = MagicMock()
        
        # Call the method
        agent = asyncio.run(self.engine.create_agent(self.agent_config))
        
        # Verify that the persona was set
        self.assertEqual(
            mock_agent.agent.llm_chain.prompt.messages[0].prompt.template,
            self.agent_config.persona
        )
    
    @patch("app.core.runtime_engine.ChatOpenAI")
    def test_initialize_llm_with_unknown_model(self, mock_openai):
        """Test initializing an LLM with an unknown model type."""
        # Setup test data
        model_name = "unknown-model"
        
        # Call the method
        self.engine._initialize_llm(model_name)
        
        # Verify that ChatOpenAI was called with the default model
        mock_openai.assert_called_once()
        self.assertEqual(mock_openai.call_args[1]["model_name"], "gpt-4")
    
    async def test_run_agent_success(self):
        """Test running an agent successfully."""
        # Setup mock agent
        mock_agent = AsyncMock()
        mock_agent.arun.return_value = "The answer is 42"
        
        # Call the method
        response = await self.engine.run_agent(mock_agent, "What is the answer?")
        
        # Verify the result
        self.assertEqual(response, "The answer is 42")
        mock_agent.arun.assert_called_once_with("What is the answer?")
    
    async def test_run_agent_error(self):
        """Test error handling when running an agent."""
        # Setup mock agent that raises an exception
        mock_agent = AsyncMock()
        mock_agent.arun.side_effect = Exception("Test error")
        
        # Call the method
        response = await self.engine.run_agent(mock_agent, "What is the answer?")
        
        # Verify the result contains the error message
        self.assertIn("Error running agent: Test error", response)


if __name__ == "__main__":
    import asyncio
    unittest.main() 