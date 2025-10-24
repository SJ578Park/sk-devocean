#!/usr/bin/env python3
"""
Manual MCP protocol test
Tests the exact JSON-RPC format expected by FastMCP
"""

import json
import subprocess
import sys
import time

def test_mcp_protocol():
    """Test MCP protocol with manual JSON-RPC messages"""
    
    # Start the server
    cmd = [sys.executable, "main.py", "--boss_alertness", "50", "--boss_alertness_cooldown", "60"]
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    time.sleep(1)
    
    try:
        # Test 1: Initialize
        print("=== Test 1: Initialize ===")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        print(f"Initialize response: {response.strip()}")
        
        # Test 2: List tools
        print("\n=== Test 2: List tools ===")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        process.stdin.write(json.dumps(tools_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        print(f"Tools list response: {response.strip()}")
        
        # Test 3: Call tool
        print("\n=== Test 3: Call tool ===")
        call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "take_a_break",
                "arguments": {}
            }
        }
        
        process.stdin.write(json.dumps(call_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        print(f"Tool call response: {response.strip()}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    test_mcp_protocol()
