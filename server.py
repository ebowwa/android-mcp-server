import os
import sys

import yaml
from mcp.server.fastmcp import FastMCP, Image

from adbdevicemanager import AdbDeviceManager

CONFIG_FILE = "config.yaml"
CONFIG_FILE_EXAMPLE = "config.yaml.example"

# Load config (make config file optional)
config = {}
device_name = None

if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE) as f:
            config = yaml.safe_load(f.read()) or {}
        device_config = config.get("device", {})
        configured_device_name = device_config.get(
            "name") if device_config else None

        # Support multiple ways to specify auto-selection:
        # 1. name: null (None in Python)
        # 2. name: "" (empty string)
        # 3. name field completely missing
        if configured_device_name and configured_device_name.strip():
            device_name = configured_device_name.strip()
            print(f"Loaded config from {CONFIG_FILE}")
            print(f"Configured device: {device_name}")
        else:
            print(f"Loaded config from {CONFIG_FILE}")
            print(
                "No device specified in config, will auto-select if only one device connected")
    except Exception as e:
        print(f"Error loading config file {CONFIG_FILE}: {e}", file=sys.stderr)
        print(
            f"Please check the format of your config file or recreate it from {CONFIG_FILE_EXAMPLE}", file=sys.stderr)
        sys.exit(1)
else:
    print(
        f"Config file {CONFIG_FILE} not found, using auto-selection for device")

# Initialize MCP and device manager
# AdbDeviceManager will handle auto-selection if device_name is None
mcp = FastMCP("android")
deviceManager = AdbDeviceManager(device_name)


@mcp.tool()
def get_packages() -> str:
    """
    Get all installed packages on the device
    Returns:
        str: A list of all installed packages on the device as a string
    """
    result = deviceManager.get_packages()
    return result


@mcp.tool()
def execute_adb_shell_command(command: str) -> str:
    """Executes an ADB command and returns the output or an error.
    Args:
        command (str): The ADB shell command to execute
    Returns:
        str: The output of the ADB command
    """
    result = deviceManager.execute_adb_shell_command(command)
    return result


@mcp.tool()
def get_uilayout() -> str:
    """
    Retrieves information about clickable elements in the current UI.
    Returns a formatted string containing details about each clickable element,
    including its text, content description, bounds, and center coordinates.

    Returns:
        str: A formatted list of clickable elements with their properties
    """
    result = deviceManager.get_uilayout()
    return result


@mcp.tool()
def get_screenshot() -> Image:
    """Takes a screenshot of the device and returns it.
    Returns:
        Image: the screenshot
    """
    deviceManager.take_screenshot()
    return Image(path="compressed_screenshot.png")


@mcp.tool()
def get_package_action_intents(package_name: str) -> list[str]:
    """
    Get all non-data actions from Activity Resolver Table for a package
    Args:
        package_name (str): The name of the package to get actions for
    Returns:
        list[str]: A list of all non-data actions from the Activity Resolver Table for the package
    """
    result = deviceManager.get_package_action_intents(package_name)
    return result


# ===== TERMUX INTEGRATION ABSTRACTION =====

class TermuxManager:
    """Clean abstraction for Termux interactions without UI friction."""

    def __init__(self, device_manager):
        self.device_manager = device_manager
        self.shared_dir = "/data/local/tmp/termux_bridge"
        self.termux_home = "/data/data/com.termux/files/home"

    def _ensure_bridge(self):
        """Create shared directory for file operations."""
        self.device_manager.device.shell(f"mkdir -p {self.shared_dir}")
        self.device_manager.device.shell(f"chmod 777 {self.shared_dir}")

    def _execute_via_api(self, command: str) -> str:
        """Execute command using Termux API for clean, direct execution."""
        try:
            # Execute command via Termux API broadcast
            broadcast_cmd = f"am broadcast -a com.termux.api.execute_command --es script '{command}'"
            result = self.device_manager.device.shell(broadcast_cmd)

            # Give it a moment to execute
            import time
            time.sleep(0.5)

            # For now, return the broadcast result
            # In a more complete implementation, we could read from a result file
            return f"Command executed via Termux API: {result}"

        except Exception as e:
            # Fallback to bridge method if API fails
            return self._execute_via_bridge_fallback(command)

    def _execute_via_bridge_fallback(self, command: str) -> str:
        """Fallback method using shared directory bridge."""
        self._ensure_bridge()
        cmd_file = f"{self.shared_dir}/cmd.sh"
        result_file = f"{self.shared_dir}/result.txt"

        self.device_manager.device.shell(f"echo '{command}' > {cmd_file}")
        self.device_manager.device.shell(f"chmod +x {cmd_file}")
        self.device_manager.device.shell(f"{cmd_file} > {result_file} 2>&1")
        result = self.device_manager.device.shell(f"cat {result_file} 2>/dev/null || echo 'No output'")
        self.device_manager.device.shell(f"rm -f {cmd_file} {result_file}")

        return result


# Initialize Termux manager
termux = TermuxManager(deviceManager)


@mcp.tool()
def termux_exec(command: str) -> str:
    """
    Execute a command directly in a Termux environment without UI friction.
    This bypasses the need for screen interaction and keyboard input simulation.

    Args:
        command (str): The command to execute in Termux environment

    Returns:
        str: Command output and result
    """
    try:
        # Try direct ADB execution first (if command doesn't need Termux specifically)
        if any(cmd in command for cmd in ['ls', 'cat', 'echo', 'pwd', 'date', 'whoami']):
            return f"ADB: {deviceManager.execute_adb_shell_command(command)}"

        # For Termux-specific commands, use Termux API
        result = termux._execute_via_api(command)
        return f"Termux: {result}"

    except Exception as e:
        return f"Error executing command: {str(e)}"


@mcp.tool()
def termux_write_file(filename: str, content: str) -> str:
    """
    Write content to a file in Termux accessible directory.

    Args:
        filename (str): Target filename (relative to shared directory)
        content (str): File content to write

    Returns:
        str: Success confirmation with file path
    """
    try:
        termux._ensure_bridge()
        file_path = f"{termux.shared_dir}/{filename}"

        # Write content using echo (handles multiline content)
        deviceManager.device.shell(f"echo '{content}' > {file_path}")

        return f"File written to: {file_path}"

    except Exception as e:
        return f"Error writing file: {str(e)}"


@mcp.tool()
def termux_read_file(filename: str) -> str:
    """
    Read content from a file in Termux accessible directory.

    Args:
        filename (str): Target filename (relative to shared directory)

    Returns:
        str: File content
    """
    try:
        termux._ensure_bridge()
        file_path = f"{termux.shared_dir}/{filename}"

        content = deviceManager.device.shell(f"cat {file_path} 2>/dev/null || echo 'File not found'")

        return content

    except Exception as e:
        return f"Error reading file: {str(e)}"


@mcp.tool()
def termux_session_start() -> str:
    """
    Initialize a clean Termux session for persistent interactions.
    Launches Termux and prepares it for command execution.

    Returns:
        str: Session status and ready confirmation
    """
    try:
        # Launch Termux in background
        result = deviceManager.device.shell("am start -n com.termux/.app.TermuxActivity")

        # Initialize bridge
        termux._ensure_bridge()

        # Create session marker
        deviceManager.device.shell(f"echo 'Session started at $(date)' > {termux.shared_dir}/session.txt")

        return f"Termux session started. Bridge directory: {termux.shared_dir}"

    except Exception as e:
        return f"Error starting session: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
