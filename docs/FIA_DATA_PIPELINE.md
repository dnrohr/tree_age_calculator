# FIA data pipeline

The pipeline downloads current state SQLite databases from the USDA Forest Service FIA DataMart, extracts live trees with positive diameter, and creates a normalized CSV plus a machine-readable quality report.

```bash
make fia-data-ne
make fia-clean-ne
```

On systems without `make`, run `python -m tree_age.fia.cli download` followed by `python -m tree_age.fia.cli clean`. Use `--states CT MA` on either command for a subset.

Raw archives and databases live under `data/raw/fia/`; cleaned files live under `data/processed/`. Both are intentionally ignored by Git. Each state download writes a manifest containing its exact source URL and UTC download time.

## Target hierarchy

The cleaner selects the first positive age in this order:

1. `TREE.TOTAGE` as `total_age` with high target quality.
2. `TREE.BHAGE` as `breast_height_age` with medium target quality.
3. `COND.STDAGE` as `stand_age_proxy` with low target quality.

Rows without any age target are rejected. Target type and quality remain in every output row, so downstream training can exclude proxy ages or evaluate them separately. Connecticut's current database, for example, defines both individual-tree fields but does not populate them; its usable rows therefore rely on low-quality stand-age proxies.

## Units and privacy

FIADB diameter in inches, height/elevation in feet, and geographic coordinates are converted to centimeters, meters, and coordinates rounded to two decimals. The cleaner retains no plot identifiers. Records with missing age, age above 600 years, or unmapped species are rejected and counted in the quality report.

## Review gate

Do not train a model merely because cleaning completed. Review `fia_new_england_quality_report.json`, especially the target-type and species distributions. A model trained mostly on stand-age proxies estimates stand cohort age, not reliably an individual tree's age.
