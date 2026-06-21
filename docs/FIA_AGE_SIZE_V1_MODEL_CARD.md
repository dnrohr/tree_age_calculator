# FIA age-size v1 model card

## Summary

`fia_age_size_v1` is a transparent baseline that estimates a forest tree's age from species, DBH, and (where supported) state. It is appropriate for exploratory estimates with prominent uncertainty, not for dating individual trees or determining planting years.

## Version and provenance

- Model version: 1.0.0
- Created: 2026-06-20
- Source: USDA Forest Service FIA DataMart state SQLite databases
- Training states: Connecticut and Massachusetts
- Training target: `SITETREE.AGEDIA` only
- Training records: 1,577
- Calibration records: 528
- Held-out validation records: 530
- Supported species: eastern hemlock, red maple, northern red oak, sugar maple, white ash, and eastern white pine

The cleaned data and raw databases are reproducible through `make fia-data-ne` and `make fia-clean-ne`, but are not committed because of their size. The serialized coefficients are stored as readable JSON alongside the package.

## Method

For each species, the trainer fits:

```text
log(age) = intercept + slope * log(DBH_cm) + state offset
```

Every fitted DBH slope must be positive, and a species requires at least 50 measured ages. State offsets require at least 20 training records. Deterministic 60/20/20 training, calibration, and validation partitions are used.

## Validation

Held-out MAE is 11.808 years and RMSE is 15.141 years, compared with 14.124 years MAE for the growth-factor fallback on the same records. Species with thin samples, including red spruce and yellow birch, are excluded rather than given unstable coefficients.

Intervals use calibration-set residuals by species and DBH class, then species, then all species when a group has fewer than ten records. Conservative 5th/95th residual quantiles target at least 80% coverage; observed held-out coverage is 86.0%, with a mean width of 44.7 years. Coverage by species is reported in `fia_age_size_v1_evaluation.json`.

## Limitations and inappropriate uses

- FIA site trees are deliberately selected for site-index work and are not a random sample of forest trees.
- Only Connecticut and Massachusetts were included in this model artifact.
- The model uses size, species, and state, not tree health, competition, climate, height, or site conditions.
- Yard and street trees are outside the training domain.
- Interval coverage is empirical and specific to this selected CT/MA sample; it is not a universal confidence guarantee.
- Do not use the result for legal, historical, safety, appraisal, or management decisions that require measured age.

Unsupported species and regions produce explicit warnings or errors; they are not silently mapped to another species.
