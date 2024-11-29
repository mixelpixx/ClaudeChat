# claude_gui.py
import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLineEdit, QLabel, QTextEdit, QFileDialog)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from claude_api import ClaudeAPI


class ClaudeChatApp(QWidget):
    def __init__(self, api_key):
        super().__init__()
        self.api = ClaudeAPI(api_key)
        self.initUI()

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

        response = self.api.send_message(message)  # Directly send, no image here
        self.update_chat_display(f"User: {message}\nClaude: {response}\n")
        self.message_input.clear()


    def upload_image(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("Image files (*.jpg *.jpeg *.png *.gif *.webp)")
        if file_dialog.exec():  # Open only if 'Open' clicked
            filename = file_dialog.selectedFiles()[0]

            user_message = self.message_input.text()  # Allows combined text and image


            response = self.api.send_message(user_message, filename)
            
            self.update_chat_display(f"User: {user_message if user_message else '[Image]'}\nClaude: {response}\n")
            self.message_input.clear()

    def clear_conversation(self):
        self.api.clear_conversation()
        self.chat_display.clear()
        self.update_chat_display("Conversation cleared.\n")

    def update_chat_display(self, text):
        self.chat_display.append(text)  # Correct method to add text



if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        ex = ClaudeChatApp() #No longer pass the API key here
        ex.show()
        sys.exit(app.exec())
    except ValueError as e:  # specifically catch the API key error
        print(f"Error: {e}") # Print to console so user knows the issue
        sys.exit(1) # Exit with error code