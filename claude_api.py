# claude_api.py
import anthropic
import base64
import httpx
import json
import os

class ClaudeAPI:
    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set.")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.conversation_history = []

    def send_message(self, message, image_path=None):
        if image_path:
            try:
                image_media_type = image_path.split('.')[-1]
                if image_media_type not in ['jpeg', 'jpg', 'png', 'gif', 'webp']:
                    raise ValueError("Unsupported image type. Please use JPEG, PNG, GIF, or WEBP.")
                
                with open(image_path, 'rb') as image_file:                    
                    image_data = base64.b64encode(image_file.read()).decode("utf-8")
                
                user_message = {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": f"image/{image_media_type}",  # Corrected format
                                "data": image_data,
                            },
                        },
                       {"type": "text", "text": message} 
                    ] if message else []  # Allows sending just images

                }

            except FileNotFoundError:
                return "Image file not found."
            except Exception as e:  # Catch broader exceptions
                return f"Error processing image: {e}"
        else:
            user_message = {"role": "user", "content": message}

        self.conversation_history.append(user_message)

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=self.conversation_history,
        )
       
        self.conversation_history.append(response.to_dict()) # Ensure consistent dictionary format
        
        return self.extract_content(response)

    def extract_content(self, response):
        content = ""
        for part in response.content:
            if part.type == "text":
                content += part.text
            elif part.type == "tool_use":
                content += f"Tool use requested: {part.name} with input {json.dumps(part.input)}\n"
        return content
    
    def clear_conversation(self):
        self.conversation_history = []