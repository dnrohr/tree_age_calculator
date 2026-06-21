import unittest

from tree_age.estimators.growth_factor import GrowthFactorEstimator
from tree_age.measurements import TreeMeasurement
from tree_age.result import SiteContext
from tree_age.species import SPECIES


class GrowthFactorTests(unittest.TestCase):
    def test_supports_every_known_species_with_interval(self):
        estimator = GrowthFactorEstimator()
        for species in SPECIES:
            result = estimator.estimate(species.canonical_name, TreeMeasurement(100))
            self.assertLess(result.lower_age_years, result.estimated_age_years)
            self.assertGreater(result.upper_age_years, result.estimated_age_years)
            self.assertEqual(result.confidence_label, "very rough")

    def test_formula_uses_dbh_in_inches(self):
        result = GrowthFactorEstimator().estimate("red maple", TreeMeasurement(2.54 * 3.141592653589793))
        self.assertEqual(result.estimated_age_years, 5)

    def test_context_warning(self):
        result = GrowthFactorEstimator().estimate(
            "sugar maple", TreeMeasurement(100), SiteContext(context="street")
        )
        self.assertTrue(any("Open-grown" in warning for warning in result.warnings))


if __name__ == "__main__":
    unittest.main()
