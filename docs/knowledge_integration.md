# Knowledge Base Integration

This guide provides detailed information on integrating different types of knowledge bases with the Generic Agent Runtime Engine to provide agents with access to domain-specific information.

## Table of Contents

- [Introduction](#introduction)
- [Knowledge Base Types](#knowledge-base-types)
  - [Vector Databases](#vector-databases)
  - [Graph Databases](#graph-databases)
  - [File-Based Knowledge](#file-based-knowledge)
- [Configuration](#configuration)
  - [Vector Database Configuration](#vector-database-configuration)
  - [Graph Database Configuration](#graph-database-configuration)
  - [File-Based Configuration](#file-based-configuration)
- [Adding Documents](#adding-documents)
  - [Document Preparation](#document-preparation)
  - [Document Ingestion](#document-ingestion)
  - [Chunking Strategies](#chunking-strategies)
- [Querying Knowledge Bases](#querying-knowledge-bases)
  - [Direct Queries](#direct-queries)
  - [Agent-Based Queries](#agent-based-queries)
- [Advanced Features](#advanced-features)
  - [Hybrid Search](#hybrid-search)
  - [Filtering](#filtering)
  - [Metadata](#metadata)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Introduction

Knowledge bases allow agents to access and reference domain-specific information beyond what is available in their training data. The Generic Agent Runtime Engine supports multiple types of knowledge bases, each with unique strengths for different use cases.

By integrating a knowledge base with your agent, you can:
- Provide access to proprietary or specialized information
- Keep agents up-to-date with the latest information
- Ground agent responses in factual, retrievable sources
- Enable citation of specific documents or data points

## Knowledge Base Types

### Vector Databases

Vector databases store information as high-dimensional vectors (embeddings) and enable semantic search based on meaning rather than just keywords. They excel at finding information based on conceptual similarity.

**Supported Vector Databases:**
- FAISS (Facebook AI Similarity Search)
- Pinecone
- Chroma
- Milvus
- PostgreSQL (with pgvector extension)

**Best For:**
- General knowledge retrieval
- Question answering over documents
- Semantic search across large corpuses
- Finding conceptually similar information

### Graph Databases

Graph databases store information as nodes and relationships, allowing for complex queries that involve multiple entities and their connections. They excel at relationship-based queries and navigating complex data structures.

**Supported Graph Databases:**
- Neo4j
- Amazon Neptune
- JanusGraph
- TigerGraph

**Best For:**
- Relationship-based queries
- Entity networks (people, companies, etc.)
- Hierarchical data
- Complex data with many connections
- Traversal queries ("find all customers who purchased product X and also live in region Y")

### File-Based Knowledge

For simpler use cases, the engine supports loading information directly from files without requiring a dedicated database.

**Supported File Types:**
- Plain text (.txt)
- Markdown (.md)
- PDF (.pdf)
- CSV (.csv)
- JSON (.json)

**Best For:**
- Simple projects
- Small knowledge bases
- Quick prototyping
- Offline operation

## Configuration

### Vector Database Configuration

To configure a vector database knowledge base in your agent definition:

```json
{
  "knowledge_base": {
    "type": "vectordb",
    "config": {
      "type": "vectordb",
      "uri": "./knowledge/research_papers",
      "index_name": "research",
      "embedding_model": "text-embedding-ada-002",
      "k": 5
    }
  }
}
```

For a remote vector database like Pinecone:

```json
{
  "knowledge_base": {
    "type": "vectordb",
    "config": {
      "type": "vectordb",
      "uri": "pinecone://",
      "api_key": "env:PINECONE_API_KEY",
      "environment": "us-west-1",
      "index_name": "customer-support",
      "namespace": "faqs",
      "k": 3
    }
  }
}
```

### Graph Database Configuration

To configure a graph database knowledge base:

```json
{
  "knowledge_base": {
    "type": "graph",
    "config": {
      "type": "graph",
      "uri": "neo4j://localhost:7687",
      "auth": {
        "username": "neo4j",
        "password": "env:NEO4J_PASSWORD"
      },
      "database": "knowledge",
      "query_template": "MATCH (n)-[r]-(m) WHERE n.name CONTAINS $query RETURN n, r, m LIMIT 10"
    }
  }
}
```

### File-Based Configuration

For a file-based knowledge base:

```json
{
  "knowledge_base": {
    "type": "files",
    "config": {
      "type": "files",
      "path": "./knowledge/product_manuals",
      "file_types": [".pdf", ".md", ".txt"],
      "recursive": true,
      "chunk_size": 1000,
      "chunk_overlap": 200
    }
  }
}
```

## Adding Documents

### Document Preparation

Before adding documents to your knowledge base, follow these best practices:

1. **Clean and normalize text**:
   - Remove unnecessary formatting
   - Fix encoding issues
   - Standardize text structure

2. **Add metadata**:
   - Include source information
   - Add timestamps
   - Tag with relevant categories
   - Include author information

3. **Structure for retrievability**:
   - Organize content logically
   - Use clear headings and sections
   - Keep related information together

### Document Ingestion

To add documents to a knowledge base, use the Knowledge Base API:

```bash
# Using curl
curl -X POST "http://localhost:8000/agents/research_agent/knowledge" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Research Paper",
    "content": "This paper presents a novel approach to...",
    "metadata": {
      "author": "Dr. Smith",
      "publication_date": "2023-06-15",
      "tags": ["ai", "research", "neural-networks"]
    }
  }'

# Using the CLI
agent kb add research_agent ./research_paper.pdf --title "Research Paper" --tags "ai,research,neural-networks"
```

### Chunking Strategies

Documents are split into chunks for efficient storage and retrieval. The engine supports several chunking strategies:

1. **Fixed-size chunking**:
   - Splits text into chunks of a specified token or character length
   - Simple but may break semantic units

2. **Semantic chunking**:
   - Tries to keep semantically related content together
   - Respects paragraph and section boundaries

3. **Hierarchical chunking**:
   - Creates parent-child relationships between chunks
   - Maintains document hierarchy for better context

Configure chunking in your knowledge base settings:

```json
"chunk_settings": {
  "strategy": "semantic",
  "chunk_size": 1000,
  "chunk_overlap": 200
}
```

## Querying Knowledge Bases

### Direct Queries

You can directly query a knowledge base using the Knowledge Base API:

```bash
# Using curl
curl -X POST "http://localhost:8000/agents/research_agent/knowledge/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the advantages of transformer models?",
    "limit": 5
  }'
```

### Agent-Based Queries

When an agent has a knowledge base configured, it automatically uses it to inform responses. The engine's query process:

1. The user sends a query to the agent
2. The query is processed through the agent's flow template
3. If knowledge is needed, the engine queries the knowledge base
4. Retrieved information is incorporated into the context
5. The LLM generates a response informed by the knowledge

## Advanced Features

### Hybrid Search

Combines vector similarity search with keyword-based (BM25) search for better results:

```json
"search_settings": {
  "type": "hybrid",
  "vector_weight": 0.7,
  "keyword_weight": 0.3
}
```

### Filtering

Filter results based on metadata:

```json
"filters": {
  "metadata": {
    "category": "technical",
    "date": {"$gt": "2023-01-01"}
  }
}
```

### Metadata

Add rich metadata to improve searchability and context:

```json
"metadata": {
  "source": "Company Handbook",
  "author": "HR Department",
  "last_updated": "2023-07-15",
  "version": "2.3",
  "department": "Engineering",
  "confidentiality": "Internal",
  "tags": ["policy", "procedures", "onboarding"]
}
```

## Best Practices

1. **Optimize chunk size**:
   - Too large: Retrieval becomes imprecise
   - Too small: Context gets fragmented
   - Aim for 300-1000 tokens per chunk for most use cases

2. **Use descriptive metadata**:
   - Include source, author, date, and relevant tags
   - Add domain-specific attributes

3. **Regular updates**:
   - Establish a process for keeping knowledge current
   - Consider version control for important documents

4. **Monitor retrieval quality**:
   - Log queries and retrieved chunks
   - Periodically review for relevance
   - Adjust embedding models or chunking if needed

5. **Security considerations**:
   - Implement proper access controls
   - Consider data privacy implications
   - Be cautious with sensitive information

## Troubleshooting

### Common Issues

#### Poor Retrieval Quality

**Possible Causes:**
- Inappropriate chunk size
- Suboptimal embedding model
- Poor document quality
- Query not specific enough

**Solutions:**
- Adjust chunking strategy and size
- Try different embedding models
- Improve document preprocessing
- Refine query techniques

#### Slow Performance

**Possible Causes:**
- Knowledge base too large
- Inefficient database configuration
- Complex query patterns
- Resource constraints

**Solutions:**
- Implement caching
- Optimize database indexes
- Use more powerful hardware
- Consider database sharding for large collections

#### Missing Information

**Possible Causes:**
- Information not properly ingested
- Retrieval k-value too low
- Document format issues
- Filter settings too restrictive

**Solutions:**
- Verify document ingestion was successful
- Increase the k-value for retrieval
- Check document processing logs
- Review and adjust filter settings 