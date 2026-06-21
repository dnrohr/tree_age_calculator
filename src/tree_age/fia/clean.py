from collections import Counter
from contextlib import closing
import csv
from datetime import date
import json
from pathlib import Path
import sqlite3

STATE_ABBREVIATIONS = {9: "CT", 23: "ME", 25: "MA", 33: "NH", 44: "RI", 50: "VT"}

OUTPUT_COLUMNS = (
    "species_code",
    "species_common_name",
    "species_scientific_name",
    "dbh_cm",
    "height_m",
    "age_years",
    "target_type",
    "target_quality",
    "state",
    "county",
    "latitude_rounded",
    "longitude_rounded",
    "elevation_m",
    "slope_percent",
    "aspect_degrees",
    "forest_type_code",
    "stand_origin_code",
    "inventory_year",
    "source_database_version",
)

QUERY = """
SELECT
    t.SPCD, r.COMMON_NAME, r.SCIENTIFIC_NAME, t.DIA, t.HT,
    t.TOTAGE, t.BHAGE, c.STDAGE, t.STATECD, t.COUNTYCD,
    p.LAT, p.LON, p.ELEV, c.SLOPE, c.ASPECT, c.FORTYPCD,
    c.STDORGCD, t.INVYR
FROM TREE AS t
JOIN PLOT AS p ON p.CN = t.PLT_CN
LEFT JOIN COND AS c ON c.PLT_CN = t.PLT_CN AND c.CONDID = t.CONDID
LEFT JOIN REF_SPECIES AS r ON r.SPCD = t.SPCD
WHERE t.STATUSCD = 1 AND t.DIA > 0
"""


def _age_target(total_age, breast_height_age, stand_age):
    if total_age and total_age > 0:
        return total_age, "total_age", "high"
    if breast_height_age and breast_height_age > 0:
        return breast_height_age, "breast_height_age", "medium"
    if stand_age and stand_age > 0:
        return stand_age, "stand_age_proxy", "low"
    return None


def clean_database(database: Path, output: Path) -> dict[str, object]:
    output.parent.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    by_species = Counter()
    by_target = Counter()
    by_state = Counter()
    with closing(sqlite3.connect(database)) as connection, output.open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for row in connection.execute(QUERY):
            counts["live_positive_dbh_rows"] += 1
            spcd, common, scientific, dia, height, total, bhage, stdage, statecd, county, lat, lon, elev, slope, aspect, forest_type, origin, invyr = row
            target = _age_target(total, bhage, stdage)
            if target is None:
                counts["rejected_missing_age"] += 1
                continue
            age, target_type, target_quality = target
            if age > 600:
                counts["rejected_implausible_age"] += 1
                continue
            if not common or not scientific:
                counts["rejected_unmapped_species"] += 1
                continue
            state = STATE_ABBREVIATIONS.get(statecd, str(statecd))
            record = {
                "species_code": spcd,
                "species_common_name": common,
                "species_scientific_name": scientific,
                "dbh_cm": round(dia * 2.54, 3),
                "height_m": round(height * 0.3048, 3) if height and height > 0 else "",
                "age_years": age,
                "target_type": target_type,
                "target_quality": target_quality,
                "state": state,
                "county": county,
                "latitude_rounded": round(lat, 2) if lat is not None else "",
                "longitude_rounded": round(lon, 2) if lon is not None else "",
                "elevation_m": round(elev * 0.3048, 2) if elev is not None else "",
                "slope_percent": slope if slope is not None else "",
                "aspect_degrees": aspect if aspect is not None else "",
                "forest_type_code": forest_type if forest_type is not None else "",
                "stand_origin_code": origin if origin is not None else "",
                "inventory_year": invyr,
                "source_database_version": database.name,
            }
            writer.writerow(record)
            counts["accepted_rows"] += 1
            by_species[common] += 1
            by_target[target_type] += 1
            by_state[state] += 1
    return {
        "generated": date.today().isoformat(),
        "source_database": str(database),
        "output": str(output),
        "counts": dict(sorted(counts.items())),
        "rows_by_state": dict(sorted(by_state.items())),
        "rows_by_target_type": dict(sorted(by_target.items())),
        "rows_by_species": dict(sorted(by_species.items())),
    }


def combine_csv(inputs: list[Path], output: Path) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for source in inputs:
            with source.open(encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle):
                    writer.writerow(row)
                    count += 1
    return count


def write_report(reports: list[dict[str, object]], path: Path, combined_rows: int) -> None:
    aggregate = {
        "generated": date.today().isoformat(),
        "combined_rows": combined_rows,
        "states": reports,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(aggregate, indent=2) + "\n", encoding="utf-8")
