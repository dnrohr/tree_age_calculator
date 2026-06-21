# Tree Age Estimator

Tree Age Estimator returns a **rough, plausible age range** for a living tree from species and circumference at breast height. It never claims to calculate an exact age.

Circumference is a weak proxy for age. Competition, climate, disease, soil, damage, and growing context can make equally sized trees very different ages. Do not use these estimates as planting dates or as substitutes for increment-core or historical evidence.

## Quick start

Python 3.10 or newer is required.

```bash
python -m pip install -e .
tree-age estimate --species "red maple" --circumference 100 --units cm --state MA --context yard
```

On Windows, pip may install command launchers into a version-specific `Scripts` directory that is not on PATH. The project installer adds the correct directory to your user PATH without hard-coding a Python version:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install.ps1
```

Open a new terminal afterward. The CLI also always works without a PATH entry:

```bash
python -m tree_age estimate --species "red maple" --circumference 100
```

Example output:

```text
Species: Red maple
Estimated age: about 61 years
Likely range: 46-83 years
Confidence: rough
Estimator: fia_age_size_v1
Warnings:
- This baseline is trained on selected FIA site trees, not a random sample of all trees.
- The interval is empirically calibrated to nominal 80% coverage on held-out FIA site trees.
- FIA is forest-derived; open-grown yard and street trees may be younger.
```

JSON output uses the same library result:

```bash
tree-age estimate --species "Acer rubrum" --circumference 40 --units in --state MA --context forest --format json
```

The original positional form remains compatible:

```bash
python tree_age_calculator.py "red spruce" 100
```

## Measure the tree

Measure trunk circumference at breast height: 1.4 m (4.5 ft) above the ground. Keep a flexible tape level and snug around the trunk. Record centimeters or inches. Multi-stemmed, forked, leaning, or swollen trees require forestry-specific conventions and may not suit this estimator.

## Species and estimators

List canonical names, scientific names, and FIA codes with:

```bash
tree-age species list
```

Ten New England species are recognized: white pine, eastern hemlock, yellow birch, red spruce, northern red oak, sugar maple, balsam fir, white ash, American beech, and red maple. Common variants and scientific names are case-insensitive. Ambiguous groups such as `oak` are rejected rather than silently resolved.

The default `ensemble` uses the Northeast urban model for yard/street sugar maples, the FIA model for supported forest trees, and otherwise reports an explicit `growth_factor` fallback. Algorithms can also be selected directly:

- `fia_age_size`: transparent CT/MA FIA site-tree log-age/log-DBH model for six well-sampled species, with state effects and empirical residual intervals.
- `growth_factor`: stable but crude horticultural rule of thumb for all ten species.
- `bai_reference`: experimental New England regional-average BAI reference model.
- `ensemble`: context-aware routing among the urban sugar-maple, FIA, and growth-factor models.
- `urban_sugar_maple`: published Northeast urban DBH-to-years-since-planting equation for open-grown sugar maples.

Inspect packaged metadata and coefficients:

```bash
tree-age explain --estimator fia_age_size
tree-age model check
```

## Interpret the interval

The FIA model uses separate training, calibration, and validation partitions. Its conservative residual intervals target at least 80% coverage; observed held-out CT/MA coverage is 86.0%. That does **not** mean any individual tree has an 86% probability of lying in its range, nor does it transfer automatically to other regions or yard trees. Estimates outside a species' training DBH range receive wider intervals and a warning.

Growth-factor and BAI intervals are broad heuristics, not statistically calibrated confidence intervals.

## Forest, yard, and street context

FIA data are forest-derived. `--context forest` is the closest match to the training domain. For sugar maple, `yard` and `street` select the separate USDA Northeast urban model; `unknown` retains the forest model with a warning. Street-tree management and urban stress can counteract the faster growth often seen in open-grown trees.

## Data, validation, and limitations

The v1 empirical artifact uses selected FIA site trees from Connecticut and Massachusetts. Held-out MAE is 11.808 years versus 14.124 years for the growth-factor fallback on the same records. It does not model tree health, competition, climate, height, elevation, soil, suppression, release, or management history.

- [FIA age-size v1 model card](docs/FIA_AGE_SIZE_V1_MODEL_CARD.md)
- [Northeast urban sugar-maple model card](docs/URBAN_SUGAR_MAPLE_MODEL_CARD.md)
- [Machine-readable evaluation report](docs/fia_age_size_v1_evaluation.json)
- [FIA download, cleaning, and quality workflow](docs/FIA_DATA_PIPELINE.md)
- [Development roadmap](ROADMAP.md)

FVS integration remains optional and deliberately separate: FVS is useful for forward projection and sanity checks, not ground-truth backward age inference. A web/API layer is likewise optional; the tested library and JSON CLI are the stable interface for v1.

## Development

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m tree_age.fia.cli download --states CT MA
python -m tree_age.fia.cli clean --states CT MA
python -m tree_age.modeling.train data/processed/fia_new_england_clean.csv
```

Raw and processed FIA data are ignored by Git. Model artifacts, model cards, provenance, and evaluation summaries are versioned.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
