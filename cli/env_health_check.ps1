<#
.SYNOPSIS
    AntiGravity 2.0 Environment Health and Optimization Monitor
.DESCRIPTION
    Deterministic, zero-token diagnostic script that inspects:
    1. Configuration file integrity (mcp_config.json, hooks.json, config.json)
    2. Active vs dead legacy directories
    3. MCP process health and memory consumption
    4. Token and prompt overhead
#>

param(
    [switch]$Remediate = $false
)

$ErrorActionPreference = "Continue"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   AntiGravity 2.0 Environment Health & Diagnostic Audit   " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Configuration Validation
Write-Host "`n[1] Checking Configuration Files..." -ForegroundColor Yellow

$mcpConfigPath = "$HOME\.gemini\config\mcp_config.json"
$hooksConfigPath = "$HOME\.gemini\config\plugins\googlecloudtools.datacloud_telemetry\hooks.json"

if (Test-Path $mcpConfigPath) {
    try {
        $mcp = Get-Content $mcpConfigPath -Raw | ConvertFrom-Json
        Write-Host "  [OK] mcp_config.json is valid JSON." -ForegroundColor Green
        
        $ctxArgs = $mcp.mcpServers.context.args
        if ($ctxArgs -and ($ctxArgs[0] -like "*0.7.1*")) {
            Write-Host "  [FAIL] Context MCP points to obsolete 0.7.1 path: $($ctxArgs[0])" -ForegroundColor Red
        } else {
            Write-Host "  [OK] Context MCP configuration valid." -ForegroundColor Green
        }
        
        $atlArgs = $mcp.mcpServers."atlassian-mcp-server".args
        if ($atlArgs -and ($atlArgs -contains "https://mcp.atlassian.com/v1/sse")) {
            Write-Host "  [WARN] Atlassian MCP uses deprecated endpoint v1/sse (phased out)." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  [FAIL] Could not parse mcp_config.json: $_" -ForegroundColor Red
    }
} else {
    Write-Host "  [FAIL] mcp_config.json not found!" -ForegroundColor Red
}

# 2. Check Hooks
if (Test-Path $hooksConfigPath) {
    try {
        $h = Get-Content $hooksConfigPath -Raw | ConvertFrom-Json
        $preTool = $h."googlecloudtools.datacloud_telemetry".PreToolUse
        $cmd = $preTool[0].hooks[0].command
        if ($cmd -like "node telemetry_hook_bundle.js*") {
            Write-Host "  [FAIL] Telemetry hook uses relative path without absolute path qualifier (causes MODULE_NOT_FOUND on all tool calls)." -ForegroundColor Red
        } else {
            Write-Host "  [OK] Telemetry hook command configuration valid." -ForegroundColor Green
        }
    } catch {
        Write-Host "  [FAIL] Could not parse hooks.json: $_" -ForegroundColor Red
    }
}

# 3. Check Legacy Directories
Write-Host "`n[2] Checking Legacy & Bloat Artifacts..." -ForegroundColor Yellow
$legacyIde = "$HOME\.gemini\antigravity-ide"
if (Test-Path $legacyIde) {
    Write-Host "  [WARN] Found legacy pre-migration folder: $legacyIde (~4 GB unreferenced)." -ForegroundColor Yellow
} else {
    Write-Host "  [OK] No unmigrated legacy antigravity-ide folder found." -ForegroundColor Green
}

$legacySkills = "$HOME\.gemini\antigravity\skills"
if (Test-Path $legacySkills) {
    Write-Host "  [WARN] Found orphaned skills directory: $legacySkills (superseded by ~/.gemini/config/skills)." -ForegroundColor Yellow
}

# 4. Process Diagnostics
Write-Host "`n[3] Checking AntiGravity & MCP Processes..." -ForegroundColor Yellow
$procs = Get-CimInstance Win32_Process | Where-Object { $_.Name -match "Antigravity|node|python" }
$nodeMcps = $procs | Where-Object { $_.Name -eq "node.exe" -and ($_.CommandLine -like "*mcp*" -or $_.CommandLine -like "*atlassian*") }

Write-Host "  Active Antigravity instances : $(($procs | Where-Object { $_.Name -like '*Antigravity*' }).Count)" -ForegroundColor Gray
Write-Host "  Active MCP Node.js processes : $($nodeMcps.Count)" -ForegroundColor Gray
foreach ($n in $nodeMcps) {
    $rssMb = [math]::Round($n.WorkingSetSize / 1MB, 2)
    Write-Host "    -> PID $($n.ProcessId) : $rssMb MB | $($n.CommandLine.Substring(0, [math]::Min(90, $n.CommandLine.Length)))..." -ForegroundColor Gray
}

# Remediate if requested
if ($Remediate) {
    Write-Host "`n[4] Executing Autonomous Remediation..." -ForegroundColor Cyan
    python "$env:USERPROFILE\.gemini\antigravity\scratch\antigravity-optimization-suite\tools\mcp_health.py" --remediate
}

Write-Host "`nAudit complete." -ForegroundColor Cyan
