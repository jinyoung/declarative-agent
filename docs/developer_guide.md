# Developer Guide

This guide provides technical details for developers who want to extend and customize the Generic Agent Runtime Engine. It covers the codebase architecture, developing custom tools, flow templates, and integrating with other systems.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Creating Custom Tools](#creating-custom-tools)
- [Developing Flow Templates](#developing-flow-templates)
- [Knowledge Base Integrations](#knowledge-base-integrations)
- [Agent Testing Framework](#agent-testing-framework)
- [Deployment](#deployment)
- [Contributing Guidelines](#contributing-guidelines)

## Architecture Overview

The Generic Agent Runtime Engine is built with a modular architecture designed to be easily extensible. The core components include:

1. **Agent Manager**: Handles loading and validating agent configurations
2. **Runtime Engine**: Processes queries through the appropriate flow template
3. **Tool System**: Manages built-in and custom tools
4. **Knowledge Base Connectors**: Integrates with various data sources
5. **LLM Interface**: Communicates with language model providers (OpenAI, etc.)

### Key Design Principles

- **Modularity**: Components are designed with clear interfaces for easy replacement
- **Extensibility**: Core systems can be extended without modifying base code
- **Configuration-driven**: Behavior is controlled through configuration rather than code changes
- **Type safety**: TypeScript interfaces ensure consistency across the codebase

## Project Structure

```
generic-agent/
├── app/
│   ├── agents/              # Agent JSON configuration files
│   ├── api/                 # API routes and controllers
│   ├── core/                # Core engine components
│   │   ├── agent.ts         # Agent loading and management
│   │   ├── runtime.ts       # Query processing runtime
│   │   ├── llm.ts           # LLM provider interfaces
│   │   └── types.ts         # TypeScript type definitions
│   ├── flows/               # Flow template implementations
│   │   ├── sequential.ts    # Sequential flow implementation
│   │   ├── react.ts         # ReAct flow implementation
│   │   └── custom.ts        # Custom flow template
│   ├── knowledge/           # Knowledge base implementations
│   │   ├── vector.ts        # Vector database connector
│   │   ├── graph.ts         # Graph database connector
│   │   └── files.ts         # File-based knowledge base
│   ├── tools/               # Tool implementations
│   │   ├── builtin/         # Built-in tools
│   │   └── mcp/             # Custom MCP tools
│   └── utils/               # Utility functions
├── config/                  # Configuration files
├── docs/                    # Documentation
├── scripts/                 # Utility scripts
├── test/                    # Test suite
└── server.js                # Main server entry point
```

## Creating Custom Tools

Tools extend an agent's capabilities by allowing it to perform actions or access external resources. 

### Tool Interface

All tools implement the `Tool` interface defined in `app/core/types.ts`:

```typescript
interface Tool {
  name: string;
  description: string;
  execute(params: any): Promise<ToolResponse>;
  validateParams(params: any): boolean;
}

interface ToolResponse {
  status: 'success' | 'error';
  data?: any;
  error?: string;
}
```

### Creating a Built-in Tool

1. Create a new file in `app/tools/builtin/` directory:

```typescript
// app/tools/builtin/weather.ts
import axios from 'axios';
import { Tool, ToolResponse } from '../../core/types';

export class WeatherTool implements Tool {
  name = 'WeatherTool';
  description = 'Get current weather for a location';
  
  private apiKey: string;
  
  constructor(params: { api_key: string }) {
    this.apiKey = params.api_key;
  }
  
  async execute(params: { location: string }): Promise<ToolResponse> {
    try {
      const { location } = params;
      
      if (!location) {
        return {
          status: 'error',
          error: 'Location parameter is required'
        };
      }
      
      const response = await axios.get(
        `https://api.weatherapi.com/v1/current.json?key=${this.apiKey}&q=${encodeURIComponent(location)}`
      );
      
      return {
        status: 'success',
        data: {
          temperature: response.data.current.temp_c,
          condition: response.data.current.condition.text,
          humidity: response.data.current.humidity,
          location: response.data.location.name
        }
      };
    } catch (error) {
      return {
        status: 'error',
        error: `Weather API error: ${error.message}`
      };
    }
  }
  
  validateParams(params: any): boolean {
    return typeof params === 'object' && typeof params.location === 'string';
  }
}
```

2. Register the tool in `app/tools/index.ts`:

```typescript
import { WeatherTool } from './builtin/weather';

export const BUILTIN_TOOLS = {
  'WeatherTool': (params: any) => new WeatherTool(params),
  // other tools...
};
```

### Creating an MCP Tool

MCP (Modular Capability Provider) tools are custom-developed tools that can be loaded dynamically.

1. Create a new file in `app/tools/mcp/` directory:

```typescript
// app/tools/mcp/database_query.ts
import { Pool } from 'pg';
import { Tool, ToolResponse } from '../../core/types';

export class DatabaseQueryTool implements Tool {
  name = 'DatabaseQueryTool';
  description = 'Execute a safe read-only SQL query against a PostgreSQL database';
  
  private pool: Pool;
  
  constructor(params: { 
    host: string; 
    port: number; 
    database: string; 
    user: string; 
    password: string;
  }) {
    this.pool = new Pool({
      host: params.host,
      port: params.port,
      database: params.database,
      user: params.user,
      password: params.password
    });
  }
  
  async execute(params: { query: string }): Promise<ToolResponse> {
    try {
      const { query } = params;
      
      // Validate query is read-only for security
      if (!/^SELECT\s/i.test(query)) {
        return {
          status: 'error',
          error: 'Only SELECT queries are allowed'
        };
      }
      
      const result = await this.pool.query(query);
      
      return {
        status: 'success',
        data: result.rows
      };
    } catch (error) {
      return {
        status: 'error',
        error: `Database error: ${error.message}`
      };
    }
  }
  
  validateParams(params: any): boolean {
    return typeof params === 'object' && typeof params.query === 'string';
  }
}
```

2. Register the MCP tool in `app/tools/mcp/index.ts`:

```typescript
import { DatabaseQueryTool } from './database_query';

export const MCP_TOOLS = {
  'DatabaseQueryTool': (params: any) => new DatabaseQueryTool(params),
  // other MCP tools...
};
```

### Using Custom Tools in Agent Configuration

Once your tool is registered, you can use it in an agent configuration:

```json
{
  "persona": "You are a data analyst assistant",
  "tools": [
    {
      "name": "DatabaseQueryTool",
      "type": "mcp",
      "description": "Execute SQL queries against our analytics database",
      "parameters": {
        "host": "db.example.com",
        "port": 5432,
        "database": "analytics",
        "user": "readonly_user",
        "password": "env:DB_PASSWORD"
      }
    }
  ],
  // other agent configuration...
}
```

## Developing Flow Templates

Flow templates define how queries are processed by the runtime engine.

### Flow Template Interface

All flow templates implement the `FlowTemplate` interface:

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

### Creating a Custom Flow Template

1. Create a new file in `app/flows/` directory:

```typescript
// app/flows/multi_agent.ts
import { FlowTemplate, FlowResponse, Agent, ChatMessage } from '../core/types';
import { LLMProvider } from '../core/llm';

export class MultiAgentFlow implements FlowTemplate {
  private llmProvider: LLMProvider;
  private maxIterations: number;
  
  constructor(params: { 
    llmProvider: LLMProvider;
    maxIterations?: number;
  }) {
    this.llmProvider = params.llmProvider;
    this.maxIterations = params.maxIterations || 3;
  }
  
  async process(
    query: string, 
    agent: Agent, 
    chatHistory: ChatMessage[]
  ): Promise<FlowResponse> {
    // Implementation of multi-agent collaboration flow
    // This is a simplified example
    
    const primaryResponse = await this.llmProvider.complete({
      model: agent.model,
      messages: [
        { role: 'system', content: agent.persona },
        ...chatHistory,
        { role: 'user', content: query }
      ]
    });
    
    // Analyze if we need specialist input
    const needsSpecialistInput = this.analyzeForSpecialistNeed(primaryResponse);
    
    if (needsSpecialistInput) {
      // Get input from specialist agent
      const specialistResponse = await this.getSpecialistInput(
        query, 
        primaryResponse, 
        needsSpecialistInput.domain
      );
      
      // Create final response combining both
      const finalResponse = await this.synthesizeResponses(
        primaryResponse, 
        specialistResponse
      );
      
      return { response: finalResponse };
    }
    
    return { response: primaryResponse };
  }
  
  private analyzeForSpecialistNeed(response: string): { domain: string } | null {
    // Logic to determine if specialist input is needed
    // This would use the LLM to analyze the response
    return null; // Simplified return
  }
  
  private async getSpecialistInput(
    query: string, 
    primaryResponse: string, 
    domain: string
  ): Promise<string> {
    // Get input from a specialist agent for a specific domain
    return ""; // Simplified return
  }
  
  private async synthesizeResponses(
    primaryResponse: string, 
    specialistResponse: string
  ): Promise<string> {
    // Synthesize multiple responses into a coherent final response
    return ""; // Simplified return
  }
}
```

2. Register the flow template in `app/flows/index.ts`:

```typescript
import { MultiAgentFlow } from './multi_agent';

export const FLOW_TEMPLATES = {
  'sequential': SequentialFlow,
  'react': ReActFlow,
  'multi_agent': MultiAgentFlow,
  // other flow templates...
};
```

### Using Custom Flow Templates in Agent Configuration

```json
{
  "persona": "You are a comprehensive assistant with multiple specialties",
  "tools": [...],
  "knowledge_base": {...},
  "model": "gpt-4",
  "flow_template": {
    "type": "multi_agent",
    "parameters": {
      "maxIterations": 5
    }
  }
}
```

## Knowledge Base Integrations

Knowledge bases allow agents to access domain-specific information.

### Creating a Custom Knowledge Base

1. Create a new file in `app/knowledge/` directory:

```typescript
// app/knowledge/elasticsearch.ts
import { Client } from '@elastic/elasticsearch';
import { KnowledgeBase, QueryResult } from '../core/types';

export class ElasticsearchKnowledgeBase implements KnowledgeBase {
  private client: Client;
  private index: string;
  
  constructor(params: { 
    node: string; 
    index: string; 
    username?: string; 
    password?: string;
  }) {
    this.client = new Client({
      node: params.node,
      auth: params.username ? {
        username: params.username,
        password: params.password || ''
      } : undefined
    });
    this.index = params.index;
  }
  
  async query(query: string, k: number = 5): Promise<QueryResult> {
    try {
      const response = await this.client.search({
        index: this.index,
        body: {
          query: {
            multi_match: {
              query: query,
              fields: ['title', 'content']
            }
          },
          size: k
        }
      });
      
      const hits = response.body.hits.hits;
      return {
        status: 'success',
        data: hits.map((hit: any) => ({
          id: hit._id,
          score: hit._score,
          content: hit._source.content,
          metadata: {
            title: hit._source.title,
            source: hit._source.source
          }
        }))
      };
    } catch (error) {
      return {
        status: 'error',
        error: `Elasticsearch error: ${error.message}`
      };
    }
  }
}
```

2. Register the knowledge base in `app/knowledge/index.ts`:

```typescript
import { ElasticsearchKnowledgeBase } from './elasticsearch';

export const KNOWLEDGE_BASES = {
  'vectordb': VectorKnowledgeBase,
  'graphdb': GraphKnowledgeBase,
  'elasticsearch': ElasticsearchKnowledgeBase,
  'none': NoKnowledgeBase,
  // other knowledge bases...
};
```

### Using Custom Knowledge Bases in Agent Configuration

```json
{
  "persona": "You are a document search assistant",
  "tools": [...],
  "knowledge_base": {
    "type": "elasticsearch",
    "parameters": {
      "node": "https://elasticsearch.example.com:9200",
      "index": "documents",
      "username": "readonly",
      "password": "env:ES_PASSWORD"
    }
  },
  "model": "gpt-4",
  "flow_template": {...}
}
```

## Agent Testing Framework

The engine includes a testing framework for validating agents before deployment.

### Writing Agent Tests

Create tests in the `test/agents/` directory:

```typescript
// test/agents/weather_agent.test.ts
import { AgentTester } from '../utils/agent_tester';

describe('Weather Agent', () => {
  const tester = new AgentTester('weather_agent');
  
  beforeAll(async () => {
    await tester.initialize();
  });
  
  test('Should respond with current weather data', async () => {
    const query = 'What is the weather in San Francisco?';
    const response = await tester.query(query);
    
    expect(response).toContain('temperature');
    expect(response).toContain('San Francisco');
  });
  
  test('Should handle invalid location gracefully', async () => {
    const query = 'What is the weather in XYZ123?';
    const response = await tester.query(query);
    
    expect(response).toContain('unable to find');
    expect(response).not.toContain('error');
  });
});
```

### Running Agent Tests

```bash
# Run all agent tests
npm run test:agents

# Run tests for a specific agent
npm run test:agents -- --agent=weather_agent
```

## Deployment

### Docker Deployment

The Generic Agent Runtime Engine can be deployed as a Docker container:

1. Build the Docker image:

```bash
docker build -t generic-agent .
```

2. Run the container:

```bash
docker run -p 8000:8000 --env-file .env generic-agent
```

### Environment Variables

Configure your environment with these variables:

```
PORT=8000
NODE_ENV=production
LOG_LEVEL=info
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
# Add other API keys as needed
```

### Performance Optimization

For production deployments:

1. Enable caching:

```typescript
// config/production.js
module.exports = {
  cache: {
    enabled: true,
    ttl: 3600, // cache TTL in seconds
    max: 1000  // maximum items in cache
  },
  llm: {
    timeout: 30000, // LLM request timeout
    retries: 2      // Number of retries for failed requests
  }
}
```

2. Use horizontal scaling:

```bash
# Start multiple instances with PM2
pm2 start server.js -i max
```

## Contributing Guidelines

### Code Style

We follow these coding standards:

- Use TypeScript for all new code
- Follow ESLint rules in the project
- Document all functions and classes with JSDoc comments
- Write unit tests for new functionality

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `npm run test`
5. Submit a pull request

### Development Workflow

1. Install dependencies: `npm install`
2. Start in development mode: `npm run dev`
3. Run linting: `npm run lint`
4. Build for production: `npm run build` 