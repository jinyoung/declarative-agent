"""
Flow Template Manager for LangGraph-based flow templates.

This module provides functionality to create and manage LangGraph flow templates
that define more complex agent behaviors beyond simple LangChain agents.
"""
import logging
from typing import Any, Dict, List, Optional, TypedDict, Callable

from langgraph.graph import StateGraph, END

from app.core.schema import FlowTemplateConfig


class GraphState(TypedDict):
    """State object for LangGraph flows."""
    input: str
    steps: List[str]
    output: Optional[str]
    

class FlowTemplateManager:
    """
    Manages LangGraph flow templates used to create more complex agent behaviors.
    
    This class provides methods to:
    - Create different types of flow templates based on configuration
    - Support sequential flows where nodes execute in order
    - Support branching flows where execution path depends on conditions
    """
    
    def __init__(self, logger=None):
        """
        Initialize the FlowTemplateManager.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        # Register template creators
        self.templates = {
            "sequential": self._create_sequential_flow,
            "branching": self._create_branching_flow,
        }
    
    def create_flow(self, flow_config: FlowTemplateConfig, tools: List[Any], llm: Any) -> Callable:
        """
        Create a LangGraph flow based on the template configuration.
        
        Args:
            flow_config: Configuration for the flow template
            tools: List of tools available to the flow
            llm: Language model instance to use in LLM nodes
            
        Returns:
            Callable: The compiled flow that can be invoked with an input
            
        Raises:
            ValueError: If the template type is not supported
        """
        flow_type = flow_config.type
        if flow_type not in self.templates:
            raise ValueError(f"Unknown flow template type: {flow_type}")
        
        # Call the appropriate template creator
        return self.templates[flow_type](flow_config, tools, llm)
    
    def _create_sequential_flow(self, flow_config: FlowTemplateConfig, tools: List[Any], llm: Any) -> Callable:
        """
        Create a sequential flow where nodes execute in order.
        
        Args:
            flow_config: Configuration for the sequential flow
            tools: List of tools available to the flow
            llm: Language model instance to use in LLM nodes
            
        Returns:
            Callable: The compiled sequential flow
        """
        # Get nodes from configuration
        nodes = flow_config.nodes
        
        # Initialize the graph
        graph = StateGraph(GraphState)
        
        # Add nodes to the graph
        for i, node_config in enumerate(nodes):
            node_name = node_config.name
            node_type = node_config.type
            
            if node_type == "llm":
                # Create an LLM node
                prompt_template = node_config.prompt or "{input}"
                
                def create_llm_node(prompt):
                    def node_fn(state):
                        formatted_prompt = prompt.format(input=state.get("input", ""))
                        result = llm.predict(formatted_prompt)
                        return {"steps": state.get("steps", []) + [result]}
                    return node_fn
                
                graph.add_node(node_name, create_llm_node(prompt_template))
            
            elif node_type == "tool":
                # Create a tool node
                tool_name = node_config.tool_name
                tool = next((t for t in tools if t.name == tool_name), None)
                
                if not tool:
                    self.logger.warning(f"Tool '{tool_name}' not found, skipping node '{node_name}'")
                    continue
                
                def create_tool_node(tool):
                    def node_fn(state):
                        input_text = state.get("input", "")
                        last_step = state.get("steps", [])[-1] if state.get("steps", []) else input_text
                        result = tool.invoke(last_step)
                        return {"steps": state.get("steps", []) + [result]}
                    return node_fn
                
                graph.add_node(node_name, create_tool_node(tool))
        
        # Connect nodes in sequence
        for i in range(len(nodes) - 1):
            current_node = nodes[i].name
            next_node = nodes[i+1].name
            graph.add_edge(current_node, next_node)
        
        # Connect last node to final node
        last_node = nodes[-1].name
        
        def final_node(state):
            last_step = state.get("steps", [])[-1] if state.get("steps", []) else ""
            return {"output": last_step}
        
        graph.add_node("final", final_node)
        graph.add_edge(last_node, "final")
        graph.add_edge("final", END)
        
        # Set the entry point
        graph.set_entry_point(nodes[0].name)
        
        # Compile the graph
        return graph.compile()
    
    def _create_branching_flow(self, flow_config: FlowTemplateConfig, tools: List[Any], llm: Any) -> Callable:
        """
        Create a branching flow where execution path depends on conditions.
        
        Args:
            flow_config: Configuration for the branching flow
            tools: List of tools available to the flow
            llm: Language model instance to use in LLM nodes
            
        Returns:
            Callable: The compiled branching flow
        """
        # Get nodes from configuration
        nodes = flow_config.nodes
        
        # Initialize the graph
        graph = StateGraph(GraphState)
        
        # Add regular nodes to the graph (same as sequential)
        for node_config in nodes:
            node_name = node_config.name
            node_type = node_config.type
            
            if node_type == "llm":
                # Create an LLM node
                prompt_template = node_config.prompt or "{input}"
                
                def create_llm_node(prompt):
                    def node_fn(state):
                        formatted_prompt = prompt.format(input=state.get("input", ""))
                        result = llm.predict(formatted_prompt)
                        return {"steps": state.get("steps", []) + [result]}
                    return node_fn
                
                graph.add_node(node_name, create_llm_node(prompt_template))
            
            elif node_type == "tool":
                # Create a tool node
                tool_name = node_config.tool_name
                tool = next((t for t in tools if t.name == tool_name), None)
                
                if not tool:
                    self.logger.warning(f"Tool '{tool_name}' not found, skipping node '{node_name}'")
                    continue
                
                def create_tool_node(tool):
                    def node_fn(state):
                        input_text = state.get("input", "")
                        last_step = state.get("steps", [])[-1] if state.get("steps", []) else input_text
                        result = tool.invoke(last_step)
                        return {"steps": state.get("steps", []) + [result]}
                    return node_fn
                
                graph.add_node(node_name, create_tool_node(tool))
            
            elif node_type == "condition":
                # Create a conditional router node
                condition_expr = node_config.condition
                
                def create_condition_node(condition, targets):
                    def decide_next(state):
                        input_text = state.get("input", "")
                        last_step = state.get("steps", [])[-1] if state.get("steps", []) else input_text
                        
                        # Simple condition evaluation using LLM
                        prompt = f"""
                        Evaluate the following condition: '{condition}'
                        Based on this context: '{last_step}'
                        
                        Return only one of these options without explanation: true, false
                        """
                        result = llm.predict(prompt).strip().lower()
                        
                        # Choose next node based on condition
                        if result == "true" and "true" in targets:
                            return targets["true"]
                        elif "false" in targets:
                            return targets["false"]
                        else:
                            # Default case
                            return list(targets.values())[0] if targets else "final"
                    
                    return decide_next
                
                # Don't add the node here, handle connections separately
                targets = node_config.targets or {}
                
                # Add a conditional edge from this node
                def router(state):
                    return create_condition_node(condition_expr, targets)(state)
                
                graph.add_node(node_name, lambda state: state)  # Pass-through node
                graph.add_conditional_edges(
                    node_name,
                    router,
                    {target: target for target in targets.values()}
                )
        
        # Add final node
        def final_node(state):
            last_step = state.get("steps", [])[-1] if state.get("steps", []) else ""
            return {"output": last_step}
        
        graph.add_node("final", final_node)
        
        # Add edge from all leaf nodes (nodes without outgoing edges) to final
        for node_config in nodes:
            if node_config.type != "condition" and not any(
                node_config.name == other.targets.get("true") or
                node_config.name == other.targets.get("false") 
                for other in nodes if other.type == "condition"
            ):
                graph.add_edge(node_config.name, "final")
        
        graph.add_edge("final", END)
        
        # Set the entry point
        graph.set_entry_point(nodes[0].name)
        
        # Compile the graph
        return graph.compile() 