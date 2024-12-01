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
        self.config_file = Path.home() / '.claude_chat' / 'config.json'
        self.config = self.load_config()
        
    def load_config(self):
        """Load configuration from file or environment"""
        try:
            if self.config_file.exists():
                with open(self.config_file) as f:
                    return json.load(f)
            else:
                # Create default config
                self.config_file.parent.mkdir(parents=True, exist_ok=True)
                default_config = {
                    "api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
                    "model": "claude-3-5-sonnet-20241022",
                    "system_prompt": "You are Claude, an AI assistant. Be helpful and concise.",
                    "whitelist": {},
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
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
            
    def get_api_key(self):
        """Get API key from config or environment"""
        return self.config.get('api_key') or os.environ.get("ANTHROPIC_API_KEY")
    
    def get_model(self):
        return self.config.get('model', "claude-3-5-sonnet-20241022")

    def get_max_tokens(self):
        return self.config.get('max_tokens', 1024)

    def get_system_prompt(self):
        return self.config.get('system_prompt', "You are Claude, an AI assistant. Be helpful and concise.")

    def get_whitelist(self):
        return self.config.get('whitelist', {})

    def set_api_key(self, api_key):
        """Set API key in config"""
        self.config['api_key'] = api_key
        self.save_config(self.config)
