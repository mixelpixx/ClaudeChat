# claude_gui.py
import sys
import time
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLineEdit, QLabel, QTextEdit, QFileDialog,
                             QMessageBox, QDialog, QScrollArea, QFrame)
from PyQt6.QtGui import QPixmap, QColor, QPalette, QScreen
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from claude_api import ClaudeAPI
from config import Config
from qt_material import apply_stylesheet

import logging
import sys
from PyQt6.QtWidgets import QApplication

# Configure basic logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LoadingIndicator(QThread):
    update_signal = pyqtSignal(str)

    def run(self):
        dots = [".", "..", "..."]
        i = 0
        while True:
            self.update_signal.emit(f"Thinking{dots[i]}")
            time.sleep(0.5)
            i = (i + 1) % 3

class MessageBubble(QFrame):
    def __init__(self, text, is_user=True):
        super().__init__()
        self.setObjectName("messageBubble")
        self.setStyleSheet("color: #000000;")  # Set text color to black
        layout = QVBoxLayout()
        self.setLayout(layout)

        message = QLabel(text)
        message.setWordWrap(True)
        message.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        message.setStyleSheet("color: #000000;")  # Set text color to black
        layout.addWidget(message)

        if is_user:
            self.setStyleSheet("""
                QFrame#messageBubble {
                    background-color: #DCF8C6;
                    border-radius: 10px;
                    color: #000000;
                    padding: 10px;
                    margin: 5px;
                }
            """)
            layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            self.setStyleSheet("""
                QFrame#messageBubble {
                    background-color: #FFFFFF;
                    border-radius: 10px;
                    color: #000000;
                    padding: 10px;
                    margin: 5px;
                }
            """)
            layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

class ScrollableMessageArea(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.setWidget(self.content_widget)

class APIKeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = Config()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('API Key Configuration')
        layout = QVBoxLayout()

        # API Key input
        self.api_key_input = QLineEdit()
        self.api_key_input.setText(self.config.get_api_key() or '')
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel('Enter your Anthropic API Key:'))
        layout.addWidget(self.api_key_input)

        # Buttons
        buttons = QHBoxLayout()
        save_button = QPushButton('Save')
        save_button.clicked.connect(self.save_api_key)
        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)

        self.setLayout(layout)

    def save_api_key(self):
        api_key = self.api_key_input.text().strip()
        if api_key:
            self.config.set_api_key(api_key)
            self.accept()
        else:
            QMessageBox.warning(self, 'Error', 'API Key cannot be empty')

class ClaudeChatApp(QWidget):
    def __init__(self):
        super().__init__()
        self.config = Config()
        
        # Check for API key
        if not self.config.get_api_key():
            if not self.show_api_key_dialog():
                sys.exit(1)
                
        logger.info("Initializing Claude Chat GUI")
        try:
            self.api = ClaudeAPI()
            self.initUI()
        except Exception as e:
            logger.error(f"Failed to initialize application: {str(e)}")
            self.show_error_dialog(str(e))
            raise

    def initUI(self):
        self.setWindowTitle("Claude Chat")
        self.setMinimumSize(600, 400)

        vbox = QVBoxLayout()
        vbox.setSpacing(10)

        self.chat_display = ScrollableMessageArea()
        vbox.addWidget(self.chat_display, 1)

        hbox = QHBoxLayout()
        hbox.setSpacing(10)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        hbox.addWidget(self.message_input)

        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        hbox.addWidget(send_button)

        upload_button = QPushButton("Upload Image")
        upload_button.clicked.connect(self.upload_image)
        hbox.addWidget(upload_button)

        clear_button = QPushButton("Clear Conversation")
        clear_button.clicked.connect(self.clear_conversation)
        hbox.addWidget(clear_button)

        vbox.addLayout(hbox)
        vbox.setContentsMargins(20, 20, 20, 20)
        self.setLayout(vbox)

        # Set initial window size to 1/4 of the screen
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        width = int(screen_geometry.width() * 0.25)
        height = int(screen_geometry.height() * 0.25)
        self.resize(width, height)

    def send_message(self):
        message = self.message_input.text()
        logger.debug(f"Sending message: {message}")
        try:
            response = self.api.send_message(message)
            self.update_chat_display(message, is_user=True)
            self.update_chat_display(response, is_user=False)
            self.message_input.clear()
            
            # Scroll to the bottom
            scrollbar = self.chat_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            self.update_chat_display(f"Error: {str(e)}\n")

    def upload_image(self):
        logger.debug("Opening file dialog for image upload")
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("Image files (*.jpg *.jpeg *.png *.gif *.webp)")
        
        if file_dialog.exec():
            filename = file_dialog.selectedFiles()[0]
            logger.debug(f"Selected image file: {filename}")
            user_message = self.message_input.text()

            try:
                response = self.api.send_message(user_message, filename)
                self.update_chat_display(user_message if user_message else '[Image]', is_user=True)
                self.update_chat_display(response, is_user=False)
                self.message_input.clear()
            except Exception as e:
                logger.error(f"Error processing image: {str(e)}")
                self.update_chat_display(f"Error: {str(e)}\n")

    def clear_conversation(self):
        self.api.clear_conversation()
        self.chat_display.content_widget.deleteLater()
        self.chat_display.content_widget = QWidget()
        self.chat_display.content_layout = QVBoxLayout(self.chat_display.content_widget)
        self.chat_display.setWidget(self.chat_display.content_widget)
        self.update_chat_display("Conversation cleared.\n")

    def update_chat_display(self, text, is_user=True):
        bubble = MessageBubble(text, is_user)
        self.chat_display.content_layout.addWidget(bubble)
        
        # Scroll to the bottom
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def show_api_key_dialog(self):
        dialog = APIKeyDialog(self)
        return dialog.exec() == QDialog.DialogCode.Accepted

    def show_error_dialog(self, message):
        QMessageBox.critical(self, 'Error', message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    logger.info("Starting Claude Chat application")
    
    try:
        # Set the base style to light
        app.setStyle("Fusion")
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        app.setPalette(palette)
        apply_stylesheet(app, theme='dark_teal.xml')
        ex = ClaudeChatApp()
        ex.show()
        logger.info("Application window displayed")
        
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Application failed to start: {str(e)}")
        print(f"Error: {e}")
        sys.exit(1)
