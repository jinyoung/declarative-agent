"""
FastAPI application with endpoints for querying agents.

This module provides the HTTP API for the Generic Agent Runtime Engine.
"""
import time
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.core.agent_manager import AgentManager
from app.core.runtime_engine import RuntimeEngine


# Create FastAPI application with metadata
app = FastAPI(
    title="Generic Agent Runtime Engine",
    description="API for interacting with configurable LangChain agents",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create instances of the core components
agent_manager = AgentManager()
runtime_engine = RuntimeEngine()

# In-memory cache for active agents
active_agents = {}


# Pydantic models for request/response
class QueryRequest(BaseModel):
    """
    Request model for agent queries.
    """
    agent_id: str = Field(..., description="ID of the agent to query")
    query: str = Field(..., description="User query to process")


class QueryResponse(BaseModel):
    """
    Response model for agent queries.
    """
    response: str = Field(..., description="Agent's response to the query")
    agent_id: str = Field(..., description="ID of the agent that processed the query")
    execution_time: float = Field(..., description="Time taken to process the query in seconds")


class AgentInfo(BaseModel):
    """
    Basic information about an agent.
    """
    id: str = Field(..., description="Unique identifier for the agent")
    persona: str = Field(..., description="Brief description of the agent's persona/role")
    model: str = Field(..., description="LLM model used by the agent")
    has_knowledge_base: bool = Field(..., description="Whether the agent has access to a knowledge base")
    tools: List[str] = Field(default_factory=list, description="List of tool names available to the agent")


class HealthResponse(BaseModel):
    """
    Response model for health check.
    """
    status: str = Field(..., description="Health status of the service")
    version: str = Field(..., description="API version")
    active_agents: int = Field(..., description="Number of active agents in memory")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify the service is running.
    
    Returns:
        Health status information
    """
    return {
        "status": "healthy",
        "version": app.version,
        "active_agents": len(active_agents)
    }


@app.get("/agents", response_model=List[AgentInfo])
async def list_agents():
    """
    List all available agents.
    
    Returns:
        List of available agent information
    """
    try:
        # Get the IDs of all available agents
        agent_ids = await agent_manager.list_agent_ids()
        
        # Gather basic information about each agent
        agents = []
        for agent_id in agent_ids:
            try:
                # Load the agent config (this will use the cache if available)
                config = await agent_manager.load_agent_config(agent_id)
                
                # Create agent info object
                agent_info = AgentInfo(
                    id=agent_id,
                    persona=config.persona.split("\n")[0] if config.persona else "Unknown",
                    model=config.model,
                    has_knowledge_base=config.knowledge_base is not None,
                    tools=[tool.name for tool in config.tools]
                )
                agents.append(agent_info)
            except ValueError:
                # Skip agents with invalid configurations
                continue
        
        return agents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing agents: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    """
    Query an agent with the given ID.
    
    Args:
        request: The query request containing agent_id and query text
        
    Returns:
        The agent's response and metadata
        
    Raises:
        HTTPException: If the agent cannot be found or another error occurs
    """
    try:
        # Record start time for performance measurement
        start_time = time.time()
        
        # Get or create the agent
        if request.agent_id not in active_agents:
            # Load agent configuration
            agent_config = await agent_manager.load_agent_config(request.agent_id)
            
            # Create the agent
            agent = await runtime_engine.create_agent(agent_config)
            
            # Cache the agent
            active_agents[request.agent_id] = agent
        else:
            # Use cached agent
            agent = active_agents[request.agent_id]
        
        # Run the agent
        response = await runtime_engine.run_agent(agent, request.query)
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        return QueryResponse(
            response=response,
            agent_id=request.agent_id,
            execution_time=execution_time
        )
    
    except ValueError as e:
        # This exception is raised when the agent is not found
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Other exceptions (runtime errors, etc.)
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@app.post("/agents/{agent_id}/reload")
async def reload_agent(agent_id: str):
    """
    Force reload an agent definition from disk.
    
    Args:
        agent_id: ID of the agent to reload
        
    Returns:
        Confirmation message
        
    Raises:
        HTTPException: If the agent cannot be found or another error occurs
    """
    try:
        # Force reload the agent configuration
        agent_config = await agent_manager.load_agent_config(agent_id, force_reload=True)
        
        # Create a new agent instance
        agent = await runtime_engine.create_agent(agent_config)
        
        # Update the cache
        active_agents[agent_id] = agent
        
        return {"message": f"Agent '{agent_id}' reloaded successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reloading agent: {str(e)}")


def cleanup_unused_agents():
    """
    Background task to clean up agents that haven't been used recently.
    This would be used with a scheduler in a production environment.
    """
    # For now, we keep all agents in memory, but this could be
    # extended to implement a time-based or LRU cache for agent instances
    pass 