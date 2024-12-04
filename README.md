Claude AI Assistant
A conversational AI chatbot with tool-calling capabilities, featuring a graphical user interface built with PyQt6. The chatbot leverages the Claude API to interact with users in a conversational manner and supports executing system commands and filesystem operations through secure and controlled interfaces.

Table of Contents
Introduction
Features
Prerequisites
Installation
Configuration
Starting the Tool Servers
Command Tool Server
Filesystem Tool Server
Running the Application
Usage
Code Structure
Contributing
License
Introduction
The Claude AI Assistant is a chatbot application that allows users to interact with an AI assistant in a conversational manner. It supports enhanced functionality such as executing system commands and performing filesystem operations through secure and controlled tool interfaces. The application includes a graphical user interface (GUI) built with PyQt6, providing an intuitive and interactive experience.

Features
Conversational AI Chatbot: Communicate with the AI assistant using natural language.
Tool Calling Capabilities: Execute system commands and perform filesystem operations through secure APIs.
Secure Execution Environment: Commands and filesystem operations are executed in a controlled and secure manner to prevent unauthorized access.
Graphical User Interface: User-friendly interface built with PyQt6.
Configuration Management: Easy configuration of API keys and settings.
Logging: Detailed logging for debugging and monitoring purposes.
Prerequisites
Python 3.8 or higher
API Key for the Claude API: Obtain an API key from Anthropic.
Operating System: The application is designed to run on Windows, macOS, and Linux systems.
Installation
Clone the Repository
   git clone https://github.com/yourusername/claude-ai-assistant.git
   cd claude-ai-assistant
Create a Virtual Environment (Optional but Recommended)
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
Install Required Packages

Install the necessary Python packages using pip:

   pip install -r requirements.txt
If a requirements.txt file is not provided, install the following packages:

   pip install Flask Flask-Cors psutil anthropic PyQt6
Configuration
Before running the application, you need to configure your API key and other settings.

Set Up API Key

You can set your Claude API key in one of two ways:

Environment Variable

Set the ANTHROPIC_API_KEY environment variable:

 export ANTHROPIC_API_KEY='your_api_key_here'  # On Windows use `set` instead of `export`
Configuration File

Edit the configuration file located at ~/.claude_chat/config.json (the first time you run the application, this file will be created automatically). Update the api_key field with your API key:

 {
   "api_key": "your_api_key_here",
   "model": "claude-3-5-sonnet-20241022",
   "system_prompt": "You are Claude, an AI assistant. Be helpful and concise.",
   "whitelist": {},
   "max_tokens": 1024
 }
Starting the Tool Servers
The application relies on two separate server components to handle command execution and filesystem operations. These servers need to be started before running the main application.

Command Tool Server
The Command Tool Server allows the AI assistant to execute system commands in a controlled environment.

Navigate to the Command Tool Directory
   cd cmd-tool
Run the Command Tool Server
   python cmd-tool.py
By default, the server runs on http://localhost:5000.

Note: Ensure that port 5000 is available. If not, you can change the port by modifying the app.run() call in cmd-tool.py:

if __name__ == '__main__':
    app.run(debug=True, port=5000)
Change port=5000 to an available port number.

Filesystem Tool Server
The Filesystem Tool Server provides secure access to filesystem operations such as reading and writing files.

Navigate to the Filesystem Directory
   cd ../filesystem
Run the Filesystem Tool Server

The Filesystem Tool Server requires you to specify the directories it is allowed to access. For example:

   python filesystem.py /path/to/allowed/directory
You can specify multiple directories:

   python filesystem.py /path/to/dir1 /path/to/dir2
Note: By default, the Filesystem Tool Server runs on port 5000, which may conflict with the Command Tool Server. To avoid this, modify the app.run() call in filesystem.py to use a different port (e.g., 5001):

   if __name__ == '__main__':
       app.run(debug=False, port=5001)
After modifying, start the server:

   python filesystem.py /path/to/allowed/directory
The server will now run on http://localhost:5001.

Running the Application
Once both servers are running, you can start the main chatbot application.

Navigate to the Project Root Directory
   cd ..
Run the GUI Application
   python gui.py
The graphical interface should launch, allowing you to interact with the Claude AI Assistant.

Usage
Conversing with the AI Assistant

Type your messages into the chat input area and send them to interact with Claude. The assistant will respond in a conversational manner.

Executing Commands

The assistant can execute system commands that are whitelisted or approved. For example, you can ask the assistant to list files in a directory.

Filesystem Operations

The assistant can read from and write to files within the allowed directories. For example, you can ask the assistant to read the contents of a file.

