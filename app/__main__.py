import uvicorn
import os
import argparse
from dotenv import load_dotenv


def main():
    """
    Main entry point when running the application directly as a module.
    Example: python -m app
    """
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Agent Framework API Server")
    parser.add_argument(
        "--host", 
        type=str, 
        default=os.getenv("HOST", "0.0.0.0"), 
        help="Host to bind the server to"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=int(os.getenv("PORT", "8000")), 
        help="Port to bind the server to"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Enable auto-reload for development"
    )
    args = parser.parse_args()
    
    # Run the server
    uvicorn.run(
        "app.api.main:app", 
        host=args.host, 
        port=args.port, 
        reload=args.reload,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
    

if __name__ == "__main__":
    main() 