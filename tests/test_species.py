import unittest

from tree_age.errors import UnknownSpeciesError
from tree_age.species import resolve_species


class SpeciesTests(unittest.TestCase):
    def test_resolves_case_and_scientific_aliases(self):
        self.assertEqual(resolve_species("  EASTERN white PINE ").canonical_name, "White pine")
        self.assertEqual(resolve_species("Acer rubrum").canonical_name, "Red maple")

    def test_unknown_species_lists_valid_values(self):
        with self.assertRaisesRegex(UnknownSpeciesError, "Supported species"):
            resolve_species("truffula")


if __name__ == "__main__":
    unittest.main()

