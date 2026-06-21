import unittest

from tree_age.estimators.ensemble import EnsembleEstimator
from tree_age.measurements import TreeMeasurement


class EnsembleTests(unittest.TestCase):
    def test_uses_fia_when_supported(self):
        result = EnsembleEstimator().estimate("red maple", TreeMeasurement(100))
        self.assertEqual(result.estimator_name, "fia_age_size_v1")

    def test_falls_back_explicitly(self):
        result = EnsembleEstimator().estimate("balsam fir", TreeMeasurement(100))
        self.assertIn("growth_factor_v1", result.estimator_name)
        self.assertTrue(result.assumptions["fallback_used"])


if __name__ == "__main__":
    unittest.main()
