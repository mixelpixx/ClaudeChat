from flask import Flask, request, jsonify
import os
from pathlib import Path
import sys
from typing import List, Dict, Any, Optional
import shutil
from datetime import datetime
import json
import stat

app = Flask(__name__)

class FileInfo:
    def __init__(self, path: str):
        stats = os.stat(path)
        self.size = stats.st_size
        self.created = datetime.fromtimestamp(stats.st_ctime)
        self.modified = datetime.fromtimestamp(stats.st_mtime)
        self.accessed = datetime.fromtimestamp(stats.st_atime)
        self.isDirectory = os.path.isdir(path)
        self.isFile = os.path.isfile(path)
        self.permissions = stat.filemode(stats.st_mode)
    
    def to_dict(self) -> Dict:
        return {
            "size": self.size,
            "created": self.created.isoformat(),
            "modified": self.modified.isoformat(),
            "accessed": self.accessed.isoformat(),
            "isDirectory": self.isDirectory,
            "isFile": self.isFile,
            "permissions": self.permissions
        }

class SecurityValidator:
    def __init__(self, allowed_directories: List[str]):
        self.allowed_directories = [self._normalize_path(Path(d).resolve()) for d in allowed_directories]
    
    def _normalize_path(self, p: str) -> str:
        return str(Path(p).resolve()).lower()
    
    def _expand_home(self, filepath: str) -> str:
        if filepath.startswith('~/') or filepath == '~':
            return str(Path.home() / filepath[2:])
        return filepath
    
    def validate_path(self, requested_path: str) -> str:
        """Validate and resolve the requested path against allowed directories."""
        expanded_path = self._expand_home(requested_path)
        absolute_path = Path(expanded_path).resolve()
        normalized_requested = self._normalize_path(absolute_path)
        
        if not any(normalized_requested.startswith(allowed_dir) 
                  for allowed_dir in self.allowed_directories):
            raise ValueError(f"Access denied - path outside allowed directories: {absolute_path}")
        
        return str(absolute_path)

