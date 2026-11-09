import os
import sys
import json
import time
import subprocess

def get_disk_stats():
    stats = {}
    paths = {
        "gemini_root": os.path.expanduser("~") + r"\.gemini",
        "antigravity": os.path.expanduser("~") + r"\.gemini\antigravity",
        "antigravity_ide_legacy": os.path.expanduser("~") + r"\.gemini\antigravity-ide",
        "antigravity_scratch": os.path.expanduser("~") + r"\.gemini\antigravity\scratch",
        "gemini_config": os.path.expanduser("~") + r"\.gemini\config",
        "gemini_skills": os.path.expanduser("~") + r"\.gemini\config\skills",
    }
    for name, path in paths.items():
        if os.path.exists(path):
            total_size = 0
            file_count = 0
            for root, dirs, files in os.walk(path):
                file_count += len(files)
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        total_size += os.path.getsize(fp)
                    except OSError:
                        pass
            stats[name] = {
                "path": path,
                "file_count": file_count,
                "size_bytes": total_size,
                "size_mb": round(total_size / (1024 * 1024), 2)
            }
        else:
            stats[name] = {"path": path, "status": "not_found"}
    return stats

def get_process_stats():
    proc_summary = {
        "antigravity_electron": {"count": 0, "total_rss_mb": 0.0, "pids": []},
        "node_mcp": {"count": 0, "total_rss_mb": 0.0, "pids": [], "details": []},
        "python_services": {"count": 0, "total_rss_mb": 0.0, "pids": [], "details": []}
    }
    
    ps_cmd = """
    Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'Antigravity|node|python' } | Select-Object ProcessId, Name, WorkingSetSize, CommandLine | ConvertTo-Json -Compress
    """
    try:
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            raw = json.loads(res.stdout.strip())
            if isinstance(raw, dict):
                raw = [raw]
            for p in raw:
                pid = p.get("ProcessId")
                name = (p.get("Name") or "").lower()
                cmd = p.get("CommandLine") or ""
                ws_bytes = p.get("WorkingSetSize") or 0
                rss_mb = round(ws_bytes / (1024 * 1024), 2)
                
                if "antigravity" in name:
                    proc_summary["antigravity_electron"]["count"] += 1
                    proc_summary["antigravity_electron"]["total_rss_mb"] += rss_mb
                    proc_summary["antigravity_electron"]["pids"].append(pid)
                elif "node" in name and any(k in cmd.lower() for k in ["mcp", "telemetry", "atlassian"]):
                    proc_summary["node_mcp"]["count"] += 1
                    proc_summary["node_mcp"]["total_rss_mb"] += rss_mb
                    proc_summary["node_mcp"]["pids"].append(pid)
                    proc_summary["node_mcp"]["details"].append({"pid": pid, "rss_mb": rss_mb, "cmd": cmd[:120]})
                elif "python" in name:
                    proc_summary["python_services"]["count"] += 1
                    proc_summary["python_services"]["total_rss_mb"] += rss_mb
                    proc_summary["python_services"]["pids"].append(pid)
                    proc_summary["python_services"]["details"].append({"pid": pid, "rss_mb": rss_mb, "cmd": cmd[:120]})
    except Exception as e:
        proc_summary["error"] = str(e)

    proc_summary["antigravity_electron"]["total_rss_mb"] = round(proc_summary["antigravity_electron"]["total_rss_mb"], 2)
    proc_summary["node_mcp"]["total_rss_mb"] = round(proc_summary["node_mcp"]["total_rss_mb"], 2)
    proc_summary["python_services"]["total_rss_mb"] = round(proc_summary["python_services"]["total_rss_mb"], 2)
    return proc_summary

