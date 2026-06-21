import unittest

from tree_age.estimators import ESTIMATORS, AgeEstimator, get_estimator
from tree_age.measurements import TreeMeasurement
from tree_age.result import AgeEstimate


class EstimatorContractTests(unittest.TestCase):
    def test_every_registered_estimator_implements_contract(self):
        for name in ESTIMATORS:
            estimator = get_estimator(name)
            self.assertIsInstance(estimator, AgeEstimator)
            result = estimator.estimate("red maple", TreeMeasurement(100))
            self.assertIsInstance(result, AgeEstimate)


if __name__ == "__main__":
    unittest.main()
