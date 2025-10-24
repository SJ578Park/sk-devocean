#!/usr/bin/env python3
"""
Simple interactive test for ChillMCP server
"""

import json
import subprocess
import sys
import time

def interactive_test():
    """Interactive test with manual JSON-RPC messages"""
    
    print("Starting ChillMCP server...")
    cmd = [sys.executable, "main.py", "--boss_alertness", "50", "--boss_alertness_cooldown", "60"]
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    time.sleep(2)
    
    try:
        print("Server started. Testing MCP protocol...")
        
        # Test 1: Initialize
        print("\n1. Testing initialize...")
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
        print(f"Response: {response.strip()}")
        
        # Test 2: Try different tool listing formats
        print("\n2. Testing tools/list...")
        
        # Try without params
        tools_msg1 = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        process.stdin.write(json.dumps(tools_msg1) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        print(f"Response (no params): {response.strip()}")
        
        # Try with empty params
        tools_msg2 = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/list",
            "params": {}
        }
        
        process.stdin.write(json.dumps(tools_msg2) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        print(f"Response (empty params): {response.strip()}")
        
        # Test 3: Try tool call
        print("\n3. Testing tools/call...")
        
        call_msg = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "take_a_break",
                "arguments": {}
            }
        }
        
        process.stdin.write(json.dumps(call_msg) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        print(f"Response: {response.strip()}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("\nTerminating server...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    interactive_test()
