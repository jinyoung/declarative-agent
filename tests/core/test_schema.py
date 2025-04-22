import pytest
from pydantic import ValidationError
import json
from app.core.schema import (
    AgentDefinition,
    ToolConfig,
    VectorDBConfig,
    GraphDBConfig,
    KnowledgeBaseConfig,
    validate_agent_json
)


class TestAgentDefinitionSchema:
    """Tests for the agent definition schema classes."""

    def test_valid_minimal_agent_definition(self):
        """Test validation of a minimal valid agent definition."""
        data = {
            "persona": "You are a helpful assistant."
        }
        
        # Should validate successfully
        agent = AgentDefinition.model_validate(data)
        assert agent.persona == "You are a helpful assistant."
        assert agent.tools == []
        assert agent.knowledge_base is None
        assert agent.model == "gpt-4"  # Default value

    def test_valid_complete_agent_definition(self):
        """Test validation of a complete valid agent definition with all fields."""
        data = {
            "persona": "You are a helpful assistant with access to tools and knowledge.",
            "tools": [
                {
                    "name": "calculator",
                    "type": "builtin",
                    "description": "Performs calculations"
                },
                {
                    "name": "external_tool",
                    "type": "mcp",
                    "endpoint": "http://example.com/api/tool",
                    "api_key": "test_key",
                    "description": "An external tool"
                }
            ],
            "knowledge_base": {
                "type": "vectordb",
                "config": {
                    "type": "vectordb",
                    "uri": "path/to/faiss",
                    "index_name": "documents",
                    "k": 10
                }
            },
            "model": "gpt-4-turbo"
        }
        
        # Should validate successfully
        agent = AgentDefinition.model_validate(data)
        assert agent.persona == "You are a helpful assistant with access to tools and knowledge."
        assert len(agent.tools) == 2
        assert agent.tools[0].name == "calculator"
        assert agent.tools[1].name == "external_tool"
        assert agent.knowledge_base.type == "vectordb"
        assert agent.knowledge_base.config.uri == "path/to/faiss"
        assert agent.knowledge_base.config.k == 10
        assert agent.model == "gpt-4-turbo"

    def test_invalid_missing_required_field(self):
        """Test validation fails when a required field is missing."""
        # Missing required 'persona' field
        data = {
            "tools": [],
            "model": "gpt-4"
        }
        
        # Should raise ValidationError
        with pytest.raises(ValidationError):
            AgentDefinition.model_validate(data)

    def test_invalid_tool_type(self):
        """Test validation fails with an invalid tool type."""
        data = {
            "persona": "You are a helpful assistant.",
            "tools": [
                {
                    "name": "invalid_tool",
                    "type": "unknown_type",  # Invalid type
                    "description": "This tool has an invalid type"
                }
            ]
        }
        
        # Should raise ValidationError
        with pytest.raises(ValidationError):
            AgentDefinition.model_validate(data)

    def test_invalid_knowledge_base_type(self):
        """Test validation fails with an invalid knowledge base type."""
        data = {
            "persona": "You are a helpful assistant.",
            "knowledge_base": {
                "type": "invalid_type",  # Invalid type
                "config": {
                    "type": "vectordb",
                    "uri": "path/to/faiss"
                }
            }
        }
        
        # Should raise ValidationError
        with pytest.raises(ValidationError):
            AgentDefinition.model_validate(data)

    def test_validate_agent_json_function(self):
        """Test the validate_agent_json helper function."""
        # Valid data
        valid_data = {
            "persona": "You are a helpful assistant.",
            "model": "claude-3"
        }
        
        # Invalid data
        invalid_data = {
            "model": "claude-3"
            # Missing required 'persona' field
        }
        
        # Should validate successfully
        agent = validate_agent_json(valid_data)
        assert agent.persona == "You are a helpful assistant."
        assert agent.model == "claude-3"
        
        # Should raise ValueError
        with pytest.raises(ValueError):
            validate_agent_json(invalid_data)


class TestToolConfig:
    """Tests for the ToolConfig schema."""
    
    def test_valid_builtin_tool(self):
        """Test validation of a valid builtin tool configuration."""
        data = {
            "name": "calculator",
            "type": "builtin",
            "description": "Performs calculations"
        }
        
        tool = ToolConfig.model_validate(data)
        assert tool.name == "calculator"
        assert tool.type == "builtin"
        assert tool.description == "Performs calculations"
        assert tool.endpoint is None
        assert tool.api_key is None

    def test_valid_mcp_tool(self):
        """Test validation of a valid MCP tool configuration."""
        data = {
            "name": "external_tool",
            "type": "mcp",
            "endpoint": "http://example.com/api/tool",
            "api_key": "test_key"
        }
        
        tool = ToolConfig.model_validate(data)
        assert tool.name == "external_tool"
        assert tool.type == "mcp"
        assert tool.description is None
        assert tool.endpoint == "http://example.com/api/tool"
        assert tool.api_key == "test_key"

    def test_invalid_missing_name(self):
        """Test validation fails when the name is missing."""
        data = {
            "type": "builtin",
            "description": "A tool without a name"
        }
        
        with pytest.raises(ValidationError):
            ToolConfig.model_validate(data)

    def test_invalid_missing_type(self):
        """Test validation fails when the type is missing."""
        data = {
            "name": "tool",
            "description": "A tool without a type"
        }
        
        with pytest.raises(ValidationError):
            ToolConfig.model_validate(data)


class TestKnowledgeBaseConfig:
    """Tests for the KnowledgeBaseConfig schema."""
    
    def test_valid_vectordb_config(self):
        """Test validation of a valid vector database configuration."""
        data = {
            "type": "vectordb",
            "config": {
                "type": "vectordb",
                "uri": "path/to/faiss",
                "index_name": "documents",
                "k": 10
            }
        }
        
        kb = KnowledgeBaseConfig.model_validate(data)
        assert kb.type == "vectordb"
        assert kb.config.type == "vectordb"
        assert kb.config.uri == "path/to/faiss"
        assert kb.config.index_name == "documents"
        assert kb.config.k == 10

    def test_valid_graphdb_config(self):
        """Test validation of a valid graph database configuration."""
        data = {
            "type": "graph",
            "config": {
                "type": "graph",
                "uri": "bolt://localhost:7687",
                "auth": {"username": "neo4j", "password": "password"},
                "query_template": "MATCH (n) RETURN n LIMIT 10"
            }
        }
        
        kb = KnowledgeBaseConfig.model_validate(data)
        assert kb.type == "graph"
        assert kb.config.type == "graph"
        assert kb.config.uri == "bolt://localhost:7687"
        assert kb.config.auth == {"username": "neo4j", "password": "password"}
        assert kb.config.query_template == "MATCH (n) RETURN n LIMIT 10"

    def test_invalid_config_type_mismatch(self):
        """Test validation fails when config type doesn't match parent type."""
        data = {
            "type": "vectordb",
            "config": {
                "type": "graph",  # Mismatch with parent type
                "uri": "bolt://localhost:7687"
            }
        }
        
        with pytest.raises(ValidationError):
            KnowledgeBaseConfig.model_validate(data)

    def test_invalid_missing_uri(self):
        """Test validation fails when uri is missing."""
        data = {
            "type": "vectordb",
            "config": {
                "type": "vectordb"
                # Missing required 'uri' field
            }
        }
        
        with pytest.raises(ValidationError):
            KnowledgeBaseConfig.model_validate(data) 