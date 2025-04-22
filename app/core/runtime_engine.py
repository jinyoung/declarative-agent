"""
Runtime Engine component that assembles and executes LangChain agents.

This module is responsible for creating and running agents based on the agent definition.
"""
import os
from typing import Any, Dict, List, Optional, Union, Callable

from langchain.agents import AgentExecutor, initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from app.core.schema import AgentDefinition
from app.core.tool_factory import ToolFactory
from app.knowledge.knowledge_base_loader import KnowledgeBaseLoader
from app.core.flow_template_manager import FlowTemplateManager


class RuntimeEngine:
    """
    Assembles and executes LangChain agents based on agent definitions.
    
    This class is responsible for:
    - Creating tools based on the agent definition
    - Adding knowledge base tools if configured
    - Initializing the appropriate LLM based on the model name
    - Creating and running the agent
    - Optionally creating and running LangGraph flows for complex behaviors
    """
    
    def __init__(self):
        """Initialize the RuntimeEngine with required components."""
        self.tool_factory = ToolFactory()
        self.kb_loader = KnowledgeBaseLoader()
        self.flow_template_manager = FlowTemplateManager()
    
    async def create_agent(self, agent_config: AgentDefinition) -> Union[AgentExecutor, Callable]:
        """
        Create a LangChain agent or LangGraph flow from the agent definition.
        
        Args:
            agent_config: The agent definition containing configuration for the agent
            
        Returns:
            Union[AgentExecutor, Callable]: The initialized agent, either a LangChain
                AgentExecutor or a compiled LangGraph flow
        """
        # Check if this agent uses a flow template
        if agent_config.flow_template:
            return await self._create_flow(agent_config)
        else:
            return await self._create_agent_executor(agent_config)
    
    async def _create_agent_executor(self, agent_config: AgentDefinition) -> AgentExecutor:
        """
        Create a standard LangChain agent executor from the agent definition.
        
        Args:
            agent_config: The agent definition containing configuration for the agent
            
        Returns:
            AgentExecutor: The initialized LangChain agent
        """
        # Create tools from the agent definition
        tools = self.tool_factory.create_tools(agent_config.tools)
        
        # Add knowledge base tool if configured
        if agent_config.knowledge_base:
            kb_tool = self.kb_loader.create_knowledge_tool(agent_config.knowledge_base)
            if kb_tool:
                tools.append(kb_tool)
        
        # Set up memory for conversation history
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        
        # Initialize LLM based on the model name
        llm = self._initialize_llm(agent_config.model)
        
        # Initialize agent with tools, LLM, and memory
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            memory=memory,
            verbose=os.environ.get("DEBUG", "false").lower() == "true"
        )
        
        # Set persona (system prompt) if provided
        if agent_config.persona:
            # Update the system message with the persona
            agent.agent.llm_chain.prompt.messages[0].prompt.template = agent_config.persona
        
        return agent
    
    async def _create_flow(self, agent_config: AgentDefinition) -> Callable:
        """
        Create a LangGraph flow from the agent definition.
        
        Args:
            agent_config: The agent definition containing configuration for the agent
            
        Returns:
            Callable: The compiled LangGraph flow
        """
        # Create tools from the agent definition
        tools = self.tool_factory.create_tools(agent_config.tools)
        
        # Add knowledge base tool if configured
        if agent_config.knowledge_base:
            kb_tool = self.kb_loader.create_knowledge_tool(agent_config.knowledge_base)
            if kb_tool:
                tools.append(kb_tool)
        
        # Initialize LLM based on the model name
        llm = self._initialize_llm(agent_config.model)
        
        # Create flow from template
        flow = self.flow_template_manager.create_flow(
            agent_config.flow_template,
            tools,
            llm
        )
        
        # Create an executor-like interface
        class FlowExecutor:
            def __init__(self, flow, llm):
                self.flow = flow
                self.llm = llm
                # Add agent executor-like interface
                # for compatibility with existing code
                self.agent = type('obj', (object,), {
                    'llm_chain': type('obj', (object,), {
                        'prompt': type('obj', (object,), {
                            'messages': [
                                type('obj', (object,), {
                                    'prompt': type('obj', (object,), {
                                        'template': agent_config.persona
                                    })
                                })
                            ]
                        })
                    })
                })
            
            async def arun(self, query):
                try:
                    # Run the flow with the provided query
                    result = await self.flow.ainvoke({
                        "input": query,
                        "steps": []
                    })
                    # Return the output if available, otherwise the last step
                    return result.get("output", "No output generated")
                except Exception as e:
                    print(f"Error running flow: {str(e)}")
                    return f"Error running flow: {str(e)}"
            
            def run(self, query):
                # Synchronous version for compatibility
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self.arun(query))
                finally:
                    loop.close()
        
        return FlowExecutor(flow, llm)
    
    async def run_agent(self, agent: Union[AgentExecutor, Any], query: str) -> str:
        """
        Run the agent with the given query.
        
        Args:
            agent: The LangChain agent executor or LangGraph flow to run
            query: The user query to process
            
        Returns:
            str: The agent's response
            
        Raises:
            Exception: If an error occurs during agent execution
        """
        try:
            # Run the agent asynchronously
            if hasattr(agent, 'arun'):
                response = await agent.arun(query)
            else:
                # Handle case where agent might be a flow without arun
                response = await agent(query)
            return response
        except Exception as e:
            # Log the error and return an error message
            print(f"Error running agent: {str(e)}")
            return f"Error running agent: {str(e)}"
    
    def _initialize_llm(self, model_name: str):
        """
        Initialize the appropriate LLM based on the model name.
        
        Args:
            model_name: The name of the model to use
            
        Returns:
            The initialized LLM instance
        """
        # Get temperature from environment or use default
        temperature = float(os.environ.get("TEMPERATURE", "0.0"))
        
        # Check if it's an OpenAI model (GPT)
        if "gpt" in model_name.lower():
            return ChatOpenAI(
                model_name=model_name, 
                temperature=temperature,
                api_key=os.environ.get("OPENAI_API_KEY")
            )
        # Check if it's an Anthropic model (Claude)
        elif "claude" in model_name.lower():
            return ChatAnthropic(
                model=model_name, 
                temperature=temperature,
                api_key=os.environ.get("ANTHROPIC_API_KEY")
            )
        # Default to OpenAI
        else:
            print(f"Warning: Unknown model type '{model_name}'. Defaulting to GPT-4.")
            return ChatOpenAI(
                model_name="gpt-4", 
                temperature=temperature,
                api_key=os.environ.get("OPENAI_API_KEY")
            ) 