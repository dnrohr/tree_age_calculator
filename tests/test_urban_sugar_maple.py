import math
import unittest

from tree_age.errors import ModelError
from tree_age.estimators.ensemble import EnsembleEstimator
from tree_age.estimators.urban_sugar_maple import UrbanSugarMapleEstimator
from tree_age.measurements import TreeMeasurement
from tree_age.result import SiteContext


class UrbanSugarMapleTests(unittest.TestCase):
    def test_published_equation_and_provenance(self):
        result = UrbanSugarMapleEstimator().estimate(
            "Acer saccharum",
            TreeMeasurement(100 * math.pi),
            SiteContext(state="MA", context="yard"),
        )
        self.assertEqual(result.estimated_age_years, 82)
        self.assertEqual(result.assumptions["source_sample_size"], 16)
        self.assertEqual(result.assumptions["source_doi"], "10.2737/RDS-2016-0005")
        self.assertLess(result.lower_age_years, result.estimated_age_years)
        self.assertGreater(result.upper_age_years, result.estimated_age_years)

    def test_rejects_other_species(self):
        with self.assertRaisesRegex(ModelError, "Sugar maple only"):
            UrbanSugarMapleEstimator().estimate("red maple", TreeMeasurement(100))

    def test_outside_source_dbh_range_widens_and_warns(self):
        estimator = UrbanSugarMapleEstimator()
        inside = estimator.estimate("sugar maple", TreeMeasurement(100 * math.pi))
        outside = estimator.estimate("sugar maple", TreeMeasurement(120 * math.pi))
        self.assertFalse(inside.assumptions["dbh_outside_regional_raw_range"])
        self.assertTrue(outside.assumptions["dbh_outside_regional_raw_range"])
        self.assertTrue(any("interval widened" in warning for warning in outside.warnings))

    def test_ensemble_routes_open_grown_sugar_maple_to_urban_model(self):
        measurement = TreeMeasurement(60 * math.pi)
        yard = EnsembleEstimator().estimate(
            "sugar maple", measurement, SiteContext(state="MA", context="yard")
        )
        forest = EnsembleEstimator().estimate(
            "sugar maple", measurement, SiteContext(state="MA", context="forest")
        )
        self.assertEqual(yard.estimator_name, "urban_sugar_maple_v1")
        self.assertEqual(forest.estimator_name, "fia_age_size_v1")


if __name__ == "__main__":
    unittest.main()
