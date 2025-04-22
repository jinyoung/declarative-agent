# Flow Templates

This document provides an in-depth explanation of the flow template system in the Generic Agent Runtime Engine, including how to configure and customize flow templates for your agents.

## Table of Contents

- [Introduction](#introduction)
- [Flow Template Types](#flow-template-types)
  - [Sequential Flow](#sequential-flow)
  - [Branching Flow](#branching-flow)
- [Node Types](#node-types)
  - [LLM Nodes](#llm-nodes)
  - [Tool Nodes](#tool-nodes)
  - [Condition Nodes](#condition-nodes)
- [Flow State Management](#flow-state-management)
- [Examples](#examples)
  - [Travel Assistant with Sequential Flow](#travel-assistant-with-sequential-flow)
  - [Customer Service with Branching Flow](#customer-service-with-branching-flow)
- [Custom Flow Templates](#custom-flow-templates)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Introduction

Flow templates are a powerful feature of the Generic Agent Runtime Engine that allow you to define more complex agent behaviors beyond simple request-response patterns. By configuring a flow template, you can create agents that follow specific sequences of operations, make decisions based on conditions, and handle complex multi-step interactions.

Flow templates are implemented using LangGraph, a library built on top of LangChain that provides directed graph-based workflows for LLM applications. Each flow consists of nodes (which perform operations) connected by edges (which define the flow of data between nodes).

## Flow Template Types

The Generic Agent Runtime Engine supports two primary types of flow templates:

### Sequential Flow

Sequential flows execute a series of operations in a predefined order. Each node in the flow receives input from the previous node and passes its output to the next node.

**Configuration Schema:**

```json
"flow_template": {
  "type": "sequential",
  "nodes": [
    {
      "name": "node1",
      "type": "llm | tool",
      "prompt": "Prompt for LLM node",
      "tool_name": "Name of tool for tool node"
    },
    // Additional nodes...
  ]
}
```

**When to Use:**
- Simple processing pipelines where operations should happen in a fixed order
- Workflows where each step depends on the results of the previous step
- When you need predictable, linear execution

### Branching Flow

Branching flows allow for conditional execution paths, where the flow can take different routes based on the output of certain nodes. This enables more dynamic and complex behavior.

**Configuration Schema:**

```json
"flow_template": {
  "type": "branching",
  "nodes": [
    {
      "name": "node1",
      "type": "llm | tool"
      // Node-specific parameters...
    },
    {
      "name": "condition_node",
      "type": "condition",
      "condition": "Condition to evaluate",
      "targets": {
        "true": "target_node_if_true",
        "false": "target_node_if_false"
      }
    },
    // Additional nodes...
  ]
}
```

**When to Use:**
- When different actions need to be taken based on the content of a response
- For implementing decision trees or complex logic
- When handling multiple categories of requests that need different processing

## Node Types

### LLM Nodes

LLM nodes execute operations using the agent's language model. They receive input, process it using a prompt template, and return the LLM's response.

**Configuration:**

```json
{
  "name": "analyze_query",
  "type": "llm",
  "prompt": "Analyze the following user query and extract key information: {input}"
}
```

**Features:**
- Customizable prompts with templating
- Access to previous steps via `{steps[index]}` syntax
- Ability to format and transform data
- Complex reasoning and analysis operations

### Tool Nodes

Tool nodes execute external tools registered with the agent. They can retrieve information, perform calculations, or interact with external systems.

**Configuration:**

```json
{
  "name": "get_weather",
  "type": "tool",
  "tool_name": "WeatherTool"
}
```

**Features:**
- Integration with any tool registered in the agent's configuration
- Automatic parameter handling based on previous node outputs
- Error handling and retry logic

### Condition Nodes

Condition nodes evaluate a condition using the LLM and determine the next node to execute based on the result.

**Configuration:**

```json
{
  "name": "check_query_type",
  "type": "condition",
  "condition": "The query is about weather",
  "targets": {
    "true": "get_weather",
    "false": "general_response"
  }
}
```

**Features:**
- LLM-based condition evaluation
- Multiple branching paths
- Dynamic routing based on content analysis

## Flow State Management

Each flow maintains a state object that tracks the execution progress and intermediate results. The state includes:

- `input`: The original query or input to the flow
- `steps`: An array containing the outputs of each executed node
- `output`: The final output of the flow

This state is passed from node to node, allowing each node to access the results of previous operations.

## Examples

### Travel Assistant with Sequential Flow

This example shows a travel assistant agent that processes queries in a sequential flow:

```json
{
  "persona": "You are a helpful travel assistant that provides information about tourist destinations, travel tips, and local attractions.",
  "tools": [
    {
      "name": "WeatherTool",
      "type": "mcp",
      "description": "Get current weather information for a location",
      "endpoint": "https://mcp-tools.example.com/weather"
    }
  ],
  "model": "gpt-4",
  "flow_template": {
    "type": "sequential",
    "nodes": [
      {
        "name": "extract_location",
        "type": "llm",
        "prompt": "Extract the name of the city or location mentioned in the user's query. If no location is mentioned, respond with 'no location'. User query: {input}"
      },
      {
        "name": "get_weather",
        "type": "tool",
        "tool_name": "WeatherTool"
      },
      {
        "name": "get_attractions",
        "type": "llm",
        "prompt": "Based on the following information, provide travel recommendations for the user's query.\n\nUser query: {input}\n\nWeather information: {steps[1]}\n\nInclude 3-5 attractions or activities suitable for the current weather."
      }
    ]
  }
}
```

**Flow Process:**
1. The agent extracts the location from the user's query
2. It retrieves weather information for that location
3. Based on the weather, it recommends suitable attractions

### Customer Service with Branching Flow

This example shows a customer service agent that uses a branching flow to handle different types of inquiries:

```json
{
  "persona": "You are a helpful customer service agent for TechGadgets, an online electronics retailer.",
  "tools": [
    {
      "name": "OrderLookup",
      "type": "mcp",
      "description": "Look up a customer's order information",
      "endpoint": "https://mcp-tools.example.com/order-lookup"
    },
    {
      "name": "ShippingStatus",
      "type": "mcp",
      "description": "Check the status of a shipped order",
      "endpoint": "https://mcp-tools.example.com/shipping-status"
    }
  ],
  "model": "gpt-4",
  "flow_template": {
    "type": "branching",
    "nodes": [
      {
        "name": "detect_intent",
        "type": "llm",
        "prompt": "Analyze the following customer query and determine the primary intent. Classify into one of these categories: 'order', 'shipping', 'product', 'return', or 'other'.\n\nCustomer query: {input}\n\nReturn only the category name without explanation."
      },
      {
        "name": "route_query",
        "type": "condition",
        "condition": "The detected intent is 'order'",
        "targets": {
          "true": "handle_order",
          "false": "check_shipping"
        }
      },
      {
        "name": "check_shipping",
        "type": "condition",
        "condition": "The detected intent is 'shipping'",
        "targets": {
          "true": "handle_shipping",
          "false": "general_response"
        }
      },
      {
        "name": "handle_order",
        "type": "tool",
        "tool_name": "OrderLookup"
      },
      {
        "name": "handle_shipping",
        "type": "tool",
        "tool_name": "ShippingStatus"
      },
      {
        "name": "general_response",
        "type": "llm",
        "prompt": "Respond to the following customer service question.\n\nCustomer query: {input}\n\nProvide a helpful and friendly response."
      },
      {
        "name": "format_response",
        "type": "llm",
        "prompt": "Format the following information into a helpful, friendly customer service response:\n\nOriginal customer query: {input}\n\nResponse data: {steps[-1]}\n\nBe sure to address any specific questions and include contact information if needed."
      }
    ]
  }
}
```

**Flow Process:**
1. The agent analyzes the customer's query to determine the intent
2. Based on the intent, it routes to the appropriate handler:
   - Order inquiries go to the OrderLookup tool
   - Shipping inquiries go to the ShippingStatus tool
   - Other inquiries go to a general response handler
3. Finally, all responses are formatted consistently in a customer-friendly style

## Custom Flow Templates

Advanced users can develop custom flow templates by implementing the `FlowTemplate` interface and registering it with the `FlowTemplateManager`. The Generic Agent Runtime Engine uses the following interface:

```typescript
interface FlowTemplate {
  process(
    query: string, 
    agent: Agent, 
    chatHistory: ChatMessage[]
  ): Promise<FlowResponse>;
}

interface FlowResponse {
  response: string;
  debugInfo?: any;
}
```

Custom flow templates can be implemented in the `app/flows/` directory and registered in `app/flows/index.ts`.

## Best Practices

### Designing Effective Flows

1. **Start Simple**: Begin with sequential flows and add complexity as needed
2. **Clear Node Names**: Use descriptive names that indicate the purpose of each node
3. **Short Prompts**: Keep prompts concise and focused on one task per node
4. **Error Handling**: Include nodes for handling edge cases and errors
5. **Limit Depth**: Avoid creating too many sequential or nested conditions
6. **Test Thoroughly**: Validate flows with diverse inputs to ensure robustness

### Optimizing Flow Performance

1. **Minimize LLM Calls**: LLM nodes are the most expensive; use them judiciously
2. **Efficient Conditioning**: Place high-probability conditions earlier in the flow
3. **Parallelization**: Consider whether operations could be performed in parallel
4. **Caching**: Implement caching for frequently-used tool results
5. **Context Management**: Be mindful of token limits when referencing previous steps

## Troubleshooting

### Common Issues

#### Flow Does Not Progress Beyond a Certain Node

**Possible Causes:**
- The node is returning an unexpected result format
- A tool is failing or timing out
- A condition is not evaluating as expected

**Solutions:**
- Check logs for error messages
- Enable debug mode for detailed execution tracking
- Verify tool configurations and API keys
- Test conditions with simpler inputs

#### Condition Nodes Not Routing Correctly

**Possible Causes:**
- Ambiguous condition statements
- LLM response format issues

**Solutions:**
- Simplify and clarify condition statements
- Use more explicit instructions (e.g., "Return only 'true' or 'false'")
- Add preprocessing nodes to standardize inputs

#### Slow Flow Execution

**Possible Causes:**
- Too many LLM node calls
- Inefficient tool implementations
- External service bottlenecks

**Solutions:**
- Consolidate multiple LLM nodes where possible
- Optimize tools for faster execution
- Implement caching for expensive operations
- Consider reducing model complexity for internal processing nodes 