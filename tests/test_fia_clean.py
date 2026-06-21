import csv
from pathlib import Path
import sqlite3
import tempfile
import unittest

from tree_age.fia.clean import clean_database


SCHEMA = """
CREATE TABLE TREE (SPCD INTEGER, DIA REAL, HT REAL, TOTAGE REAL, BHAGE REAL, STATECD INTEGER, COUNTYCD INTEGER, PLT_CN TEXT, CONDID INTEGER, STATUSCD INTEGER, INVYR INTEGER);
CREATE TABLE PLOT (CN TEXT, LAT REAL, LON REAL, ELEV REAL);
CREATE TABLE COND (PLT_CN TEXT, CONDID INTEGER, STDAGE REAL, SLOPE REAL, ASPECT REAL, FORTYPCD INTEGER, STDORGCD INTEGER);
CREATE TABLE REF_SPECIES (SPCD INTEGER, COMMON_NAME TEXT, SCIENTIFIC_NAME TEXT);
"""


class FiaCleanerTests(unittest.TestCase):
    def test_target_hierarchy_units_and_rejections(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "fixture.db"
            with sqlite3.connect(database) as connection:
                connection.executescript(SCHEMA)
                connection.execute("INSERT INTO PLOT VALUES ('p1', 42.123, -72.987, 1000)")
                connection.execute("INSERT INTO COND VALUES ('p1', 1, 50, 12, 180, 101, 0)")
                connection.execute("INSERT INTO REF_SPECIES VALUES (316, 'Red maple', 'Acer rubrum')")
                connection.executemany(
                    "INSERT INTO TREE VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    [
                        (316, 10, 50, 80, 70, 9, 1, "p1", 1, 1, 2025),
                        (316, 11, 55, None, 70, 9, 1, "p1", 1, 1, 2025),
                        (316, 12, 60, None, None, 9, 1, "p1", 1, 1, 2025),
                        (316, 0, 60, 20, None, 9, 1, "p1", 1, 1, 2025),
                    ],
                )
            output = root / "clean.csv"
            report = clean_database(database, output)
            with output.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 3)
            self.assertEqual([row["target_type"] for row in rows], ["total_age", "breast_height_age", "stand_age_proxy"])
            self.assertEqual(rows[0]["dbh_cm"], "25.4")
            self.assertEqual(rows[0]["latitude_rounded"], "42.12")
            self.assertEqual(report["counts"]["accepted_rows"], 3)


if __name__ == "__main__":
    unittest.main()
