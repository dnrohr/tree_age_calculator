import unittest
import math

from tree_age.errors import ModelError
from tree_age.estimators.fia_age_size import FiaAgeSizeEstimator
from tree_age.measurements import TreeMeasurement
from tree_age.result import SiteContext


class FiaModelTests(unittest.TestCase):
    def test_supported_species_returns_structured_estimate(self):
        result = FiaAgeSizeEstimator().estimate(
            "Acer rubrum", TreeMeasurement(100), SiteContext(state="MA", context="forest")
        )
        self.assertEqual(result.estimator_name, "fia_age_size_v1")
        self.assertLess(result.lower_age_years, result.estimated_age_years)
        self.assertGreater(result.upper_age_years, result.estimated_age_years)
        self.assertIn(result.assumptions["interval_source"], {"species_dbh_class", "species", "global"})

    def test_unsupported_species_fails_cleanly(self):
        with self.assertRaisesRegex(ModelError, "does not support"):
            FiaAgeSizeEstimator().estimate("balsam fir", TreeMeasurement(100))

    def test_untrained_state_emits_warning(self):
        result = FiaAgeSizeEstimator().estimate(
            "red maple", TreeMeasurement(100), SiteContext(state="NY")
        )
        self.assertTrue(any("not represented" in warning for warning in result.warnings))

    def test_interval_model_is_empirical_and_conservative(self):
        estimator = FiaAgeSizeEstimator()
        self.assertEqual(estimator.model["interval_model"]["nominal_coverage"], 0.8)
        self.assertGreaterEqual(estimator.model["interval_model"]["global"]["records"], 10)

    def test_age_is_monotonic_and_extrapolation_widens_interval(self):
        estimator = FiaAgeSizeEstimator()
        small = estimator.estimate("red maple", TreeMeasurement(20 * math.pi))
        typical = estimator.estimate("red maple", TreeMeasurement(35 * math.pi))
        huge = estimator.estimate("red maple", TreeMeasurement(100 * math.pi))
        self.assertLess(small.estimated_age_years, typical.estimated_age_years)
        self.assertLess(typical.estimated_age_years, huge.estimated_age_years)
        self.assertGreater(
            huge.upper_age_years - huge.lower_age_years,
            typical.upper_age_years - typical.lower_age_years,
        )


if __name__ == "__main__":
    unittest.main()
