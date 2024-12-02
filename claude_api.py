import logging
import os
import base64
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
        """Handle tool use requests from Claude"""
        tool_name = tool_use_content.name
        tool_input = tool_use_content.input
        tool_id = tool_use_content.id
        
        if tool_name == "execute_command":
            command = tool_input.get('command')
            if not command:
                return "Error: No command provided"
            success, result = self.tools.execute_cmd(command)
            return {
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": result,
                "is_error": not success
            }

        elif tool_name == "read_file":
            path = tool_input.get('path')
            if not path:
                return "Error: No file path provided"
            return self.tools.file_operation(OperationType.FILE_READ, path)
            
        elif tool_name == "write_file":
            path = tool_input.get('path')
            content = tool_input.get('content')
            if not path or not content:
                return "Error: No file path or content provided"
            return self.tools.file_operation(OperationType.FILE_WRITE, path, content)
            
        elif tool_name == "create_file":
            path = tool_input.get('path')
            if not path:
                return "Error: No file path provided"
            return self.tools.file_operation(OperationType.FILE_CREATE, path)
            
        elif tool_name == "edit_file":
            path = tool_input.get('path')
            content = tool_input.get('content')
            if not path or not content:
                return "Error: No file path or content provided"
            return self.tools.file_operation(OperationType.FILE_EDIT, path, content)
            
        elif tool_name == "read_directory":
            path = tool_input.get('path')
            if not path:
                return "Error: No directory path provided"
            return self.tools.dir_operation(OperationType.DIR_READ, path)
            
        elif tool_name == "create_directory":
            path = tool_input.get('path')
            if not path:
                return "Error: No directory path provided"
            return self.tools.dir_operation(OperationType.DIR_CREATE, path)
            
        elif tool_name == "edit_directory":
            path = tool_input.get('path')
            if not path:
                return "Error: No directory path provided"
            return self.tools.dir_operation(OperationType.DIR_EDIT, path)
            
        else:
            return f"Unsupported tool: {tool_name}"

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
                "description": "Execute a command in the command prompt or terminal. This tool should be used when needing to run system commands.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "The command to execute. Must be a valid system command."},
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "read_file",
                "description": "Read the contents of a file at the specified path",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The file path to read from"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "write_file",
                "description": "Write to a file at the specified path",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The file path to write to"
                        },
                        "content": {
                            "type": "string",
                            "description": "The content to write to the file"
                        }
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "create_file",
                "description": "Create a new file at the specified path",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The file path to create"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "edit_file",
                "description": "Edit a file at the specified path",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The file path to edit"
                        },
                        "content": {
                            "type": "string",
                            "description": "The new content to write to the file"
                        }
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "read_directory",
                "description": "Read the contents of a directory at the specified path",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The directory path to read from"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "create_directory",
                "description": "Create a new directory at the specified path",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The directory path to create"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "edit_directory",
                "description": "Edit a directory at the specified path",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The directory path to edit"
                        }
                    },
                    "required": ["path"]
                }
            }
        ]
