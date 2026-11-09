"""
Model Routing and Token Governance Layer for AntiGravity 2.0
Enforces complexity-based model selection, deterministic pre-checks,
and strict token budgeting to maximize reasoning efficiency while minimizing cost.
"""

import os
import sys
import json
import re

# Verified models available in the current AntiGravity environment
AVAILABLE_MODELS = {
    "gemini-3.8-flash-low": {"tier": "efficiency", "rpm_cost": "minimal", "context_window": 1000000},
    "gemini-3.8-flash-medium": {"tier": "balanced", "rpm_cost": "low", "context_window": 1000000},
    "gemini-3.8-flash-high": {"tier": "coding", "rpm_cost": "moderate", "context_window": 1000000},
    "claude-sonnet-4-6": {"tier": "reasoning", "rpm_cost": "high", "context_window": 200000},
    "claude-opus-4-6-thinking": {"tier": "deep_reasoning", "rpm_cost": "premium", "context_window": 200000},
    "gpt-oss-120b-medium": {"tier": "open_weights", "rpm_cost": "moderate", "context_window": 128000}
}

ROUTING_POLICY = [
    {
        "category": "DETERMINISTIC_OP",
        "description": "File search, directory walk, format validation, git status, syntax checking",
        "recommended_model": None,
        "execution_type": "NATIVE_SCRIPT_OR_SHELL",
        "rationale": "Always prefer zero-token deterministic code over LLM inference."
    },
    {
        "category": "ROUTINE_RETRIEVAL_AND_LOOKUP",
        "description": "API signature lookups, simple string edits, log parsing, documentation grep",
        "recommended_model": "gemini-3.8-flash-low",
        "execution_type": "MODEL_INFERENCE",
        "rationale": "Fastest response time, lowest token expenditure for basic tasks."
    },
    {
        "category": "STANDARD_ENGINEERING",
        "description": "Feature development, unit tests, bug fixes, refactoring, code review",
        "recommended_model": "gemini-3.8-flash-high",
        "execution_type": "MODEL_INFERENCE",
        "rationale": "Strong coding ability with high token headroom and low latency."
    },
    {
        "category": "COMPLEX_DEBUGGING_AND_INTEGRATION",
        "description": "Multi-component diagnosis, distributed tracing, race conditions, schema design",
        "recommended_model": "claude-sonnet-4-6",
        "execution_type": "MODEL_INFERENCE",
        "rationale": "High reasoning strength for nuanced debugging and multi-file dependencies."
    },
    {
        "category": "MISSION_CRITICAL_ARCHITECTURE",
        "description": "Security audit, cryptography, high-risk refactoring, disaster recovery plans",
        "recommended_model": "claude-opus-4-6-thinking",
        "execution_type": "MODEL_INFERENCE_WITH_VERIFICATION",
        "rationale": "Deepest reasoning capability, reserved strictly for critical architectural decisions."
    }
]

class TokenGovernor:
    @staticmethod
    def estimate_tokens(text):
        if not text:
            return 0
        # Standard approximation: ~4 characters per token for English / code
        return max(1, round(len(text) / 4))

    @staticmethod
    def classify_task(prompt_text):
        prompt_lower = prompt_text.lower()
        
        # Check for deterministic matches
        if any(w in prompt_lower for w in ["git status", "list files", "dir", "find file", "format json", "lint"]):
            return ROUTING_POLICY[0]
            
        # Check for architectural / critical keywords
        if any(w in prompt_lower for w in ["security audit", "vulnerability assessment", "cryptograph", "threat model", "architecture decision"]):
            return ROUTING_POLICY[4]
            
        # Check for complex debugging
        if any(w in prompt_lower for w in ["race condition", "memory leak", "deadlock", "root cause analysis", "multi-service", "flaky test"]):
            return ROUTING_POLICY[3]
            
        # Check for routine retrieval
        if any(w in prompt_lower for w in ["what is the syntax", "quick summary", "lookup", "rename variable", "typo"]):
            return ROUTING_POLICY[1]
            
        # Default standard coding
        return ROUTING_POLICY[2]

    @staticmethod
    def lint_prompt(prompt_text):
        """Analyzes a prompt for token bloat and filler."""
        findings = []
        tokens = TokenGovernor.estimate_tokens(prompt_text)
        
        fillers = [
            "could you please", "would you mind", "i was wondering if",
            "as an ai assistant", "please be thorough and detailed",
            "make sure to explain everything step by step"
        ]
        
        for f in fillers:
            if f in prompt_text.lower():
                findings.append(f"Prompt contains conversational filler: '{f}'. Can be omitted.")
                
        # Repetition check
        paragraphs = [p.strip() for p in prompt_text.split("\n\n") if len(p.strip()) > 30]
        if len(paragraphs) != len(set(paragraphs)):
            findings.append("Prompt contains duplicate paragraphs.")
            
        return {
            "token_count": tokens,
            "status": "WARN" if findings or tokens > 4000 else "OPTIMAL",
            "recommendations": findings
        }

if __name__ == "__main__":
    test_queries = [
        "Check git status and branch list",
        "Fix the null pointer exception when parsing user session tokens in auth_service.py",
        "Perform a full security threat model of the authentication gateway and encryption keys",
        "What is the function signature of get_active_gcp_connection?"
    ]
    
    print("=== MODEL ROUTING & TOKEN GOVERNANCE TESTS ===")
    for q in test_queries:
        decision = TokenGovernor.classify_task(q)
        print(f"\nPrompt: '{q}'")
        print(f"Classification: {decision['category']}")
        print(f"Target Execution: {decision['execution_type']} -> {decision['recommended_model']}")
        print(f"Rationale: {decision['rationale']}")
