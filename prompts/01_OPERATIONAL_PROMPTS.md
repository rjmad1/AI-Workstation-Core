# AI Workbench — Operational Prompt Library

Use these structured, battle-tested operational prompts to direct your AI agent.

---

### 1. Financial Analysis & Excel Model
```
Objective: Analyze quarterly revenue and net margins from provided data.
Inputs: Q1 Revenue $1.25M / Net $310k; Q2 Revenue $1.42M / Net $380k; Q3 Revenue $1.68M / Net $450k; Q4 Revenue $1.95M / Net $580k.
Method: Execute Python using openpyxl and matplotlib.
Output: Excel workbook at ./artifacts/financial_analysis.xlsx with formatted currency cells and a chart at ./artifacts/margin_trend.png.
Quality Check: Ensure SUM formulas and margin calculations are mathematically accurate.
```

### 2. Cited Market Research & PDF Briefing
```
Objective: Conduct deep research on Model Context Protocol (MCP) standards.
Inputs: Public web documentation and GitHub specifications.
Method: Search web, extract architectural standards, security isolation boundaries, and SDKs.
Output: 2-page publication PDF saved to ./artifacts/mcp_report.pdf using reportlab.
Quality Check: Include full source URLs and verifiable citations.
```

### 3. Executive PowerPoint Presentation
```
Objective: Build an executive summary presentation deck from provided system notes.
Inputs: System architecture and deployment specifications.
Method: Use python-pptx to generate a 5-slide deck with structured layouts.
Output: Presentation file saved to ./artifacts/executive_briefing.pptx.
Quality Check: Ensure clear visual hierarchy, slide titles, and concise bullet points.
```

### 4. Formal Standard Operating Procedure (DOCX)
```
Objective: Create a Standard Operating Procedure for disaster recovery and stack restoration.
Inputs: Backup and recovery instructions from backups.md.
Method: Execute python-docx to generate a formatted Word document.
Output: Document saved to ./artifacts/SOP_Disaster_Recovery.docx.
Quality Check: Include step-by-step verification commands, prerequisites, and rollback actions.
```

### 5. Git Repository Refactoring & Unit Testing
```
Objective: Refactor main.py in ./workspaces/test-git-project with robust error handling.
Inputs: Existing code in test-git-project workspace.
Method: Inspect code, implement try/catch blocks, run unit tests, and commit to Git.
Output: Clean git commit on master branch.
Quality Check: Run python main.py and verify zero unhandled exceptions.
```
