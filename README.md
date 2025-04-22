# Generic Agent Runtime Engine

A flexible, JSON-defined AI agent runtime engine built with LangChain and LangGraph for creating and running AI agents with different personas, tools, and knowledge sources.

## Overview

The Generic Agent Runtime Engine provides a unified way to define and run AI agents through a JSON configuration format. Instead of hard-coding agent behaviors and capabilities, this system allows you to define agents externally and load them at runtime. 

Key features:
- Define agents using JSON files with personas, tools, and knowledge bases
- Support for different LLM providers (OpenAI, Anthropic)
- Built-in support for vector databases (FAISS) and graph databases (Neo4j)
- LangGraph-based flow templates for complex agent behaviors
- Simple API for querying agents
- Easy extension with new tools and knowledge sources
- Multi-agent conversations where specialized agents collaborate
- Continuous conversations with chat history

## Quick Start

### Prerequisites

- Python 3.9+
- Neo4j (optional, for graph database knowledge base)
- OpenAI API key or Anthropic API key

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/generic-agent.git
cd generic-agent
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Copy the sample environment file and edit with your API keys
```bash
cp .env.example .env
# Edit .env with your favorite editor
```

4. Run the server
```bash
python -m app
```

### Creating an Agent

Create a JSON file in the `app/agents` directory:

```json
{
  "persona": "You are a helpful assistant that specializes in answering questions about programming.",
  "tools": [
    {
      "name": "GoogleSearch",
      "type": "builtin",
      "description": "Search for information on the web",
      "api_key": "${GOOGLE_API_KEY}"
    }
  ],
  "model": "gpt-4",
  "supports_chat": true
}
```

### Using the API

Query your agent using the API:

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "math_assistant",
    "query": "1+1?"
  }'
```

## Agent Definition Schema

Agents are defined using JSON files with the following structure:

```json
{
  "persona": "System prompt / persona for the agent",
  "tools": [
    {
      "name": "ToolName",
      "type": "builtin | mcp",
      "description": "Description of what the tool does",
      "endpoint": "URL for MCP tools",
      "api_key": "API key for tools requiring authentication"
    }
  ],
  "knowledge_base": {
    "type": "vectordb | graph",
    "config": {
      // Configuration specific to the knowledge base type
    }
  },
  "model": "gpt-4 | claude-3-opus-20240229",
  "flow_template": {
    // Optional flow template configuration
  },
  "supports_chat": true
}
```

### Tool Types

- **builtin**: Standard LangChain tools like search engines, calculators, etc.
- **mcp**: Model Context Protocol

### Knowledge Base Types

- **vectordb**: Vector databases for semantic search (FAISS)
- **graph**: Graph databases for relational data (Neo4j)

### Flow Templates

Flow templates allow for more complex agent behaviors:

```json
"flow_template": {
  "type": "sequential | branching",
  "nodes": [
    {
      "name": "node1",
      "type": "llm | tool | condition",
      "prompt": "Prompt template for LLM nodes",
      "tool_name": "Name of tool for tool nodes",
      "condition": "Condition for condition nodes",
      "targets": {
        "true": "target_node_if_true",
        "false": "target_node_if_false"
      }
    }
  ]
}
```

#### Multi-Agent Flow Templates

For multi-agent flows, use the special `multi_agent` flow type:

```json
"flow_template": {
  "type": "multi_agent",
  "description": "A flow that coordinates multiple specialized agents",
  "config": {
    "persona": "You are a helpful coordinator that can call multiple expert agents...",
    "agent_tools": [
      "agent_id1",
      "agent_id2"
    ]
  }
}
```

## API Endpoints

### POST /query

Submit a query to an agent.

**Request:**
```json
{
  "agent_id": "name_of_agent_json_file_without_extension",
  "query": "User query for the agent"
}
```

**Response:**
```json
{
  "response": "Agent's response to the query",
  "agent_id": "agent_id from the request",
  "execution_time": 1.23
}
```

### POST /chat

Chat with an agent maintaining conversation history.

**Request:**
```json
{
  "agent_id": "name_of_agent_json_file_without_extension",
  "message": "User message",
  "session_id": "optional_session_id_for_continuing_conversation"
}
```

**Response:**
```json
{
  "response": "Agent's response to the message",
  "agent_id": "agent_id from the request",
  "session_id": "session_id for this conversation",
  "execution_time": 1.23
}
```

### POST /multi-agent

Create a multi-agent flow and run an initial query.

**Request:**
```json
{
  "coordinator_id": "id_of_coordinator_agent",
  "query": "User query",
  "agent_ids": ["optional_list_of_specific_agent_ids"],
  "excluded_agent_ids": ["optional_list_of_agents_to_exclude"]
}
```

**Response:**
```json
{
  "response": "Coordinated response from multiple agents",
  "coordinator_id": "coordinator_agent_id",
  "flow_id": "id_for_future_reference",
  "execution_time": 1.23
}
```

### POST /multi-agent/chat

Continue a conversation with a multi-agent flow.

**Request:**
```json
{
  "flow_id": "id_received_from_multi-agent_endpoint",
  "message": "User message",
  "session_id": "optional_session_id_for_continuing_conversation"
}
```

**Response:**
```json
{
  "response": "Coordinated response from multiple agents",
  "flow_id": "flow_id from the request",
  "session_id": "session_id for this conversation",
  "execution_time": 1.23
}
```

### DELETE /sessions/{session_id}

Delete a chat session.

## Configuration

The system is configured using environment variables:

- `OPENAI_API_KEY`: API key for OpenAI models
- `ANTHROPIC_API_KEY`: API key for Anthropic models
- `NEO4J_USERNAME`: Username for Neo4j connection
- `NEO4J_PASSWORD`: Password for Neo4j connection
- `NEO4J_DATABASE`: Database name for Neo4j connection
- `TEMPERATURE`: Temperature for LLM responses (default: 0.0)
- `DEBUG`: Enable debug logging (true/false)

## Sample Agents

The repository includes several sample agent definitions:

- `travel_agent_flow.json`: Travel assistant with sequential flow
- `customer_service_flow.json`: Customer service agent with branching flow
- `research_assistant.json`: AI research assistant with vector knowledge base
- `knowledge_graph_agent.json`: Financial analyst with graph knowledge base
- `multi_agent_coordinator.json`: Coordinator agent for multi-agent flows
- `tech_expert.json`: Technology specialist agent for multi-agent collaboration
- `finance_expert.json`: Finance specialist agent for multi-agent collaboration
- `travel_expert.json`: Travel specialist agent for multi-agent collaboration

## Testing Multi-Agent Flows and Chat

### Setting Up the Sample Agents

1. Copy the sample agent files from the `examples` directory to your `app/agents` directory:

```bash
mkdir -p app/agents
cp examples/multi_agent_coordinator.json app/agents/
cp examples/tech_expert.json app/agents/
cp examples/finance_expert.json app/agents/
cp examples/travel_expert.json app/agents/
```

### Testing Single Agent Chat

1. Simple Query

```
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "math_assistant",
    "query": "calculate this :  1+1?"                                 
  }'
