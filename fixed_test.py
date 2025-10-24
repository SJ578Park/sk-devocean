#!/usr/bin/env python3
"""
Fixed test for ChillMCP server
Tests stress auto-increase and boss alert cooldown more accurately
"""

import asyncio
import json
import subprocess
import sys
import time
from typing import Dict, Any

class FixedChillMCPTest:
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
        
        await asyncio.sleep(2)
        
    async def send_request(self, method: str, params: Dict[str, Any] = None, request_id: int = 1) -> Dict[str, Any]:
        """Send a JSON-RPC request to the server"""
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }
        
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()
        
        response_line = await self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("No response from server")
            
        return json.loads(response_line.decode().strip())
        
    async def send_notification(self, method: str, params: Dict[str, Any] = None):
        """Send a JSON-RPC notification to the server"""
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
        response = await self.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        })
        
        await self.send_notification("notifications/initialized")
        return response["result"]
        
    async def call_tool(self, tool_name: str):
        """Call a specific tool and parse response"""
        response = await self.send_request("tools/call", {
            "name": tool_name,
            "arguments": {}
        }, request_id=3)
        
        if "result" in response and "content" in response["result"]:
            content = response["result"]["content"]
            if content and len(content) > 0:
                text_content = content[0].get("text", "")
                
                # Parse the response
                lines = text_content.split('\n')
                stress_level = None
                boss_alert_level = None
                
                for line in lines:
                    if line.startswith("Stress Level:"):
                        stress_level = int(line.replace("Stress Level:", "").strip())
                    elif line.startswith("Boss Alert Level:"):
                        boss_alert_level = int(line.replace("Boss Alert Level:", "").strip())
                
                return {
                    "success": True,
                    "stress_level": stress_level,
                    "boss_alert_level": boss_alert_level,
                    "full_text": text_content
                }
                
        return {"success": False}
        
    async def test_stress_auto_increase_fixed(self):
        """Test stress level auto-increase by checking the stress growth message"""
        print("\n=== Test: Stress Level Auto-Increase (Fixed) ===")
        
        await self.start_server(boss_alertness=0, boss_alertness_cooldown=300)  # No boss alerts
        await self.initialize()
        
        # Get initial stress level
        result1 = await self.call_tool("take_a_break")
        initial_stress = result1["stress_level"]
        print(f"Initial stress level: {initial_stress}")
        print(f"Initial response: {result1['full_text']}")
        
        # Wait for stress to increase (should increase by 1 every minute)
        print("Waiting 65 seconds for stress to auto-increase...")
        await asyncio.sleep(65)
        
        # Call tool again to see if stress increased
        result2 = await self.call_tool("take_a_break")
        new_stress = result2["stress_level"]
        
        print(f"Stress level after 65 seconds: {new_stress}")
        print(f"Second response: {result2['full_text']}")
        
        # Check if the response mentions stress growth
        if "Stress kept climbing" in result2['full_text']:
            print("✅ Stress auto-increase working correctly (found growth message)")
        else:
            print("❌ Stress auto-increase NOT working (no growth message)")
            
        await self.cleanup()
        
    async def test_boss_alert_cooldown_fixed(self):
        """Test boss alert level cooldown mechanism with better timing"""
        print("\n=== Test: Boss Alert Cooldown (Fixed) ===")
        
        await self.start_server(boss_alertness=100, boss_alertness_cooldown=5)  # Very short cooldown
        await self.initialize()
        
        # Raise boss alert level to 2
        result1 = await self.call_tool("take_a_break")
        boss_level_1 = result1["boss_alert_level"]
        print(f"Boss Alert Level after first call: {boss_level_1}")
        
        result2 = await self.call_tool("take_a_break")
        boss_level_2 = result2["boss_alert_level"]
        print(f"Boss Alert Level after second call: {boss_level_2}")
        
        # Wait for cooldown period
        print("Waiting 7 seconds for cooldown...")
        await asyncio.sleep(7)
        
        # Call tool again (should trigger cooldown)
        result3 = await self.call_tool("take_a_break")
        boss_level_3 = result3["boss_alert_level"]
        print(f"Boss Alert Level after cooldown: {boss_level_3}")
        print(f"Third response: {result3['full_text']}")
        
        # Check if the response mentions cooldown
        if "cooled down" in result3['full_text']:
            print("✅ Boss alert cooldown working correctly (found cooldown message)")
        else:
            print("❌ Boss alert cooldown NOT working (no cooldown message)")
            
        await self.cleanup()
        
    async def cleanup(self):
        """Clean up the server process"""
        if self.process:
            try:
                self.process.terminate()
                await self.process.wait()
            except:
                pass

async def main():
    """Run fixed tests"""
    print("Starting fixed ChillMCP tests...")
    
    test_client = FixedChillMCPTest()
    
    try:
        # Test 1: Stress auto-increase (fixed)
        await test_client.test_stress_auto_increase_fixed()
        
        # Test 2: Boss alert cooldown (fixed)
        await test_client.test_boss_alert_cooldown_fixed()
        
        print("\n=== All fixed tests completed ===")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await test_client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
