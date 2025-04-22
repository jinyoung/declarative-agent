"""
Agent Tool module for wrapping agents as tools.

This module provides functionality for wrapping agents as tools that can be used 
within LangGraph flows, enabling multi-agent conversations.
"""
from typing import Any, Dict, List, Optional
import logging

from langchain.tools import Tool

# Configure logging
logger = logging.getLogger(__name__)

class AgentTool:
    """
    A wrapper that allows an agent to be used as a tool within a LangGraph flow.
    
    This wrapper enables creating multi-agent systems where one agent can invoke
    another agent as a tool within a LangGraph flow.
    """
    
    def __init__(self, agent, agent_id: str, description: str = None):
        """
        Initialize the AgentTool wrapper.
        
        Args:
            agent: The agent instance to wrap as a tool
            agent_id: The ID of the agent
            description: Optional description of what the agent does
        """
        self.agent = agent
        self.agent_id = agent_id
        self.name = f"agent_{agent_id}"
        self.description = description or f"Tool that allows consulting agent '{agent_id}' for specialized knowledge or reasoning"
        
    def invoke(self, query: str) -> str:
        """
        Invoke the agent with the given query.
        
        Args:
            query: The query to send to the agent
            
        Returns:
            str: The agent's response
            
        Raises:
            Exception: If an error occurs during agent execution
        """
        try:
            # Handle both arun and run methods based on agent type
            if hasattr(self.agent, 'arun'):
                # For async calls, we need to run in an event loop
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self.agent.arun(query))
                finally:
                    loop.close()
            else:
                # For synchronous calls or callable objects
                return self.agent.run(query) if hasattr(self.agent, 'run') else self.agent(query)
                
        except Exception as e:
            logger.error(f"Error calling agent '{self.agent_id}': {str(e)}")
            return f"Error calling agent '{self.agent_id}': {str(e)}"
    
    def as_tool(self) -> Tool:
        """
        Convert the agent wrapper to a LangChain Tool.
        
        Returns:
            Tool: LangChain Tool that invokes the wrapped agent
        """
        return Tool(
            name=self.name,
            description=self.description,
            func=self.invoke
        ) 