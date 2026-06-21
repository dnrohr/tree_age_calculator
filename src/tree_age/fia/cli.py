import argparse
from pathlib import Path

from . import NEW_ENGLAND_STATES
from .clean import clean_database, combine_csv, write_report
from .download import download_states


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare USDA FIA data for tree age modeling")
    subparsers = parser.add_subparsers(dest="command", required=True)
    download = subparsers.add_parser("download", help="Download and extract state SQLite databases")
    download.add_argument("--states", nargs="+", default=list(NEW_ENGLAND_STATES))
    download.add_argument("--destination", type=Path, default=Path("data/raw/fia"))
    download.add_argument("--force", action="store_true")
    clean = subparsers.add_parser("clean", help="Build a normalized modeling CSV and quality report")
    clean.add_argument("--states", nargs="+", default=list(NEW_ENGLAND_STATES))
    clean.add_argument("--source", type=Path, default=Path("data/raw/fia"))
    clean.add_argument("--destination", type=Path, default=Path("data/processed"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    states = tuple(state.upper() for state in args.states)
    if args.command == "download":
        for database in download_states(states, args.destination, args.force):
            print(database)
        return 0

    reports = []
    outputs = []
    for state in states:
        candidates = list((args.source / state).glob("*.db"))
        if len(candidates) != 1:
            raise SystemExit(f"Expected one .db file in {args.source / state}; run download first.")
        output = args.destination / f"fia_{state.lower()}_clean.csv"
        reports.append(clean_database(candidates[0], output))
        outputs.append(output)
    combined = args.destination / "fia_new_england_clean.csv"
    rows = combine_csv(outputs, combined)
    report = args.destination / "fia_new_england_quality_report.json"
    write_report(reports, report, rows)
    print(f"Wrote {rows:,} rows to {combined}")
    print(f"Quality report: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

