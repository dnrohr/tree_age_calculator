# FIA age-size v1 model card

## Summary

`fia_age_size_v1` is a transparent baseline that estimates a forest tree's age from species, DBH, and (where supported) state. It is appropriate for exploratory estimates with prominent uncertainty, not for dating individual trees or determining planting years.

## Version and provenance

- Model version: 1.0.0
- Created: 2026-06-20
- Source: USDA Forest Service FIA DataMart state SQLite databases
- Training states: Connecticut and Massachusetts
- Training target: `SITETREE.AGEDIA` only
- Training records: 2,157
- Held-out validation records: 544
- Supported species: eastern hemlock, red maple, northern red oak, red spruce, sugar maple, white ash, eastern white pine, and yellow birch

The cleaned data and raw databases are reproducible through `make fia-data-ne` and `make fia-clean-ne`, but are not committed because of their size. The serialized coefficients are stored as readable JSON alongside the package.

## Method

For each species, the trainer fits:

```text
log(age) = intercept + slope * log(DBH_cm) + state offset
```

Every fitted DBH slope must be positive. State offsets require at least 20 training records. A deterministic 80/20 split is used for this first baseline.

## Validation

Overall held-out MAE is 11.828 years and RMSE is 15.268 years, compared with 14.169 years MAE for the growth-factor fallback on the same records. Results by species and state are recorded in `fia_age_size_v1_evaluation.json`. The baseline is strongest only as an inspectable starting point; red spruce has just 30 total records and particularly weak validation performance.

## Limitations and inappropriate uses

- FIA site trees are deliberately selected for site-index work and are not a random sample of forest trees.
- Only Connecticut and Massachusetts were included in this model artifact.
- The model uses size, species, and state, not tree health, competition, climate, height, or site conditions.
- Yard and street trees are outside the training domain.
- The current interval is a broad heuristic pending empirical calibration.
- Do not use the result for legal, historical, safety, appraisal, or management decisions that require measured age.

Unsupported species and regions produce explicit warnings or errors; they are not silently mapped to another species.
