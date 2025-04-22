"""
Multi-Agent Flow module for creating LangGraph flows with multiple agents.

This module provides functionality for creating LangGraph flows where multiple
agents can interact with each other through tool calls.
"""
from typing import Any, Dict, List, Optional, Callable
import logging
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from langgraph.graph import StateGraph, END
from langgraph.graph.message import Messages, add_messages

from app.core.schema import FlowTemplateConfig
from app.core.agent_tool import AgentTool

# Configure logging
logger = logging.getLogger(__name__)


class MultiAgentFlowBuilder:
    """
    Builds LangGraph flows for multi-agent conversations.
    
    This class creates flows where multiple agents can be invoked as tools,
    enabling complex multi-agent conversations.
    """
    
    def __init__(self, logger=None):
        """
        Initialize the MultiAgentFlowBuilder.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def create_multi_agent_flow(
        self,
        coordinator_llm,
        agent_tools: List[AgentTool],
        additional_tools: List[Any] = None,
        persona: str = None
    ) -> Callable:
        """
        Create a LangGraph flow with multiple agent tools.
        
        Args:
            coordinator_llm: The LLM to use as the central coordinator
            agent_tools: List of agent tools to include in the flow
            additional_tools: List of additional non-agent tools
            persona: Optional persona for the coordinator agent
            
        Returns:
            The compiled multi-agent flow
        """
        # Combine all tools
        all_tools = []
        
        # Add agent tools
        for agent_tool in agent_tools:
            all_tools.append(agent_tool.as_tool())
        
        # Add additional tools if provided
        if additional_tools:
            all_tools.extend(additional_tools)
        
        # Create a state type for the graph
        class GraphState(Dict):
            """State for the multi-agent conversation graph."""
            chat_history: Messages
        
        # Create the graph
        graph = StateGraph(GraphState)
        
        # Create the coordinator node
        coordinator_prompt = ChatPromptTemplate.from_messages([
            ("system", persona or """You are a helpful coordinator that can call multiple expert agents to solve problems. 
            Consider which agent would be best for each query or subtask.
            When appropriate, you can use non-agent tools directly.
            If no agent or tool is needed, you can respond directly.
            Maintain context of the conversation and build upon previous interactions."""),
            MessagesPlaceholder(variable_name="chat_history"),
        ])
        
        # Create the coordinator node with tools
        coordinator = coordinator_llm.bind_tools(
            all_tools,
            prompt=coordinator_prompt
        )
        
        # Define nodes
        def coordinator_node(state: GraphState):
            """Coordinator node that processes user queries and decides on actions."""
            # Extract the last message from the chat history
            last_message = state["chat_history"][-1]
            
            # Call the coordinator to decide on actions
            response = coordinator.invoke({
                "chat_history": [
                    state["chat_history"][-1]  # Only the last message
                ]
            })
            
            # Add the response to the chat history
            return {"chat_history": add_messages(state["chat_history"], response)}
        
        # Add the node to the graph
        graph.add_node("coordinator", coordinator_node)
        
        # Add edges
        graph.add_edge("coordinator", END)
        
        # Set the entry point
        graph.set_entry_point("coordinator")
        
        # Compile the graph
        flow = graph.compile()
        
        # Create an executable chat flow
        def chat_flow(state: Dict) -> Dict:
            """Execute a multi-agent chat flow."""
            # Initialize chat history if not present
            if "chat_history" not in state:
                state["chat_history"] = []
                
            # Add the user message to chat history
            user_message = {"role": "user", "content": state.get("input", "")}
            state["chat_history"] = add_messages(state.get("chat_history", []), user_message)
            
            # Run the flow
            result = flow.invoke(state)
            
            # Extract assistant's response (last assistant message)
            assistant_messages = [
                msg for msg in result["chat_history"] 
                if isinstance(msg, dict) and msg.get("role") == "assistant"
            ]
            last_assistant_message = assistant_messages[-1]["content"] if assistant_messages else "No response generated"
            
            # Return the result
            return {
                "chat_history": result["chat_history"],
                "output": last_assistant_message
            }
        
        return chat_flow


def create_default_multi_agent_flow(llm, agent_tools, additional_tools=None, persona=None):
    """
    Create a default multi-agent flow with the given LLM and tools.
    
    This is a convenience function for creating a standard multi-agent flow.
    
    Args:
        llm: The LLM to use as the central coordinator
        agent_tools: List of agent tools to include in the flow
        additional_tools: List of additional non-agent tools
        persona: Optional persona for the coordinator agent
        
    Returns:
        The compiled multi-agent flow
    """
    builder = MultiAgentFlowBuilder()
    return builder.create_multi_agent_flow(
        coordinator_llm=llm,
        agent_tools=agent_tools,
        additional_tools=additional_tools,
        persona=persona
    ) 