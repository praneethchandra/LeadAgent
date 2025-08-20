#!/usr/bin/env python3
"""
Simple script to run the Lead Agent API server.
This is a convenience script for development and testing.
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Run the Lead Agent API server with default settings."""
    # Check if we're in the correct directory
    if not Path("src/lead_agent").exists():
        print("Error: Please run this script from the project root directory.")
        print("Expected to find 'src/lead_agent' directory.")
        sys.exit(1)
    
    # Default arguments
    args = [
        sys.executable, "-m", "lead_agent.api.server",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload",  # Enable auto-reload for development
        "--debug"    # Enable debug mode
    ]
    
    print("🚀 Starting Lead Agent API Server...")
    print("📍 URL: http://127.0.0.1:8000")
    print("📚 API Docs: http://127.0.0.1:8000/docs")
    print("🔍 ReDoc: http://127.0.0.1:8000/redoc")
    print("💚 Health Check: http://127.0.0.1:8000/api/v1/health")
    print()
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Run the server
        subprocess.run(args)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("\nTry installing dependencies first:")
        print("  poetry install")
        print("  # or")
        print("  pip install -r requirements.txt")
        sys.exit(1)


if __name__ == "__main__":
    main()
