# Tree Age Estimator

Tree Age Estimator gives a **rough, plausible age range** for a living tree from its species and circumference at breast height. It includes an experimental regional-average basal-area-increment (BAI) reference model and a conservative growth-factor fallback for ten New England species.

Circumference alone cannot reveal a tree's exact age. Competition, climate, disease, soil, damage, and growing context can produce very different ages at the same trunk size. Results are estimates, not planting dates or substitutes for increment-core measurements.

## Supported species

- White pine
- Eastern hemlock (shown as Hemlock)
- Yellow birch
- Red spruce
- Northern red oak (shown as Red oak)
- Sugar maple
- Balsam fir
- White ash
- American beech
- Red maple

Common variants and scientific names are accepted without regard to capitalization. For example, `eastern white pine`, `White Pine`, and `Pinus strobus` resolve to the same species.

## Measure the tree

Measure trunk circumference at breast height: 1.4 m (4.5 ft) above the ground. Keep a flexible tape level and snug around the trunk. Record centimeters or inches. Multi-stemmed, forked, leaning, or unusually swollen trees require forestry-specific measurement conventions and may not be suitable for this estimator.

## Install and run

Python 3.10 or newer is required.

```bash
python -m pip install -e .
tree-age "Red Spruce" 100
```

The repository's compatibility script also works without installation:

```bash
python tree_age_calculator.py "red spruce" 100
python tree_age_calculator.py "Acer rubrum" 40 --units in --context yard --json
python tree_age_calculator.py "red maple" 100 --estimator bai_reference
python tree_age_calculator.py "red maple" 100 --estimator growth_factor
```

Example output:

```text
Species: Red spruce
Estimated age: about 102 years
Plausible range: 61-163 years
Confidence: very rough
Estimator: bai_reference_v1
Warning: This is a rough estimate from a regional-average BAI model, not a measured age.
Warning: The model does not account for competition, disease, soil, climate, or tree-specific growth history.
```

Use `--estimator` to select a registered algorithm, `--context forest|yard|street|unknown` to identify the growing setting, `--state` to retain location context, and `--json` for structured output. The current model does not adjust its estimate by state or context; it adds a warning for open-grown yard and street trees.

## Model and limitations

`growth_factor` multiplies DBH in inches by a species reference factor. It is stable and easy to interpret, but is only a horticultural rule of thumb; its interval is intentionally broad.

`bai_reference` is based on the species-level reference values reported in *Regionally Averaged Diameter Growth in New England Forests* (Smith, Hornbeck, Federer, and Krusic, USDA Forest Service Research Paper NE-637, 1990). It bounds the paper's 1950-1980 growth curve outside that period and integrates annual basal-area growth backward from the present.

The broad interval is deliberately conservative, but it is a heuristic interval rather than a statistically calibrated confidence interval. The model is primarily forest-derived, limited to New England species, and does not model temperature, elevation, soil, suppression, release, management, or tree health.

## Development

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

The implementation roadmap is in [ROADMAP.md](ROADMAP.md). The safe CLI, modular estimator registry, conservative fallback, and reproducible USDA FIA pipeline are complete; empirical model training and calibrated uncertainty are next.

The reproducible FIA download and cleaning workflow is documented in [docs/FIA_DATA_PIPELINE.md](docs/FIA_DATA_PIPELINE.md). Data quality review is a required gate before model training.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
