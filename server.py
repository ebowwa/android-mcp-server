#!/usr/bin/env python3
"""
Android MCP Server Entry Point

Wrapper script to maintain backward compatibility after restructuring.
"""

import sys
import os

# Add server directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

# Import and run the actual server
from server import mcp

if __name__ == "__main__":
    print("Android MCP Server starting from wrapper...")
    mcp.run()