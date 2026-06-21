import math
import unittest

from tree_age.measurements import TreeMeasurement


class MeasurementTests(unittest.TestCase):
    def test_converts_circumference_to_dbh(self):
        self.assertAlmostEqual(TreeMeasurement(math.pi * 10).dbh_cm, 10)

    def test_rejects_nonpositive_value(self):
        with self.assertRaisesRegex(ValueError, "positive"):
            TreeMeasurement(0)


if __name__ == "__main__":
    unittest.main()

