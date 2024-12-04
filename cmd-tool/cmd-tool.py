from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import subprocess
import threading
import queue
import time
import os
import json
import psutil
import signal

app = Flask(__name__)
CORS(app)

class CommandExecutor:
    def __init__(self):
        self.active_processes = {}
        self.output_queues = {}
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        def cleanup_old_processes():
            while True:
                time.sleep(60)  # Check every minute
                current_time = time.time()
                for pid in list(self.active_processes.keys()):
                    if current_time - self.active_processes[pid]['start_time'] > 3600:  # 1 hour timeout
                        self.terminate_process(pid)

        thread = threading.Thread(target=cleanup_old_processes, daemon=True)
        thread.start()

    def execute_command(self, command, working_dir):
        # Create process with pipe for output
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=working_dir,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Store process info
        pid = process.pid
        self.active_processes[pid] = {
            'process': process,
            'command': command,
            'start_time': time.time(),
            'working_dir': working_dir
        }
        
        # Create output queue for this process
        self.output_queues[pid] = queue.Queue()
        
        # Start output monitoring threads
        def monitor_output(pipe, output_type):
            try:
                for line in pipe:
                    if pid in self.output_queues:
                        self.output_queues[pid].put({
                            'type': output_type,
                            'data': line.strip()
                        })
            except (ValueError, OSError):
                pass  # Pipe closed
        
        threading.Thread(target=monitor_output, args=(process.stdout, 'stdout'), daemon=True).start()
        threading.Thread(target=monitor_output, args=(process.stderr, 'stderr'), daemon=True).start()
        
        return pid

    def get_output(self, pid):
        if pid not in self.output_queues:
            return None
        
        output = []
        try:
            while True:
                output.append(self.output_queues[pid].get_nowait())
        except queue.Empty:
            pass
        
        return output

    def terminate_process(self, pid):
        if pid in self.active_processes:
            try:
                # Kill process and all children
                parent = psutil.Process(pid)
                children = parent.children(recursive=True)
                for child in children:
                    child.terminate()
                parent.terminate()
            except psutil.NoSuchProcess:
                pass
            
            # Clean up our tracking
            if pid in self.output_queues:
                del self.output_queues[pid]
            del self.active_processes[pid]
            return True
        return False

    def is_process_running(self, pid):
        if pid not in self.active_processes:
            return False
        return self.active_processes[pid]['process'].poll() is None

executor = CommandExecutor()

# Whitelist configuration
WHITELIST = {
    'nmap': {'requires_approval': True, 'approved': False},
    'dir': {'requires_approval': False, 'approved': True},
    'ipconfig': {'requires_approval': False, 'approved': True},
}

def check_whitelist(command):
    cmd = command.split()[0].lower()
    if cmd in WHITELIST:
        return WHITELIST[cmd]['approved']
    return False

@app.route('/execute', methods=['POST'])
def execute_command():
    command = request.json.get('command', '').strip()
    working_dir = request.json.get('working_directory', os.getcwd())
    
    if not command:
        return jsonify({'error': 'No command provided'}), 400
    
    base_cmd = command.split()[0].lower()
    
    # Check whitelist
    if base_cmd not in WHITELIST:
        return jsonify({
            'status': 'approval_required',
            'command': command
        }), 202
    
    if WHITELIST[base_cmd]['requires_approval'] and not WHITELIST[base_cmd]['approved']:
        return jsonify({
            'status': 'approval_required',
            'command': command
        }), 202
    
    try:
        pid = executor.execute_command(command, working_dir)
        return jsonify({
            'status': 'started',
            'pid': pid
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/output/<int:pid>', methods=['GET'])
def get_output(pid):
    if not executor.is_process_running(pid):
        return jsonify({'status': 'completed'})
    
    output = executor.get_output(pid)
    if output is None:
        return jsonify({'error': 'Process not found'}), 404
    
    return jsonify({
        'status': 'running',
        'output': output
    })

@app.route('/terminate/<int:pid>', methods=['POST'])
def terminate_process(pid):
    if executor.terminate_process(pid):
        return jsonify({'status': 'terminated'})
    return jsonify({'error': 'Process not found'}), 404

@app.route('/approve', methods=['POST'])
def approve_command():
    command = request.json.get('command', '').strip()
    approval_type = request.json.get('type', 'once')
    
    if not command:
        return jsonify({'error': 'No command provided'}), 400
    
    base_cmd = command.split()[0].lower()
    
    if approval_type == 'always':
        WHITELIST[base_cmd] = {'requires_approval': False, 'approved': True}
    elif approval_type == 'once':
        WHITELIST[base_cmd] = {'requires_approval': True, 'approved': True}
    
    return jsonify({'status': 'approved'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)