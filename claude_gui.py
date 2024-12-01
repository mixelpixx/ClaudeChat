import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                            QFileDialog, QMessageBox, QLabel, QDialog, 
                            QInputDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QTextCursor
from claude_api import ClaudeAPI
import logging
from secure_tools import ToolManager

logger = logging.getLogger(__name__)

class ApiKeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API Key Setup")
        self.setModal(True)
        layout = QVBoxLayout()
        
        # Add explanation label
        label = QLabel("Please enter your Anthropic API key.\nYou can find this in your Anthropic Console.")
        layout.addWidget(label)
        
        # Add input field
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.api_key_input)
        
        # Add buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

class MessageThread(QThread):
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, claude_api, message, image_path=None):
        super().__init__()
        self.claude_api = claude_api
        self.message = message
        self.image_path = image_path
        
    def run(self):
        try:
            response = self.claude_api.send_message(self.message, self.image_path)
            self.response_received.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Claude Chat")
        self.setMinimumSize(800, 600)
        
        try:
            self.claude_api = ClaudeAPI()
            # Initialize tool manager and connect to API
            self.tool_manager = ToolManager(self)
            self.claude_api.tools = self.tool_manager
        except ValueError:
            self.get_api_key()
            try:
                self.claude_api = ClaudeAPI()
                self.tool_manager = ToolManager(self)
                self.claude_api.tools = self.tool_manager
            except ValueError as e:
                QMessageBox.critical(self, "Error", str(e))
                sys.exit(1)
        
        self.setup_ui()
        
    def get_api_key(self):
        dialog = ApiKeyDialog(self)
        if dialog.exec():
            api_key = dialog.api_key_input.text().strip()
            if api_key:
                from config import Config
                config = Config()
                config.set_api_key(api_key)
            else:
                QMessageBox.warning(self, "Warning", "API key cannot be empty")
                self.get_api_key()
    
    def setup_ui(self):
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QHBoxLayout()
        
        # Message input
        self.message_input = QLineEdit()
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)
        
        # Upload image button
        self.upload_button = QPushButton("Upload Image")
        self.upload_button.clicked.connect(self.upload_image)
        input_layout.addWidget(self.upload_button)
        
        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        
        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_conversation)
        input_layout.addWidget(self.clear_button)
        
        layout.addLayout(input_layout)
        
        # Status bar for showing image path
        self.statusBar().showMessage("")
        
        # Initialize image path
        self.current_image_path = None
        
    def upload_image(self):
        file_dialog = QFileDialog()
        image_path, _ = file_dialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.webp)"
        )
        
        if image_path:
            self.current_image_path = image_path
            self.statusBar().showMessage(f"Image selected: {os.path.basename(image_path)}")
            
    def send_message(self):
        message = self.message_input.text().strip()
        if not message and not self.current_image_path:
            return
            
        # Disable input while processing
        self.message_input.setEnabled(False)
        self.send_button.setEnabled(False)
        self.upload_button.setEnabled(False)
        
        # Display user message
        self.chat_display.append(f"\nYou: {message}")
        if self.current_image_path:
            self.chat_display.append(f"[Attached image: {os.path.basename(self.current_image_path)}]")
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)
        
        # Create and start message thread
        self.message_thread = MessageThread(
            self.claude_api,
            message,
            self.current_image_path
        )
        self.message_thread.response_received.connect(self.handle_response)
        self.message_thread.error_occurred.connect(self.handle_error)
        self.message_thread.finished.connect(self.enable_input)
        self.message_thread.start()
        
        # Clear input
        self.message_input.clear()
        self.current_image_path = None
        self.statusBar().clearMessage()
        
    def handle_response(self, response):
        self.chat_display.append(f"\nClaude: {response}")
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)
        
    def handle_error(self, error_message):
        QMessageBox.critical(self, "Error", f"An error occurred: {error_message}")
        
    def enable_input(self):
        self.message_input.setEnabled(True)
        self.send_button.setEnabled(True)
        self.upload_button.setEnabled(True)
        self.message_input.setFocus()
        
    def clear_conversation(self):
        self.chat_display.clear()
        self.claude_api.clear_conversation()
        
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, 'Exit',
            "Are you sure you want to quit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()