from typing import Optional, Dict, Any
import os
from langchain.tools import Tool
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphQAChain

from app.core.schema import KnowledgeBaseConfig, GraphDBConfig, VectorDBConfig


class KnowledgeBaseLoader:
    """
    Creates knowledge base tools based on the configuration,
    supporting both vector databases (FAISS) and graph databases (Neo4j).
    """
    
    def __init__(self, model_name: str = "gpt-4"):
        self.model_name = model_name
        # Initialize embeddings with potential API key from environment
        self.embeddings = OpenAIEmbeddings(
            api_key=os.environ.get("OPENAI_API_KEY")
        )
    
    def create_knowledge_tool(self, kb_config: KnowledgeBaseConfig) -> Optional[Tool]:
        """
        Create a tool for querying the knowledge base
        
        Args:
            kb_config: Knowledge base configuration
            
        Returns:
            Tool: LangChain tool for querying the knowledge base, or None if creation fails
        """
        if kb_config.type == "vectordb":
            return self._create_vectordb_tool(kb_config.config)
        elif kb_config.type == "graph":
            return self._create_graphdb_tool(kb_config.config)
        return None
    
    def _create_vectordb_tool(self, config: VectorDBConfig) -> Optional[Tool]:
        """
        Create a tool for querying a vector database
        
        Args:
            config: Vector database configuration
            
        Returns:
            Tool: LangChain tool for querying the vector database, or None if creation fails
        """
        try:
            # Load the vector store
            vectordb = FAISS.load_local(config.uri, self.embeddings)
            retriever = vectordb.as_retriever(search_kwargs={"k": config.k})
            
            # Create a retrieval QA chain
            llm = ChatOpenAI(model_name=self.model_name, temperature=0)
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=retriever
            )
            
            # Create a tool that uses the QA chain
            tool = Tool(
                name="VectorKnowledgeBase",
                func=qa_chain.run,
                description="Use this tool to answer questions based on the vector knowledge base. It contains specific information related to the domain you're operating in."
            )
            
            return tool
        except Exception as e:
            print(f"Error creating vector DB tool: {str(e)}")
            return None
    
    def _create_graphdb_tool(self, config: GraphDBConfig) -> Optional[Tool]:
        """
        Create a tool for querying a graph database (Neo4j)
        
        Args:
            config: Graph database configuration
            
        Returns:
            Tool: LangChain tool for querying the graph database, or None if creation fails
        """
        try:
            # Extract authentication details
            auth = config.auth or {}
            username = auth.get("username", os.environ.get("NEO4J_USERNAME", "neo4j"))
            password = auth.get("password", os.environ.get("NEO4J_PASSWORD", ""))
            database = auth.get("database", os.environ.get("NEO4J_DATABASE", "neo4j"))
            
            # Initialize the Neo4j graph
            graph = Neo4jGraph(
                url=config.uri,
                username=username,
                password=password,
                database=database
            )
            
            # Create a GraphQAChain
            llm = ChatOpenAI(model_name=self.model_name, temperature=0)
            chain = GraphQAChain.from_llm(
                llm=llm,
                graph=graph,
                verbose=True
            )
            
            # Use custom query template if provided
            if config.query_template:
                chain.query_prompt.template = config.query_template
            
            # Create a tool that uses the graph QA chain
            tool = Tool(
                name="GraphKnowledgeBase",
                func=chain.run,
                description="Use this tool to answer questions that require understanding relationships between entities. The knowledge is stored in a graph database that can handle complex queries about connections and networks of information."
            )
            
            return tool
        except Exception as e:
            print(f"Error creating graph DB tool: {str(e)}")
            return None 