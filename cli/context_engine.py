"""
Context Efficiency Layer for AntiGravity 2.0
Provides deterministic, change-aware repository indexing, selective file retrieval,
and strict exclusion filtering to prevent unnecessary token consumption.
"""

import os
import sys
import json
import time
import hashlib
import fnmatch

DEFAULT_EXCLUDES = [
    # VCS & IDE
    ".git", ".svn", ".hg", ".vscode", ".idea", ".antigravity", ".gemini",
    # Dependencies & Package Managers
    "node_modules", "vendor", "bower_components", "packages",
    # Virtual Environments
    ".venv", "venv", "env", ".env", "virtualenv", "__pycache__", ".pytest_cache",
    # Build Artifacts & Dist
    "dist", "build", "out", "target", "bin", "obj", ".next", ".nuxt", ".svelte-kit",
    # Cache & Temporary
    "cache", "tmp", "temp", ".cache", ".turbo", ".webpack",
    # Logs & Diagnostics
    "logs", "*.log", "*.tmp", "*.bak", "*.swp",
    # Large Binaries / Media
    "*.exe", "*.dll", "*.so", "*.dylib", "*.bin", "*.zip", "*.tar", "*.gz",
    "*.mp4", "*.mkv", "*.avi", "*.mov", "*.webm", "*.iso", "*.img",
    "*.sqlite", "*.db", "*.db-wal", "*.db-shm", "*.parquet"
]

class ContextEngine:
    def __init__(self, root_dir, custom_excludes=None):
        self.root_dir = os.path.abspath(root_dir)
        self.excludes = set(DEFAULT_EXCLUDES)
        if custom_excludes:
            self.excludes.update(custom_excludes)
            
        # Check for .agyignore or .gitignore
        self._load_ignore_file(".agyignore")
        self._load_ignore_file(".gitignore")
        
        self.index_file = os.path.join(self.root_dir, ".agy_context_index.json")
        self.index = self._load_index()

    def _load_ignore_file(self, filename):
        ignore_path = os.path.join(self.root_dir, filename)
        if os.path.exists(ignore_path):
            try:
                with open(ignore_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            self.excludes.add(line)
            except Exception:
                pass

    def _is_excluded(self, path):
        rel_path = os.path.relpath(path, self.root_dir).replace("\\", "/")
        parts = rel_path.split("/")
        
        for part in parts:
            for pattern in self.excludes:
                if fnmatch.fnmatch(part, pattern):
                    return True
        for pattern in self.excludes:
            if fnmatch.fnmatch(rel_path, pattern):
                return True
        return False

    def _load_index(self):
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_index(self):
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(self.index, f, indent=2)
        except Exception as e:
            print(f"[ContextEngine] Warning: Could not save index: {e}", file=sys.stderr)

    def scan_and_index(self, max_file_size_kb=512):
        """Builds or refreshes the index deterministically."""
        changes = {"added": 0, "modified": 0, "deleted": 0, "unchanged": 0}
        seen_files = set()
        
        for root, dirs, files in os.walk(self.root_dir):
            # Prune excluded directories in-place to avoid deep traversal
            dirs[:] = [d for d in dirs if not self._is_excluded(os.path.join(root, d))]
            
            for file in files:
                file_path = os.path.join(root, file)
                if self._is_excluded(file_path):
                    continue
                    
                rel_path = os.path.relpath(file_path, self.root_dir).replace("\\", "/")
                seen_files.add(rel_path)
                
                try:
                    stat = os.stat(file_path)
                    mtime = stat.st_mtime
                    size = stat.st_size
                    
                    if size > max_file_size_kb * 1024:
                        # Exclude oversized text/data files from full ingestion
                        continue
                        
                    cached = self.index.get(rel_path)
                    if cached and cached.get("mtime") == mtime and cached.get("size") == size:
                        changes["unchanged"] += 1
                        continue
                        
                    # Calculate lightweight hash (first 8KB + file size)
                    with open(file_path, "rb") as f:
                        header = f.read(8192)
                    quick_hash = hashlib.sha256(header + str(size).encode()).hexdigest()[:16]
                    
                    if not cached:
                        changes["added"] += 1
                    else:
                        changes["modified"] += 1
                        
                    self.index[rel_path] = {
                        "mtime": mtime,
                        "size": size,
                        "hash": quick_hash,
                        "last_scanned": time.time()
                    }
                except OSError:
                    pass
                    
        # Check for deleted files
        for indexed_file in list(self.index.keys()):
            if indexed_file not in seen_files:
                del self.index[indexed_file]
                changes["deleted"] += 1
                
        self._save_index()
        return changes

    def get_concise_outline(self):
        """Produces a compact directory tree for the prompt without raw file bodies."""
        tree = {}
        for rel_path in sorted(self.index.keys()):
            parts = rel_path.split("/")
            curr = tree
            for part in parts[:-1]:
                curr = curr.setdefault(part, {})
            curr[parts[-1]] = self.index[rel_path]["size"]
            
        def _render(node, indent=0):
            lines = []
            for k, v in sorted(node.items()):
                prefix = "  " * indent
                if isinstance(v, dict):
                    lines.append(f"{prefix}📁 {k}/")
                    lines.extend(_render(v, indent + 1))
                else:
                    size_kb = round(v / 1024, 1)
                    lines.append(f"{prefix}📄 {k} ({size_kb} KB)")
            return lines
            
        return "\n".join(_render(tree))

    def get_incremental_file_content(self, rel_path, max_lines=300):
        """Retrieves file content only if valid, truncating if over max_lines."""
        full_path = os.path.join(self.root_dir, rel_path)
        if not os.path.exists(full_path) or self._is_excluded(full_path):
            return None, "File excluded or not found"
            
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            if len(lines) > max_lines:
                content = "".join(lines[:max_lines]) + f"\n\n... [Truncated: {len(lines) - max_lines} more lines] ..."
            else:
                content = "".join(lines)
            return content, None
        except Exception as e:
            return None, str(e)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    engine = ContextEngine(target)
    print(f"Scanning target: {engine.root_dir}")
    changes = engine.scan_and_index()
    print("Scan results:", json.dumps(changes, indent=2))
    print(f"Total indexed files: {len(engine.index)}")
    print("\n--- Project Outline Preview ---")
    outline = engine.get_concise_outline()
    print("\n".join(outline.splitlines()[:30]))
