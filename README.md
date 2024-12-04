# Claude AI Assistant with Tool Calling & GUI

A sophisticated desktop application that provides a graphical interface for interacting with Claude AI, featuring secure tool calling capabilities and filesystem operations.

## Installation

1. **Prerequisites**
   - Python 3.8 or higher
   - PyQt6
   - Anthropic API key

2. **Setup**
   ```bash
   # Install required packages
   pip install anthropic PyQt6 flask flask-cors psutil

   # Configure your API key
   # Either set environment variable:
   export ANTHROPIC_API_KEY='your-api-key'
   # Or add to ~/.claude_chat/config.json
   ```

## Usage

1. **Starting the Application**
   ```bash
   # Start the command tool service
   python cmd-tool/cmd-tool.py
   
   # Start the filesystem service (specify allowed directories)
   python filesystem/filesystem.py /path/to/allowed/directory
   
   # Launch the GUI
   python gui.py
   ```

2. **Chat Interface**
   - Type messages in the input field
   - View conversation history in the main window
   - Use the file browser to navigate directories
   - Access tools through the tools panel

## Available Tools

### Command Execution

### Filesystem Operations

## Safety Features

1. **Command Security**
   - Whitelist-based command execution
   - Approval required for potentially dangerous commands
   - Process isolation and monitoring
   - Automatic cleanup of old processes

2. **Filesystem Security**
   - Path validation against allowed directories
   - Secure file operations
   - Permission checking
   - Directory access control

## Configuration

Configuration file location: `~/.claude_chat/config.json`
