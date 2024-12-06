import logging
import os
import base64
import requests
from anthropic import Anthropic
from secure_tools import ToolManager, OperationType
from config import Config

logger = logging.getLogger(__name__)

class ClaudeAPI:
    def __init__(self):
        logger.info("Initializing ClaudeAPI")
        try:
            self.config = Config()
            api_key = self.config.get_api_key()
            
            if not api_key:
                raise ValueError("API key not found")
            
            self.client = Anthropic(api_key=api_key)
            self.conversation_history = []
            self.tools = None  # Will be set by GUI
        except Exception as e:
            logger.error(f"Error initializing ClaudeAPI: {e}")
            raise

    def send_message(self, message, image_path=None):
        logger.info("Sending message to Claude")
        try:
            # Prepare the message content
            message_content = message
            if image_path:
                with open(image_path, "rb") as img:
                    image_data = base64.b64encode(img.read()).decode()
                    message_content = [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data
                            }
                        },
                        {"type": "text", "text": message}
                    ]

            response = self.client.messages.create(
                model=self.config.get_model(),
                max_tokens=self.config.get_max_tokens(),
                messages=self.conversation_history + [{"role": "user", "content": message_content}],
                system=self.config.get_system_prompt(),
                tools=self.define_tools(),
                tool_choice={"type": "auto"}
            )
            
            response_text = ""
            for content in response.content:
                if content.type == "text":
                    response_text += content.text
                elif content.type == "tool_use":
                    tool_result = self.handle_tool_use(content)
                    response_text += f"\nTool use result: {tool_result}\n"

            self.conversation_history.append({"role": "user", "content": message_content})
            self.conversation_history.append({"role": "assistant", "content": response_text})
            return response_text
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            raise
            
    def handle_tool_use(self, tool_use_content):
        """Handle tool use requests from Claude with enhanced tool support"""
        tool_name = tool_use_content.name
        tool_input = tool_use_content.input
        tool_id = tool_use_content.id
        
        if tool_name == "execute_command":
            command = tool_input.get('command')
            working_directory = tool_input.get('working_directory', os.getcwd())
            
            if not command:
                return "Error: No command provided"
            
            try:
                response = requests.post('http://localhost:5000/execute', json={
                    'command': command,
                    'working_directory': working_directory
                })
                
                if response.status_code == 202:  # Command requires approval
                    # Show approval dialog
                    if self.handle_command_approval(command):
                        # Retry command after approval
                        response = requests.post('http://localhost:5000/execute', json={
                            'command': command,
                            'working_directory': working_directory
                        })
                    else:
                        return {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": "Command requires approval: " + command,
                            "is_error": True
                        }
                
                result = response.json()
                if result.get('status') == 'started':
                    pid = result.get('pid')
                    return {
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": f"Command started with PID: {pid}"
                    }
            except Exception as e:
                return {
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": f"Error executing command: {str(e)}",
                    "is_error": True
                }
        
        elif tool_name == "filesystem_operation":
            operation = tool_input.get('operation')
            path = tool_input.get('path')
            content = tool_input.get('content')
            pattern = tool_input.get('pattern')
            
            try:
                response = requests.post('http://localhost:5000/mcp', json={
                    'type': 'call_tool_request',
                    'params': {
                        'name': operation,
                        'arguments': {
                            'path': path,
                            'content': content,
                            'pattern': pattern
                        }
                    }
                })
                
                result = response.json()
                return {
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": result.get('content', 'No result')
                }
            except Exception as e:
                return {
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": f"Error performing filesystem operation: {str(e)}",
                    "is_error": True
                }
        
        else:
            return f"Unsupported tool: {tool_name}"

    def handle_command_approval(self, command):
        """Handle command approval through GUI dialog"""
        dialog = CommandApprovalDialog(command)
        dialog.exec()
        
        result = dialog.result
        if result == "deny":
            return False
        
        if result == "approve_always":
            # Add to whitelist permanently
            base_cmd = command.split()[0].lower()
            self.tools.approve_command(base_cmd, permanent=True)
        elif result == "approve":
            # Add to whitelist temporarily
            base_cmd = command.split()[0].lower()
            self.tools.approve_command(base_cmd, permanent=False)
            
        return True

    def clear_conversation(self):
        self.conversation_history = []

    def set_tool_manager(self, tool_manager):
        """Set the tool manager instance"""
        self.tools = tool_manager

    def define_tools(self):
        """Define available tools for Claude to use"""
        return [
            {
                "name": "execute_command",
                "description": "Execute a command in the command prompt or terminal using the cmd-tool service. This tool allows running system commands with controlled execution and output retrieval.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string", 
                            "description": "The command to execute. Must be a valid system command."
                        },
                        "working_directory": {
                            "type": "string",
                            "description": "Optional working directory for command execution. Defaults to current directory if not specified."
                        }
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "filesystem_operation",
                "description": "Perform various file system operations using the secure filesystem service. Supports reading, writing, creating, and searching files and directories with strict security controls.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["read_file", "write_file", "create_directory", "list_directory", "search_files", "get_file_info"],
                            "description": "The type of filesystem operation to perform."
                        },
                        "path": {"type": "string", "description": "The file or directory path for the operation"},
                        "content": {"type": "string", "description": "Optional content for write operations"},
                        "pattern": {"type": "string", "description": "Optional search pattern for search operations"}
                    },
                    "required": ["operation", "path"]
                }
            }
        ]
