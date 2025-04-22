#!/usr/bin/env python
"""
Command-line script for validating agent definition files.

This script validates agent definition JSON files against the schema defined in app.core.schema.
It can validate a single file or all files in a directory.

Usage:
    python -m app.cli.validate_agents [path]
    
If [path] is a directory, validates all .json files in that directory.
If [path] is a file, validates just that file.
If [path] is not provided, defaults to the "app/agents" directory.
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Dict, List, Union

from app.core.utils.validation import validate_agent_file, validate_all_agents


async def validate_single_file(file_path: str) -> bool:
    """
    Validate a single agent definition file.
    
    Args:
        file_path: Path to the agent definition JSON file
        
    Returns:
        bool: True if the file is valid, False otherwise
    """
    try:
        agent = await validate_agent_file(file_path)
        print(f"✅ {file_path} is valid")
        print(f"  - Persona: {agent.persona[:50]}...")
        print(f"  - Model: {agent.model}")
        print(f"  - Tools: {len(agent.tools)}")
        if agent.knowledge_base:
            print(f"  - Knowledge Base: {agent.knowledge_base.type}")
        return True
    except FileNotFoundError as e:
        print(f"❌ {file_path} not found")
        return False
    except ValueError as e:
        print(f"❌ {file_path} is invalid: {str(e)}")
        return False


async def validate_directory(dir_path: str) -> Dict[str, Union[List[str], List[Dict[str, str]]]]:
    """
    Validate all agent definition files in a directory.
    
    Args:
        dir_path: Path to directory containing agent definition JSON files
        
    Returns:
        Dict containing lists of valid and invalid agent definitions
    """
    if not os.path.exists(dir_path):
        print(f"❌ Directory {dir_path} not found")
        return {"valid": [], "invalid": []}
    
    print(f"Validating agent definitions in {dir_path}...")
    results = await validate_all_agents(dir_path)
    
    # Print results
    print("\nResults:")
    print(f"✅ Valid agent definitions: {len(results['valid'])}")
    for agent in results['valid']:
        print(f"  - {agent['id']}")
    
    print(f"\n❌ Invalid agent definitions: {len(results['invalid'])}")
    for agent in results['invalid']:
        print(f"  - {agent['id']}: {agent['status']}")
    
    return results


async def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Validate agent definition JSON files.")
    parser.add_argument("path", nargs="?", default="app/agents",
                        help="Path to a JSON file or directory containing JSON files (default: app/agents)")
    args = parser.parse_args()
    
    # Normalize path
    path = os.path.abspath(args.path)
    
    # Check if path exists
    if not os.path.exists(path):
        print(f"❌ {path} does not exist")
        sys.exit(1)
    
    # Validate based on path type
    if os.path.isfile(path):
        valid = await validate_single_file(path)
        sys.exit(0 if valid else 1)
    else:  # Directory
        results = await validate_directory(path)
        sys.exit(0 if len(results["invalid"]) == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main()) 