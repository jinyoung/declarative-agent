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
from app.core.chat_session import ChatSessionManager


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
session_manager = ChatSessionManager()

# In-memory cache for active agents
active_agents = {}
# In-memory cache for multi-agent flows
active_flows = {}


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


class ChatRequest(BaseModel):
    """
    Request model for chat sessions.
    """
    agent_id: str = Field(..., description="ID of the agent to chat with")
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for continuing a conversation")


class ChatResponse(BaseModel):
    """
    Response model for chat sessions.
    """
    response: str = Field(..., description="Agent's response to the message")
    agent_id: str = Field(..., description="ID of the agent that processed the message")
    session_id: str = Field(..., description="Session ID for the conversation")
    execution_time: float = Field(..., description="Time taken to process the message in seconds")


class MultiAgentRequest(BaseModel):
    """
    Request model for multi-agent queries.
    """
    coordinator_id: str = Field(..., description="ID of the agent to use as coordinator")
    query: str = Field(..., description="User query to process")
    agent_ids: List[str] = Field(default_factory=list, description="IDs of agents to include (empty for all available)")
    excluded_agent_ids: List[str] = Field(default_factory=list, description="IDs of agents to exclude")


class MultiAgentResponse(BaseModel):
    """
    Response model for multi-agent queries.
    """
    response: str = Field(..., description="Coordinated response from multiple agents")
    coordinator_id: str = Field(..., description="ID of the coordinator agent")
    flow_id: str = Field(..., description="ID of the flow for future reference")
    execution_time: float = Field(..., description="Time taken to process the query in seconds")


class MultiAgentChatRequest(BaseModel):
    """
    Request model for multi-agent chat sessions.
    """
    flow_id: str = Field(..., description="ID of the multi-agent flow")
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for continuing a conversation")


class MultiAgentChatResponse(BaseModel):
    """
    Response model for multi-agent chat sessions.
    """
    response: str = Field(..., description="Coordinated response from multiple agents")
    flow_id: str = Field(..., description="ID of the multi-agent flow")
    session_id: str = Field(..., description="Session ID for the conversation")
    execution_time: float = Field(..., description="Time taken to process the message in seconds")


class AgentInfo(BaseModel):
    """
    Basic information about an agent.
    """
    id: str = Field(..., description="Unique identifier for the agent")
    persona: str = Field(..., description="Brief description of the agent's persona/role")
    model: str = Field(..., description="LLM model used by the agent")
    has_knowledge_base: bool = Field(..., description="Whether the agent has access to a knowledge base")
    tools: List[str] = Field(default_factory=list, description="List of tool names available to the agent")
    supports_chat: bool = Field(False, description="Whether the agent supports continuous chat sessions")


class HealthResponse(BaseModel):
    """
    Response model for health check.
    """
    status: str = Field(..., description="Health status of the service")
    version: str = Field(..., description="API version")
    active_agents: int = Field(..., description="Number of active agents in memory")
    active_flows: int = Field(..., description="Number of active multi-agent flows in memory")
    active_sessions: int = Field(..., description="Number of active chat sessions")


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
        "active_agents": len(active_agents),
        "active_flows": len(active_flows),
        "active_sessions": len(session_manager.sessions)
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
                    tools=[tool.name for tool in config.tools],
                    supports_chat=config.supports_chat
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