def get_mcp_and_hook_status():
    status = {}
    
    # 1. Check context MCP path
    mcp_config_path = os.path.expanduser("~") + r"\.gemini\config\mcp_config.json"
    if os.path.exists(mcp_config_path):
        with open(mcp_config_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        status['mcp_servers_configured'] = list(cfg.get('mcpServers', {}).keys())
        
        ctx_args = cfg.get('mcpServers', {}).get('context', {}).get('args', [])
        if ctx_args:
            ctx_path = ctx_args[0]
            status['context_mcp_path_valid'] = os.path.exists(ctx_path)
            status['context_mcp_path'] = ctx_path
    
    # 2. Check hook configuration
    hook_path = os.path.expanduser("~") + r"\.gemini\config\plugins\googlecloudtools.datacloud_telemetry\hooks.json"
    if os.path.exists(hook_path):
        with open(hook_path, 'r', encoding='utf-8') as f:
            h_cfg = json.load(f)
        pre_tool = h_cfg.get('googlecloudtools.datacloud_telemetry', {}).get('PreToolUse', [])
        status['telemetry_hook_configured'] = len(pre_tool) > 0
        if pre_tool:
            cmd = pre_tool[0].get('hooks', [{}])[0].get('command', '')
            status['telemetry_hook_cmd'] = cmd
            parts = cmd.split()
            status['telemetry_hook_has_fullpath'] = os.path.isabs(parts[1].replace('"', '')) if len(parts) > 1 else False
            
    # 3. Test telemetry hook execution in default CWD
    t0 = time.time()
    res = subprocess.run(
        ["node", "telemetry_hook_bundle.js", "--agent_name", "gemini", "--install_source", "AntigravityIDE"],
        capture_output=True,
        text=True,
        cwd=os.path.expanduser("~") + r"\AppData\Local\Programs\antigravity",
        shell=True
    )
    t1 = time.time()
    status['telemetry_hook_cwd_run'] = {
        "exit_code": res.returncode,
        "latency_ms": round((t1 - t0) * 1000, 2),
        "stderr_snippet": res.stderr[:120].strip()
    }
    
    return status

def get_token_baselines():
    metrics = {}
    gemini_md = os.path.expanduser("~") + r"\.gemini\GEMINI.md"
    if os.path.exists(gemini_md):
        size = os.path.getsize(gemini_md)
        metrics['gemini_md_bytes'] = size
        metrics['gemini_md_est_tokens'] = round(size / 4)
        
    skills_dir = os.path.expanduser("~") + r"\.gemini\config\skills"
    total_skill_desc_bytes = 0
    skill_counts = 0
    if os.path.exists(skills_dir):
        for s in os.listdir(skills_dir):
            sk_file = os.path.join(skills_dir, s, "SKILL.md")
            if os.path.exists(sk_file):
                skill_counts += 1
                try:
                    with open(sk_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    in_frontmatter = False
                    for line in lines:
                        if line.strip() == '---':
                            in_frontmatter = not in_frontmatter
                            continue
                        if in_frontmatter:
                            total_skill_desc_bytes += len(line.encode('utf-8'))
                except Exception:
                    pass
    metrics['skill_count'] = skill_counts
    metrics['skills_frontmatter_bytes'] = total_skill_desc_bytes
    metrics['skills_est_tokens'] = round(total_skill_desc_bytes / 4)
    metrics['total_static_system_overhead_est_tokens'] = metrics.get('gemini_md_est_tokens', 0) + metrics['skills_est_tokens'] + 1000
    return metrics

def main():
    print("Collecting system baseline metrics...")
    baseline = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "disk": get_disk_stats(),
        "processes": get_process_stats(),
        "mcp_and_hooks": get_mcp_and_hook_status(),
        "token_economics": get_token_baselines()
    }
    
    out_file = os.path.expanduser("~") + r"\.gemini\antigravity\scratch\antigravity-optimization-suite\benchmarks\baseline_metrics.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(baseline, f, indent=2)
    print(f"Baseline saved to {out_file}")
    print(json.dumps(baseline, indent=2))

if __name__ == "__main__":
    main()
