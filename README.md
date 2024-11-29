# Claude Chat Application

Claude Chat is a desktop application that allows users to interact with Claude, an AI assistant powered by Anthropic's API. This application provides a user-friendly interface for sending messages to Claude and receiving responses, including the ability to upload and analyze images.

## Features


## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/claude-chat.git
   cd claude-chat
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your Anthropic API key:
   - Create an account at [Anthropic](https://www.anthropic.com) and obtain an API key.
   - Set your API key as an environment variable:
     ```
     export ANTHROPIC_API_KEY=your_api_key_here
     ```
   Alternatively, you can enter your API key in the application when prompted.

## Usage

1. Run the application:
   ```
   python claude_gui.py
   ```

2. If you haven't set up your API key as an environment variable, you'll be prompted to enter it when you first run the application.

3. Type your message in the input field and click "Send" or press Enter to send a message to Claude.

4. To upload an image for analysis, click the "Upload Image" button and select an image file.

5. To clear the conversation, click the "Clear Conversation" button.

## File Structure


## Dependencies


## Building the Executable

To build a standalone executable:

1. Install PyInstaller:
   ```
   pip install pyinstaller
   ```

2. Run PyInstaller with the spec file:
   ```
   pyinstaller claude_chat.spec
   ```

3. The executable will be created in the `dist` directory.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

