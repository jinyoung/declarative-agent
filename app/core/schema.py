from pydantic import BaseModel, Field
from typing import List, Dict, Literal, Optional, Union, Any


class ToolConfig(BaseModel):
    """Configuration for a tool that can be used by an agent."""
    name: str = Field(..., description="Name of the tool")
    type: Literal["builtin", "mcp"] = Field(..., description="Type of tool (builtin or MCP)")
    description: Optional[str] = Field(None, description="Description of what the tool does")
    endpoint: Optional[str] = Field(None, description="Endpoint URL for MCP tools")
    api_key: Optional[str] = Field(None, description="API key for tools requiring authentication")
    # Additional tool-specific fields can be added dynamically


class VectorDBConfig(BaseModel):
    """Configuration for a vector database knowledge base."""
    type: Literal["vectordb"] = Field("vectordb", description="Type of knowledge base")
    uri: str = Field(..., description="URI or path to the vector database")
    index_name: Optional[str] = Field(None, description="Name of the index to use")
    k: int = Field(5, description="Number of results to retrieve", ge=1)


class GraphDBConfig(BaseModel):
    """Configuration for a graph database knowledge base."""
    type: Literal["graph"] = Field("graph", description="Type of knowledge base")
    uri: str = Field(..., description="URI of the graph database")
    auth: Optional[Dict[str, str]] = Field(None, description="Authentication details for the graph database")
    query_template: Optional[str] = Field(None, description="Template for graph database queries")


class KnowledgeBaseConfig(BaseModel):
    """Configuration for a knowledge base that can be queried by an agent."""
    type: Literal["vectordb", "graph"] = Field(..., description="Type of knowledge base")
    config: Union[VectorDBConfig, GraphDBConfig] = Field(..., description="Configuration for the knowledge base")


class FlowNodeConfig(BaseModel):
    """Configuration for a node in a LangGraph flow."""
    name: str = Field(..., description="Name of the node")
    type: Literal["llm", "tool", "condition"] = Field(..., description="Type of node")
    prompt: Optional[str] = Field(None, description="Prompt template for LLM nodes")
    tool_name: Optional[str] = Field(None, description="Name of the tool to use for tool nodes")
    condition: Optional[str] = Field(None, description="Condition expression for condition nodes")
    targets: Optional[Dict[str, str]] = Field(None, description="Target nodes for condition branches")


class FlowTemplateConfig(BaseModel):
    """Configuration for a LangGraph flow template."""
    type: Literal["sequential", "branching"] = Field("sequential", description="Type of flow template")
    nodes: List[FlowNodeConfig] = Field(..., description="Nodes in the flow")
    description: Optional[str] = Field(None, description="Description of what the flow does")
    config: Optional[Dict[str, Any]] = Field(None, description="Additional configuration for the flow")


class AgentDefinition(BaseModel):
    """Definition of an agent including its persona, tools, and knowledge base."""
    persona: str = Field(..., description="System prompt / persona for the agent")
    tools: List[ToolConfig] = Field(default_factory=list, description="List of tools available to the agent")
    knowledge_base: Optional[KnowledgeBaseConfig] = Field(None, description="Knowledge base configuration")
    model: str = Field("gpt-4", description="LLM model to use for the agent")
    flow_template: Optional[FlowTemplateConfig] = Field(None, description="LangGraph flow template configuration")


def validate_agent_json(json_data: dict) -> AgentDefinition:
    """
    Validate that the provided JSON data conforms to the agent definition schema.
    
    Args:
        json_data: Dictionary containing the agent definition data
        
    Returns:
        AgentDefinition: Validated agent definition object
        
    Raises:
        ValueError: If validation fails
    """
    try:
        return AgentDefinition.model_validate(json_data)
    except Exception as e:
        raise ValueError(f"Invalid agent definition: {str(e)}") 