class MCPServer:
    def __init__(self, allowed_directories: List[str]):
        self.validator = SecurityValidator(allowed_directories)
        self.tools = self._initialize_tools()
    
    def _initialize_tools(self) -> Dict:
        return {
            "read_file": {
                "name": "read_file",
                "description": "Read the complete contents of a file from the file system.",
                "handler": self.read_file
            },
            "read_multiple_files": {
                "name": "read_multiple_files",
                "description": "Read the contents of multiple files simultaneously.",
                "handler": self.read_multiple_files
            },
            "write_file": {
                "name": "write_file",
                "description": "Create a new file or overwrite an existing file.",
                "handler": self.write_file
            },
            "create_directory": {
                "name": "create_directory",
                "description": "Create a new directory or ensure a directory exists.",
                "handler": self.create_directory
            },
            "list_directory": {
                "name": "list_directory",
                "description": "Get a detailed listing of all files and directories.",
                "handler": self.list_directory
            },
            "move_file": {
                "name": "move_file",
                "description": "Move or rename files and directories.",
                "handler": self.move_file
            },
            "search_files": {
                "name": "search_files",
                "description": "Recursively search for files and directories matching a pattern.",
                "handler": self.search_files
            },
            "get_file_info": {
                "name": "get_file_info",
                "description": "Retrieve detailed metadata about a file or directory.",
                "handler": self.get_file_info
            },
            "list_allowed_directories": {
                "name": "list_allowed_directories",
                "description": "Returns the list of directories that this server is allowed to access.",
                "handler": self.list_allowed_directories
            }
        }

    def read_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            path = self.validator.validate_path(args['path'])
            with open(path, 'r') as f:
                content = f.read()
            return {"content": [{"type": "text", "text": content}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}
    
    def read_multiple_files(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            results = []
            for file_path in args['paths']:
                try:
                    valid_path = self.validator.validate_path(file_path)
                    with open(valid_path, 'r') as f:
                        content = f.read()
                    results.append(f"{file_path}:\n{content}")
                except Exception as e:
                    results.append(f"{file_path}: Error - {str(e)}")
            
            return {"content": [{"type": "text", "text": "\n---\n".join(results)}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}
    
    def write_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            path = self.validator.validate_path(args['path'])
            with open(path, 'w') as f:
                f.write(args['content'])
            return {"content": [{"type": "text", "text": f"Successfully wrote to {args['path']}"}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}
    
    def create_directory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            path = self.validator.validate_path(args['path'])
            os.makedirs(path, exist_ok=True)
            return {"content": [{"type": "text", "text": f"Successfully created directory {args['path']}"}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}

    def list_directory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            path = self.validator.validate_path(args['path'])
            entries = []
            for entry in os.listdir(path):
                full_path = os.path.join(path, entry)
                entry_type = "[DIR]" if os.path.isdir(full_path) else "[FILE]"
                entries.append(f"{entry_type} {entry}")
            return {"content": [{"type": "text", "text": "\n".join(entries)}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}

    def move_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            source = self.validator.validate_path(args['source'])
            destination = self.validator.validate_path(args['destination'])
            shutil.move(source, destination)
            return {
                "content": [{"type": "text", "text": f"Successfully moved {args['source']} to {args['destination']}"}]
            }
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}

    def search_files(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            root_path = self.validator.validate_path(args['path'])
            pattern = args['pattern'].lower()
            results = []

            for root, _, files in os.walk(root_path):
                try:
                    # Validate each directory we traverse
                    self.validator.validate_path(root)
                    
                    # Check directory name
                    if pattern in os.path.basename(root).lower():
                        results.append(root)
                    
                    # Check files
                    for file in files:
                        if pattern in file.lower():
                            full_path = os.path.join(root, file)
                            results.append(full_path)
                except Exception:
                    # Skip invalid paths during search
                    continue

            return {
                "content": [{"type": "text", "text": "\n".join(results) if results else "No matches found"}]
            }
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}

    def get_file_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            path = self.validator.validate_path(args['path'])
            info = FileInfo(path)
            return {
                "content": [{"type": "text", "text": "\n".join(
                    f"{key}: {value}" for key, value in info.to_dict().items()
                )}]
            }
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}

    def list_allowed_directories(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return {
                "content": [{"type": "text", "text": "Allowed directories:\n" + 
                           "\n".join(self.validator.allowed_directories)}]
            }
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}

def create_server(allowed_directories):
    return MCPServer(allowed_directories)

@app.route('/mcp', methods=['POST'])
def mcp_handler():
    data = request.json
    if data.get('type') == 'list_tools_request':
        return list_tools()
    elif data.get('type') == 'call_tool_request':
        return call_tool(data)
    else:
        return jsonify({"error": "Invalid request type"}), 400

def list_tools():
    tools = server.tools
    return jsonify({
        "tools": [
            {
                "name": tool["name"],
                "description": tool["description"],
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            } for tool in tools.values()
        ]
    })

def call_tool(data):
    try:
        params = data.get('params', {})
        tool_name = params.get('name')
        arguments = params.get('arguments', {})
        
        if tool_name not in server.tools:
            return jsonify({
                "content": [{"type": "text", "text": f"Error: Unknown tool {tool_name}"}],
                "isError": True
            }), 400
        
        result = server.tools[tool_name]["handler"](arguments)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "isError": True
        }), 500

def main():
    if len(sys.argv) < 2:
        print("Usage: python filesystem.py <allowed-directory> [additional-directories...]")
        sys.exit(1)
    
    allowed_directories = sys.argv[1:]
    global server
    server = create_server(allowed_directories)
    print("Secure MCP Filesystem Server running on http://127.0.0.1:5000")
    print("Allowed directories:", allowed_directories)
    app.run(debug=False)

if __name__ == '__main__':
    main()
