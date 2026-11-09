import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tools")))
from model_router import TokenGovernor, ROUTING_POLICY, AVAILABLE_MODELS

class TestModelRouter(unittest.TestCase):
    def test_available_models(self):
        self.assertIn("gemini-3.8-flash-low", AVAILABLE_MODELS)
        self.assertIn("gemini-3.8-flash-high", AVAILABLE_MODELS)
        self.assertIn("claude-sonnet-4-6", AVAILABLE_MODELS)
        self.assertIn("claude-opus-4-6-thinking", AVAILABLE_MODELS)

    def test_deterministic_task_classification(self):
        decision = TokenGovernor.classify_task("Please check git status and list files in this repo")
        self.assertEqual(decision["category"], "DETERMINISTIC_OP")
        self.assertEqual(decision["execution_type"], "NATIVE_SCRIPT_OR_SHELL")
        self.assertIsNone(decision["recommended_model"])

    def test_routine_retrieval_classification(self):
        decision = TokenGovernor.classify_task("Quick summary of what is the syntax for declaring an enum in typescript")
        self.assertEqual(decision["category"], "ROUTINE_RETRIEVAL_AND_LOOKUP")
        self.assertEqual(decision["recommended_model"], "gemini-3.8-flash-low")

    def test_standard_coding_classification(self):
        decision = TokenGovernor.classify_task("Implement a unit test for the user authentication helper")
        self.assertEqual(decision["category"], "STANDARD_ENGINEERING")
        self.assertEqual(decision["recommended_model"], "gemini-3.8-flash-high")

    def test_complex_debugging_classification(self):
        decision = TokenGovernor.classify_task("Debug intermittent race condition and deadlock in session manager")
        self.assertEqual(decision["category"], "COMPLEX_DEBUGGING_AND_INTEGRATION")
        self.assertEqual(decision["recommended_model"], "claude-sonnet-4-6")

    def test_mission_critical_architecture_classification(self):
        decision = TokenGovernor.classify_task("Perform a security audit and architecture decision on JWT signing keys")
        self.assertEqual(decision["category"], "MISSION_CRITICAL_ARCHITECTURE")
        self.assertEqual(decision["recommended_model"], "claude-opus-4-6-thinking")

    def test_prompt_linter(self):
        bloated_prompt = "Could you please as an AI assistant help me with this task? Could you please make sure to explain everything step by step?"
        lint_res = TokenGovernor.lint_prompt(bloated_prompt)
        self.assertEqual(lint_res["status"], "WARN")
        self.assertTrue(len(lint_res["recommendations"]) >= 1)

if __name__ == "__main__":
    unittest.main()
