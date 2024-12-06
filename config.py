import os
import json
import logging

logger = logging.getLogger(__name__)

class Config:
    def __init__(self):
        self.config_file = 'config.json'
        self.load_config()

    def load_config(self):
        """Load configuration from JSON file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = {
                    'api_key': '',
                    'model': 'claude-3-opus-20240229',
                    'max_tokens': 4096,
                    'temperature': 0.7
                }
                self.save_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.config = {
                'api_key': '',
                'model': 'claude-3-opus-20240229',
                'max_tokens': 4096,
                'temperature': 0.7
            }

    def save_config(self):
        """Save configuration to JSON file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def get_api_key(self):
        """Get API key from environment variable first, then config file"""
        # Try to get API key from environment variable
        env_api_key = os.getenv('ANTHROPIC_API_KEY')
        if env_api_key:
            logger.info("Using API key from environment variable")
            return env_api_key
            
        # Fallback to config file
        config_api_key = self.config.get('api_key', '')
        if config_api_key:
            logger.info("Using API key from config file")
            return config_api_key
            
        logger.error("No API key found in environment variable or config file")
        return None

    def set_api_key(self, api_key):
        """Set API key in config"""
        self.config['api_key'] = api_key
        self.save_config()

    def get_model(self):
        """Get model from config"""
        return self.config.get('model', 'claude-3-opus-20240229')

    def set_model(self, model):
        """Set model in config"""
        self.config['model'] = model
        self.save_config()

    def get_max_tokens(self):
        """Get max tokens from config"""
        return self.config.get('max_tokens', 4096)

    def set_max_tokens(self, max_tokens):
        """Set max tokens in config"""
        self.config['max_tokens'] = max_tokens
        self.save_config()

    def get_temperature(self):
        """Get temperature from config"""
        return self.config.get('temperature', 0.7)

    def set_temperature(self, temperature):
        """Set temperature in config"""
        self.config['temperature'] = temperature
        self.save_config()

    def get_system_prompt(self):
        """Get system prompt"""
        return """You are a helpful AI assistant. When working on tasks that involve multiple steps:
1. Think through the entire process before starting
2. Execute one step at a time
3. Verify each step's success before moving to the next
4. If a step fails, either retry with modifications or explain why it cannot proceed
5. Keep the user informed of progress throughout
6. Clearly indicate when the entire task is complete

When using tools:
- Use the execute_command tool for running system commands
- Use the filesystem_operation tool for file operations
- Always check tool execution results
- Handle errors appropriately
- Ask for user intervention when needed

Be efficient and clear in your communications while maintaining a helpful and professional tone."""