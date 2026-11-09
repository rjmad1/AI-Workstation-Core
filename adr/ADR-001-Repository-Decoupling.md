# ADR-001: Separation of Monolithic Workstation into 4 Decoupled Repositories

**Date:** 2026-11-09  
**Status:** Accepted  
**Deciders:** Principal AI Systems Architect, Enterprise Platform Architect  
**Consulted:** Infrastructure Intelligence Council  

---

## Context
The AI Workstation on `primary-workstation-node` historically ran as a single mixed directory containing source code, runtime databases (`storage.sqlite`), model weights, Obsidian notes, logs, and sensitive configurations. This monolith created several critical operational risks:
1. Accidental commitment of SQLite databases or DPAPI secrets to Git.
2. High file-watcher overhead across 350k+ temporary files.
3. Inability to perform automated bare-metal recovery without carrying multi-gigabyte cache artifacts.

## Decision
We decouple the workstation into four independent, single-responsibility Git repositories and an isolated runtime plane:
1. **`AI-Workstation-Core`**: Executable code, prompt templates, agent manifests, skills, test suites.
2. **`Knowledge-Repository`**: Semantic Obsidian vault, architecture documentation, RAG documents.
3. **`AI-Workstation-Infrastructure`**: Docker Compose, NSSM service scripts, bootstrap, DR recovery engines.
4. **`AI-Workstation-Configuration`**: Sanitized templates ONLY (`.env.template`, `openclaw.template.json`).
5. **`AI-Operations` (Runtime Host)**: Quarantined local storage on drive D: containing databases, model weights, logs, and runtime caches (strictly barred from Git).

## Consequences
- **Positive:**
  - Zero-secret Git hygiene enforced by structure and pre-commit scans.
  - Disaster recovery time reduced from indeterminate to < 60 minutes.
  - Subagents and IDEs observe clean directory trees with zero file-watcher stutter.
- **Negative / Trade-offs:**
  - Multi-repo updates require coordinated commits or a meta-orchestrator.
  - Developers must configure local `.env` files from templates during bootstrap.

## Compliance & Verification
- Validated via `Validate-Workstation.ps1` and strict `.gitignore` rules.
