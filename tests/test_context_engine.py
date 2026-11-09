import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tools")))
from context_engine import ContextEngine

class TestContextEngine(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        # Create dummy directory structure
        os.makedirs(os.path.join(self.test_dir, "src"), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, "node_modules", "pkg"), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, ".git"), exist_ok=True)
        
        # Files
        with open(os.path.join(self.test_dir, "src", "index.ts"), "w") as f:
            f.write("console.log('hello');\n")
        with open(os.path.join(self.test_dir, "node_modules", "pkg", "bad.js"), "w") as f:
            f.write("// should be excluded\n")
        with open(os.path.join(self.test_dir, ".git", "config"), "w") as f:
            f.write("[core]\n")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_exclusion_filter(self):
        engine = ContextEngine(self.test_dir)
        changes = engine.scan_and_index()
        self.assertEqual(changes["added"], 1)
        self.assertIn("src/index.ts", engine.index)
        self.assertNotIn("node_modules/pkg/bad.js", engine.index)
        self.assertNotIn(".git/config", engine.index)

    def test_change_detection(self):
        engine = ContextEngine(self.test_dir)
        engine.scan_and_index()
        
        # Modify file
        with open(os.path.join(self.test_dir, "src", "index.ts"), "w") as f:
            f.write("console.log('updated content');\n")
            
        changes2 = engine.scan_and_index()
        self.assertEqual(changes2["modified"], 1)
        self.assertEqual(changes2["unchanged"], 0)

    def test_concise_outline(self):
        engine = ContextEngine(self.test_dir)
        engine.scan_and_index()
        outline = engine.get_concise_outline()
        self.assertIn("📁 src/", outline)
        self.assertIn("📄 index.ts", outline)
        self.assertNotIn("node_modules", outline)

if __name__ == "__main__":
    unittest.main()
