import anthropic
import base64
import json
import os
import logging
from config import Config

from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

# Configure basic logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ClaudeAPI:
    def __init__(self):
        logger.info("Initializing ClaudeAPI")
        self.config = Config()
        api_key = self.config.get_api_key()
        if not api_key:
            logger.error("No API key found in config or environment")
            raise ValueError("No API key found. Please set your API key in the settings.")
        self.client = Anthropic(api_key=api_key)
        self.conversation_history = []

    def send_message(self, message, image_path=None):
        if image_path:
            try:
                # Image handling code here (not implemented in this example)
                pass
            except FileNotFoundError:
                logger.error(f"Image file not found: {image_path}")
                return "Image file not found."
            except Exception as e:  # Catch broader exceptions
                logger.error(f"Error processing image: {str(e)}")
                return f"Error processing image: {e}"
        
        self.conversation_history.append(f"{HUMAN_PROMPT} {message}")

        logger.debug("Sending message to Claude API")
        try:
            response = self.client.completions.create(
                model="claude-2.0",
                prompt=f"{''.join(self.conversation_history)}{AI_PROMPT}",
                max_tokens_to_sample=1024,
            )
            logger.debug("Received response from Claude API")
            ai_response = response.completion
            self.conversation_history.append(f"{AI_PROMPT} {ai_response}")
            
            return ai_response
        except Exception as e:
            logger.error(f"Error communicating with Claude API: {str(e)}")
            raise

    def clear_conversation(self):
        self.conversation_history = []
