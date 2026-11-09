"""
System Environment and Resource Monitor for AntiGravity 2.0
Monitors memory, process health, configuration integrity, and flags dead legacy artifacts.
"""

import os
import sys
import json
import time
import subprocess

def run_ps(cmd):
    try:
        res = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
        return res.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def check_legacy_paths():
    findings = []
    legacy_ide = os.path.expanduser("~") + r"\.gemini\antigravity-ide"
    if os.path.exists(legacy_ide):
        file_count = 0
        total_size = 0
        for root, dirs, files in os.walk(legacy_ide):
            file_count += len(files)
            for f in files:
                try:
                    total_size += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
        findings.append({
            "target": legacy_ide,
            "type": "DEAD_LEGACY_DIRECTORY",
            "file_count": file_count,
            "size_mb": round(total_size / (1024 * 1024), 2),
            "recommendation": "Legacy pre-migration directory. Back up essential archives and prune to reclaim disk and eliminate file-watcher overhead."
        })
        
    legacy_skills = os.path.expanduser("~") + r"\.gemini\antigravity\skills"
    if os.path.exists(legacy_skills):
        file_count = sum(len(files) for _, _, files in os.walk(legacy_skills))
        findings.append({
            "target": legacy_skills,
            "type": "ORPHANED_SKILLS_FOLDER",
            "file_count": file_count,
            "recommendation": "Old skills folder from 03-06-2026. Customizations are now discovered in ~/.gemini/config/skills. Safe to archive."
        })
        
    return findings

def check_process_health():
    ps_cmd = """
    Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'Antigravity|node|python' } | Select-Object ProcessId, Name, WorkingSetSize, CommandLine | ConvertTo-Json -Compress
    """
    raw_json = run_ps(ps_cmd)
    processes = []
    if raw_json and not raw_json.startswith("Error"):
        try:
            parsed = json.loads(raw_json)
            if isinstance(parsed, dict):
                parsed = [parsed]
            for p in parsed:
                processes.append({
                    "pid": p.get("ProcessId"),
                    "name": p.get("Name"),
                    "rss_mb": round((p.get("WorkingSetSize") or 0) / (1024 * 1024), 2),
                    "cmd": (p.get("CommandLine") or "")[:120]
                })
        except Exception:
            pass
    return processes

def generate_health_report():
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "legacy_artifacts": check_legacy_paths(),
        "active_processes": check_process_health()
    }
    return report

if __name__ == "__main__":
    report = generate_health_report()
    print("=== ENVIRONMENT HEALTH REPORT ===")
    print(json.dumps(report, indent=2))
