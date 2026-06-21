# Northeast urban sugar-maple model card

## Summary

`urban_sugar_maple_v1` estimates years since planting for an open-grown sugar maple from DBH. It packages the Northeast `Acer saccharum` DBH-to-age equation published in the USDA Forest Service Urban Tree Database. It is kept separate from the forest-derived FIA model.

## Version and provenance

- Estimator version: 1.0.0
- Prepared: 2026-06-21
- Dataset: Urban Tree Database, updated 21 January 2020
- Authors: E. Gregory McPherson, Natalie S. van Doorn, and Paula J. Peper
- Publisher: USDA Forest Service Research Data Archive
- DOI: [10.2737/RDS-2016-0005](https://doi.org/10.2737/RDS-2016-0005)
- Source coefficient file: `Data/TS6_Growth_coefficients.csv`
- Source raw-tree file: `Data/TS3_Raw_tree_data.csv`
- Climate region: `NoEast`
- Species: `Acer saccharum` (`ACSA2`)

The source archive checksum and exact coefficient row are packaged with the library. Run `python -m tree_age.urban.prepare` to download the official archive, verify its SHA-256 checksum, and inspect the source row.

## Method

The published `loglogw1` equation is:

```text
age = exp(a + b * ln(ln(DBH_cm + 1) + MSE / 2))
```

with `a = -0.54715`, `b = 3.22652`, `MSE = 0.0706`, and `sigma = 0.2657`. The equation has 16 observations and adjusted R² of 0.91. The estimator constructs a rough 80% log-scale interval from the published sigma.

## Domain and limitations

- Age means years since planting, not biological age from germination.
- The Northeast raw sample contains 31 Queens, New York sugar maples spanning 2.5-105.7 cm DBH, but their raw age field contains missing-value sentinels. The published equation, not those missing ages, drives the estimate.
- Massachusetts was not sampled directly. Applying the Northeast equation there is geographic transfer.
- Sixteen observations are too few for narrow uncertainty or fine-grained site corrections.
- The model is intended for yard, park, and street trees. It should not replace the FIA model for forest trees.
- DBH outside the regional raw range triggers a wider interval and warning.

This estimator is appropriate as a second, context-specific line of evidence for large open-grown Massachusetts sugar maples. It is inappropriate for exact planting dates, legal or historical claims, or safety decisions.
