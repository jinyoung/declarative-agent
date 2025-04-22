"""
Tests for the FastAPI application endpoints.
"""
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.api.main import app, QueryRequest, active_agents
from app.core.schema import AgentConfig, ToolConfig, KnowledgeBaseConfig


class TestAPIEndpoints(unittest.TestCase):
    """
    Test cases for the FastAPI application endpoints.
    """
    
    def setUp(self):
        """
        Set up the test client and mock objects.
        """
        self.client = TestClient(app)
        
        # Create sample agent configurations for testing
        self.sample_agent_config = AgentConfig(
            id="test-agent",
            model="gpt-3.5-turbo",
            persona="A helpful assistant for testing",
            tools=[
                ToolConfig(name="calculator", description="Performs calculations")
            ],
            knowledge_base=None
        )
        
        self.agent_with_kb_config = AgentConfig(
            id="kb-agent",
            model="gpt-4",
            persona="An agent with knowledge base access",
            tools=[],
            knowledge_base=KnowledgeBaseConfig(
                type="vector",
                source="test-source",
                config={"path": "/tmp/test_kb"}
            )
        )
        
        # Clear the active agents cache before each test
        active_agents.clear()
    
    @patch('app.core.agent_manager.AgentManager.list_agent_ids')
    async def test_list_agents_success(self, mock_list_agent_ids):
        """
        Test listing agents successfully.
        """
        # Configure the mock
        mock_list_agent_ids.return_value = ["test-agent", "kb-agent"]
        
        with patch('app.core.agent_manager.AgentManager.load_agent_config') as mock_load_config:
            # Return different configs based on agent_id
            async def mock_load_config_impl(agent_id, **kwargs):
                if agent_id == "test-agent":
                    return self.sample_agent_config
                elif agent_id == "kb-agent":
                    return self.agent_with_kb_config
                else:
                    raise ValueError(f"Unknown agent: {agent_id}")
            
            mock_load_config.side_effect = mock_load_config_impl
            
            # Make the request
            response = self.client.get("/agents")
            
            # Verify response
            self.assertEqual(response.status_code, 200)
            agents = response.json()
            self.assertEqual(len(agents), 2)
            
            # Verify first agent details
            self.assertEqual(agents[0]["id"], "test-agent")
            self.assertEqual(agents[0]["model"], "gpt-3.5-turbo")
            self.assertEqual(agents[0]["has_knowledge_base"], False)
            self.assertEqual(agents[0]["tools"], ["calculator"])
            
            # Verify second agent details
            self.assertEqual(agents[1]["id"], "kb-agent")
            self.assertEqual(agents[1]["model"], "gpt-4")
            self.assertEqual(agents[1]["has_knowledge_base"], True)
    
    @patch('app.core.agent_manager.AgentManager.list_agent_ids')
    async def test_list_agents_error(self, mock_list_agent_ids):
        """
        Test handling errors when listing agents.
        """
        # Simulate an error
        mock_list_agent_ids.side_effect = Exception("Database error")
        
        # Make the request
        response = self.client.get("/agents")
        
        # Verify response
        self.assertEqual(response.status_code, 500)
        self.assertIn("Error listing agents", response.json()["detail"])
    
    @patch('app.core.agent_manager.AgentManager.load_agent_config')
    @patch('app.core.runtime_engine.RuntimeEngine.create_agent')
    @patch('app.core.runtime_engine.RuntimeEngine.run_agent')
    async def test_query_agent_success(self, mock_run_agent, mock_create_agent, mock_load_config):
        """
        Test querying an agent successfully.
        """
        # Configure mocks
        mock_load_config.return_value = self.sample_agent_config
        mock_agent = MagicMock()
        mock_create_agent.return_value = mock_agent
        mock_run_agent.return_value = "This is a test response"
        
        # Make the request
        response = self.client.post(
            "/query",
            json={"agent_id": "test-agent", "query": "What is the meaning of life?"}
        )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["agent_id"], "test-agent")
        self.assertEqual(data["response"], "This is a test response")
        self.assertIn("execution_time", data)
        
        # Verify mocks were called correctly
        mock_load_config.assert_called_once_with("test-agent")
        mock_create_agent.assert_called_once_with(self.sample_agent_config)
        mock_run_agent.assert_called_once_with(mock_agent, "What is the meaning of life?")
    
    @patch('app.core.agent_manager.AgentManager.load_agent_config')
    async def test_query_agent_not_found(self, mock_load_config):
        """
        Test querying a non-existent agent.
        """
        # Simulate agent not found
        mock_load_config.side_effect = ValueError("Agent not found")
        
        # Make the request
        response = self.client.post(
            "/query",
            json={"agent_id": "nonexistent-agent", "query": "Hello"}
        )
        
        # Verify response
        self.assertEqual(response.status_code, 404)
        self.assertIn("Agent not found", response.json()["detail"])
    
    @patch('app.core.agent_manager.AgentManager.load_agent_config')
    @patch('app.core.runtime_engine.RuntimeEngine.create_agent')
    @patch('app.core.runtime_engine.RuntimeEngine.run_agent')
    async def test_query_cached_agent(self, mock_run_agent, mock_create_agent, mock_load_config):
        """
        Test querying an agent that's already in the cache.
        """
        # Setup a cached agent
        mock_agent = MagicMock()
        active_agents["cached-agent"] = mock_agent
        mock_run_agent.return_value = "Response from cached agent"
        
        # Make the request
        response = self.client.post(
            "/query",
            json={"agent_id": "cached-agent", "query": "Hello from cache test"}
        )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["response"], "Response from cached agent")
        
        # Verify we didn't try to load or create the agent again
        mock_load_config.assert_not_called()
        mock_create_agent.assert_not_called()
        
        # Verify we ran the agent with the correct query
        mock_run_agent.assert_called_once_with(mock_agent, "Hello from cache test")
    
    @patch('app.core.agent_manager.AgentManager.load_agent_config')
    @patch('app.core.runtime_engine.RuntimeEngine.create_agent')
    async def test_reload_agent_success(self, mock_create_agent, mock_load_config):
        """
        Test reloading an agent successfully.
        """
        # Configure mocks
        mock_load_config.return_value = self.sample_agent_config
        mock_agent = MagicMock()
        mock_create_agent.return_value = mock_agent
        
        # Make the request
        response = self.client.post("/agents/test-agent/reload")
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertIn("reloaded successfully", response.json()["message"])
        
        # Verify mocks were called correctly
        mock_load_config.assert_called_once_with("test-agent", force_reload=True)
        mock_create_agent.assert_called_once_with(self.sample_agent_config)
        
        # Verify agent was cached
        self.assertIn("test-agent", active_agents)
        self.assertEqual(active_agents["test-agent"], mock_agent)
    
    @patch('app.core.agent_manager.AgentManager.load_agent_config')
    async def test_reload_agent_not_found(self, mock_load_config):
        """
        Test reloading a non-existent agent.
        """
        # Simulate agent not found
        mock_load_config.side_effect = ValueError("Agent not found")
        
        # Make the request
        response = self.client.post("/agents/nonexistent-agent/reload")
        
        # Verify response
        self.assertEqual(response.status_code, 404)
        self.assertIn("Agent not found", response.json()["detail"])
    
    def test_health_check(self):
        """
        Test the health check endpoint.
        """
        # Add a couple of agents to the cache
        active_agents["agent1"] = MagicMock()
        active_agents["agent2"] = MagicMock()
        
        # Make the request
        response = self.client.get("/health")
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["version"], "0.1.0")
        self.assertEqual(data["active_agents"], 2)


if __name__ == "__main__":
    unittest.main() 