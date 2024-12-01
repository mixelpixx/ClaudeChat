# claude_api.py
import anthropic
import base64
import httpx
import json
import os
import logging
from config import Config

# Configure basic logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ClaudeAPI:
    def __init__(self):
    logger.info("Initializing ClaudeAPI")
    self.config = Config()
    self.api_key = self.config.get_api_key()
    if not self.api_key:
        logger.error("No API key found in config or environment")
        raise ValueError("No API key found. Please set your API key in the settings.")
    self.client = anthropic.Anthropic(api_key=self.api_key)
    self.conversation_history = []
    self.tools = None  # Will be set by the GUI

def send_message(self, message, image_path=None):
    if image_path:
        try:
            logger.debug(f"Processing image: {image_path}")
            image_media_type = image_path.split('.')[-1]
            if image_media_type not in ['jpeg', 'jpg', 'png', 'gif', 'webp']:
                raise ValueError("Unsupported image type. Please use JPEG, PNG, GIF, or WEBP.")
            
            with open(image_path, 'rb') as image_file:                    
                image_data = base64.b64encode(image_file.read()).decode("utf-8")
            
            user_message = {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": f"image/{image_media_type}",
                            "data": image_data,
                        },
                    },
                   {"type": "text", "text": message} 
                ] if message else []
            }
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return f"Error processing image: {e}"
    else:
        user_message = {"role": "user", "content": message}

    self.conversation_history.append(user_message)

    logger.debug("Sending message to Claude API")
    try:
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=self.conversation_history,
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "execute_command",
                        "description": "Execute a command in Windows command prompt",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "command": {
                                    "type": "string",
                                    "description": "The command to execute"
                                }
                            },
                            "required": ["command"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "file_operation",
                        "description": "Perform file operations (read/write/create/edit)",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "operation": {
                                    "type": "string",
                                    "enum": ["read", "write", "create", "edit"],
                                    "description": "The type of operation to perform"
                                },
                                "path": {
                                    "type": "string",
                                    "description": "The file path"
                                },
                                "content": {
                                    "type": "string",
                                    "description": "Content for write/edit operations"
                                }
                            },
                            "required": ["operation", "path"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "dir_operation",
                        "description": "Perform directory operations (read/create/edit)",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "operation": {
                                    "type": "string",
                                    "enum": ["read", "create", "edit"],
                                    "description": "The type of operation to perform"
                                },
                                "path": {
                                    "type": "string",
                                    "description": "The directory path"
                                }
                            },
                            "required": ["operation", "path"]
                        }
                    }
                }
            ]
        )
        logger.debug("Received response from Claude API")
        self.conversation_history.append(response.to_dict())
        
        return self.extract_content(response)
    except Exception as e:
        logger.error(f"Error communicating with Claude API: {str(e)}")
        raise

def extract_content(self, response):
    content = ""
    for part in response.content:
        if part.type == "text":
            content += part.text
        elif part.type == "tool_use":
            if not self.tools:
                content += f"Tool use requested but tools not available: {part.name}\n"
                continue
                
            if part.name == "execute_command":
                success, result = self.tools.execute_cmd(part.parameters["command"])
            elif part.name == "file_operation":
                op_type = OperationType[f"FILE_{part.parameters['operation'].upper()}"]
                success, result = self.tools.file_operation(
                    op_type,
                    part.parameters["path"],
                    part.parameters.get("content")
                )
            elif part.name == "dir_operation":
                op_type = OperationType[f"DIR_{part.parameters['operation'].upper()}"]
                success, result = self.tools.dir_operation(
                    op_type,
                    part.parameters["path"]
                )
            
            content += f"Tool result ({'success' if success else 'failed'}): {result}\n"
            
    return content