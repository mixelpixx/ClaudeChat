import logging
import os
import base64
import requests
import time
from anthropic import Anthropic
from secure_tools import ToolManager, OperationType
from config import Config

logger = logging.getLogger(__name__)

class ClaudeAPI:
    def __init__(self):
        logger.info("Initializing ClaudeAPI")
        try:
            self.max_iterations = 10  # Maximum number of conversation turns to prevent infinite loops
            self.config = Config()
            api_key = self.config.get_api_key()
            
            if not api_key:
                raise ValueError("API key not found")
            
            self.client = Anthropic(api_key=api_key)
            self.conversation_history = []
            self.tools = None  # Will be set by GUI
            
            # Server configurations
            self.filesystem_url = 'http://localhost:5000/mcp'  # Filesystem tool endpoint
            self.cmdtool_url = 'http://localhost:5001/execute'  # Command tool endpoint
            self.max_retries = 3  # Maximum number of retry attempts
            self.retry_delay = 2  # Seconds between retries
            
        except Exception as e:
            logger.error(f"Error initializing ClaudeAPI: {e}")
            raise

    def _needs_continuation(self, response_text, tool_result):
        """Determine if the process should continue based on response and tool result"""
        # Check for explicit continuation phrases in the AI's response
        continuation_phrases = [
            "next step",
            "continue",
            "proceed",
            "moving on",
            "following up",
        ]
        
        # Check if the response indicates more steps
        if any(phrase in response_text.lower() for phrase in continuation_phrases):
            return True
            
        # Check if the tool result was successful and incomplete
        if isinstance(tool_result, dict) and tool_result.get('success'):
            if tool_result.get('needs_continuation'):
                return True
                
        return False

    def _format_tool_result_message(self, result):
        """Format tool result for conversation history"""
        if isinstance(result, dict):
            if result.get('success'):
                return {
                    "role": "system",
                    "content": (
                        f"Tool execution successful.\n"
                        f"Result: {result.get('content')}\n"
                        f"You can proceed with the next step."
                    )
                }
            elif result.get('is_error'):
                return {
                    "role": "system",
                    "content": (
                        f"Tool execution failed.\n"
                        f"Error: {result.get('content')}\n"
                        f"Please handle this error or try an alternative approach."
                    )
                }
        
        return {
            "role": "system",
            "content": f"Tool execution completed with result: {str(result)}"
        }

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

            # Initialize variables for the conversation loop
            continue_processing = True
            current_response = ""
            iteration_count = 0
            
            while continue_processing and iteration_count < self.max_iterations:
                iteration_count += 1
                logger.debug(f"Conversation iteration {iteration_count}")

                # Get the response from Claude
                response = self.client.messages.create(
                    model=self.config.get_model(),
                    max_tokens=self.config.get_max_tokens(),
                    messages=self.conversation_history + [{"role": "user", "content": message_content}],
                    system=self.config.get_system_prompt(),
                    tools=self.define_tools(),
                    tool_choice={"type": "auto"}
                )
                
                # Process the response and handle tools
                response_text = ""
                tool_results = []
                continue_processing = False  # Reset for each iteration

                for content in response.content:
                    if content.type == "text":
                        response_text += content.text
                    elif content.type == "tool_use":
                        result = self.handle_tool_use(content)
                        
                        # Handle tool results
                        if result:
                            tool_results.append(result)
                            if isinstance(result, dict):
                                if result.get('is_error'):
                                    response_text += f"\nTool error: {result.get('content')}\n"
                                    continue_processing = False
                                else:
                                    # Format tool result for conversation history
                                    tool_result_msg = self._format_tool_result_message(result)
                                    self.conversation_history.append(tool_result_msg)
                                    
                                    # Check if we need to continue processing
                                    continue_processing = self._needs_continuation(response_text, result)
                                    if continue_processing:
                                        message_content = "Continue with the next step based on the previous result."

                # Add the current exchange to conversation history
                self.conversation_history.append({"role": "user", "content": message_content})
                self.conversation_history.append({"role": "assistant", "content": response_text})
                
                # Accumulate responses
                current_response += response_text + "\n"
                
                # Add tool results to logging
                if tool_results:
                    logger.info(f"Tool results: {tool_results}")
            
            if iteration_count >= self.max_iterations:
                logger.warning("Reached maximum number of conversation iterations")
                current_response += "\nReached maximum number of conversation iterations. Some tasks may be incomplete."
            
            return current_response.strip()
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            raise

    def handle_tool_use(self, tool_use_content):
        """Handle tool use requests from Claude with retry logic and error handling"""
        tool_name = tool_use_content.name
        tool_input = tool_use_content.input
        tool_id = tool_use_content.id
        
        logger.debug(f"Handling tool use: {tool_name}")
        logger.debug(f"Tool input: {tool_input}")
        
        if tool_name in ["read_file", "write_file", "create_directory", "list_directory", "search_files", "get_file_info"]:
            return self._handle_filesystem_operation(tool_name, tool_input, tool_id)
        elif tool_name == "execute_command":
            return self._execute_command_with_retry(tool_input, tool_id)
            
        return {
            "type": "tool_result",
            "tool_use_id": tool_id,
            "content": f"Unknown tool: {tool_name}",
            "is_error": True
        }

    def _handle_filesystem_operation(self, operation, tool_input, tool_id):
        """Handle filesystem operations using MCP protocol"""
        try:
            response = requests.post(
                self.filesystem_url,
                json={
                    "type": "call_tool_request",
                    "params": {
                        "name": operation,
                        "arguments": tool_input
                    }
                }
            )
            
            result = response.json()
            return {
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": result.get("content", ""),
                "is_error": result.get("is_error", False)
            }
        except Exception as e:
            return {
                "type": "tool_result", 
                "tool_use_id": tool_id,
                "content": f"Error performing filesystem operation: {str(e)}",
                "is_error": True
            }

    def _execute_command_with_retry(self, tool_input, tool_id):
        """Execute command with retry logic and human intervention"""
        command = tool_input.get('command')
        working_directory = tool_input.get('working_directory', os.getcwd())
        retries = 0
        last_error = None
        
        while retries < self.max_retries:
            try:
                response = requests.post(
                    self.cmdtool_url,
                    json={
                        'command': command,
                        'working_directory': working_directory
                    },
                    timeout=10
                )
                
                result = response.json()
                logger.debug(f"Command result: {result}")
                
                # Check for success
                if 'output' in result:
                    return {
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": result['output'],
                        "success": True
                    }
                
                # Handle errors
                if 'error' in result:
                    last_error = result['error']
                    if self._should_retry(last_error):
                        retries += 1
                        if retries < self.max_retries:
                            logger.info(f"Retrying command after error: {last_error}")
                            time.sleep(self.retry_delay)
                            continue
                    
                    # Ask for human intervention
                    if self._ask_human_intervention(command, last_error):
                        retries = 0  # Reset retry counter if human wants to continue
                        continue
                    else:
                        break  # Human chose to stop retrying
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"Error executing command: {last_error}")
                retries += 1
                if retries < self.max_retries and self._should_retry(last_error):
                    time.sleep(self.retry_delay)
                    continue
                break
        
        # If we get here, all retries failed
        return {
            "type": "tool_result",
            "tool_use_id": tool_id,
            "content": f"Command failed after {retries} attempts. Last error: {last_error}",
            "is_error": True
        }

    def _should_retry(self, error):
        """Determine if error is retryable"""
        retryable_errors = [
            "connection refused",
            "timeout",
            "temporary failure",
            "resource temporarily unavailable"
        ]
        return any(err in str(error).lower() for err in retryable_errors)

    def _ask_human_intervention(self, command, error):
        """Ask human what to do about error"""
        if not self.tools:
            logger.warning("No tool manager set, cannot ask for human intervention")
            return False
            
        dialog = ErrorInterventionDialog(
            command=command,
            error=error,
            retry_count=self.max_retries
        )
        dialog.exec()
        
        return dialog.should_continue

    def clear_conversation(self):
        self.conversation_history = []

    def set_tool_manager(self, tool_manager):
        """Set the tool manager instance"""
        self.tools = tool_manager

    def define_tools(self):
        """Define available tools for Claude to use"""
        return [
            {
                "name": "read_file",
                "description": "Read the complete contents of a file from the file system. Handles various text encodings and provides detailed error messages if the file cannot be read. Use this tool when you need to examine the contents of a single file. Only works within allowed directories.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The file path to read"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "read_multiple_files",
                "description": "Read multiple files simultaneously. This is more efficient than reading files one by one when you need to analyze or compare multiple files. Each file's content is returned with its path as a reference. Failed reads for individual files won't stop the entire operation. Only works within allowed directories.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "paths": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of file paths to read"
                        }
                    },
                    "required": ["paths"]
                }
            },
            {
                "name": "write_file", 
                "description": "Create a new file or overwrite an existing file with new content. Use with caution as it will overwrite existing files without warning. Handles text content with proper encoding. Only works within allowed directories.",
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
                "name": "edit_file",
                "description": "Make selective edits using advanced pattern matching and formatting. Features line-based and multi-line content matching, whitespace normalization with indentation preservation, multiple simultaneous edits with correct positioning, git-style diff output with context, and preview changes with dry run mode.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File to edit"
                        },
                        "edits": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "oldText": {
                                        "type": "string",
                                        "description": "Text to search for (can be substring)"
                                    },
                                    "newText": {
                                        "type": "string",
                                        "description": "Text to replace with"
                                    }
                                },
                                "required": ["oldText", "newText"]
                            }
                        },
                        "dryRun": {
                            "type": "boolean",
                            "description": "Preview changes without applying",
                            "default": False
                        }
                    },
                    "required": ["path", "edits"]
                }
            },
            {
                "name": "create_directory",
                "description": "Create a new directory or ensure a directory exists. Can create multiple nested directories in one operation. If the directory already exists, this operation will succeed silently. Only works within allowed directories.",
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
                "name": "list_directory",
                "description": "List all files and directories in a specified path. Results include [FILE] and [DIR] prefixes to distinguish types. Only works within allowed directories.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The directory path to list"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "move_file",
                "description": "Move or rename files and directories. Can move files between directories and rename them in a single operation. If the destination exists, the operation will fail. Works across different directories and can be used for simple renaming within the same directory. Both source and destination must be within allowed directories.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "source": {
                            "type": "string",
                            "description": "Source file/directory path"
                        },
                        "destination": {
                            "type": "string",
                            "description": "Destination file/directory path"
                        }
                    },
                    "required": ["source", "destination"]
                }
            },
            {
                "name": "search_files",
                "description": "Recursively search for files and directories matching a pattern. Searches through all subdirectories from the starting path. The search is case-insensitive and matches partial names. Returns full paths to all matching items. Great for finding files when you don't know their exact location. Only searches within allowed directories.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Starting directory path"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "Search pattern to match"
                        }
                    },
                    "required": ["path", "pattern"]
                }
            },
            {
                "name": "list_allowed_directories",
                "description": "Returns the list of directories that this server is allowed to access. Use this to understand which directories are available before trying to access files.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
