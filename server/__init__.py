"""
Android MCP Server

A comprehensive MCP server for Android device automation with Termux integration.
Provides clean abstractions for device control, file operations, and command execution.
"""

from .server import *

__version__ = "0.2.0"
__all__ = ["server", "adbdevicemanager"]