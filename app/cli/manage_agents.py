#!/usr/bin/env python
"""
Command-line script for managing agent definitions.

This script provides functionality for listing, validating, loading, and deleting agent definitions.

Usage:
    python -m app.cli.manage_agents [command] [options]
    
Commands:
    list                List all available agent definitions
    show <agent_id>     Show details for a specific agent
    validate <agent_id> Validate a specific agent definition
    delete <agent_id>   Delete an agent definition
"""

import argparse
import asyncio
import json
import sys
from typing import List, Dict, Any

from app.core.agent_manager import AgentManager


async def list_agents(manager: AgentManager, args: argparse.Namespace) -> None:
    """List all available agent definitions."""
    agents = await manager.list_agents()
    
    if not agents:
        print("No agent definitions found.")
        return
    
    print(f"Found {len(agents)} agent definition(s):")
    
    # Determine maximum ID length for pretty formatting
    max_id_len = max(len(agent["id"]) for agent in agents)
    
    # Print agents with status
    for agent in agents:
        status_icon = "✅" if agent["status"] == "valid" else "❌"
        print(f"{status_icon} {agent['id']:{max_id_len}} - {agent['status']}")


async def show_agent(manager: AgentManager, args: argparse.Namespace) -> None:
    """Show details for a specific agent."""
    agent_id = args.agent_id
    
    try:
        # Load the agent configuration
        agent_config = await manager.load_agent_config(agent_id)
        
        # Convert to dictionary for pretty printing
        config_dict = agent_config.model_dump()
        
        # Print details
        print(f"Agent ID: {agent_id}")
        print(f"Persona: {config_dict['persona'][:100]}...")
        print(f"Model: {config_dict['model']}")
        
        if config_dict.get("tools"):
            print(f"Tools: {len(config_dict['tools'])}")
            for i, tool in enumerate(config_dict['tools'], 1):
                print(f"  {i}. {tool['name']} ({tool['type']})")
        else:
            print("Tools: None")
        
        if config_dict.get("knowledge_base"):
            kb = config_dict["knowledge_base"]
            print(f"Knowledge Base: {kb['type']}")
            print(f"  Configuration: {kb['config']}")
        else:
            print("Knowledge Base: None")
        
        if args.json:
            # Print full JSON representation
            print("\nFull configuration:")
            print(json.dumps(config_dict, indent=2))
            
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


async def validate_agent(manager: AgentManager, args: argparse.Namespace) -> None:
    """Validate a specific agent definition."""
    agent_id = args.agent_id
    
    try:
        # Force reload to ensure validation
        agent_config = await manager.load_agent_config(agent_id, force_reload=True)
        print(f"✅ Agent definition '{agent_id}' is valid")
        
        # Print basic info
        print(f"  Persona: {agent_config.persona[:50]}...")
        print(f"  Model: {agent_config.model}")
        print(f"  Tools: {len(agent_config.tools)}")
        if agent_config.knowledge_base:
            print(f"  Knowledge Base: {agent_config.knowledge_base.type}")
            
    except ValueError as e:
        print(f"❌ Agent definition '{agent_id}' is invalid: {e}")
        sys.exit(1)


async def delete_agent(manager: AgentManager, args: argparse.Namespace) -> None:
    """Delete an agent definition."""
    agent_id = args.agent_id
    
    if not args.force:
        # Confirm deletion
        confirm = input(f"Are you sure you want to delete agent '{agent_id}'? (y/n): ")
        if confirm.lower() not in ("y", "yes"):
            print("Deletion cancelled.")
            return
    
    # Delete the agent
    success = await manager.delete_agent(agent_id)
    
    if success:
        print(f"✅ Agent definition '{agent_id}' deleted successfully")
    else:
        print(f"❌ Agent definition '{agent_id}' not found")
        sys.exit(1)


async def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Manage agent definitions.")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all available agent definitions")
    list_parser.add_argument("--agents-dir", default="app/agents", help="Directory containing agent definitions")
    
    # Show command
    show_parser = subparsers.add_parser("show", help="Show details for a specific agent")
    show_parser.add_argument("agent_id", help="ID of the agent to show")
    show_parser.add_argument("--agents-dir", default="app/agents", help="Directory containing agent definitions")
    show_parser.add_argument("--json", action="store_true", help="Print full JSON configuration")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a specific agent definition")
    validate_parser.add_argument("agent_id", help="ID of the agent to validate")
    validate_parser.add_argument("--agents-dir", default="app/agents", help="Directory containing agent definitions")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete an agent definition")
    delete_parser.add_argument("agent_id", help="ID of the agent to delete")
    delete_parser.add_argument("--agents-dir", default="app/agents", help="Directory containing agent definitions")
    delete_parser.add_argument("--force", action="store_true", help="Delete without confirmation")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Create AgentManager instance
    manager = AgentManager(agents_dir=args.agents_dir)
    
    # Execute the appropriate command
    commands = {
        "list": list_agents,
        "show": show_agent,
        "validate": validate_agent,
        "delete": delete_agent
    }
    
    await commands[args.command](manager, args)


if __name__ == "__main__":
    asyncio.run(main()) 