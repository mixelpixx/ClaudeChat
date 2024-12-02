import subprocess
import os
import json
from pathlib import Path
import logging
from PyQt6.QtWidgets import QMessageBox
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class OperationType(Enum):
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_EDIT = "file_edit"
    FILE_CREATE = "file_create"
    DIR_READ = "dir_read"
    DIR_WRITE = "dir_write"
    DIR_CREATE = "dir_create"
    DIR_EDIT = "dir_edit"
    CMD_EXECUTE = "cmd_execute"

@dataclass
class Operation:
    type: OperationType
    path: str
    command: Optional[str] = None

class SecurityManager:
    def __init__(self):
        self.config_dir = Path.home() / '.claude_chat'
        self.whitelist_file = self.config_dir / 'whitelist.json'
        self.whitelist: Dict[str, List[str]] = self._load_whitelist()

    def _load_whitelist(self) -> Dict[str, List[str]]:
        try:
            if self.whitelist_file.exists():
                with open(self.whitelist_file) as f:
                    return json.load(f)
            else:
                self.config_dir.mkdir(parents=True, exist_ok=True)
                default_whitelist = {op.value: [] for op in OperationType}
                self._save_whitelist(default_whitelist)
                return default_whitelist
        except Exception as e:
            logger.error(f"Error loading whitelist: {e}")
            return {op.value: [] for op in OperationType}

    def _save_whitelist(self, whitelist: Dict[str, List[str]]) -> bool:
        try:
            with open(self.whitelist_file, 'w') as f:
                json.dump(whitelist, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving whitelist: {e}")
            return False

    def check_operation(self, parent_widget, operation: Operation) -> bool:
        """Check if operation is allowed and prompt user if necessary"""
        op_type = operation.type.value
        op_path = str(Path(operation.path).resolve())

        # Check if operation is whitelisted
        if op_path in self.whitelist[op_type]:
            return True

        # Prompt user for permission
        message = f"Allow the following operation?\n\nType: {op_type}\nPath: {op_path}"
        if operation.command:
            message += f"\nCommand: {operation.command}"

        reply = QMessageBox.question(
            parent_widget,
            'Security Check',
            message,
            QMessageBox.StandardButton.Yes | 
            QMessageBox.StandardButton.YesToAll | 
            QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.YesToAll:
            # Add to whitelist
            self.whitelist[op_type].append(op_path)
            self._save_whitelist(self.whitelist)
            return True
        elif reply == QMessageBox.StandardButton.Yes:
            return True
        return False

class ToolManager:
    def __init__(self, parent_widget):
        self.security = SecurityManager()
        self.parent_widget = parent_widget

    def execute_cmd(self, command: str) -> Tuple[bool, str]:
        """Execute a command in Windows command prompt"""
        operation = Operation(
            type=OperationType.CMD_EXECUTE,
            path="cmd.exe",
            command=command
        )

        reply = self.security.check_operation(self.parent_widget, operation)
        if not reply:
            return False, "Operation not authorized"

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, f"Command failed: {e.stderr}"
        except Exception as e:
            return False, f"Error executing command: {str(e)}"

    def file_operation(self, op_type: OperationType, path: str, content: str = None) -> Tuple[bool, str]:
        """Handle file operations"""
        operation = Operation(type=op_type, path=path)
        
        if not self.security.check_operation(self.parent_widget, operation):
            return False, "Operation not authorized"

        try:
            path_obj = Path(path)
            
            if op_type == OperationType.FILE_READ:
                with open(path_obj, 'r') as f:
                    return True, f.read()
                    
            elif op_type == OperationType.FILE_WRITE:
                with open(path_obj, 'w') as f:
                    f.write(content)
                return True, "File written successfully"
                
            elif op_type == OperationType.FILE_CREATE:
                path_obj.touch()
                return True, "File created successfully"
                
            elif op_type == OperationType.FILE_EDIT:
                if not path_obj.exists():
                    return False, "File does not exist"
                with open(path_obj, 'r+') as f:
                    current_content = f.read()
                    f.seek(0)
                    f.write(content)
                    f.truncate()
                return True, "File edited successfully"
                
        except Exception as e:
            return False, f"Error performing file operation: {str(e)}"

    def dir_operation(self, op_type: OperationType, path: str) -> Tuple[bool, str]:
        """Handle directory operations"""
        operation = Operation(type=op_type, path=path)
        
        if not self.security.check_operation(self.parent_widget, operation):
            return False, "Operation not authorized"

        try:
            path_obj = Path(path)
            
            if op_type == OperationType.DIR_READ:
                return True, "\n".join(str(p) for p in path_obj.iterdir())
                
            elif op_type == OperationType.DIR_CREATE:
                path_obj.mkdir(parents=True, exist_ok=True)
                return True, "Directory created successfully"
                
            elif op_type == OperationType.DIR_EDIT:
                if not path_obj.exists():
                    return False, "Directory does not exist"
                return True, "Directory modified successfully"
                
        except Exception as e:
            return False, f"Error performing directory operation: {str(e)}"
