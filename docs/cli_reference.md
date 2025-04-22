# CLI Reference

This document provides a comprehensive reference for the Generic Agent Runtime Engine command-line interface (CLI) commands and options.

## Table of Contents

- [Installation](#installation)
- [Global Options](#global-options)
- [Agent Commands](#agent-commands)
  - [List Agents](#list-agents)
  - [Create Agent](#create-agent)
  - [Delete Agent](#delete-agent)
  - [Validate Agent](#validate-agent)
  - [Export Agent](#export-agent)
  - [Import Agent](#import-agent)
- [Query Commands](#query-commands)
  - [Query Agent](#query-agent)
  - [Interactive Mode](#interactive-mode)
- [Knowledge Base Commands](#knowledge-base-commands)
  - [Add Document](#add-document)
  - [List Documents](#list-documents)
  - [Delete Document](#delete-document)
- [Development Commands](#development-commands)
  - [Create Project](#create-project)
  - [Serve](#serve)
  - [Test](#test)
- [Configuration Commands](#configuration-commands)
  - [Set Config](#set-config)
  - [Get Config](#get-config)
  - [List Config](#list-config)

## Installation

To install the Generic Agent Runtime Engine CLI:

```bash
# Using npm
npm install -g generic-agent-cli

# Using yarn
yarn global add generic-agent-cli
```

After installation, you can use the `agent` command:

```bash
agent --help
```

## Global Options

These options apply to all commands:

```
--help, -h     Show help information
--version, -v  Show version information
--quiet, -q    Suppress all output except errors
--json         Output in JSON format
--debug        Enable debug logging
--config       Specify a configuration file (default: ~/.generic-agent/config.json)
```

## Agent Commands

### List Agents

Lists all available agents.

```bash
agent list
```

**Options:**
```
--format       Output format: table, json, yaml (default: table)
--filter       Filter agents by criteria (e.g., "has-tool:TavilySearch")
```

**Example:**
```bash
agent list --format json
```

**Output:**
```
+------------------+----------------------+----------------+
| ID               | Name                 | Description    |
+------------------+----------------------+----------------+
| weather_agent    | Weather Assistant    | Get weather... |
| research_agent   | Research Assistant   | Research and.. |
+------------------+----------------------+----------------+
```

### Create Agent

Creates a new agent from a definition file or interactively.

```bash
agent create [options] [agent_id]
```

**Options:**
```
--file, -f     Path to agent definition file (JSON or YAML)
--interactive  Create agent interactively
--template     Use a predefined template
```

**Example:**
```bash
agent create customer_support --file ./customer_support_agent.json
```

**Interactive Mode:**
```bash
agent create --interactive
```

This starts an interactive wizard that guides you through the agent creation process.

### Delete Agent

Deletes an existing agent.

```bash
agent delete <agent_id>
```

**Options:**
```
--force, -f    Force deletion without confirmation
```

**Example:**
```bash
agent delete weather_agent
```

### Validate Agent

Validates an agent definition file without creating an agent.

```bash
agent validate --file <path_to_agent_file>
```

**Options:**
```
--fix          Attempt to fix validation issues
```

**Example:**
```bash
agent validate --file ./customer_support_agent.json
```

### Export Agent

Exports an agent configuration to a file.

```bash
agent export <agent_id> [filepath]
```

**Options:**
```
--format       Export format: json, yaml (default: json)
```

**Example:**
```bash
agent export weather_agent ./weather_agent_backup.json
```

### Import Agent

Imports an agent from a configuration file.

```bash
agent import <filepath> [agent_id]
```

**Options:**
```
--overwrite    Overwrite existing agent if it exists
```

**Example:**
```bash
agent import ./weather_agent_backup.json
```

## Query Commands

### Query Agent

Sends a single query to an agent.

```bash
agent query <agent_id> "Your query text here"
```

**Options:**
```
--file, -f     Take query from a file
--context, -c  Provide context JSON file
--output, -o   Write response to a file
--debug        Show debug information including tool calls
```

**Example:**
```bash
agent query weather_agent "What's the weather like in London today?"
```

### Interactive Mode

Start an interactive chat session with an agent.

```bash
agent chat <agent_id>
```

**Options:**
```
--history      Load chat history from a file
--save         Save chat history to a file
--markdown     Render responses in markdown (if terminal supports it)
```

**Example:**
```bash
agent chat research_agent
```

In interactive mode, type your queries and receive responses. Special commands:
- `/exit` or `/quit` - Exit the chat
- `/clear` - Clear the conversation history
- `/save [filename]` - Save the conversation to a file
- `/debug [on|off]` - Toggle debug mode
- `/help` - Show help

## Knowledge Base Commands

### Add Document

Adds a document to an agent's knowledge base.

```bash
agent kb add <agent_id> <filepath>
```

**Options:**
```
--title        Document title
--tags         Comma-separated list of tags
--metadata     JSON string with additional metadata
--format       Document format (auto-detected by default)
--chunk-size   Custom chunk size for document splitting
```

**Example:**
```bash
agent kb add customer_support ./product_manual.pdf --title "Product Manual v2.1" --tags "manual,product,reference"
```

### List Documents

Lists documents in an agent's knowledge base.

```bash
agent kb list <agent_id>
```

**Options:**
```
--format       Output format: table, json, yaml (default: table)
--tag          Filter by tag
```

**Example:**
```bash
agent kb list customer_support --tag manual
```

### Delete Document

Deletes a document from an agent's knowledge base.

```bash
agent kb delete <agent_id> <document_id>
```

**Options:**
```
--force, -f    Force deletion without confirmation
```

**Example:**
```bash
agent kb delete customer_support doc_12345
```

## Development Commands

### Create Project

Creates a new Generic Agent project.

```bash
agent create-project <project_name>
```

**Options:**
```
--template     Project template to use (default: basic)
--dir          Directory to create the project in (default: ./<project_name>)
```

**Example:**
```bash
agent create-project my-agent-project --template webapp
```

### Serve

Starts a local development server.

```bash
agent serve
```

**Options:**
```
--port, -p     Port to run the server on (default: 8000)
--host         Host to bind to (default: localhost)
--watch        Watch for file changes and restart
```

**Example:**
```bash
agent serve --port 3000 --watch
```

### Test

Runs tests for your agent project.

```bash
agent test [test_path]
```

**Options:**
```
--watch        Watch for file changes and rerun tests
--coverage     Generate test coverage report
```

**Example:**
```bash
agent test ./tests/agent_tests.js
```

## Configuration Commands

### Set Config

Sets a configuration value.

```bash
agent config set <key> <value>
```

**Example:**
```bash
agent config set default.model gpt-4
```

### Get Config

Gets a configuration value.

```bash
agent config get <key>
```

**Example:**
```bash
agent config get default.model
```

### List Config

Lists all configuration values.

```bash
agent config list
```

**Options:**
```
--format       Output format: table, json, yaml (default: table)
```

**Example:**
```bash
agent config list --format json
```

## Environment Variables

The CLI also supports configuration via environment variables:

- `GENERIC_AGENT_API_KEY` - API key for remote servers
- `GENERIC_AGENT_API_URL` - URL of the Generic Agent API server
- `GENERIC_AGENT_CONFIG` - Path to config file
- `GENERIC_AGENT_OUTPUT_FORMAT` - Default output format
- `GENERIC_AGENT_DEBUG` - Enable debug mode (set to "true")

Example:
```bash
export GENERIC_AGENT_API_KEY=your_api_key
agent list
``` 