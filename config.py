import os
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('claude_chat.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Config:
    def __init__(self):
        self.config_file = os.path.expanduser('~/.claude_chat/config.json')
        self.config = self.load_config()
        
    def load_config(self):
        """Load configuration from file or environment"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file) as f:
                    return json.load(f)
            else:
                # Create default config
                os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
                default_config = {
                    "api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
                    "model": "claude-2.0",
                    "max_tokens": 1024,
                }
                self.save_config(default_config)
                return default_config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
            
    def save_config(self, config):
        """Save configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
            
    def get_api_key(self):
        """Get API key from config or environment"""
        return self.config.get('api_key') or os.environ.get("ANTHROPIC_API_KEY")
    
    def set_api_key(self, api_key):
        """Set API key in config"""
        self.config['api_key'] = api_key
        self.save_config(self.config)
