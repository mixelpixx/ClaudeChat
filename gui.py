import sys
import os
import json
import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QTextEdit, QTreeWidget, QTreeWidgetItem, 
    QTabWidget, QMenuBar, QMenu, QToolBar, QStatusBar, QPlainTextEdit,
    QMessageBox, QFileDialog, QDialog, QLabel, QLineEdit, QPushButton
)
from PyQt6.QtGui import QAction, QIcon, QTextCharFormat, QColor, QSyntaxHighlighter, QFont, QKeySequence
from PyQt6.QtCore import Qt, QRegularExpression

from claude_api import ClaudeAPI
from config import Config

class CodeHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Define syntax highlighting rules
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))  # Blue
        keyword_format.setFontWeight(QFont.Weight.Bold)
        
        keywords = [
            "def", "class", "import", "from", "if", "else", "elif", 
            "for", "while", "return", "try", "except", "finally"
        ]
        
        self.highlighting_rules = [(QRegularExpression(f"\\b{keyword}\\b"), keyword_format) for keyword in keywords]

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = QRegularExpression(pattern)
            iterator = expression.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

class ConversationView(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.highlighter = CodeHighlighter(self.document())

class ToolsPanel(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["Tool", "Status"])
        self.setup_tools()

    def setup_tools(self):
        # Populate tools tree
        cmd_tools = QTreeWidgetItem(self, ["Command Tools"])
        file_tools = QTreeWidgetItem(self, ["Filesystem Tools"])
        
        cmd_list = ["Execute Command", "Process Management"]
        file_list = ["Read File", "Write File", "List Directory"]
        
        for tool in cmd_list:
            QTreeWidgetItem(cmd_tools, [tool, "Available"])
        
        for tool in file_list:
            QTreeWidgetItem(file_tools, [tool, "Available"])

class FileSystemBrowser(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["Name", "Type"])
        self.populate_root()

    def populate_root(self):
        home = QTreeWidgetItem(self, ["Home", "Directory"])
        home.setIcon(0, QIcon.fromTheme("folder-home"))
        
        # Add some default directories
        dirs = ["Documents", "Downloads", "Desktop"]
        for dir_name in dirs:
            dir_item = QTreeWidgetItem(home, [dir_name, "Directory"])
            dir_item.setIcon(0, QIcon.fromTheme("folder"))

class CommandApprovalDialog(QDialog):
    def __init__(self, command, parent=None):
        super().__init__(parent)
        self.command = command
        self.result = "deny"
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Command Approval Required")
        layout = QVBoxLayout(self)
        
        # Command display
        command_label = QLabel(f"Command requires approval:\n{self.command}")
        layout.addWidget(command_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        deny_btn = QPushButton("Deny")
        deny_btn.clicked.connect(self.deny_clicked)
        
        approve_btn = QPushButton("Approve Once")
        approve_btn.clicked.connect(self.approve_clicked)
        
        approve_always_btn = QPushButton("Approve Always")
        approve_always_btn.clicked.connect(self.approve_always_clicked)
        
        button_layout.addWidget(deny_btn)
        button_layout.addWidget(approve_btn)
        button_layout.addWidget(approve_always_btn)
        
        layout.addLayout(button_layout)
    
    def deny_clicked(self):
        self.result = "deny"
        self.accept()
    
    def approve_clicked(self):
        self.result = "approve"
        self.accept()
    
    def approve_always_clicked(self):
        self.result = "approve_always"
        self.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Claude AI Assistant")
        self.resize(1200, 800)
        
        # Initialize core components
        self.claude_api = ClaudeAPI()
        self.config = Config()
        self.setup_ui()

    def setup_ui(self):
        # Central widget and main layout
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        
        # Left sidebar: Tools Panel
        tools_panel = ToolsPanel()
        tools_panel.setMaximumWidth(250)
        
        # Central area: Conversation and Tabs
        central_splitter = QSplitter(Qt.Orientation.Vertical)
        conversation_view = ConversationView()
        self.conversation_view = conversation_view  # Store reference
        
        # Tabs for additional functionality
        tabs = QTabWidget()
        
        # Initialize command history and tool output tabs with text areas
        self.command_history = QPlainTextEdit()
        self.command_history.setReadOnly(True)
        self.tool_outputs = QPlainTextEdit()
        self.tool_outputs.setReadOnly(True)
        
        tabs.addTab(self.command_history, "Command History")
        tabs.addTab(self.tool_outputs, "Tool Outputs")
        
        central_splitter.addWidget(conversation_view)
        central_splitter.addWidget(tabs)
        
        # Add input area at the bottom
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        
        # Message input
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(100)
        self.message_input.setPlaceholderText("Type your message here... (Enter to send, Shift+Enter for new line)")
        
        # Attach image button
        attach_button = QPushButton("Attach Image")
        attach_button.clicked.connect(self.attach_image)
        
        # Send button
        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(attach_button)
        input_layout.addWidget(send_button)
        
        # Add input widget to central splitter
        central_splitter.addWidget(input_widget)
        
        # Right sidebar: Filesystem Browser
        filesystem_browser = FileSystemBrowser()
        filesystem_browser.setMaximumWidth(250)
        
        # Assemble main layout
        main_layout.addWidget(tools_panel)
        main_layout.addWidget(central_splitter)
        main_layout.addWidget(filesystem_browser)
        
        self.setCentralWidget(central_widget)

    def setup_menus(self):
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        new_chat_action = QAction("New Chat", self)
        file_menu.addAction(new_chat_action)
        
        # Tools Menu
        tools_menu = menubar.addMenu("&Tools")
        
        # Settings Menu
        settings_menu = menubar.addMenu("&Settings")
        api_key_action = QAction("Configure API Key", self)
        settings_menu.addAction(api_key_action)

    def setup_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # Add toolbar actions
        new_chat_action = QAction(QIcon.fromTheme("document-new"), "New Chat", self)
        toolbar.addAction(new_chat_action)

    def setup_statusbar(self):
        statusbar = self.statusBar()
        statusbar.showMessage("Ready")
        
    def add_to_command_history(self, command):
        """Add a command to the command history tab"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.command_history.appendPlainText(f"[{timestamp}] {command}")
        
    def add_to_tool_outputs(self, output):
        """Add tool output to the tool outputs tab"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(output, dict):
            formatted_output = json.dumps(output, indent=2)
        else:
            formatted_output = str(output)
        self.tool_outputs.appendPlainText(f"[{timestamp}]\n{formatted_output}\n")
        
    def send_message(self):
        """Send the current message to Claude"""
        message = self.message_input.toPlainText().strip()
        if message:
            # Add user message to conversation
            self.conversation_view.append(f"You: {message}")
            self.add_to_command_history(message)
            
            # Get Claude's response
            try:
                response = self.claude_api.send_message(message)
                if isinstance(response, dict) and 'type' in response and response['type'] == 'tool_result':
                    self.add_to_tool_outputs(response)
                    self.conversation_view.append("Claude: Tool execution completed. See Tool Outputs tab for details.")
                else:
                    self.conversation_view.append(f"Claude: {response}")
            except Exception as e:
                self.conversation_view.append(f"Error: {str(e)}")
            
            # Clear input
            self.message_input.clear()
            
    def attach_image(self):
        """Open file dialog to attach an image"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", 
            "Images (*.png *.jpg *.jpeg *.gif *.webp)")
        if file_path:
            self.image_path = file_path
            self.statusBar().showMessage(f"Image attached: {os.path.basename(file_path)}")

    def keyPressEvent(self, event):
        """Handle key press events for the main window"""
        if self.message_input.hasFocus():
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                    # Shift+Enter: insert newline
                    self.message_input.insertPlainText('\n')
                else:
                    # Enter: send message
                    self.send_message()
                event.accept()
                return
        super().keyPressEvent(event)
        
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
