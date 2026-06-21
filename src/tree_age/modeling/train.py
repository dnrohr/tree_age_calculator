from collections import defaultdict
import argparse
import csv
from datetime import date
import json
import math
from pathlib import Path

from ..species import resolve_species
from ..estimators.growth_factor import load_growth_factors


def _fit_log_linear(rows: list[dict[str, object]]) -> tuple[float, float]:
    xs = [math.log(float(row["dbh_cm"])) for row in rows]
    ys = [math.log(float(row["age_years"])) for row in rows]
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    denominator = sum((value - mean_x) ** 2 for value in xs)
    if denominator == 0:
        raise ValueError("Cannot fit a model when every DBH value is identical")
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / denominator
    if slope <= 0:
        raise ValueError(f"Fitted DBH slope must be positive, got {slope:.4f}")
    return mean_y - slope * mean_x, slope


def _predict(intercept: float, slope: float, dbh_cm: float, state_offset: float = 0.0) -> float:
    return math.exp(intercept + state_offset + slope * math.log(dbh_cm))


def _dbh_class(dbh_cm: float) -> str:
    if dbh_cm < 20:
        return "lt20"
    if dbh_cm < 40:
        return "20to39"
    if dbh_cm < 60:
        return "40to59"
    return "ge60"


def _quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def _interval_entry(residuals: list[float]) -> dict[str, object]:
    return {
        "lower_residual_years": round(_quantile(residuals, 0.05), 3),
        "upper_residual_years": round(_quantile(residuals, 0.95), 3),
        "records": len(residuals),
    }


