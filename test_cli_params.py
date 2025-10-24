#!/usr/bin/env python3
"""
Test command line parameters
"""

import subprocess
import sys
import time

def test_cli_parameters():
    """Test different command line parameter combinations"""
    
    test_cases = [
        {
            "name": "Default parameters",
            "args": []
        },
        {
            "name": "High boss alertness",
            "args": ["--boss_alertness", "100", "--boss_alertness_cooldown", "10"]
        },
        {
            "name": "Low boss alertness",
            "args": ["--boss_alertness", "0", "--boss_alertness_cooldown", "300"]
        },
        {
            "name": "Medium settings",
            "args": ["--boss_alertness", "50", "--boss_alertness_cooldown", "60"]
        }
    ]
    
    for test_case in test_cases:
        print(f"\n=== Testing: {test_case['name']} ===")
        
        cmd = [sys.executable, "main.py"] + test_case["args"]
        
        try:
            # Start server
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            time.sleep(2)
            
            # Check if server is running
            if process.poll() is None:
                print(f"✅ Server started successfully with args: {test_case['args']}")
                
                # Read stderr to see the startup message
                try:
                    stderr_output = process.stderr.read()
                    if "Starting ChillMCP with boss_alertness" in stderr_output:
                        print(f"✅ Startup message found in stderr")
                    else:
                        print(f"⚠️ Startup message not found")
                except:
                    pass
                    
            else:
                print(f"❌ Server failed to start with args: {test_case['args']}")
                
            # Terminate server
            process.terminate()
            process.wait()
            
        except Exception as e:
            print(f"❌ Error testing {test_case['name']}: {e}")

if __name__ == "__main__":
    test_cli_parameters()
