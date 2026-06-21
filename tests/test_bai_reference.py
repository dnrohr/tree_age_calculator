import unittest

from tree_age.errors import ModelError
from tree_age.estimators.bai_reference import BaiReferenceEstimator, PARAMETERS
from tree_age.measurements import TreeMeasurement
from tree_age.result import SiteContext


class BaiEstimatorTests(unittest.TestCase):
    def test_all_supported_curves_are_positive(self):
        for species in PARAMETERS:
            for year in range(1950, 1981):
                self.assertGreater(BaiReferenceEstimator.growth_rate(species, year), 0)

    def test_estimate_has_interval_and_warning(self):
        result = BaiReferenceEstimator().estimate("red spruce", TreeMeasurement(100))
        self.assertLess(result.lower_age_years, result.estimated_age_years)
        self.assertGreater(result.upper_age_years, result.estimated_age_years)
        self.assertTrue(result.warnings)

    def test_open_grown_tree_gets_context_warning(self):
        result = BaiReferenceEstimator().estimate(
            "red maple", TreeMeasurement(100), SiteContext(context="yard")
        )
        self.assertTrue(any("Open-grown" in warning for warning in result.warnings))

    def test_estimator_is_bounded(self):
        with self.assertRaises(ModelError):
            BaiReferenceEstimator(max_age=1).estimate("red spruce", TreeMeasurement(1000))


if __name__ == "__main__":
    unittest.main()