@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Chat with an agent, maintaining conversation history across requests.
    
    Args:
        request: The chat request containing agent_id, message, and optional session_id
        
    Returns:
        The agent's response and session metadata
        
    Raises:
        HTTPException: If the agent cannot be found or another error occurs
    """
    try:
        # Record start time for performance measurement
        start_time = time.time()
        
        # Load agent configuration
        agent_config = await agent_manager.load_agent_config(request.agent_id)
        
        # Check if agent supports chat
        if not agent_config.supports_chat:
            raise HTTPException(
                status_code=400, 
                detail=f"Agent '{request.agent_id}' does not support chat sessions"
            )
        
        # Get or create a session
        session = None
        if request.session_id:
            session = session_manager.get_session(request.session_id)
            if not session or session.agent_id != request.agent_id:
                # Session not found or belongs to a different agent
                session = session_manager.create_session(request.agent_id)
        else:
            # Create a new session
            session = session_manager.create_session(request.agent_id)
        
        # Get or create the agent
        if request.agent_id not in active_agents:
            # Create the agent
            agent = await runtime_engine.create_agent(agent_config)
            
            # Cache the agent
            active_agents[request.agent_id] = agent
        else:
            # Use cached agent
            agent = active_agents[request.agent_id]
        
        # Run the agent with the chat session
        response = await runtime_engine.run_chat_session(agent, session, request.message)
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        return ChatResponse(
            response=response,
            agent_id=request.agent_id,
            session_id=session.session_id,
            execution_time=execution_time
        )
    
    except ValueError as e:
        # This exception is raised when the agent is not found
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Other exceptions (runtime errors, etc.)
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")


@app.post("/multi-agent", response_model=MultiAgentResponse)
async def create_multi_agent_flow(request: MultiAgentRequest):
    """
    Create a multi-agent flow and run an initial query.
    
    Args:
        request: The multi-agent request with coordinator_id, query, and optional agent IDs
        
    Returns:
        The coordinated response from multiple agents
        
    Raises:
        HTTPException: If agents cannot be found or another error occurs
    """
    try:
        # Record start time for performance measurement
        start_time = time.time()
        
        # Generate a unique ID for this flow
        flow_id = f"flow_{int(time.time())}"
        
        # Get all agent configs
        agent_configs = {}
        
        # If specific agent IDs are provided, use only those
        agent_ids_to_load = request.agent_ids if request.agent_ids else await agent_manager.list_agent_ids()
        
        # Remove excluded agent IDs
        if request.excluded_agent_ids:
            agent_ids_to_load = [aid for aid in agent_ids_to_load if aid not in request.excluded_agent_ids]
        
        # Make sure the coordinator is included
        if request.coordinator_id not in agent_ids_to_load:
            agent_ids_to_load.append(request.coordinator_id)
        
        # Load configurations for all required agents
        for agent_id in agent_ids_to_load:
            try:
                config = await agent_manager.load_agent_config(agent_id)
                agent_configs[agent_id] = config
            except ValueError:
                # Skip agents with invalid configurations
                continue
        
        # Check if we have the coordinator
        if request.coordinator_id not in agent_configs:
            raise HTTPException(
                status_code=404,
                detail=f"Coordinator agent '{request.coordinator_id}' not found"
            )
        
        # Create a multi-agent flow
        flow = await runtime_engine.create_multi_agent_flow(
            agent_configs=agent_configs,
            coordinator_agent_id=request.coordinator_id,
            excluded_agent_ids=request.excluded_agent_ids
        )
        
        # Store the flow
        active_flows[flow_id] = flow
        
        # Run the initial query
        response = await flow({
            "input": request.query,
            "chat_history": []
        })
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        return MultiAgentResponse(
            response=response.get("output", "No response generated"),
            coordinator_id=request.coordinator_id,
            flow_id=flow_id,
            execution_time=execution_time
        )
    
    except ValueError as e:
        # This exception is raised when an agent is not found
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Other exceptions (runtime errors, etc.)
        raise HTTPException(status_code=500, detail=f"Error creating multi-agent flow: {str(e)}")


@app.post("/multi-agent/chat", response_model=MultiAgentChatResponse)
async def chat_with_multi_agent_flow(request: MultiAgentChatRequest):
    """
    Continue a conversation with a multi-agent flow.
    
    Args:
        request: The multi-agent chat request with flow_id, message, and optional session_id
        
    Returns:
        The coordinated response from multiple agents
        
    Raises:
        HTTPException: If the flow cannot be found or another error occurs
    """
    try:
        # Record start time for performance measurement
        start_time = time.time()
        
        # Check if the flow exists
        if request.flow_id not in active_flows:
            raise HTTPException(
                status_code=404,
                detail=f"Multi-agent flow '{request.flow_id}' not found"
            )
        
        # Get the flow
        flow = active_flows[request.flow_id]
        
        # Get or create a session
        session = None
        if request.session_id:
            session = session_manager.get_session(request.session_id)
            if not session or not session.agent_id == request.flow_id:
                # Session not found or belongs to a different flow
                session = session_manager.create_session(request.flow_id)
        else:
            # Create a new session
            session = session_manager.create_session(request.flow_id)
        
        # Add user message to the session
        session.add_message("user", request.message)
        
        # Run the flow with the chat session
        result = await flow({
            "input": request.message,
            "chat_history": session.get_messages()
        })
        
        # Extract response
        response = result.get("output", "No response generated")
        
        # Add assistant message to the session
        session.add_message("assistant", response)
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        return MultiAgentChatResponse(
            response=response,
            flow_id=request.flow_id,
            session_id=session.session_id,
            execution_time=execution_time
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Other exceptions (runtime errors, etc.)
        raise HTTPException(status_code=500, detail=f"Error processing multi-agent chat: {str(e)}")


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
        
        # Clear any flows that use this agent
        flows_to_remove = []
        for flow_id in active_flows:
            if agent_id in flow_id:  # Simple heuristic for now
                flows_to_remove.append(flow_id)
                
        for flow_id in flows_to_remove:
            active_flows.pop(flow_id, None)
        
        return {
            "message": f"Agent '{agent_id}' reloaded successfully",
            "affected_flows": len(flows_to_remove)
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reloading agent: {str(e)}")


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a chat session.
    
    Args:
        session_id: ID of the session to delete
        
    Returns:
        Confirmation message
        
    Raises:
        HTTPException: If the session cannot be found or another error occurs
    """
    try:
        # Delete the session
        if session_manager.delete_session(session_id):
            return {"message": f"Session '{session_id}' deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Other exceptions
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")


def cleanup_unused_agents():
    """
    Background task to clean up agents that haven't been used recently.
    This would be used with a scheduler in a production environment.
    """
    # For now, we keep all agents in memory, but this could be
    # extended to implement a time-based or LRU cache for agent instances
    pass 