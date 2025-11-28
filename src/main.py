#!/usr/bin/env python3
"""
Main entry point for the Gemini MCP Server.

This server provides integration with Google Gemini CLI for AI-powered
development assistance through the Model Context Protocol.
"""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.server.gemini_server import create_server

# Expose server object at module level for MCP install command
# The MCP install command looks for objects named 'mcp', 'app', or 'server'
mcp = create_server()
server = mcp  # Alias for compatibility
app = mcp  # Alias for compatibility


def main() -> None:
    """
    Main entry point for the Gemini MCP Server.

    Starts the FastMCP server with stdio transport.
    """
    try:
        # Run the server with stdio transport (default)
        mcp.run()
    except KeyboardInterrupt:
        print("\nShutting down Gemini MCP Server...")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
