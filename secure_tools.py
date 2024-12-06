from enum import Enum
import json
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OperationType(Enum):
    """Operation types for tool management"""
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    DIR_READ = "dir_read"
    DIR_CREATE = "dir_create"
    CMD_EXECUTE = "cmd_execute"

class ToolManager:
    def __init__(self):
        """Initialize the tool manager with whitelist"""
        # Update paths for tools in new locations
        self.cmd_tool_path = Path('Tools/cmd-tool/cmd-tool.py')
        self.filesystem_path = Path('Tools/filesystem/filesystem.py')
        self.whitelist_file = Path.home() / '.claude_chat' / 'whitelist.json'
        self.whitelist = self.load_whitelist()

    def load_whitelist(self):
        """Load the command whitelist from file"""
        try:
            if self.whitelist_file.exists():
                with open(self.whitelist_file) as f:
                    return json.load(f)
            else:
                # Create default empty whitelist
                self.whitelist_file.parent.mkdir(parents=True, exist_ok=True)
                default_whitelist = {}
                self.save_whitelist(default_whitelist)
                return default_whitelist
        except Exception as e:
            logger.error(f"Error loading whitelist: {e}")
            return {}

    def save_whitelist(self, whitelist):
        """Save the command whitelist to file"""
        try:
            self.whitelist_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.whitelist_file, 'w') as f:
                json.dump(whitelist, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving whitelist: {e}")
            return False

    def check_whitelist(self, command):
        """Check if a command is in the whitelist"""
        base_cmd = command.split()[0].lower()
        return self.whitelist.get(base_cmd, {}).get('approved', False)

    def approve_command(self, command, permanent=False):
        """Add a command to the whitelist"""
        base_cmd = command.split()[0].lower()
        self.whitelist[base_cmd] = {
            'approved': True,
            'permanent': permanent,
            'last_used': None
        }
        self.save_whitelist(self.whitelist)

    def execute_cmd(self, command):
        """Execute a command after checking whitelist"""
        if not command:
            return False, "No command provided"

        base_cmd = command.split()[0].lower()
        
        if base_cmd not in self.whitelist:
            return False, f"Command '{base_cmd}' requires approval. Use approve_command() first."
            
        if not self.whitelist[base_cmd].get('approved', False):
            return False, f"Command '{base_cmd}' is not approved. Use approve_command() first."
            
        try:
            # Execute command using the command-tool service
            import requests
            response = requests.post('http://localhost:5001/execute', 
                                  json={'command': command})
            return True, response.json()
        except Exception as e:
            return False, f"Error executing command: {str(e)}"

    def file_operation(self, operation, path, content=None):
        """Perform a file operation"""
        try:
            # Use the filesystem service for file operations
            import requests
            response = requests.post('http://localhost:5000/mcp', json={
                'type': 'call_tool_request',
                'params': {
                    'name': operation.value,
                    'arguments': {
                        'path': path,
                        'content': content
                    }
                }
            })
            return response.json()
        except Exception as e:
            return f"Error performing file operation: {str(e)}"

    def dir_operation(self, operation, path):
        """Perform a directory operation"""
        try:
            # Use the filesystem service for directory operations
            import requests
            response = requests.post('http://localhost:5000/mcp', json={
                'type': 'call_tool_request',
                'params': {
                    'name': operation.value,
                    'arguments': {
                        'path': path
                    }
                }
            })
            return response.json()
        except Exception as e:
            return f"Error performing directory operation: {str(e)}"
