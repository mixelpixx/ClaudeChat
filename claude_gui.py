# claude_gui.py
import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLineEdit, QLabel, QTextEdit, QFileDialog)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from claude_api import ClaudeAPI
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ClaudeChatApp(QWidget):
    def __init__(self):
        super().__init__()
        logger.info("Initializing Claude Chat GUI")
        try:
            self.api = ClaudeAPI()
            self.initUI()
        except Exception as e:
            logger.error(f"Failed to initialize application: {str(e)}")
            raise

    def initUI(self):
        self.setWindowTitle("Claude Chat")

        vbox = QVBoxLayout()

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)  # Make display area read-only
        vbox.addWidget(self.chat_display)

        hbox = QHBoxLayout()
        self.message_input = QLineEdit()
        hbox.addWidget(self.message_input)

        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)  # No parentheses here
        hbox.addWidget(send_button)

        upload_button = QPushButton("Upload Image")
        upload_button.clicked.connect(self.upload_image)
        hbox.addWidget(upload_button)
        
        clear_button = QPushButton("Clear Conversation")
        clear_button.clicked.connect(self.clear_conversation)
        hbox.addWidget(clear_button)

        vbox.addLayout(hbox)
        self.setLayout(vbox)

    def send_message(self):
        message = self.message_input.text()
        logger.debug(f"Sending message: {message}")
        try:
            response = self.api.send_message(message)
            self.update_chat_display(f"User: {message}\nClaude: {response}\n")
            self.message_input.clear()
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
                self.update_chat_display(f"User: {user_message if user_message else '[Image]'}\nClaude: {response}\n")
                self.message_input.clear()
            except Exception as e:
                logger.error(f"Error processing image: {str(e)}")
                self.update_chat_display(f"Error: {str(e)}\n")

    def clear_conversation(self):
        self.api.clear_conversation()
        self.chat_display.clear()
        self.update_chat_display("Conversation cleared.\n")

    def update_chat_display(self, text):
        self.chat_display.append(text)  # Correct method to add text

if __name__ == "__main__":
    app = QApplication(sys.argv)
    logger.info("Starting Claude Chat application")
    try:
        ex = ClaudeChatApp()
        ex.show()
        logger.info("Application window displayed")
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Application failed to start: {str(e)}")
        print(f"Error: {e}")
        sys.exit(1)
