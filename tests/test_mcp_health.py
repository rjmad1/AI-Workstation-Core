import os
import sys
import json
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tools")))
from mcp_health import McpHealthEngine

class TestMcpHealth(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mcp_file = os.path.join(self.temp_dir, "mcp_config.json")
        self.hooks_file = os.path.join(self.temp_dir, "hooks.json")
        
        # Write dummy configs matching real failure cases
        mcp_data = {
            "mcpServers": {
                "context": {
                    "command": "node",
                    "args": ["c:\\dummy\\datacloud-0.7.1-universal\\mcp_proxy_bundle.js"]
                },
                "atlassian-mcp-server": {
                    "command": "npx",
                    "args": ["-y", "mcp-remote", "https://mcp.atlassian.com/v1/sse"]
                }
            }
        }
        with open(self.mcp_file, "w") as f:
            json.dump(mcp_data, f)
            
        hooks_data = {
            "googlecloudtools.datacloud_telemetry": {
                "PreToolUse": [
                    {
                        "hooks": [
                            {"command": "node telemetry_hook_bundle.js --agent_name gemini"}
                        ]
                    }
                ]
            }
        }
        with open(self.hooks_file, "w") as f:
            json.dump(hooks_data, f)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_audit_detection(self):
        engine = McpHealthEngine()
        engine.mcp_config_path = self.mcp_file
        engine.hooks_path = self.hooks_file
        
        findings = engine.audit()
        self.assertTrue(any(f["id"] == "MCP-ERR-CONTEXT-PATH" for f in findings))
        self.assertTrue(any(f["id"] == "MCP-ERR-ATLASSIAN-DEPRECATED" for f in findings))
        self.assertTrue(any(f["id"] == "HOOK-ERR-REL-PATH" for f in findings))

if __name__ == "__main__":
    unittest.main()
