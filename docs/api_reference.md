# API Reference

This document provides detailed information about the Generic Agent Runtime Engine API endpoints, request/response formats, and error codes.

## Table of Contents

- [Base URL](#base-url)
- [Authentication](#authentication)
- [Agents API](#agents-api)
  - [List Agents](#list-agents)
  - [Get Agent Details](#get-agent-details)
  - [Create Agent](#create-agent)
  - [Update Agent](#update-agent)
  - [Delete Agent](#delete-agent)
- [Query API](#query-api)
  - [Send Query](#send-query)
  - [Streaming Response](#streaming-response)
- [Knowledge Base API](#knowledge-base-api)
  - [Add Document](#add-document)
  - [List Documents](#list-documents)
  - [Delete Document](#delete-document)
- [Tools API](#tools-api)
  - [List Available Tools](#list-available-tools)
  - [Register Custom Tool](#register-custom-tool)
- [Error Codes](#error-codes)
- [Rate Limits](#rate-limits)

## Base URL

All API endpoints are relative to the base URL:

```
https://your-deployment.example.com/api/v1
```

## Authentication

The API uses API key authentication. Include your API key in the request header:

```
Authorization: Bearer YOUR_API_KEY
```

## Agents API

### List Agents

Returns a list of all available agents.

**Endpoint:** `GET /agents`

**Query Parameters:**
- `page` (optional): Page number for pagination (default: 1)
- `limit` (optional): Number of items per page (default: 20)

**Response:**

```json
{
  "status": "success",
  "data": {
    "agents": [
      {
        "id": "weather_assistant",
        "name": "Weather Assistant",
        "description": "Get weather information and forecasts",
        "created_at": "2023-04-15T10:30:00Z",
        "updated_at": "2023-04-20T14:45:00Z"
      },
      {
        "id": "data_analyst",
        "name": "Data Analyst",
        "description": "Analyze data and generate insights",
        "created_at": "2023-04-10T08:15:00Z",
        "updated_at": "2023-04-18T11:20:00Z"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 3,
      "total_items": 45,
      "items_per_page": 20
    }
  }
}
```

### Get Agent Details

Returns detailed information about a specific agent.

**Endpoint:** `GET /agents/{agent_id}`

**Path Parameters:**
- `agent_id`: ID of the agent to retrieve

**Response:**

```json
{
  "status": "success",
  "data": {
    "id": "weather_assistant",
    "name": "Weather Assistant",
    "description": "Get weather information and forecasts",
    "persona": "You are a helpful weather assistant...",
    "tools": [
      {
        "name": "WeatherTool",
        "type": "builtin",
        "description": "Get current weather for a location"
      }
    ],
    "knowledge_base": {
      "type": "vectordb",
      "description": "Weather-related knowledge",
      "document_count": 150
    },
    "model": "gpt-4",
    "flow_template": {
      "type": "sequential",
      "parameters": {
        "max_iterations": 3
      }
    },
    "created_at": "2023-04-15T10:30:00Z",
    "updated_at": "2023-04-20T14:45:00Z"
  }
}
```

### Create Agent

Creates a new agent with the provided configuration.

**Endpoint:** `POST /agents`

**Request Body:**

```json
{
  "id": "customer_support",
  "name": "Customer Support Assistant",
  "description": "Handles customer inquiries and support requests",
  "persona": "You are a friendly customer support assistant...",
  "tools": [
    {
      "name": "TavilySearch",
      "type": "builtin",
      "description": "Search for information on the web"
    },
    {
      "name": "TicketCreator",
      "type": "mcp",
      "description": "Create support tickets in the ticketing system",
      "parameters": {
        "api_url": "https://helpdesk.example.com/api",
        "api_key": "env:HELPDESK_API_KEY"
      }
    }
  ],
  "knowledge_base": {
    "type": "vectordb",
    "parameters": {
      "collection": "customer_support_docs"
    }
  },
  "model": "gpt-4",
  "flow_template": {
    "type": "react",
    "parameters": {
      "max_iterations": 5
    }
  }
}
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "id": "customer_support",
    "created_at": "2023-05-10T15:20:00Z",
    "updated_at": "2023-05-10T15:20:00Z"
  }
}
```

### Update Agent

Updates an existing agent's configuration.

**Endpoint:** `PUT /agents/{agent_id}`

**Path Parameters:**
- `agent_id`: ID of the agent to update

**Request Body:** Same format as Create Agent

**Response:**

```json
{
  "status": "success",
  "data": {
    "id": "customer_support",
    "updated_at": "2023-05-15T09:45:00Z"
  }
}
```

### Delete Agent

Deletes an agent.

**Endpoint:** `DELETE /agents/{agent_id}`

**Path Parameters:**
- `agent_id`: ID of the agent to delete

**Response:**

```json
{
  "status": "success",
  "data": {
    "id": "customer_support",
    "deleted_at": "2023-05-20T11:30:00Z"
  }
}
```

## Query API

### Send Query

Sends a query to an agent and returns the response.

**Endpoint:** `POST /agents/{agent_id}/query`

**Path Parameters:**
- `agent_id`: ID of the agent to query

**Request Body:**

```json
{
  "query": "What is the weather like in San Francisco?",
  "conversation_id": "conv_12345",
  "stream": false,
  "context": {
    "user_timezone": "America/Los_Angeles",
    "user_preferences": {
      "temperature_unit": "celsius"
    }
  }
}
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "response": "The current weather in San Francisco is 18°C with partly cloudy skies. Humidity is at 75% with a light breeze from the west at 8 km/h.",
    "conversation_id": "conv_12345",
    "tool_calls": [
      {
        "tool": "WeatherTool",
        "input": {
          "location": "San Francisco"
        },
        "output": {
          "temperature": 18,
          "condition": "Partly cloudy",
          "humidity": 75,
          "wind_speed": 8,
          "wind_direction": "west"
        }
      }
    ],
    "timestamp": "2023-05-25T14:20:30Z"
  }
}
```

### Streaming Response

Streams the response from an agent in real-time.

**Endpoint:** `POST /agents/{agent_id}/query/stream`

**Path Parameters:**
- `agent_id`: ID of the agent to query

**Request Body:** Same format as Send Query

**Response:**

Server-sent events (SSE) stream with the following event types:

1. `message`: Partial response text
   ```
   event: message
   data: {"text": "The current weather in "}
   
   event: message
   data: {"text": "San Francisco is 18°C "}
   ```

2. `tool_call`: Tool call information
   ```
   event: tool_call
   data: {"tool": "WeatherTool", "input": {"location": "San Francisco"}}
   
   event: tool_result
   data: {"tool": "WeatherTool", "output": {"temperature": 18, "condition": "Partly cloudy"}}
   ```

3. `complete`: End of stream
   ```
   event: complete
   data: {"conversation_id": "conv_12345", "timestamp": "2023-05-25T14:20:35Z"}
   ```

## Knowledge Base API

### Add Document

Adds a document to an agent's knowledge base.

**Endpoint:** `POST /agents/{agent_id}/knowledge`

**Path Parameters:**
- `agent_id`: ID of the agent

**Request Body:**

```json
{
  "title": "Product Documentation",
  "content": "This is the full text content of the document...",
  "metadata": {
    "source": "Internal Wiki",
    "author": "Jane Smith",
    "created_at": "2023-03-15T10:00:00Z",
    "tags": ["product", "documentation", "user guide"]
  },
  "file": null
}
```

Alternatively, upload a file:

```
Content-Type: multipart/form-data
```

With form fields:
- `title`: Document title
- `metadata`: JSON string with metadata
- `file`: File upload

**Response:**

```json
{
  "status": "success",
  "data": {
    "document_id": "doc_78901",
    "title": "Product Documentation",
    "chunks": 15,
    "created_at": "2023-05-30T09:45:00Z"
  }
}
```

### List Documents

Lists documents in an agent's knowledge base.

**Endpoint:** `GET /agents/{agent_id}/knowledge`

**Path Parameters:**
- `agent_id`: ID of the agent

**Query Parameters:**
- `page` (optional): Page number for pagination (default: 1)
- `limit` (optional): Number of items per page (default: 20)
- `tag` (optional): Filter by tag

**Response:**

```json
{
  "status": "success",
  "data": {
    "documents": [
      {
        "document_id": "doc_78901",
        "title": "Product Documentation",
        "chunks": 15,
        "metadata": {
          "source": "Internal Wiki",
          "author": "Jane Smith",
          "tags": ["product", "documentation"]
        },
        "created_at": "2023-05-30T09:45:00Z"
      },
      {
        "document_id": "doc_78902",
        "title": "Troubleshooting Guide",
        "chunks": 10,
        "metadata": {
          "source": "Support Team",
          "author": "John Doe",
          "tags": ["troubleshooting", "support"]
        },
        "created_at": "2023-05-28T14:20:00Z"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 2,
      "total_items": 25,
      "items_per_page": 20
    }
  }
}
```

### Delete Document

Deletes a document from an agent's knowledge base.

**Endpoint:** `DELETE /agents/{agent_id}/knowledge/{document_id}`

**Path Parameters:**
- `agent_id`: ID of the agent
- `document_id`: ID of the document to delete

**Response:**

```json
{
  "status": "success",
  "data": {
    "document_id": "doc_78901",
    "deleted_at": "2023-06-01T11:30:00Z"
  }
}
```

## Tools API

### List Available Tools

Lists all available tools (built-in and custom).

**Endpoint:** `GET /tools`

**Response:**

```json
{
  "status": "success",
  "data": {
    "builtin_tools": [
      {
        "name": "TavilySearch",
        "description": "Search for information on the web",
        "parameter_schema": {
          "type": "object",
          "properties": {
            "query": {
              "type": "string",
              "description": "The search query"
            },
            "max_results": {
              "type": "number",
              "description": "Maximum number of search results to return"
            }
          },
          "required": ["query"]
        }
      },
      {
        "name": "WebBrowser",
        "description": "Browse and extract content from a webpage",
        "parameter_schema": {
          "type": "object",
          "properties": {
            "url": {
              "type": "string",
              "description": "URL of the webpage to browse"
            }
          },
          "required": ["url"]
        }
      }
    ],
    "mcp_tools": [
      {
        "name": "DatabaseQueryTool",
        "description": "Execute SQL queries against a database",
        "parameter_schema": {
          "type": "object",
          "properties": {
            "query": {
              "type": "string",
              "description": "SQL query to execute"
            }
          },
          "required": ["query"]
        },
        "configuration_schema": {
          "type": "object",
          "properties": {
            "host": {
              "type": "string",
              "description": "Database host"
            },
            "port": {
              "type": "number",
              "description": "Database port"
            },
            "database": {
              "type": "string",
              "description": "Database name"
            },
            "user": {
              "type": "string",
              "description": "Database user"
            },
            "password": {
              "type": "string",
              "description": "Database password"
            }
          },
          "required": ["host", "database", "user", "password"]
        }
      }
    ]
  }
}
```

### Register Custom Tool

Registers a new custom tool.

**Endpoint:** `POST /tools/register`

**Request Body:**

```json
{
  "name": "GitHubIssueCreator",
  "description": "Create issues in GitHub repositories",
  "implementation": {
    "type": "http",
    "url": "https://custom-tool-handler.example.com/github-issues",
    "method": "POST",
    "headers": {
      "x-api-key": "env:CUSTOM_TOOL_API_KEY"
    }
  },
  "parameter_schema": {
    "type": "object",
    "properties": {
      "repository": {
        "type": "string",
        "description": "GitHub repository in format owner/repo"
      },
      "title": {
        "type": "string",
        "description": "Issue title"
      },
      "body": {
        "type": "string",
        "description": "Issue description"
      },
      "labels": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "Issue labels"
      }
    },
    "required": ["repository", "title", "body"]
  },
  "configuration_schema": {
    "type": "object",
    "properties": {
      "github_token": {
        "type": "string",
        "description": "GitHub Personal Access Token"
      }
    },
    "required": ["github_token"]
  }
}
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "name": "GitHubIssueCreator",
    "created_at": "2023-06-05T13:40:00Z"
  }
}
```

## Error Codes

| Status Code | Error Code      | Description                                    |
|-------------|-----------------|------------------------------------------------|
| 400         | INVALID_REQUEST | The request format is invalid                  |
| 401         | UNAUTHORIZED    | Missing or invalid API key                     |
| 403         | FORBIDDEN       | The API key doesn't have access to the resource|
| 404         | NOT_FOUND       | The requested resource was not found           |
| 409         | CONFLICT        | Resource already exists                        |
| 422         | VALIDATION_ERROR| Request validation failed                      |
| 429         | RATE_LIMITED    | Rate limit exceeded                            |
| 500         | SERVER_ERROR    | Internal server error                          |
| 503         | SERVICE_UNAVAILABLE | Service temporarily unavailable            |

**Error Response Format:**

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "tools[0].parameters.api_key",
        "message": "Required field is missing"
      }
    ]
  }
}
```

## Rate Limits

The API enforces rate limits to ensure fair usage:

| Endpoint                | Rate Limit                        |
|-------------------------|-----------------------------------|
| List Agents             | 100 requests per minute           |
| Agent Queries           | 60 requests per minute            |
| Knowledge Base Updates  | 30 requests per minute            |
| All Other Endpoints     | 50 requests per minute            |

Rate limit information is included in the response headers:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1623347040
```

If you exceed the rate limit, you'll receive a 429 Too Many Requests response. 