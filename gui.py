import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QTextEdit, QTreeWidget, QTreeWidgetItem, 
    QTabWidget, QMenuBar, QMenu, QToolBar, QStatusBar,
    QMessageBox, QFileDialog, QDialog, QLabel, QLineEdit, QPushButton
)
from PyQt6.QtGui import QAction, QIcon, QTextCharFormat, QColor, QSyntaxHighlighter, QFont
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Claude AI Assistant")
        self.resize(1200, 800)
        
        # Initialize core components
        self.claude_api = ClaudeAPI()
        self.config = Config()
        
        # Setup main UI
        self.setup_ui()
        self.setup_menus()
        self.setup_toolbar()
        self.setup_statusbar()

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
        
        # Tabs for additional functionality
        tabs = QTabWidget()
        tabs.addTab(QWidget(), "Command History")
        tabs.addTab(QWidget(), "Tool Outputs")
        
        central_splitter.addWidget(conversation_view)
        central_splitter.addWidget(tabs)
        
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

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
