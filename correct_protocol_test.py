#!/usr/bin/env python3
"""
Correct MCP protocol test with proper initialization sequence
"""

import json
import subprocess
import sys
import time

def test_correct_protocol():
    """Test with correct MCP protocol sequence"""
    
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
        print("Testing correct MCP protocol sequence...")
        
        # Step 1: Initialize
        print("\n1. Initialize...")
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
        
        # Step 2: Send initialized notification
        print("\n2. Sending initialized notification...")
        initialized_msg = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        process.stdin.write(json.dumps(initialized_msg) + "\n")
        process.stdin.flush()
        
        # Step 3: Now try tools/list
        print("\n3. Testing tools/list...")
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
        
        # Step 4: Try tool call
        print("\n4. Testing tools/call...")
        call_msg = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "take_a_break",
                "arguments": {}
            }
        }
        
        process.stdin.write(json.dumps(call_msg) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        print(f"Tool call response: {response.strip()}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("\nTerminating server...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    test_correct_protocol()