```

2. Start a chat session with a specific agent that supports chat:

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "tech_expert",
    "message": "What are the key features of Python?"
  }'
```

3. Continue the conversation using the `session_id` from the previous response:

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "tech_expert",
    "message": "How does it compare to JavaScript?",
    "session_id": "SESSION_ID_FROM_PREVIOUS_RESPONSE"
  }'
```

### Testing Multi-Agent Flow

1. Create a multi-agent flow with a coordinator and run an initial query:

```bash
curl -X POST "http://localhost:8000/multi-agent" \
  -H "Content-Type: application/json" \
  -d '{
    "coordinator_id": "multi_agent_coordinator",
    "query": "Which programming language should I learn for finance applications?",
    "agent_ids": ["tech_expert", "finance_expert"]
  }'
```

2. Continue the conversation with the multi-agent flow using the `flow_id` from the previous response:

```bash
curl -X POST "http://localhost:8000/multi-agent/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "flow_id": "FLOW_ID_FROM_PREVIOUS_RESPONSE",
    "message": "What libraries would I need to learn in that language?"
  }'
```

3. For complex queries spanning multiple domains, the coordinator will delegate to the appropriate expert agents:

```bash
curl -X POST "http://localhost:8000/multi-agent" \
  -H "Content-Type: application/json" \
  -d '{
    "coordinator_id": "multi_agent_coordinator",
    "query": "I need recommendations for a laptop for software development and some advice on how to budget for it."
  }'
```

The coordinator will delegate the technical aspects to the tech expert and the financial aspects to the finance expert, creating a comprehensive response that combines both perspectives.

## Extending the System

### Adding New Tools

To add a new built-in tool:

1. Update the `ToolFactory` class in `app/core/tool_factory.py`
2. Add a new method to handle your tool type
3. Register it in the `create_builtin_tool` method

### Adding New Knowledge Base Types

To add a new knowledge base type:

1. Update the `KnowledgeBaseLoader` class in `app/knowledge/knowledge_base_loader.py`
2. Add a new method to create your knowledge base tool
3. Register it in the `create_knowledge_tool` method

## Development

### Running Tests

```bash
pytest
```

### Code Style

```bash
ruff check .
mypy .
```

## License

MIT

## Acknowledgements

- [LangChain](https://github.com/langchain-ai/langchain)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [FastAPI](https://fastapi.tiangolo.com/)
- [OpenAI](https://openai.com/)
- [Anthropic](https://www.anthropic.com/) 