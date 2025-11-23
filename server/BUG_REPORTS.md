# Android MCP Server - Bug Reports & Issues

## Issue #1: MCP Tool Responses Not Displayed to Users

### Description
The Android MCP server tools (particularly `execute_adb_shell_command`) are configured to return output, but the responses are not being displayed to users in Claude conversations.

### Expected Behavior
- `execute_adb_shell_command("ls -la")` should return the directory listing as text
- Users should see command output directly in Claude's responses
- Other tools like `get_packages()` should show package lists

### Actual Behavior
- Tools execute successfully on the Android device
- No command output is displayed to users
- Users must take screenshots to see results (workaround)

### Technical Analysis

#### Code Configuration (✅ Correct)
```python
@mcp.tool()
def execute_adb_shell_command(command: str) -> str:
    """Executes an ADB command and returns the output or an error.
    Returns:
        str: The output of the ADB command
    """
    result = deviceManager.execute_adb_shell_command(command)
    return result  # Line 71 - Should return output
```

- Tool properly decorated with `@mcp.tool()`
- Return type correctly specified as `str`
- Explicit `return result` statement
- Documentation confirms output should be returned

#### ADB Device Manager Implementation
```python
def execute_adb_shell_command(self, command: str) -> str:
    """Executes an ADB command and returns the output."""
    if command.startswith("adb shell "):
        command = command[10:]
    elif command.startswith("adb "):
        command = command[4:]
    result = self.device.shell(command)
    return result  # Line 123 - Returns ADB output
```

- Function returns `self.device.shell(command)` result
- Should capture and return all command output

### Potential Root Causes

#### 1. Claude MCP Response Handling
- Claude may be filtering out tool responses from user display
- MCP responses might be available internally but not shown in conversation
- Could be a design decision to reduce conversation noise

#### 2. FastMCP Framework Configuration
- The FastMCP framework might have response filtering
- Tool outputs might need explicit configuration to be displayed
- Error handling could be swallowing responses

#### 3. ADB Output Encoding/Format Issues
- ADB output might contain characters that break MCP response parsing
- Binary data or special characters could cause response truncation
- Output length limits might be exceeded

### Investigation Steps

#### Step 1: Test Simple Commands
```bash
# Test with minimal output
execute_adb_shell_command("echo 'hello world'")

# Test with known output format
execute_adb_shell_command("whoami")

# Test with empty output
execute_adb_shell_command("true")
```

#### Step 2: Check MCP Logs
- Look at MCP server logs for response handling
- Check if output is being captured but not forwarded
- Look for errors in response processing

#### Step 3: Compare Working vs Non-working Tools
- `get_screenshot()` works (returns Image type)
- `get_packages()` status unknown
- `get_uilayout()` status unknown
- Compare response types and handling

#### Step 4: FastMCP Framework Analysis
- Check FastMCP documentation for response display configuration
- Look for response filtering or output formatting options
- Investigate if tool responses need explicit user display flags

### Workarounds Currently Used

1. **Screenshot Method** - Take screenshots of terminal output
2. **Manual Verification** - Use `adb shell` directly from Mac
3. **Alternative Tools** - Use other MCP tools that return different data types

### Impact
- Reduces usability of Android MCP for automation
- Forces users to use screenshots for basic command output
- Limits practical development workflows
- Makes debugging difficult

### Files Referenced
- `/Users/ebowwa/android-mcp-server/server.py` (Lines 62-71)
- `/Users/ebowwa/android-mcp-server/adbdevicemanager.py` (Lines 116-123)

### Environment
- Android MCP Server: Python with FastMCP framework
- Device: INMO Air3 AR glasses (YM00FCE8100706)
- Claude Code: Latest version with MCP support
- Platform: macOS Darwin 24.5.0

### Priority
**HIGH** - This is a core functionality issue that significantly impacts the usability of the Android MCP server for automation and development workflows.

### Next Steps
1. Test with simple commands to verify basic response functionality
2. Check MCP server logs for response handling details
3. Investigate FastMCP framework configuration options
4. Consider alternative response handling approaches if needed

---

*Report created: 2025-11-19*
*Status: Open Investigation*