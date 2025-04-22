"""Test cases for the KnowledgeBaseLoader."""
import os
import unittest
from unittest.mock import patch, MagicMock, Mock

from app.core.schema import KnowledgeBaseConfig, VectorDBConfig, GraphDBConfig
from app.knowledge.knowledge_base_loader import KnowledgeBaseLoader


class TestKnowledgeBaseLoader(unittest.TestCase):
    """Test cases for the KnowledgeBaseLoader class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.loader = KnowledgeBaseLoader(model_name="gpt-3.5-turbo")
    
    @patch("app.knowledge.knowledge_base_loader.FAISS")
    @patch("app.knowledge.knowledge_base_loader.ChatOpenAI")
    @patch("app.knowledge.knowledge_base_loader.RetrievalQA")
    def test_create_vectordb_tool(self, mock_qa, mock_llm, mock_faiss):
        """Test creating a vector database tool."""
        # Setup mocks
        mock_vectordb = MagicMock()
        mock_faiss.load_local.return_value = mock_vectordb
        mock_retriever = MagicMock()
        mock_vectordb.as_retriever.return_value = mock_retriever
        mock_chain = MagicMock()
        mock_qa.from_chain_type.return_value = mock_chain
        
        # Create config
        config = KnowledgeBaseConfig(
            type="vectordb",
            config=VectorDBConfig(
                type="vectordb",
                uri="/path/to/vectordb",
                k=3
            )
        )
        
        # Call the method
        tool = self.loader.create_knowledge_tool(config)
        
        # Verify tool creation
        self.assertIsNotNone(tool)
        self.assertEqual(tool.name, "VectorKnowledgeBase")
        
        # Verify mocks were called correctly
        mock_faiss.load_local.assert_called_once_with("/path/to/vectordb", self.loader.embeddings)
        mock_vectordb.as_retriever.assert_called_once_with(search_kwargs={"k": 3})
        mock_llm.assert_called_once_with(model_name="gpt-3.5-turbo", temperature=0)
        mock_qa.from_chain_type.assert_called_once()
    
    @patch("app.knowledge.knowledge_base_loader.Neo4jGraph")
    @patch("app.knowledge.knowledge_base_loader.ChatOpenAI")
    @patch("app.knowledge.knowledge_base_loader.GraphQAChain")
    def test_create_graphdb_tool(self, mock_graph_qa, mock_llm, mock_neo4j):
        """Test creating a graph database tool."""
        # Setup mocks
        mock_graph = MagicMock()
        mock_neo4j.return_value = mock_graph
        mock_chain = MagicMock()
        mock_graph_qa.from_llm.return_value = mock_chain
        mock_chain.query_prompt = MagicMock()
        
        # Create config
        config = KnowledgeBaseConfig(
            type="graph",
            config=GraphDBConfig(
                type="graph",
                uri="bolt://localhost:7687",
                auth={
                    "username": "test_user",
                    "password": "test_password",
                    "database": "test_db"
                },
                query_template="Custom query template: {question}"
            )
        )
        
        # Call the method
        tool = self.loader.create_knowledge_tool(config)
        
        # Verify tool creation
        self.assertIsNotNone(tool)
        self.assertEqual(tool.name, "GraphKnowledgeBase")
        
        # Verify mocks were called correctly
        mock_neo4j.assert_called_once_with(
            url="bolt://localhost:7687",
            username="test_user",
            password="test_password",
            database="test_db"
        )
        mock_llm.assert_called_once_with(model_name="gpt-3.5-turbo", temperature=0)
        mock_graph_qa.from_llm.assert_called_once_with(
            llm=mock_llm.return_value,
            graph=mock_graph,
            verbose=True
        )
        self.assertEqual(mock_chain.query_prompt.template, "Custom query template: {question}")
    
    @patch("app.knowledge.knowledge_base_loader.FAISS")
    def test_vectordb_tool_error_handling(self, mock_faiss):
        """Test error handling when creating a vector database tool."""
        # Setup error
        mock_faiss.load_local.side_effect = Exception("Test error")
        
        # Create config
        config = KnowledgeBaseConfig(
            type="vectordb",
            config=VectorDBConfig(
                type="vectordb",
                uri="/path/to/vectordb",
                k=3
            )
        )
        
        # Call the method
        tool = self.loader.create_knowledge_tool(config)
        
        # Verify error handling
        self.assertIsNone(tool)
    
    @patch("app.knowledge.knowledge_base_loader.Neo4jGraph")
    def test_graphdb_tool_error_handling(self, mock_neo4j):
        """Test error handling when creating a graph database tool."""
        # Setup error
        mock_neo4j.side_effect = Exception("Test error")
        
        # Create config
        config = KnowledgeBaseConfig(
            type="graph",
            config=GraphDBConfig(
                type="graph",
                uri="bolt://localhost:7687"
            )
        )
        
        # Call the method
        tool = self.loader.create_knowledge_tool(config)
        
        # Verify error handling
        self.assertIsNone(tool)
    
    def test_unknown_kb_type(self):
        """Test handling of unknown knowledge base type."""
        # Create mock config with unknown type
        # This test uses monkey patching to create a config with an invalid type
        config = MagicMock()
        config.type = "unknown"
        
        # Call the method
        tool = self.loader.create_knowledge_tool(config)
        
        # Verify no tool is created
        self.assertIsNone(tool)


if __name__ == "__main__":
    unittest.main() 