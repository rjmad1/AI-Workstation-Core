"""
MCP and Plugin Health Engine for AntiGravity 2.0
Audits, diagnoses, tests, and autonomously remediates configuration errors in
MCP servers and agent lifecycle hooks.
"""

import os
import sys
import json
import shutil
import time

MCP_CONFIG_PATH = os.path.expanduser("~") + r"\.gemini\config\mcp_config.json"
HOOKS_CONFIG_PATH = os.path.expanduser("~") + r"\.gemini\config\plugins\googlecloudtools.datacloud_telemetry\hooks.json"
BACKUP_DIR = os.path.expanduser("~") + r"\.gemini\antigravity\backups\pre_audit_20261107"

class McpHealthEngine:
    def __init__(self):
        self.mcp_config_path = MCP_CONFIG_PATH
        self.hooks_path = HOOKS_CONFIG_PATH

    def audit(self):
        findings = []
        
        # 1. Audit MCP servers
        if os.path.exists(self.mcp_config_path):
            with open(self.mcp_config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            servers = cfg.get("mcpServers", {})
            for name, scfg in servers.items():
                args = scfg.get("args", [])
                cmd = scfg.get("command", "")
                
                # Check path validity for stdio scripts
                for arg in args:
                    if (arg.endswith(".js") or arg.endswith(".py") or "\\" in arg or "/" in arg) and not arg.startswith("http"):
                        if not os.path.exists(arg):
                            findings.append({
                                "id": f"MCP-ERR-{name.upper()}-PATH",
                                "severity": "P0",
                                "target": name,
                                "type": "MISSING_FILE",
                                "detail": f"Path does not exist: {arg}",
                                "remediation": "Update path to active installed extension version."
                            })
                            
                # Check for deprecated Atlassian SSE endpoint
                for arg in args:
                    if "atlassian.com/v1/sse" in arg:
                        findings.append({
                            "id": "MCP-ERR-ATLASSIAN-DEPRECATED",
                            "severity": "P0",
                            "target": name,
                            "type": "DEPRECATED_ENDPOINT",
                            "detail": "HTTP+SSE endpoint https://mcp.atlassian.com/v1/sse is phased out by Atlassian.",
                            "remediation": "Migrate to https://mcp.atlassian.com/v2/mcp or disable server."
                        })
        else:
            findings.append({
                "id": "MCP-ERR-NOCONFIG",
                "severity": "P1",
                "detail": f"mcp_config.json not found at {self.mcp_config_path}"
            })
            
        # 2. Audit Lifecycle Hooks
        if os.path.exists(self.hooks_path):
            with open(self.hooks_path, "r", encoding="utf-8") as f:
                hcfg = json.load(f)
            pre_tool = hcfg.get("googlecloudtools.datacloud_telemetry", {}).get("PreToolUse", [])
            for pt in pre_tool:
                for h in pt.get("hooks", []):
                    c = h.get("command", "")
                    tokens = c.split()
                    if len(tokens) > 1 and tokens[0] == "node":
                        target_script = tokens[1].replace('"', '')
                        if not os.path.isabs(target_script):
                            findings.append({
                                "id": "HOOK-ERR-REL-PATH",
                                "severity": "P0",
                                "target": "googlecloudtools.datacloud_telemetry",
                                "type": "RELATIVE_HOOK_PATH",
                                "detail": f"Hook script '{target_script}' has relative path, causing MODULE_NOT_FOUND on every tool call.",
                                "remediation": "Use absolute path to telemetry_hook_bundle.js."
                            })
                            
        return findings

    def remediate(self, dry_run=False):
        results = []
        
        # Ensure backup exists
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        # 1. Remediate Context MCP server path
        if os.path.exists(self.mcp_config_path):
            with open(self.mcp_config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            
            modified_mcp = False
            ctx = cfg.get("mcpServers", {}).get("context", {})
            if ctx:
                args = ctx.get("args", [])
                new_args = []
                for arg in args:
                    if "datacloud-0.7.1-universal" in arg:
                        upgraded = arg.replace("datacloud-0.7.1-universal", "datacloud-1.2.0-universal")
                        if os.path.exists(upgraded):
                            new_args.append(upgraded)
                            modified_mcp = True
                            results.append(f"Fixed 'context' MCP server path: updated 0.7.1 to 1.2.0 ({upgraded})")
                        else:
                            new_args.append(arg)
                    else:
                        new_args.append(arg)
                ctx["args"] = new_args

            # Check atlassian endpoint
            atlassian = cfg.get("mcpServers", {}).get("atlassian-mcp-server", {})
            if atlassian:
                atl_args = atlassian.get("args", [])
                new_atl_args = []
                for arg in atl_args:
                    if "https://mcp.atlassian.com/v1/sse" in arg:
                        new_atl_args.append("https://mcp.atlassian.com/v2/mcp")
                        modified_mcp = True
                        results.append("Updated 'atlassian-mcp-server' endpoint: migrated v1/sse to v2/mcp")
                    else:
                        new_atl_args.append(arg)
                atlassian["args"] = new_atl_args
                
            if modified_mcp and not dry_run:
                # Backup
                shutil.copy2(self.mcp_config_path, os.path.join(BACKUP_DIR, f"mcp_config.json.pre_fix_{int(time.time())}"))
                with open(self.mcp_config_path, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, indent=2)
                results.append("Saved updated mcp_config.json")
                
        # 2. Remediate Telemetry Hook path
        if os.path.exists(self.hooks_path):
            with open(self.hooks_path, "r", encoding="utf-8") as f:
                hcfg = json.load(f)
                
            modified_hooks = False
            bundle_abs_path = os.path.abspath(os.path.join(os.path.dirname(self.hooks_path), "telemetry_hook_bundle.js"))
            
            pre_tool = hcfg.get("googlecloudtools.datacloud_telemetry", {}).get("PreToolUse", [])
            for pt in pre_tool:
                for h in pt.get("hooks", []):
                    c = h.get("command", "")
                    if "node telemetry_hook_bundle.js" in c:
                        # Fix to use absolute quoted path
                        fixed_cmd = f'node "{bundle_abs_path}" --agent_name gemini --install_source AntigravityIDE || exit 0'
                        h["command"] = fixed_cmd
                        modified_hooks = True
                        results.append(f"Fixed telemetry hook command to use absolute path: {fixed_cmd}")
                        
            if modified_hooks and not dry_run:
                shutil.copy2(self.hooks_path, os.path.join(BACKUP_DIR, f"hooks.json.pre_fix_{int(time.time())}"))
                with open(self.hooks_path, "w", encoding="utf-8") as f:
                    json.dump(hcfg, f, indent=2)
                results.append("Saved updated hooks.json")
                
        return results

if __name__ == "__main__":
    engine = McpHealthEngine()
    print("=== MCP & HOOK AUDIT ===")
    findings = engine.audit()
    print(json.dumps(findings, indent=2))
    
    if "--remediate" in sys.argv:
        print("\n=== EXECUTING REMEDIATION ===")
        remed_results = engine.remediate(dry_run=False)
        for r in remed_results:
            print(f"[REMEDIATED] {r}")
