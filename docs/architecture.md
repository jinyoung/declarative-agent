# System Architecture

This document provides a comprehensive overview of the Generic Agent Runtime Engine architecture, explaining how the different components interact to create a flexible and powerful agent system.

## High-Level Architecture

The Generic Agent Runtime Engine is built around a few core principles:

1. **Configuration over Code**: Agent behaviors are defined in external JSON files rather than hardcoded.
2. **Component-Based Design**: The system is divided into modular components with clear responsibilities.
3. **Extensibility**: Each component is designed to be easily extended with new capabilities.
4. **Standardized Interfaces**: Components interact through well-defined interfaces.

![Architecture Diagram](architecture-diagram.png)

## Core Components

### AgentManager

The AgentManager is responsible for loading agent definitions from JSON files and caching them for efficient reuse. It acts as the entry point for accessing agent capabilities.

**Key Responsibilities**:
- Load agent definitions from JSON files
- Validate definitions against the schema
- Cache definitions to avoid unnecessary reloading
- Provide access to agent definitions by ID

### RuntimeEngine

The RuntimeEngine is the central component that assembles and runs agents. It integrates the other components to create a complete agent system.

**Key Responsibilities**:
- Create LangChain agent executors or LangGraph flows
- Configure the appropriate LLM based on the agent definition
- Integrate tools and knowledge bases
- Provide a unified interface for executing agent queries

### ToolFactory

The ToolFactory creates LangChain tool objects based on tool configurations in the agent definition.

**Key Responsibilities**:
- Create built-in tools (search engines, calculators, etc.)
- Create MCP tools for integrated microservices
- Validate tool configurations
- Handle tool authentication and API keys

### KnowledgeBaseLoader

The KnowledgeBaseLoader connects to various knowledge sources and creates tools for querying them.

**Key Responsibilities**:
- Connect to vector databases (FAISS)
- Connect to graph databases (Neo4j)
- Create knowledge base query tools
- Configure retrievers with appropriate parameters

### FlowTemplateManager

The FlowTemplateManager creates LangGraph flows based on template configurations in the agent definition.

**Key Responsibilities**:
- Create sequential flow templates
- Create branching flow templates
- Configure flow nodes (LLM nodes, tool nodes, condition nodes)
- Ensure proper flow connectivity

### API Layer

The API layer provides a RESTful interface for interacting with agents.

**Key Responsibilities**:
- Define API endpoints
- Handle request validation
- Manage routing to the appropriate agent
- Format and return responses

## Data Flow

1. **API Request**: A client sends a request to the `/query` endpoint with an agent ID and query.
2. **Agent Loading**: The AgentManager loads the specified agent definition.
3. **Agent Assembly**: The RuntimeEngine assembles the agent by:
   - Configuring the LLM
   - Creating tools via the ToolFactory
   - Adding knowledge base tools via the KnowledgeBaseLoader
   - Creating a flow via the FlowTemplateManager (if applicable)
4. **Query Execution**: The agent processes the query using the appropriate LLM and tools.
5. **Response Generation**: The agent's response is returned to the client.

## Agent Definition Structure

The core data structure is the `AgentDefinition`, which includes:

```
AgentDefinition
├── persona: str
├── tools: List[ToolConfig]
│   ├── name: str
│   ├── type: "builtin" | "mcp"
│   ├── description: Optional[str]
│   ├── endpoint: Optional[str]
│   └── api_key: Optional[str]
├── knowledge_base: Optional[KnowledgeBaseConfig]
│   ├── type: "vectordb" | "graph"
│   └── config: Union[VectorDBConfig, GraphDBConfig]
├── model: str
└── flow_template: Optional[FlowTemplateConfig]
    ├── type: "sequential" | "branching"
    └── nodes: List[FlowNodeConfig]
```

## Flow Execution Model

For LangGraph-based flow templates, the execution follows these patterns:

### Sequential Flow

1. The flow processes nodes in a predefined sequence.
2. Each node can be an LLM node or a tool node.
3. The output of each node is passed to the next node in the sequence.
4. The final node's output is returned as the flow's result.

### Branching Flow

1. The flow includes condition nodes that determine the execution path.
2. Condition nodes evaluate their condition (using an LLM) to decide the next node.
3. The flow can take different paths based on the condition results.
4. All paths eventually converge to a final node that returns the result.

## Extension Points

The system can be extended in several ways:

1. **New Tool Types**: Adding new types to the ToolFactory.
2. **New Knowledge Base Types**: Adding new types to the KnowledgeBaseLoader.
3. **New Flow Templates**: Adding new templates to the FlowTemplateManager.
4. **Additional LLM Providers**: Adding new LLM configurations to the RuntimeEngine.

## Deployment Model

The system is designed to be deployed as a standalone service or as part of a larger application:

1. **Standalone Service**: Running in a Docker container with appropriate environment variables.
2. **Embedded Service**: Imported as a Python package and integrated with other services.
3. **Serverless**: Deployed as a serverless function with appropriate configuration.

## Security Considerations

The system addresses several security concerns:

1. **API Key Management**: API keys are stored as environment variables and not hardcoded.
2. **Input Validation**: All inputs are validated using Pydantic models.
3. **Error Handling**: Errors are caught and handled appropriately to prevent information leakage.
4. **Rate Limiting**: The API layer can implement rate limiting to prevent abuse.

## Performance Optimizations

Several optimizations improve performance:

1. **Caching**: Agent definitions are cached to avoid repeated loading.
2. **Parallel Processing**: Tool execution can be parallelized for better performance.
3. **Resource Pooling**: Connections to knowledge bases are pooled for efficiency.
4. **Asynchronous Execution**: API endpoints use async/await for better concurrency. 