"""Reproduce the packaged Northeast sugar-maple coefficient extract."""

import csv
import hashlib
from io import TextIOWrapper
import json
from pathlib import Path
from urllib.request import Request, urlopen
import zipfile

ARCHIVE_URL = "https://www.fs.usda.gov/rds/archive/products/RDS-2016-0005/RDS-2016-0005.zip"
ARCHIVE_SHA256 = "c0c888e2531ca58b673b7c18a30a01cbd33e90bd8b041fb3483e394bd8664faf"


def download_archive(destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(ARCHIVE_URL, headers={"User-Agent": "tree-age-estimator/1.1"})
    with urlopen(request, timeout=120) as response, destination.open("wb") as handle:
        while chunk := response.read(1024 * 1024):
            handle.write(chunk)
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    if digest != ARCHIVE_SHA256:
        destination.unlink(missing_ok=True)
        raise RuntimeError(f"Urban Tree Database checksum mismatch: {digest}")
    return destination


def inspect_source(archive: Path) -> dict[str, object]:
    with zipfile.ZipFile(archive) as bundle:
        with bundle.open("Data/TS6_Growth_coefficients.csv") as raw:
            coefficients = list(csv.DictReader(TextIOWrapper(raw, encoding="utf-8-sig")))
        with bundle.open("Data/TS3_Raw_tree_data.csv") as raw:
            trees = list(csv.DictReader(TextIOWrapper(raw, encoding="utf-8-sig")))
    matches = [
        row for row in coefficients
        if row["Region"] == "NoEast"
        and row["SpCode"] == "ACSA2"
        and row["Independent variable"] == "dbh"
        and row["Predicts component "] == "age"
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one Northeast sugar-maple age equation, found {len(matches)}")
    regional_trees = [row for row in trees if row["Region"] == "NoEast" and row["SpCode"] == "ACSA2"]
    dbh_values = [float(row["DBH (cm)"]) for row in regional_trees if row["DBH (cm)"]]
    return {
        "coefficient_row": matches[0],
        "regional_raw_records": len(regional_trees),
        "regional_raw_dbh_min_cm": min(dbh_values),
        "regional_raw_dbh_max_cm": max(dbh_values),
    }


def main() -> int:
    archive = download_archive(Path("data/raw/urban/RDS-2016-0005.zip"))
    print(json.dumps(inspect_source(archive), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
