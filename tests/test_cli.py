import contextlib
from io import StringIO
import unittest

from tree_age.cli import main


class CliTests(unittest.TestCase):
    def test_readme_style_command_prints_range(self):
        output = StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["Red Spruce", "100"])
        self.assertEqual(code, 0)
        self.assertIn("Likely range:", output.getvalue())

    def test_unknown_species_is_actionable(self):
        error = StringIO()
        with contextlib.redirect_stderr(error):
            code = main(["truffula", "100"])
        self.assertEqual(code, 2)
        self.assertIn("Supported species", error.getvalue())

    def test_estimator_can_be_selected(self):
        output = StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["red maple", "100", "--estimator", "bai_reference"])
        self.assertEqual(code, 0)
        self.assertIn("Estimator: bai_reference_v1", output.getvalue())

    def test_flag_style_estimate_and_json_format(self):
        output = StringIO()
        with contextlib.redirect_stdout(output):
            code = main([
                "estimate", "--species", "red maple", "--circumference", "100",
                "--state", "MA", "--context", "forest", "--format", "json",
            ])
        self.assertEqual(code, 0)
        self.assertIn('"estimator_name": "fia_age_size_v1"', output.getvalue())

    def test_species_list_includes_fia_code(self):
        output = StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["species", "list"])
        self.assertEqual(code, 0)
        self.assertIn("Pinus strobus\tFIA SPCD 129", output.getvalue())

    def test_model_check(self):
        output = StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["model", "check"])
        self.assertEqual(code, 0)
        self.assertIn('"ok": true', output.getvalue())


if __name__ == "__main__":
    unittest.main()
