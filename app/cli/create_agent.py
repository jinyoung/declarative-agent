#!/usr/bin/env python
"""
Command-line script for creating agent definition files interactively.

This script guides the user through creating a valid agent definition JSON file
by prompting for the required fields and validating the input.

Usage:
    python -m app.cli.create_agent [agent_id]
    
If [agent_id] is provided, creates an agent definition with that ID.
Otherwise, prompts the user for an agent ID.
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Dict, Any, List, Optional

from app.core.schema import validate_agent_json


def prompt_yes_no(question: str) -> bool:
    """Prompt the user for a yes/no answer."""
    while True:
        response = input(f"{question} (y/n): ").lower().strip()
        if response in ("y", "yes"):
            return True
        elif response in ("n", "no"):
            return False
        print("Please answer 'y' or 'n'.")


async def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Create an agent definition JSON file interactively.")
    parser.add_argument("agent_id", nargs="?", help="ID for the agent (used as filename)")
    parser.add_argument("--output-dir", default="app/agents",
                        help="Directory to save the agent definition file (default: app/agents)")
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Get agent ID
    agent_id = args.agent_id
    if not agent_id:
        agent_id = input("Enter agent ID (used as filename, e.g., 'math_assistant'): ").strip()
        if not agent_id:
            print("❌ Agent ID is required")
            sys.exit(1)
    
    # Check if file already exists
    file_path = os.path.join(args.output_dir, f"{agent_id}.json")
    if os.path.exists(file_path):
        if not prompt_yes_no(f"File {file_path} already exists. Overwrite?"):
            print("❌ Aborted")
            sys.exit(1)
    
    # Build agent definition
    agent_def: Dict[str, Any] = {}
    
    # Persona (required)
    agent_def["persona"] = input("Enter agent persona/system prompt: ").strip()
    if not agent_def["persona"]:
        print("❌ Persona is required")
        sys.exit(1)
    
    # Model (optional, has default)
    model = input("Enter LLM model name (default: gpt-4): ").strip()
    if model:
        agent_def["model"] = model
    
    # Tools (optional)
    if prompt_yes_no("Add tools to this agent?"):
        tools: List[Dict[str, Any]] = []
        while True:
            tool: Dict[str, Any] = {}
            
            # Tool name (required)
            tool["name"] = input("Tool name: ").strip()
            if not tool["name"]:
                print("❌ Tool name is required")
                continue
            
            # Tool type (required)
            tool_type = input("Tool type ('builtin' or 'mcp'): ").strip().lower()
            if tool_type not in ("builtin", "mcp"):
                print("❌ Tool type must be 'builtin' or 'mcp'")
                continue
            tool["type"] = tool_type
            
            # Description (optional)
            description = input("Tool description (optional): ").strip()
            if description:
                tool["description"] = description
            
            # MCP-specific fields
            if tool_type == "mcp":
                endpoint = input("MCP endpoint URL: ").strip()
                if endpoint:
                    tool["endpoint"] = endpoint
                
                api_key = input("API key (optional): ").strip()
                if api_key:
                    tool["api_key"] = api_key
            
            tools.append(tool)
            
            if not prompt_yes_no("Add another tool?"):
                break
        
        if tools:
            agent_def["tools"] = tools
    
    # Knowledge base (optional)
    if prompt_yes_no("Add a knowledge base to this agent?"):
        kb_type = input("Knowledge base type ('vectordb' or 'graph'): ").strip().lower()
        if kb_type not in ("vectordb", "graph"):
            print("❌ Knowledge base type must be 'vectordb' or 'graph'")
        else:
            kb_config: Dict[str, Any] = {"type": kb_type}
            
            # URI (required)
            uri = input(f"Enter {kb_type} URI: ").strip()
            if not uri:
                print(f"❌ {kb_type} URI is required")
            else:
                kb_config["uri"] = uri
                
                if kb_type == "vectordb":
                    # Index name (optional)
                    index_name = input("Index name (optional): ").strip()
                    if index_name:
                        kb_config["index_name"] = index_name
                    
                    # k (optional, has default)
                    k_str = input("Number of results to retrieve (default: 5): ").strip()
                    if k_str:
                        try:
                            k = int(k_str)
                            if k > 0:
                                kb_config["k"] = k
                            else:
                                print("❌ Number of results must be a positive integer")
                        except ValueError:
                            print("❌ Invalid number format")
                
                elif kb_type == "graph":
                    # Auth (optional)
                    if prompt_yes_no("Add authentication for the graph database?"):
                        username = input("Username: ").strip()
                        password = input("Password: ").strip()
                        if username and password:
                            kb_config["auth"] = {"username": username, "password": password}
                    
                    # Query template (optional)
                    query_template = input("Query template (optional): ").strip()
                    if query_template:
                        kb_config["query_template"] = query_template
            
            if "uri" in kb_config:
                agent_def["knowledge_base"] = {
                    "type": kb_type,
                    "config": kb_config
                }
    
    # Validate the agent definition
    try:
        validate_agent_json(agent_def)
        
        # Save to file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(agent_def, f, indent=2)
        
        print(f"✅ Agent definition saved to {file_path}")
    except ValueError as e:
        print(f"❌ Invalid agent definition: {e}")
        
        # Save anyway if user wants to
        if prompt_yes_no("Save the file anyway? (It may not validate)"):
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(agent_def, f, indent=2)
            print(f"⚠️ Agent definition saved to {file_path} (with validation errors)")


if __name__ == "__main__":
    asyncio.run(main()) 