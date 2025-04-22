# User Guide

This guide provides a detailed explanation of how to use the Generic Agent Runtime Engine to create, configure, and run custom agents for various tasks.

## Table of Contents

- [Introduction](#introduction)
- [Understanding Agent Architecture](#understanding-agent-architecture)
- [Creating Custom Agents](#creating-custom-agents)
- [Agent Configuration Reference](#agent-configuration-reference)
- [Available Tools](#available-tools)
- [Knowledge Base Integration](#knowledge-base-integration)
- [Flow Templates](#flow-templates)
- [Advanced Configuration](#advanced-configuration)
- [Troubleshooting](#troubleshooting)

## Introduction

The Generic Agent Runtime Engine is a flexible framework for creating and running AI agents powered by large language models (LLMs). Each agent is defined through a JSON configuration file that specifies its behavior, capabilities, and knowledge sources.

## Understanding Agent Architecture

An agent in this framework consists of several core components:

1. **Persona**: The character, role, and behavioral guidelines for the agent
2. **Tools**: External capabilities the agent can use (web search, data processing, etc.)
3. **Knowledge Base**: Optional information sources the agent can access
4. **Flow Template**: The processing pattern for handling queries
5. **LLM**: The underlying language model powering the agent

### How Agents Process Queries

When an agent receives a query, it follows these general steps:

1. The query is received through the API
2. The flow template determines how to process the query
3. The agent may use tools to gather information
4. The agent consults its knowledge base if configured
5. The LLM generates a response based on all available information
6. The response is returned to the user

## Creating Custom Agents

### Basic Structure

All agents are defined in JSON files stored in the `app/agents/` directory. The filename (without the `.json` extension) becomes the agent's ID.

Here's a minimal agent definition:

```json
{
  "id": "minimal_agent",
  "persona": "You are a helpful assistant who provides clear, concise answers.",
  "tools": [],
  "knowledge_base": {
    "type": "none"
  },
  "model": "gpt-3.5-turbo",
  "flow_template": {
    "type": "sequential",
    "parameters": {}
  }
}
```

### Real-World Example

Here's a more complex example of a research agent:

```json
{
  "id": "research_agent",
  "persona": "You are a research assistant specialized in finding and summarizing information. You always provide comprehensive answers with citations to your sources.",
  "tools": [
    {
      "name": "TavilySearch",
      "type": "builtin",
      "description": "Search for up-to-date information on the internet",
      "parameters": {
        "api_key": "env:TAVILY_API_KEY"
      }
    },
    {
      "name": "WebBrowser",
      "type": "builtin",
      "description": "Browse and extract content from web pages",
      "parameters": {}
    }
  ],
  "knowledge_base": {
    "type": "none"
  },
  "model": "gpt-4",
  "flow_template": {
    "type": "sequential",
    "parameters": {
      "max_iterations": 3,
      "thinking_mode": "verbose"
    }
  }
}
```

## Agent Configuration Reference

### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique identifier for the agent |
| persona | string | Yes | Instructions that define the agent's behavior and characteristics |
| tools | array | No | List of tools the agent can use |
| knowledge_base | object | Yes | Configuration for the agent's knowledge source |
| model | string | Yes | The LLM to use (e.g., "gpt-3.5-turbo", "gpt-4") |
| flow_template | object | Yes | The processing pattern for handling queries |

### Persona

The persona field should contain instructions for the LLM about how to behave. This can include:

- The agent's role (e.g., "You are a research assistant")
- Style guidelines (e.g., "Provide concise answers")
- Behavioral constraints (e.g., "Never make up information")
- Response formats (e.g., "Always structure responses with bullet points")

Example:

```json
"persona": "You are a travel planning assistant. You help users plan trips by providing information about destinations, attractions, accommodations, and travel logistics. Always be enthusiastic and helpful. When you don't know something, admit it rather than making up information. Format your answers with clear sections and bullet points for readability."
```

## Available Tools

The engine provides several built-in tools that agents can use to extend their capabilities.

### TavilySearch

A web search tool that allows the agent to search for up-to-date information on the internet.

```json
{
  "name": "TavilySearch",
  "type": "builtin",
  "description": "Search for up-to-date information on the internet",
  "parameters": {
    "api_key": "env:TAVILY_API_KEY"
  }
}
```

### WebBrowser

A tool for browsing and extracting content from web pages.

```json
{
  "name": "WebBrowser",
  "type": "builtin",
  "description": "Browse and extract content from web pages",
  "parameters": {}
}
```

### Calculator

A tool for performing mathematical calculations.

```json
{
  "name": "Calculator",
  "type": "builtin",
  "description": "Perform mathematical calculations",
  "parameters": {}
}
```

### Creating Custom Tools

You can create custom tools by implementing a tool handler in the `app/tools/` directory. See the [Developer Guide](developer_guide.md) for details.

## Knowledge Base Integration

The knowledge_base field allows you to connect your agent to various sources of information.

### None

No knowledge base.

```json
"knowledge_base": {
  "type": "none"
}
```

### File System

A simple file-based knowledge base.

```json
"knowledge_base": {
  "type": "files",
  "path": "./knowledge/product_docs",
  "file_types": [".txt", ".md", ".pdf"]
}
```

### Vector Database

A vector database for semantic search.

```json
"knowledge_base": {
  "type": "vectordb",
  "uri": "./knowledge/research_papers",
  "embedding_model": "text-embedding-ada-002"
}
```

## Flow Templates

Flow templates define how the agent processes queries.

### Sequential

The most common flow where the agent processes a query in a linear sequence of steps.

```json
"flow_template": {
  "type": "sequential",
  "parameters": {
    "max_iterations": 3,
    "thinking_mode": "verbose"
  }
}
```

Parameters:
- `max_iterations`: Maximum number of tool use iterations (default: 5)
- `thinking_mode`: How detailed the thinking process should be ("concise", "normal", "verbose")

### ReAct

A flow based on the Reasoning and Acting paradigm.

```json
"flow_template": {
  "type": "react",
  "parameters": {
    "reasoning_steps": 3
  }
}
```

Parameters:
- `reasoning_steps`: Number of reasoning steps to perform (default: 3)

## Advanced Configuration

### Environment Variables

Tools and other components can reference environment variables using the `env:` prefix:

```json
"parameters": {
  "api_key": "env:OPENAI_API_KEY"
}
```

### Configuring Models

You can specify different models for different purposes:

```json
"models": {
  "main": "gpt-4",
  "summarization": "gpt-3.5-turbo",
  "embedding": "text-embedding-ada-002"
}
```

### Conversation Memory

Configure how the agent remembers conversation history:

```json
"memory": {
  "type": "conversation",
  "max_messages": 20,
  "summarize_after": 15
}
```

## Troubleshooting

### Common Issues

#### Agent Not Found

If you receive an "Agent not found" error, check that:
- The agent JSON file exists in the `app/agents/` directory
- The filename matches the agent_id you're using in the API call
- The JSON file has valid syntax

#### Tool Errors

If a tool fails to execute:
- Check that all required API keys are properly set in `.env`
- Verify the tool parameters in the agent configuration
- Look for error messages in the server logs

#### Model Errors

If you encounter model-related errors:
- Verify your OpenAI API key is valid and has sufficient credits
- Check that the model specified exists and is available to your account
- For large queries, try using a model with a larger context window

### Logs

Server logs are available at:
- Development: Console output
- Production: `logs/runtime.log`

Look for error messages or warnings that might indicate the source of the problem.

### Getting Help

If you continue to experience issues:
- Check the [GitHub repository](https://github.com/yourusername/generic-agent) for known issues
- Join our community Discord for support
- Submit a detailed bug report with steps to reproduce the issue 