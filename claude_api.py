import logging
import os
from anthropic import Anthropic
from config import Config

logger = logging.getLogger(__name__)

class ClaudeAPI:
    def __init__(self):
        logger.info("Initializing ClaudeAPI")
        self.config = Config()
        api_key = self.config.get_api_key()
        
        if not api_key:
            raise ValueError("API key not found")
            
        self.client = Anthropic(api_key=api_key)
        self.conversation_history = []
        self.tools = None
        
    def send_message(self, message, image_path=None):
        logger.info("Sending message to Claude")
        try:
            if image_path:
                with open(image_path, "rb") as img:
                    response = self.client.messages.create(
                        model="claude-3-opus-20240229",
                        max_tokens=1024,
                        messages=[{"role": "user", "content": message}],
                        system="You are Claude, an AI assistant. Be helpful and concise."
                    )
            else:
                response = self.client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": message}],
                    system="You are Claude, an AI assistant. Be helpful and concise."
                )
            
            response_text = response.content[0].text
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": response_text})
            return response_text
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            raise
            
    def clear_conversation(self):
        self.conversation_history = []
