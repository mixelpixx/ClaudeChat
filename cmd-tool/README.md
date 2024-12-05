# MCP Server Documentation

## Overview
The MCP Server is a Flask-based command execution server that provides a secure way to run system commands through a REST API. It includes features like process management, output streaming, and a whitelist-based security system.

## Server Setup & Running
1. Ensure you have the required dependencies installed:
   ```bash
   pip install flask flask-cors psutil
   ```
2. Run the server:
   ```bash
   python cmd-tool.py
   ```
   The server will start on port 5000 by default.

## API Endpoints

### 1. Execute Command
- **Endpoint:** `/execute`
- **Method:** POST
- **Payload:**
  ```json
  {
    "command": "your_command_here",
    "working_directory": "/path/to/directory"  // Optional
  }
  ```
- **Response:** Returns a process ID (pid) for tracking

### 2. Get Command Output
- **Endpoint:** `/output/<pid>`
- **Method:** GET
- **Response:** Streams command output in real-time

### 3. Terminate Process
- **Endpoint:** `/terminate/<pid>`
- **Method:** POST
- **Response:** Confirms process termination

### 4. Approve Command
- **Endpoint:** `/approve`
- **Method:** POST
- **Payload:**
  ```json
  {
    "command": "command_to_approve",
    "type": "once|always"
  }
  ```

## Whitelist Configuration

The whitelist configuration is defined in the `WHITELIST` dictionary. Each command has two properties:
- `requires_approval`: Whether the command needs approval before execution
- `approved`: Current approval status

### Example Whitelist Configuration:
```python
WHITELIST = {
    'nmap': {'requires_approval': True, 'approved': False},
    'dir': {'requires_approval': False, 'approved': True},
    'ipconfig': {'requires_approval': False, 'approved': True}
}
```

### To Add New Commands:
1. Add a new entry to the WHITELIST dictionary:
   ```python
   WHITELIST['new_command'] = {
       'requires_approval': True|False,
       'approved': True|False
   }
   ```

### Security Levels:
1. **Pre-approved Commands:**
   ```python
   {'requires_approval': False, 'approved': True}
   ```

2. **One-time Approval Required:**
   ```python
   {'requires_approval': True, 'approved': False}
   ```

## Example Usage

### 1. Execute a Command
```bash
curl -X POST http://localhost:5000/execute \
  -H "Content-Type: application/json" \
  -d '{"command": "dir", "working_directory": "C:/"}'
```

### 2. Get Command Output
```bash
curl http://localhost:5000/output/1234  # Replace 1234 with actual PID
```

### 3. Approve a Command
```bash
curl -X POST http://localhost:5000/approve \
  -H "Content-Type: application/json" \
  -d '{"command": "nmap", "type": "always"}'
```

## Security Considerations
1. All commands are checked against the whitelist before execution
2. Unknown commands require explicit approval
3. Processes are automatically terminated after 1 hour
4. Child processes are terminated along with parent processes
5. Working directory can be specified for command execution

## Error Handling
- Invalid commands return 400 status code
- Non-existent processes return 404 status code
- Server errors return 500 status code
- Commands requiring approval return 202 status code
