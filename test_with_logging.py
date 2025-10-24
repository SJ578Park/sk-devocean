#!/usr/bin/env python3
"""
Test with stderr logging to see what's happening
"""

import json
import subprocess
import sys
import time
import threading

def read_stderr(process):
    """Read stderr in a separate thread"""
    while True:
        line = process.stderr.readline()
        if not line:
            break
        print(f"STDERR: {line.strip()}")

def test_with_logging():
    """Test with stderr logging"""
    
    print("Starting ChillMCP server with logging...")
    cmd = [sys.executable, "main.py", "--boss_alertness", "50", "--boss_alertness_cooldown", "60"]
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Start stderr reader thread
    stderr_thread = threading.Thread(target=read_stderr, args=(process,))
    stderr_thread.daemon = True
    stderr_thread.start()
    
    # Wait for server to start
    time.sleep(2)
    
    try:
        print("Server started. Testing...")
        
        # Test initialize
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"}
            }
        }
        
        process.stdin.write(json.dumps(init_msg) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        print(f"Initialize response: {response.strip()}")
        
        # Test tools/list
        tools_msg = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        process.stdin.write(json.dumps(tools_msg) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        print(f"Tools list response: {response.strip()}")
        
        # Wait a bit for stderr to catch up
        time.sleep(1)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Terminating server...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    test_with_logging()