def train_model(input_path: Path, model_path: Path, report_path: Path, min_records: int = 50) -> dict[str, object]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    target_counts: dict[str, int] = defaultdict(int)
    with input_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["target_quality"] == "low":
                continue
            try:
                canonical = resolve_species(row["species_scientific_name"]).canonical_name
            except Exception:
                continue
            grouped[canonical].append(row)
            target_counts[row["target_type"]] += 1

    species_models: dict[str, object] = {}
    evaluations = []
    calibrations = []
    growth_factor_errors = []
    growth_factors = load_growth_factors()
    for species, rows in sorted(grouped.items()):
        if len(rows) < min_records:
            continue
        training = [row for index, row in enumerate(rows) if index % 5 in {2, 3, 4}]
        calibration = [row for index, row in enumerate(rows) if index % 5 == 1]
        validation = [row for index, row in enumerate(rows) if index % 5 == 0]
        if len(training) < max(10, min_records // 2):
            continue
        intercept, slope = _fit_log_linear(training)
        residuals_by_state: dict[str, list[float]] = defaultdict(list)
        for row in training:
            residuals_by_state[row["state"]].append(
                math.log(float(row["age_years"]))
                - (intercept + slope * math.log(float(row["dbh_cm"])))
            )
        state_offsets = {
            state: sum(residuals) / len(residuals)
            for state, residuals in residuals_by_state.items()
            if len(residuals) >= 20
        }
        errors = []
        for row in calibration:
            prediction = _predict(
                intercept,
                slope,
                float(row["dbh_cm"]),
                state_offsets.get(row["state"], 0.0),
            )
            calibrations.append(
                (
                    species,
                    _dbh_class(float(row["dbh_cm"])),
                    float(row["age_years"]) - prediction,
                )
            )
        for row in validation:
            prediction = _predict(
                intercept,
                slope,
                float(row["dbh_cm"]),
                state_offsets.get(row["state"], 0.0),
            )
            errors.append(prediction - float(row["age_years"]))
            evaluations.append(
                (
                    species,
                    row["state"],
                    _dbh_class(float(row["dbh_cm"])),
                    prediction,
                    float(row["age_years"]),
                )
            )
            growth_prediction = float(row["dbh_cm"]) / 2.54 * growth_factors[species]
            growth_factor_errors.append(abs(growth_prediction - float(row["age_years"])))
        species_models[species] = {
            "intercept": round(intercept, 8),
            "log_dbh_slope": round(slope, 8),
            "state_offsets": {key: round(value, 8) for key, value in sorted(state_offsets.items())},
            "training_records": len(training),
            "calibration_records": len(calibration),
            "validation_records": len(validation),
            "validation_mae_years": round(sum(abs(value) for value in errors) / len(errors), 3),
        }

    if not species_models:
        raise ValueError("No species had enough medium/high-quality age records to train")
    residuals_by_species = defaultdict(list)
    residuals_by_species_class = defaultdict(list)
    all_residuals = []
    for species, dbh_class, residual in calibrations:
        residuals_by_species[species].append(residual)
        residuals_by_species_class[(species, dbh_class)].append(residual)
        all_residuals.append(residual)
    interval_model = {
        "method": "conservative calibration residual 5th/95th percentiles",
        "nominal_coverage": 0.8,
        "fallback_order": ["species_dbh_class", "species", "global"],
        "global": _interval_entry(all_residuals),
        "species": {
            species: _interval_entry(values)
            for species, values in sorted(residuals_by_species.items())
            if len(values) >= 10
        },
        "species_dbh_class": {
            f"{species}|{dbh_class}": _interval_entry(values)
            for (species, dbh_class), values in sorted(residuals_by_species_class.items())
            if len(values) >= 10
        },
    }
    absolute_errors = [abs(predicted - observed) for _, _, _, predicted, observed in evaluations]
    squared_errors = [(predicted - observed) ** 2 for _, _, _, predicted, observed in evaluations]
    by_species = defaultdict(list)
    by_state = defaultdict(list)
    covered = []
    coverage_by_species = defaultdict(list)
    interval_widths = []
    for species, state, dbh_class, predicted, observed in evaluations:
        by_species[species].append(abs(predicted - observed))
        by_state[state].append(abs(predicted - observed))
        entry = interval_model["species_dbh_class"].get(
            f"{species}|{dbh_class}", interval_model["species"].get(species, interval_model["global"])
        )
        lower = max(1.0, predicted + entry["lower_residual_years"])
        upper = predicted + entry["upper_residual_years"]
        is_covered = lower <= observed <= upper
        covered.append(is_covered)
        coverage_by_species[species].append(is_covered)
        interval_widths.append(max(0.0, upper - lower))
    metadata = {
        "model_name": "fia_age_size_v1",
        "model_version": "1.0.0",
        "created": date.today().isoformat(),
        "training_data": input_path.name,
        "target_types": dict(sorted(target_counts.items())),
        "formula": "log(age) = species_intercept + species_slope * log(DBH_cm) + state_offset",
        "minimum_records_per_species": min_records,
        "states": sorted({state for _, state, _, _, _ in evaluations}),
    }
    model = {"metadata": metadata, "species_models": species_models, "interval_model": interval_model}
    report = {
        "metadata": metadata,
        "training_records": sum(item["training_records"] for item in species_models.values()),
        "calibration_records": len(calibrations),
        "validation_records": len(evaluations),
        "mae_years": round(sum(absolute_errors) / len(absolute_errors), 3),
        "growth_factor_baseline_mae_years": round(
            sum(growth_factor_errors) / len(growth_factor_errors), 3
        ),
        "rmse_years": round(math.sqrt(sum(squared_errors) / len(squared_errors)), 3),
        "interval_80_coverage": round(sum(covered) / len(covered), 4),
        "mean_interval_width_years": round(sum(interval_widths) / len(interval_widths), 3),
        "interval_80_coverage_by_species": {
            key: round(sum(values) / len(values), 4)
            for key, values in sorted(coverage_by_species.items())
        },
        "mae_by_species": {key: round(sum(values) / len(values), 3) for key, values in sorted(by_species.items())},
        "mae_by_state": {key: round(sum(values) / len(values), 3) for key, values in sorted(by_state.items())},
    }
    model_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train transparent FIA log-age/log-DBH baseline")
    parser.add_argument("input", type=Path)
    parser.add_argument("--model", type=Path, default=Path("src/tree_age/data/fia_age_size_v1.json"))
    parser.add_argument("--report", type=Path, default=Path("docs/fia_age_size_v1_evaluation.json"))
    parser.add_argument("--min-records", type=int, default=50)
    args = parser.parse_args(argv)
    report = train_model(args.input, args.model, args.report, args.min_records)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
