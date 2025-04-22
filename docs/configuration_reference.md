# Configuration Reference

This document provides comprehensive information about the configuration options available for the Generic Agent Runtime Engine.

## Table of Contents

- [Configuration File Locations](#configuration-file-locations)
- [Configuration Format](#configuration-format)
- [Core Configuration](#core-configuration)
  - [Server Settings](#server-settings)
  - [Database Settings](#database-settings)
  - [Authentication Settings](#authentication-settings)
  - [Logging Settings](#logging-settings)
- [LLM Providers](#llm-providers)
  - [OpenAI](#openai)
  - [Anthropic](#anthropic)
  - [Local Models](#local-models)
  - [Custom LLM Provider](#custom-llm-provider)
- [Vector Stores](#vector-stores)
  - [Pinecone](#pinecone)
  - [Chroma](#chroma)
  - [Milvus](#milvus)
  - [Postgres PGVECTOR](#postgres-pgvector)
  - [Local Vector Store](#local-vector-store)
- [Tool Configuration](#tool-configuration)
  - [Built-in Tools](#built-in-tools)
  - [External API Tools](#external-api-tools)
  - [Custom Tools](#custom-tools)
- [Agent Configuration](#agent-configuration)
  - [Agent Types](#agent-types)
  - [Default Agent Settings](#default-agent-settings)
  - [Memory Settings](#memory-settings)
- [Environment Variables](#environment-variables)
- [Configuration Examples](#configuration-examples)
  - [Minimal Configuration](#minimal-configuration)
  - [Production Configuration](#production-configuration)
  - [Development Configuration](#development-configuration)

## Configuration File Locations

The Generic Agent Runtime Engine searches for configuration files in the following locations (in order of precedence):

1. Path specified via the `--config` command-line option
2. Environment variable `GENERIC_AGENT_CONFIG`
3. `./config.{json,yaml,js}`
4. `~/.generic-agent/config.{json,yaml,js}`
5. `/etc/generic-agent/config.{json,yaml,js}`

## Configuration Format

Configuration can be defined in JSON, YAML, or as a JavaScript module. Examples in this document use YAML for readability.

## Core Configuration

### Server Settings

```yaml
server:
  host: "0.0.0.0"           # Server host (default: localhost)
  port: 8000                # Server port (default: 8000)
  baseUrl: "/api/v1"        # Base URL path for the API (default: /api/v1)
  cors:
    enabled: true           # Enable CORS (default: false)
    origin: "*"             # CORS origin (default: *)
    methods: "GET,POST,PUT,DELETE"  # Allowed methods
  rateLimits:
    enabled: true           # Enable rate limiting (default: true)
    defaultLimit: 100       # Requests per window (default: 100)
    windowMs: 900000        # 15 minutes in milliseconds (default)
  ssl:
    enabled: false          # Enable SSL (default: false)
    key: "/path/to/key.pem" # Path to SSL key
    cert: "/path/to/cert.pem" # Path to SSL certificate
```

### Database Settings

```yaml
database:
  type: "postgres"          # Database type: postgres, sqlite, mysql (default: sqlite)
  connectionString: "postgresql://user:password@localhost:5432/generic_agent"
  # For SQLite:
  # connectionString: "sqlite:///path/to/database.sqlite"
  pool:
    min: 2                  # Minimum pool connections
    max: 10                 # Maximum pool connections
  migrations:
    auto: true              # Run migrations on startup (default: true)
```

### Authentication Settings

```yaml
auth:
  type: "apiKey"            # Authentication type: apiKey, oauth, jwt (default: apiKey)
  apiKey:
    header: "X-API-Key"     # Header name for API key (default: X-API-Key)
    queryParam: "api_key"   # Query param name for API key (default: api_key)
  
  # JWT configuration (if type is jwt)
  jwt:
    secret: "your-jwt-secret"  # JWT secret for signing
    expiresIn: "24h"        # Token expiration time
    
  # OAuth configuration (if type is oauth)
  oauth:
    provider: "auth0"       # OAuth provider
    clientId: "your-client-id"
    clientSecret: "your-client-secret"
    callbackUrl: "https://your-app.com/callback"
```

### Logging Settings

```yaml
logging:
  level: "info"             # Logging level: debug, info, warn, error (default: info)
  format: "json"            # Log format: json, text (default: json)
  destination: "file"       # Log destination: console, file (default: console)
  file: "/var/log/generic-agent/app.log"  # Log file path (if destination is file)
  rotation:
    enabled: true           # Enable log rotation (default: true)
    maxSize: "100m"         # Max file size before rotation
    maxFiles: 10            # Max number of files to keep
```

## LLM Providers

### OpenAI

```yaml
llm:
  providers:
    openai:
      apiKey: "${OPENAI_API_KEY}"  # Can use environment variables
      organization: "org-123456"   # Optional organization ID
      baseUrl: "https://api.openai.com/v1" # Default OpenAI API URL
      models:
        default: "gpt-4"           # Default model to use
        chat: "gpt-4"              # Model for chat
        embedding: "text-embedding-ada-002" # Model for embeddings
      requestTimeout: 60000        # Timeout in milliseconds
      maxRetries: 3                # Max retries on failure
```

### Anthropic

```yaml
llm:
  providers:
    anthropic:
      apiKey: "${ANTHROPIC_API_KEY}"
      models:
        default: "claude-3-opus-20240229"
        chat: "claude-3-sonnet-20240229"
      maxTokens: 4096
      temperature: 0.7
```

### Local Models

```yaml
llm:
  providers:
    localLlm:
      type: "ollama"              # Type of local LLM: ollama, llama.cpp, etc.
      baseUrl: "http://localhost:11434" # URL for Ollama server
      models:
        default: "llama2"
        chat: "llama2"
        embedding: "nomic-embed-text"
      contextWindow: 4096         # Context window size
```

### Custom LLM Provider

```yaml
llm:
  providers:
    custom:
      module: "./custom-llm-provider.js" # Path to custom provider module
      options:
        # Provider-specific options
        apiKey: "${CUSTOM_API_KEY}"
        baseUrl: "https://api.custom-llm.com"
```

## Vector Stores

### Pinecone

```yaml
vectorStores:
  pinecone:
    apiKey: "${PINECONE_API_KEY}"
    environment: "us-west1-gcp"
    indexName: "generic-agent-index"
    namespace: "default"
    dimensions: 1536           # Dimensions of the vectors
    metric: "cosine"           # Similarity metric: cosine, dotproduct, euclidean
```

### Chroma

```yaml
vectorStores:
  chroma:
    path: "/path/to/chroma/db"  # Local path for persistent storage
    url: "http://localhost:8000" # Chroma server URL (if remote)
    collectionName: "documents"
```

### Milvus

```yaml
vectorStores:
  milvus:
    address: "localhost:19530"
    username: "username"
    password: "password"
    database: "default"
    collection: "documents"
    dimensions: 1536
```

### Postgres PGVECTOR

```yaml
vectorStores:
  pgvector:
    connectionString: "postgresql://user:password@localhost:5432/generic_agent"
    tableSchema: "public"
    tableName: "document_embeddings"
    vectorColumnName: "embedding"
    dimensions: 1536
```

### Local Vector Store

```yaml
vectorStores:
  local:
    path: "./data/vectors"     # Path to store vectors
    dimensions: 1536
    algorithm: "hnsw"          # Algorithm: hnsw, flat
    distanceMetric: "cosine"   # Distance metric: cosine, euclidean, dot
```

## Tool Configuration

### Built-in Tools

```yaml
tools:
  builtIn:
    websearch:
      enabled: true
      provider: "tavily"       # Search provider
      apiKey: "${TAVILY_API_KEY}"
      maxResults: 5
    
    calculator:
      enabled: true
    
    fileIO:
      enabled: true
      rootDirectory: "./data/files"
      allowedExtensions: [".txt", ".md", ".pdf", ".csv"]
      maxFileSize: "10MB"
    
    wikipedia:
      enabled: true
      maxResults: 3
      language: "en"
```

### External API Tools

```yaml
tools:
  externalAPI:
    weather:
      enabled: true
      provider: "openweathermap"
      apiKey: "${OPENWEATHERMAP_API_KEY}"
      units: "metric"
    
    news:
      enabled: true
      provider: "newsapi"
      apiKey: "${NEWSAPI_API_KEY}"
      defaultCountry: "us"
```

### Custom Tools

```yaml
tools:
  custom:
    - name: "companyDatabase"
      description: "Query the company's internal database"
      module: "./tools/company-database.js"
      options:
        connectionString: "${DB_CONNECTION_STRING}"
        maxRows: 100
    
    - name: "internalAPI"
      description: "Access internal company API"
      module: "./tools/internal-api.js"
      options:
        baseUrl: "https://api.internal.company.com"
        apiKey: "${INTERNAL_API_KEY}"
```

## Agent Configuration

### Agent Types

```yaml
agents:
  types:
    conversational:
      systemPromptTemplate: "./templates/conversational-agent.txt"
      maxHistoryItems: 10
    
    researchAssistant:
      systemPromptTemplate: "./templates/research-agent.txt"
      tools: ["websearch", "wikipedia"]
      maxHistoryItems: 15
    
    customerSupport:
      systemPromptTemplate: "./templates/customer-support.txt"
      tools: ["companyDatabase", "internalAPI"]
      maxHistoryItems: 8
```

### Default Agent Settings

```yaml
agents:
  defaults:
    llmProvider: "openai"
    llmModel: "gpt-4"
    temperature: 0.7
    maxTokens: 2048
    responseFormat: "markdown"
    vectorStore: "pinecone"
    tools: ["calculator"]
    streamResponse: true
    timeout: 60000           # Timeout in milliseconds
```

### Memory Settings

```yaml
agents:
  memory:
    type: "conversational"    # Memory type: conversational, summary, none
    maxHistoryItems: 10       # Maximum history items to maintain
    pruneThreshold: 0.85      # Token threshold for pruning (0-1)
    summarizationInterval: 20 # Number of exchanges before summarization
```

## Environment Variables

Environment variables can be used in the configuration file by using the `${VARIABLE_NAME}` syntax. For example:

```yaml
llm:
  providers:
    openai:
      apiKey: "${OPENAI_API_KEY}"
```

Common environment variables:

- `GENERIC_AGENT_ENV`: Environment (development, production, test)
- `GENERIC_AGENT_PORT`: Server port
- `GENERIC_AGENT_HOST`: Server host
- `GENERIC_AGENT_LOG_LEVEL`: Logging level
- `GENERIC_AGENT_DATABASE_URL`: Database connection string
- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `PINECONE_API_KEY`: Pinecone API key

## Configuration Examples

### Minimal Configuration

```yaml
server:
  port: 8000

database:
  type: "sqlite"
  connectionString: "sqlite://./data/generic-agent.sqlite"

llm:
  providers:
    openai:
      apiKey: "${OPENAI_API_KEY}"
      models:
        default: "gpt-3.5-turbo"

vectorStores:
  local:
    path: "./data/vectors"
    dimensions: 1536
```

### Production Configuration

```yaml
server:
  host: "0.0.0.0"
  port: 8000
  cors:
    enabled: true
    origin: "https://your-app.com"
  rateLimits:
    enabled: true
    defaultLimit: 60
    windowMs: 60000
  ssl:
    enabled: true
    key: "/etc/ssl/private/your-app.key"
    cert: "/etc/ssl/certs/your-app.cert"

database:
  type: "postgres"
  connectionString: "${DATABASE_URL}"
  pool:
    min: 5
    max: 20

auth:
  type: "jwt"
  jwt:
    secret: "${JWT_SECRET}"
    expiresIn: "12h"

logging:
  level: "info"
  format: "json"
  destination: "file"
  file: "/var/log/generic-agent/app.log"
  rotation:
    enabled: true
    maxSize: "100m"
    maxFiles: 10

llm:
  providers:
    openai:
      apiKey: "${OPENAI_API_KEY}"
      models:
        default: "gpt-4"
        chat: "gpt-4"
        embedding: "text-embedding-ada-002"

vectorStores:
  pinecone:
    apiKey: "${PINECONE_API_KEY}"
    environment: "us-west1-gcp"
    indexName: "generic-agent-index"

tools:
  builtIn:
    websearch:
      enabled: true
      provider: "tavily"
      apiKey: "${TAVILY_API_KEY}"
    calculator:
      enabled: true
    wikipedia:
      enabled: true
```

### Development Configuration

```yaml
server:
  host: "localhost"
  port: 8000
  cors:
    enabled: true
    origin: "*"

database:
  type: "sqlite"
  connectionString: "sqlite://./data/generic-agent.sqlite"

auth:
  type: "apiKey"
  apiKey:
    header: "X-API-Key"
    
logging:
  level: "debug"
  format: "text"
  destination: "console"

llm:
  providers:
    openai:
      apiKey: "${OPENAI_API_KEY}"
      models:
        default: "gpt-3.5-turbo"
        embedding: "text-embedding-ada-002"
    localLlm:
      type: "ollama"
      baseUrl: "http://localhost:11434"
      models:
        default: "llama2"

vectorStores:
  local:
    path: "./data/vectors"
    dimensions: 1536

tools:
  builtIn:
    calculator:
      enabled: true
    wikipedia:
      enabled: true
``` 