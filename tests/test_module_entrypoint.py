import subprocess
import sys
import unittest


class ModuleEntrypointTests(unittest.TestCase):
    def test_python_m_tree_age_runs_cli(self):
        result = subprocess.run(
            [sys.executable, "-m", "tree_age", "model", "check"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"ok": true', result.stdout)


if __name__ == "__main__":
    unittest.main()
