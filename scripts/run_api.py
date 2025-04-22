#!/usr/bin/env python
"""
Script to run the FastAPI server using uvicorn.
"""
import sys
import os
import argparse
import uvicorn

# Add the parent directory to sys.path to enable imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    """
    Parse command line arguments and run the FastAPI server.
    """
    parser = argparse.ArgumentParser(description="Run the FastAPI server for agent queries")
    
    parser.add_argument(
        "--host", 
        type=str, 
        default="127.0.0.1", 
        help="Host to bind the server to"
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind the server to"
    )
    
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Enable auto-reload for development"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes"
    )
    
    args = parser.parse_args()
    
    # Run the API using uvicorn
    uvicorn.run(
        "app.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers
    )


if __name__ == "__main__":
    main() 