import logging
import os
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
            
            self.client = Anthropic(api_key=api_key, max_retries=3)
            self.conversation_history = []
            self.tools = None  # Will be set by GUI
        except Exception as e:
            logger.error(f"Error initializing ClaudeAPI: {e}")
            raise

    def send_message(self, message, image_path=None):
        logger.info("Sending message to Claude")
        try:
            if image_path:
                # Handle image upload logic here
                pass
            else:
                response = self.client.messages.create(
                    model=self.config.get_model(),
                    max_tokens=self.config.get_max_tokens(),
                    messages=[{"role": "user", "content": message}],
                    system=self.config.get_system_prompt()
                )
            
            response_text = ""
            for content in response.content:
                if content.type == "text":
                    response_text += content.text
                elif content.type == "tool_use":
                    tool_result = self.handle_tool_use(content)
                    response_text += f"\nTool use result: {tool_result}\n"

            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": response_text})
            return response_text
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            raise
            
    def handle_tool_use(self, tool_use_content):
        """Handle tool use requests from Claude"""
        tool_name = tool_use_content.tool_name
        tool_input = tool_use_content.tool_input

        if tool_name == "execute_command":
            success, result = self.tools.execute_cmd(tool_input)
        elif tool_name == "read_file":
            success, result = self.tools.file_operation(OperationType.FILE_READ, tool_input)
        elif tool_name == "write_file":
            success, result = self.tools.file_operation(OperationType.FILE_WRITE, tool_input['path'], tool_input['content'])
        elif tool_name == "create_file":
            success, result = self.tools.file_operation(OperationType.FILE_CREATE, tool_input)
        elif tool_name == "edit_file":
            success, result = self.tools.file_operation(OperationType.FILE_EDIT, tool_input['path'], tool_input['content'])
        elif tool_name == "read_directory":
            success, result = self.tools.dir_operation(OperationType.DIR_READ, tool_input)
        elif tool_name == "create_directory":
            success, result = self.tools.dir_operation(OperationType.DIR_CREATE, tool_input)
        elif tool_name == "edit_directory":
            success, result = self.tools.dir_operation(OperationType.DIR_EDIT, tool_input)
        else:
            return f"Unsupported tool: {tool_name}"

        if success:
            return result
        else:
            return f"Error executing {tool_name}: {result}"

    def clear_conversation(self):
        self.conversation_history = []

    def set_tool_manager(self, tool_manager):
        """Set the tool manager instance"""
        self.tools = tool_manager
