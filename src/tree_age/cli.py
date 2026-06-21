import argparse
import sys

from .errors import TreeAgeError
from .estimators.bai_reference import BaiReferenceEstimator
from .measurements import TreeMeasurement
from .result import SiteContext


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tree-age",
        description="Estimate a plausible tree age range from species and circumference at breast height.",
    )
    parser.add_argument("species", help="Common or scientific species name")
    parser.add_argument("circumference", type=float, help="Circumference at breast height")
    parser.add_argument("--units", choices=("cm", "in"), default="cm")
    parser.add_argument("--context", choices=("forest", "yard", "street", "unknown"), default="unknown")
    parser.add_argument("--state", help="Two-letter US state code")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    circumference_cm = args.circumference * 2.54 if args.units == "in" else args.circumference
    try:
        estimate = BaiReferenceEstimator().estimate(
            args.species,
            TreeMeasurement(circumference_cm),
            SiteContext(state=args.state, context=args.context),
        )
    except (TreeAgeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(estimate.to_json())
    else:
        print(f"Species: {estimate.species}")
        print(f"Estimated age: about {estimate.estimated_age_years} years")
        print(f"Plausible range: {estimate.lower_age_years}-{estimate.upper_age_years} years")
        print(f"Confidence: {estimate.confidence_label}")
        print(f"Estimator: {estimate.estimator_name}")
        for warning in estimate.warnings:
            print(f"Warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

