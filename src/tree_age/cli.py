import argparse
import json
import sys

from .errors import TreeAgeError
from .estimators.fia_age_size import FiaAgeSizeEstimator
from .estimators.urban_sugar_maple import UrbanSugarMapleEstimator
from .estimators.registry import ESTIMATORS, get_estimator
from .measurements import TreeMeasurement
from .result import SiteContext
from .species import SPECIES

ESTIMATOR_DESCRIPTIONS = {
    "ensemble": "Default: context-aware urban/FIA routing with an explicit growth-factor fallback.",
    "fia_age_size": "Empirical CT/MA FIA site-tree log-age/log-DBH model.",
    "growth_factor": "Stable but crude species growth-factor rule of thumb.",
    "bai_reference": "Experimental New England regional-average BAI reference model.",
    "urban_sugar_maple": "Published Northeast urban sugar-maple DBH-to-age equation.",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tree-age",
        description="Estimate a plausible tree age range from circumference at breast height (1.4 m / 4.5 ft).",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    estimate = commands.add_parser("estimate", help="Estimate a tree age range")
    estimate.add_argument("species_pos", nargs="?", help="Common or scientific species name")
    estimate.add_argument("circumference_pos", nargs="?", type=float, help="Circumference at breast height")
    estimate.add_argument("--species", dest="species_option", help="Common or scientific species name")
    estimate.add_argument("--circumference", dest="circumference_option", type=float)
    estimate.add_argument("--units", choices=("cm", "in"), default="cm")
    estimate.add_argument("--context", choices=("forest", "yard", "street", "unknown"), default="unknown")
    estimate.add_argument("--state", help="Two-letter US state code")
    estimate.add_argument(
        "--estimator", choices=tuple(sorted(ESTIMATORS)), default="ensemble",
        help="Estimation algorithm (default: ensemble)",
    )
    estimate.add_argument("--format", choices=("text", "json"), default="text")
    estimate.add_argument("--json", action="store_true", help="Alias for --format json")

    species = commands.add_parser("species", help="Inspect species support")
    species.add_argument("action", choices=("list",))

    explain = commands.add_parser("explain", help="Explain an estimator and its metadata")
    explain.add_argument("--estimator", choices=tuple(sorted(ESTIMATORS)), default="ensemble")

    model = commands.add_parser("model", help="Inspect packaged model files")
    model.add_argument("action", choices=("check",))
    return parser


def _normalize_argv(argv: list[str]) -> list[str]:
    commands = {"estimate", "species", "explain", "model"}
    if argv and argv[0] not in commands and argv[0] not in {"-h", "--help"}:
        return ["estimate", *argv]
    return argv


def _print_estimate(estimate) -> None:
    print(f"Species: {estimate.species}")
    print(f"Estimated age: about {estimate.estimated_age_years} years")
    print(f"Likely range: {estimate.lower_age_years}-{estimate.upper_age_years} years")
    print(f"Confidence: {estimate.confidence_label}")
    print(f"Estimator: {estimate.estimator_name}")
    if estimate.warnings:
        print("Warnings:")
        for warning in estimate.warnings:
            print(f"- {warning}")


def _check_model() -> dict[str, object]:
    model = FiaAgeSizeEstimator().model
    failures = []
    for species, values in model["species_models"].items():
        if values["log_dbh_slope"] <= 0:
            failures.append(f"{species}: non-positive DBH slope")
    interval = model.get("interval_model", {})
    if not interval.get("global"):
        failures.append("missing global interval fallback")
    return {
        "ok": not failures,
        "model": model["metadata"]["model_name"],
        "version": model["metadata"]["model_version"],
        "supported_species": sorted(model["species_models"]),
        "failures": failures,
    }


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(_normalize_argv(raw_argv))

    if args.command == "species":
        for species in SPECIES:
            print(f"{species.canonical_name}\t{species.scientific_name}\tFIA SPCD {species.fia_code}")
        return 0
    if args.command == "explain":
        print(f"{args.estimator}: {ESTIMATOR_DESCRIPTIONS[args.estimator]}")
        if args.estimator in {"fia_age_size", "ensemble"}:
            print(json.dumps(FiaAgeSizeEstimator().model["metadata"], indent=2))
        if args.estimator == "urban_sugar_maple":
            print(json.dumps(UrbanSugarMapleEstimator().metadata, indent=2))
        return 0
    if args.command == "model":
        result = _check_model()
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1

    species = args.species_option or args.species_pos
    circumference = args.circumference_option if args.circumference_option is not None else args.circumference_pos
    if species is None or circumference is None:
        print("Error: estimate requires species and circumference.", file=sys.stderr)
        return 2
    circumference_cm = circumference * 2.54 if args.units == "in" else circumference
    try:
        estimate = get_estimator(args.estimator).estimate(
            species,
            TreeMeasurement(circumference_cm),
            SiteContext(state=args.state, context=args.context),
        )
    except (TreeAgeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if args.json or args.format == "json":
        print(estimate.to_json())
    else:
        _print_estimate(estimate)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
