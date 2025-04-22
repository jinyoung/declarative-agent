# Quick Start Guide

This quick start guide will help you get the Generic Agent Runtime Engine up and running with a simple agent in just a few minutes.

## Prerequisites

- Node.js 18+
- npm or yarn
- Git

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/generic-agent.git
   cd generic-agent
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env` file in the project root with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ```

## Creating Your First Agent

1. Create a new file in `app/agents/` called `quickstart_agent.json` with this content:

   ```json
   {
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

2. Start the server:
   ```bash
   npm run dev
   ```

3. Test your agent using curl:
   ```bash
   curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{
       "agent_id": "quickstart_agent",
       "query": "Hello! Can you tell me what you can do?"
     }'
   ```

   Or with JavaScript:
   ```javascript
   fetch('http://localhost:8000/query', {
     method: 'POST',
     headers: {
       'Content-Type': 'application/json',
     },
     body: JSON.stringify({
       agent_id: 'quickstart_agent',
       query: 'Hello! Can you tell me what you can do?'
     }),
   })
   .then(response => response.json())
   .then(data => console.log(data.response));
   ```

## Adding Tools

Let's enhance our agent with a tool that can search the web:

1. Update your `.env` file to add the Tavily API key:
   ```
   OPENAI_API_KEY=your_openai_api_key
   TAVILY_API_KEY=your_tavily_api_key
   ```

2. Update `app/agents/quickstart_agent.json`:
   ```json
   {
     "persona": "You are a helpful assistant who provides clear, concise answers based on current information when available.",
     "tools": [
       {
         "name": "TavilySearch",
         "type": "builtin",
         "description": "Search for up-to-date information on the internet",
         "parameters": {
           "api_key": "env:TAVILY_API_KEY"
         }
       }
     ],
     "knowledge_base": {
       "type": "none"
     },
     "model": "gpt-4",
     "flow_template": {
       "type": "sequential",
       "parameters": {}
     }
   }
   ```

3. Restart the server and test the enhanced agent with a question that requires current information:
   ```bash
   curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{
       "agent_id": "quickstart_agent",
       "query": "What are the latest developments in quantum computing?"
     }'
   ```

## Next Steps

1. Explore the [User Guide](user_guide.md) for detailed information on agent configuration options
2. Check the [API Reference](api_reference.md) for a complete list of API endpoints
3. Try creating specialized agents for different tasks:
   - A travel planning agent
   - A research assistant
   - A coding helper

## Troubleshooting

- **Error: Agent not found** - Make sure your agent file is in the correct location and the `agent_id` matches the filename
- **API Key errors** - Verify your `.env` file is properly configured
- **Server won't start** - Check for error messages in the console, ensure all dependencies are installed 