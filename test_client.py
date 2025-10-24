#!/usr/bin/env python3
"""
Simple test client for ChillMCP server
Tests the basic functionality and command line parameters
"""

import asyncio
import json
import subprocess
import sys
import time
from typing import Dict, Any

class MCPTestClient:
    def __init__(self):
        self.process = None
        
    async def start_server(self, boss_alertness: int = 50, boss_alertness_cooldown: int = 60):
        """Start the ChillMCP server with given parameters"""
        cmd = [
            sys.executable, "main.py",
            "--boss_alertness", str(boss_alertness),
            "--boss_alertness_cooldown", str(boss_alertness_cooldown)
        ]
        
        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait a moment for server to start
        await asyncio.sleep(1)
        
    async def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a JSON-RPC request to the server"""
        if not self.process:
            raise RuntimeError("Server not started")
            
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }
        
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()
        
        # Read response
        response_line = await self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("No response from server")
            
        return json.loads(response_line.decode().strip())
        
    async def test_initialization(self):
        """Test server initialization"""
        print("Testing server initialization...")
        
        # Initialize request
        response = await self.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        })
        
        print(f"Initialize response: {response}")
        return response.get("result") is not None
        
    async def test_list_tools(self):
        """Test listing available tools"""
        print("Testing tool listing...")
        
        response = await self.send_request("tools/list", {})
        print(f"Tools list response: {response}")
        
        if "result" in response and "tools" in response["result"]:
            tools = response["result"]["tools"]
            print(f"Available tools: {[tool['name'] for tool in tools]}")
            return len(tools) >= 8  # Should have at least 8 tools
        return False
        
    async def test_tool_execution(self, tool_name: str):
        """Test executing a specific tool"""
        print(f"Testing tool execution: {tool_name}")
        
        response = await self.send_request("tools/call", {
            "name": tool_name,
            "arguments": {}
        })
        
        print(f"Tool execution response: {response}")
        
        if "result" in response and "content" in response["result"]:
            content = response["result"]["content"]
            if content and len(content) > 0:
                text_content = content[0].get("text", "")
                print(f"Tool output: {text_content}")
                
                # Check if response contains required fields
                has_break_summary = "Break Summary:" in text_content
                has_stress_level = "Stress Level:" in text_content
                has_boss_alert = "Boss Alert Level:" in text_content
                
                print(f"Response validation: Break Summary={has_break_summary}, Stress Level={has_stress_level}, Boss Alert={has_boss_alert}")
                return has_break_summary and has_stress_level and has_boss_alert
                
        return False
        
    async def cleanup(self):
        """Clean up the server process"""
        if self.process:
            self.process.terminate()
            await self.process.wait()

async def main():
    """Main test function"""
    print("Starting ChillMCP server tests...")
    
    client = MCPTestClient()
    
    try:
        # Test with different parameters
        print("\n=== Test 1: Basic parameters ===")
        await client.start_server(boss_alertness=50, boss_alertness_cooldown=60)
        
        # Test initialization
        init_success = await client.test_initialization()
        print(f"Initialization test: {'PASS' if init_success else 'FAIL'}")
        
        # Test tool listing
        tools_success = await client.test_list_tools()
        print(f"Tool listing test: {'PASS' if tools_success else 'FAIL'}")
        
        # Test a few tools
        test_tools = ["take_a_break", "watch_netflix", "show_meme"]
        for tool in test_tools:
            tool_success = await client.test_tool_execution(tool)
            print(f"Tool {tool} test: {'PASS' if tool_success else 'FAIL'}")
            await asyncio.sleep(0.5)  # Small delay between tests
            
        await client.cleanup()
        
        # Test with high boss alertness
        print("\n=== Test 2: High boss alertness ===")
        await client.start_server(boss_alertness=100, boss_alertness_cooldown=10)
        
        init_success = await client.test_initialization()
        print(f"Initialization test: {'PASS' if init_success else 'FAIL'}")
        
        # Test tool with high boss alertness (should trigger boss alert)
        tool_success = await client.test_tool_execution("take_a_break")
        print(f"Tool with high boss alertness test: {'PASS' if tool_success else 'FAIL'}")
        
        await client.cleanup()
        
        print("\n=== All tests completed ===")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