Tool Outputs

Outputs from executed commands and filesystem operations are displayed in the "Tool Outputs" tab in the GUI.

Command History

You can view the history of executed commands in the "Command History" tab.

Code Structure
The project is organized into several components:

gui.py

The main entry point for the application.

Defines the graphical user interface using PyQt6.

Handles user interactions and displays conversation history.

claude_api.py

Manages communication with the Claude API.

Handles sending messages to Claude and processing responses.

Implements tool handling logic, including command execution and filesystem operations.

cmd-tool/cmd-tool.py

A Flask server that handles command execution requests.

Provides a secure environment for executing system commands.

Manages active processes and outputs.

filesystem/filesystem.py

A Flask server that handles filesystem operation requests.

Provides secure access to filesystem functions such as reading and writing files.

Validates paths against allowed directories to prevent unauthorized access.

config.py

Manages application configuration.

Loads configuration from a file or environment variables.

Handles saving and retrieving API keys and settings.

Contributing
Contributions are welcome! Please fork the repository and submit a pull request for any enhancements or bug fixes.

License
This project is licensed under the MIT License. See the LICENSE file for details.

Feel free to customize this README to better suit your project's specifics, such as updating the GitHub repository URL, adding screenshots, or providing additional usage examples.

Certainly! I'll create a comprehensive README file for your project. Here's the content for the new README.md file:

/README.md

# Claude AI Assistant with Tool Calling

This project is a chatbot application with advanced features including tool calling, file system operations, and a graphical user interface. It leverages the Claude AI model from Anthropic to provide intelligent responses and execute various system commands and file operations.

## Table of Contents
1. [Installation](#installation)
2. [Running the Application](#running-the-application)
3. [Starting Tool Servers](#starting-tool-servers)
4. [Features](#features)
5. [Configuration](#configuration)
6. [Usage](#usage)
7. [Security Considerations](#security-considerations)
8. [Troubleshooting](#troubleshooting)
9. [Contributing](#contributing)
10. [License](#license)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/claude-ai-assistant.git
   cd claude-ai-assistant
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your Anthropic API key:
   - Create a `.env` file in the project root
   - Add your API key: `ANTHROPIC_API_KEY=your_api_key_here`

## Running the Application

To start the main application with the graphical user interface:

python gui.py

This will launch the Claude AI Assistant interface.

## Starting Tool Servers

The application relies on two separate tool servers for command execution and file system operations. Start these servers before using the related features in the main application.

1. Command Tool Server:
   ```
   python cmd-tool/cmd-tool.py
   ```
   This server handles command execution and process management.

2. Filesystem Tool Server:
   ```
   python filesystem/filesystem.py /path/to/allowed/directory [additional/directories...]
   ```
   Replace `/path/to/allowed/directory` with the directory you want to give the AI access to. You can specify multiple directories.

Both servers should be running alongside the main application for full functionality.

## Features

1. **AI-powered Chat**: Interact with the Claude AI model for intelligent conversations and task assistance.
2. **Command Execution**: Run system commands through a secure interface.
3. **File System Operations**: Perform read, write, and directory listing operations on allowed directories.
4. **Graphical User Interface**: User-friendly interface for easy interaction with the AI and tools.
5. **Tool Calling**: The AI can use various tools to perform tasks and retrieve information.
6. **Syntax Highlighting**: Code snippets in the conversation are highlighted for better readability.
7. **Configuration Management**: Easily configure API keys and other settings.

## Configuration

The application uses a configuration file located at `~/.claude_chat/config.json`. You can modify this file to change settings such as:

- API key
- AI model
- System prompt
- Maximum tokens
- Whitelisted commands

You can also set the API key through the GUI in the Settings menu.

## Usage

1. Start the main application and both tool servers.
2. Use the chat interface to interact with the AI assistant.
3. The AI can perform various tasks using tool calling:
   - Execute system commands
   - Read and write files
   - List directory contents
   - Search for files
   - Get file information
4. Use the file system browser to navigate through allowed directories.
5. The tools panel shows available tools and their status.

## Security Considerations

- The command execution and file system operations are restricted to prevent unauthorized access.
- Ensure that you only allow access to directories that you want the AI to interact with.
- Regularly review the whitelist of allowed commands in the configuration.
- Be cautious when executing commands or performing file operations suggested by the AI.

## Troubleshooting

- If tools are not working, ensure both tool servers are running.
- Check the `claude_chat.log` file for any error messages or issues.
- Verify that your API key is correctly set in the configuration.
- Make sure you have the necessary permissions for the directories you're trying to access.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
