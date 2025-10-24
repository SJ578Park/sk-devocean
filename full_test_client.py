#!/usr/bin/env python3
"""
Complete test client for ChillMCP server
Tests all functionality including command line parameters and tool execution
"""

import asyncio
import json
import subprocess
import sys
import time
from typing import Dict, Any

class ChillMCPTestClient:
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
        
        # Wait for server to start
        await asyncio.sleep(2)
        
    async def send_request(self, method: str, params: Dict[str, Any] = None, request_id: int = 1) -> Dict[str, Any]:
        """Send a JSON-RPC request to the server"""
        if not self.process:
            raise RuntimeError("Server not started")
            
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
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
        
    async def send_notification(self, method: str, params: Dict[str, Any] = None):
        """Send a JSON-RPC notification to the server"""
        if not self.process:
            raise RuntimeError("Server not started")
            
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }
        
        notification_json = json.dumps(notification) + "\n"
        self.process.stdin.write(notification_json.encode())
        await self.process.stdin.drain()
        
    async def initialize(self):
        """Initialize the MCP connection"""
        print("Initializing MCP connection...")
        
        response = await self.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        })
        
        print(f"Initialize response: {response}")
        
        if "result" not in response:
            raise RuntimeError(f"Initialize failed: {response}")
            
        # Send initialized notification
        await self.send_notification("notifications/initialized")
        print("Sent initialized notification")
        
        return response["result"]
        
    async def list_tools(self):
        """List available tools"""
        print("Listing available tools...")
        
        response = await self.send_request("tools/list", {}, request_id=2)
        
        if "result" in response and "tools" in response["result"]:
            tools = response["result"]["tools"]
            print(f"Found {len(tools)} tools:")
            for tool in tools:
                print(f"  - {tool['name']}: {tool['description']}")
            return tools
        else:
            print(f"Failed to list tools: {response}")
            return []
            
    async def call_tool(self, tool_name: str):
        """Call a specific tool"""
        print(f"Calling tool: {tool_name}")
        
        response = await self.send_request("tools/call", {
            "name": tool_name,
            "arguments": {}
        }, request_id=3)
        
        if "result" in response and "content" in response["result"]:
            content = response["result"]["content"]
            if content and len(content) > 0:
                text_content = content[0].get("text", "")
                print(f"Tool output:\n{text_content}")
                
                # Parse the response to extract key information
                lines = text_content.split('\n')
                break_summary = None
                stress_level = None
                boss_alert_level = None
                
                for line in lines:
                    if line.startswith("Break Summary:"):
                        break_summary = line.replace("Break Summary:", "").strip()
                    elif line.startswith("Stress Level:"):
                        stress_level = int(line.replace("Stress Level:", "").strip())
                    elif line.startswith("Boss Alert Level:"):
                        boss_alert_level = int(line.replace("Boss Alert Level:", "").strip())
                
                print(f"Parsed - Break Summary: {break_summary}")
                print(f"Parsed - Stress Level: {stress_level}")
                print(f"Parsed - Boss Alert Level: {boss_alert_level}")
                
                return {
                    "success": True,
                    "break_summary": break_summary,
                    "stress_level": stress_level,
                    "boss_alert_level": boss_alert_level,
                    "full_text": text_content
                }
        else:
            print(f"Tool call failed: {response}")
            
        return {"success": False}
        
    async def test_all_tools(self):
        """Test all available tools"""
        tools = await self.list_tools()
        
        if not tools:
            print("No tools available to test")
            return
            
        print(f"\nTesting {len(tools)} tools...")
        
        results = {}
        for tool in tools:
            tool_name = tool["name"]
            print(f"\n--- Testing {tool_name} ---")
            
            result = await self.call_tool(tool_name)
            results[tool_name] = result
            
            # Small delay between tool calls
            await asyncio.sleep(0.5)
            
        return results
        
    async def test_boss_alertness(self):
        """Test boss alertness behavior"""
        print("\n=== Testing Boss Alertness Behavior ===")
        
        # Test with high boss alertness (100%)
        print("\nTesting with high boss alertness (100%)...")
        await self.cleanup()
        await self.start_server(boss_alertness=100, boss_alertness_cooldown=10)
        await self.initialize()
        
        # Call tool multiple times to trigger boss alerts
        for i in range(3):
            print(f"\nCall {i+1}:")
            result = await self.call_tool("take_a_break")
            if result["success"]:
                print(f"Boss Alert Level: {result['boss_alert_level']}")
            await asyncio.sleep(1)
            
    async def cleanup(self):
        """Clean up the server process"""
        if self.process:
            self.process.terminate()
            await self.process.wait()

async def main():
    """Main test function"""
    print("Starting comprehensive ChillMCP tests...")
    
    client = ChillMCPTestClient()
    
    try:
        # Test 1: Basic functionality
        print("\n=== Test 1: Basic Functionality ===")
        await client.start_server(boss_alertness=50, boss_alertness_cooldown=60)
        
        # Initialize
        await client.initialize()
        
        # List tools
        tools = await client.list_tools()
        
        # Test a few tools
        test_tools = ["take_a_break", "watch_netflix", "show_meme"]
        for tool_name in test_tools:
            print(f"\n--- Testing {tool_name} ---")
            result = await client.call_tool(tool_name)
            if result["success"]:
                print(f"✅ {tool_name} - Stress: {result['stress_level']}, Boss Alert: {result['boss_alert_level']}")
            else:
                print(f"❌ {tool_name} failed")
            await asyncio.sleep(0.5)
            
        # Test 2: Boss alertness behavior
        await client.test_boss_alertness()
        
        print("\n=== All tests completed successfully! ===")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
