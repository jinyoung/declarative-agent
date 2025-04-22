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
from app.core.agent_tool import AgentTool
from app.core.chat_session import ChatSession


class RuntimeEngine:
    """
    Assembles and executes LangChain agents based on agent definitions.
    
    This class is responsible for:
    - Creating tools based on the agent definition
    - Adding knowledge base tools if configured
    - Initializing the appropriate LLM based on the model name
    - Creating and running the agent
    - Optionally creating and running LangGraph flows for complex behaviors
    - Supporting continuous chat sessions for stateful interactions
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
    
    async def create_multi_agent_flow(
        self, 
        agent_configs: Dict[str, AgentDefinition],
        coordinator_agent_id: str,
        excluded_agent_ids: List[str] = None
    ) -> Callable:
        """
        Create a multi-agent flow where multiple agents can interact.
        
        Args:
            agent_configs: Dictionary mapping agent IDs to agent definitions
            coordinator_agent_id: ID of the agent to use as the coordinator
            excluded_agent_ids: Optional list of agent IDs to exclude from the flow
            
        Returns:
            Callable: The compiled multi-agent flow
            
        Raises:
            ValueError: If the coordinator agent doesn't exist or if no agent tools are created
        """
        if coordinator_agent_id not in agent_configs:
            raise ValueError(f"Coordinator agent '{coordinator_agent_id}' not found")
        
        # Get coordinator agent definition
        coordinator_config = agent_configs[coordinator_agent_id]
        
        # Initialize LLM for the coordinator
        coordinator_llm = self._initialize_llm(coordinator_config.model)
        
        # Create tools for the coordinator
        coordinator_tools = self.tool_factory.create_tools(coordinator_config.tools)
        
        # Add knowledge base tool if configured for coordinator
        if coordinator_config.knowledge_base:
            kb_tool = self.kb_loader.create_knowledge_tool(coordinator_config.knowledge_base)
            if kb_tool:
                coordinator_tools.append(kb_tool)
        
        # Create agent tools for other agents
        agent_tools = []
        excluded_ids = excluded_agent_ids or []
        excluded_ids.append(coordinator_agent_id)  # Don't include coordinator as a tool
        
        # Create agent instances for each agent (except excluded ones)
        for agent_id, agent_config in agent_configs.items():
            if agent_id not in excluded_ids:
                # Create the agent
                agent = await self.create_agent(agent_config)
                
                # Create description for the agent
                description = f"Expert agent for: {agent_config.persona.split('.')[0]}" if agent_config.persona else None
                
                # Create a wrapper that allows the agent to be used as a tool
                agent_tool = AgentTool(agent, agent_id, description)
                agent_tools.append(agent_tool)
        
        if not agent_tools:
            raise ValueError("No agent tools were created for the multi-agent flow")
        
        # Create a multi-agent flow
        # Import here to avoid circular imports
        from app.core.multi_agent_flow import create_default_multi_agent_flow
        
        return create_default_multi_agent_flow(
            llm=coordinator_llm,
            agent_tools=agent_tools,
            additional_tools=coordinator_tools,
            persona=coordinator_config.persona
        )
    
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
    
    async def run_chat_session(self, agent: Union[AgentExecutor, Any], session: ChatSession, query: str) -> str:
        """
        Run the agent within a chat session for continuous conversation.
        
        Args:
            agent: The LangChain agent executor or LangGraph flow to run
            session: The chat session containing conversation history
            query: The user query to process
            
        Returns:
            str: The agent's response
            
        Raises:
            Exception: If an error occurs during agent execution
        """
        try:
            # Add user message to the session
            session.add_message("user", query)
            
            # For FlowExecutor or other flow-based agents that support chat history
            if hasattr(agent, 'flow'):
                # Check if the agent has a specialized chat interface
                result = await agent.flow.ainvoke({
                    "input": query,
                    "chat_history": session.get_history_as_string()
                })
                
                # Extract response from result
                if isinstance(result, dict):
                    response = result.get("output", "No output generated")
                else:
                    response = str(result)
            else:
                # For standard LangChain agents, include history in the query
                history = session.get_history_as_string()
                prompt = f"Previous conversation:\n{history}\n\nNew query: {query}"
                response = await agent.arun(prompt)
            
            # Add assistant message to the session
            session.add_message("assistant", response)
            return response
            
        except Exception as e:
            # Log the error and return an error message
            error_msg = f"Error running chat session: {str(e)}"
            print(error_msg)
            
            # Add error message to the session
            session.add_message("assistant", error_msg)
            return error_msg
    
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