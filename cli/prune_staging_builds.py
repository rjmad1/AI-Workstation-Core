"""
Scratch Staging Build Pruner
Deterministically prunes disposable build and dependency artifacts (node_modules, .build, dist)
from scratch staging clones while preserving all source code, git histories, and configuration files.
"""

import os
import sys
import shutil
import time

TARGETS = [
    os.path.expanduser("~") + r"\.gemini\antigravity\scratch\omniroute-staging\.build",
    os.path.expanduser("~") + r"\.gemini\antigravity\scratch\omniroute-staging\node_modules",
    os.path.expanduser("~") + r"\.gemini\antigravity\scratch\omniroute-staging\dist",
    os.path.expanduser("~") + r"\.gemini\antigravity\scratch\deepseek-harness-repo\node_modules",
    os.path.expanduser("~") + r"\.gemini\antigravity\scratch\dsh-platform\node_modules"
]

def get_dir_metrics(path):
    total_size = 0
    file_count = 0
    if not os.path.exists(path):
        return 0, 0
    for root, dirs, files in os.walk(path):
        file_count += len(files)
        for f in files:
            try:
                total_size += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return file_count, total_size

def prune_directory(path):
    if not os.path.exists(path):
        return 0, 0
    print(f"Scanning {path}...")
    file_count, size_bytes = get_dir_metrics(path)
    size_mb = round(size_bytes / (1024 * 1024), 2)
    print(f"  Target: {file_count} files, {size_mb} MB")
    
    # Prune directory tree safely
    try:
        shutil.rmtree(path)
        print(f"  [SUCCESS] Removed {path}")
        return file_count, size_bytes
    except Exception as e:
        print(f"  [ERROR] Failed to remove {path}: {e}")
        return 0, 0

def main():
    print("=== STARTING SCRATCH BUILD & CACHE PRUNING ===")
    total_files_pruned = 0
    total_bytes_pruned = 0
    
    for t in TARGETS:
        fc, sz = prune_directory(t)
        total_files_pruned += fc
        total_bytes_pruned += sz
        
    total_mb = round(total_bytes_pruned / (1024 * 1024), 2)
    total_gb = round(total_bytes_pruned / (1024 * 1024 * 1024), 2)
    
    print("\n=== PRUNING SUMMARY ===")
    print(f"Total files removed: {total_files_pruned:,}")
    print(f"Total storage reclaimed: {total_mb:,} MB ({total_gb} GB)")

if __name__ == "__main__":
    main()
