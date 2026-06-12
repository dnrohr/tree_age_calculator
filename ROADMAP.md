# Tree Age Estimator Roadmap

## Purpose

Build a tree-age estimation program that is honest about uncertainty, easy to extend, and grounded in better data than a single regional average growth table.

The immediate goal is **not** to produce exact tree ages. Circumference alone cannot do that. The goal is to produce a defensible estimate such as:

```text
Estimated age: 72 years
Likely range: 50–105 years
Estimator: FIA age-size model, Northeast region, red maple
Warnings: forest-derived model; open-grown yard trees may be younger
```

The long-term goal is a modular estimator that can support multiple backends:

1. A simple fallback estimator.
2. A cleaned-up version of the current BAI-based estimator.
3. A data-driven FIA estimator.
4. Optional forward-growth simulations using FVS-style models.
5. Clear uncertainty intervals and warnings.

\---

## Guiding principles

### 1\. Return ranges, not false precision

A program that says a tree is **83 years old** is likely misleading. A better estimator says **roughly 60–110 years old**, explains why, and identifies which assumptions dominate the estimate.

### 2\. Separate measurement, data, model, and presentation

Do not let the command-line interface, species table, data source, and statistical model become one file. Keep them separable from the start.

### 3\. Treat forest trees and yard/street trees differently

Forest inventory data are mostly forest-derived. Open-grown yard trees often have less competition and may reach a given diameter faster than forest trees. The program should ask for `context`, even if the first version only warns about it.

### 4\. Make scientific uncertainty visible

The result object should always have room for:

* Point estimate.
* Lower and upper interval.
* Model name.
* Data source.
* Warnings.
* Input assumptions.

### 5\. Make every estimator testable by itself

Every estimator should be runnable from a unit test without invoking the CLI.

\---

## Recommended project structure

```text
tree\_age\_estimator/
  pyproject.toml
  README.md
  data/
    species\_aliases.yaml
    species\_codes\_fia.csv
    bai\_reference\_table.csv
    model\_registry.yaml
  src/
    tree\_age/
      \_\_init\_\_.py
      cli.py
      measurements.py
      species.py
      result.py
      estimators/
        \_\_init\_\_.py
        base.py
        growth\_factor.py
        bai\_reference.py
        fia\_age\_size.py
        ensemble.py
      fia/
        download.py
        schema.py
        extract.py
        clean.py
      modeling/
        train.py
        features.py
        evaluate.py
        intervals.py
      validation/
        benchmark\_cases.py
      report.py
  tests/
    test\_measurements.py
    test\_species.py
    test\_growth\_factor.py
    test\_bai\_reference.py
    test\_result\_contract.py
    test\_cli.py
  notebooks/
    01\_explore\_fia\_age\_data.ipynb
    02\_fit\_age\_dbh\_models.ipynb
    03\_validate\_estimators.ipynb
```

For a small first version, this can be compressed, but preserve the boundaries conceptually.

\---

# Phase 0 — Define the product honestly

## Objective

Decide what the program is and is not trying to do.

## Tasks

1. Define the primary use case.

   Suggested default:

   > Estimate the approximate age range of a living tree in the northeastern United States from species and circumference at breast height.

2. Define required inputs.

   Minimum:

   * Species.
   * Circumference at breast height.

   Strongly recommended:

   * State or region.
   * Forest / yard / street / unknown context.
   * Measurement units.
3. Define output semantics.

   Example:

   ```json
   {
     "estimated\_age\_years": 78,
     "lower\_age\_years": 52,
     "upper\_age\_years": 119,
     "confidence\_label": "rough",
     "estimator": "fia\_age\_size\_v1",
     "warnings": \[
       "Model is trained primarily on forest inventory data.",
       "Open-grown trees may be younger than the estimate."
     ]
   }
   ```

4. Decide what counts as a successful result.

   Suggested standard:

   * The program should never hang.
   * The program should never return a precise-looking number without a warning or interval.
   * Unknown species should produce an actionable error.
   * Large, old, or unusual trees should trigger wider uncertainty.

   ## Acceptance criteria

* README says “estimate” and “range,” not “calculate exact age.”
* CLI examples show intervals.
* Known limitations are explicit.

  \---

  # Phase 1 — Stabilize the current estimator

  ## Objective

  Make the existing program safe, testable, and internally consistent before adding better data.

  ## Current problem areas to fix

1. Species names are case-sensitive.
2. Some species can produce zero growth and an infinite loop.
3. The README describes environmental adjustments that the code does not implement.
4. The model returns a single number with false precision.
5. The growth equation likely mixes absolute calendar year and normalized year.
6. The code catches `ValueError`, but unknown species raise `KeyError`.

   ## Tasks

   ### 1\. Add a measurement conversion layer

   Create a `TreeMeasurement` object.

   ```python
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class TreeMeasurement:
    circumference\_cm: float

    @property
    def dbh\_cm(self) -> float:
        return self.circumference\_cm / math.pi

    @property
    def radius\_cm(self) -> float:
        return self.circumference\_cm / (2 \* math.pi)

    @property
    def basal\_area\_cm2(self) -> float:
        return math.pi \* self.radius\_cm \*\* 2
```

   Note: forestry DBH is diameter at breast height, so circumference converts to DBH as:

   ```text
DBH = circumference / pi
```

   ### 2\. Normalize species names

   Create aliases such as:

   ```yaml
red maple:
  canonical: Red maple
  aliases:
    - red maple
    - acer rubrum
sugar maple:
  canonical: Sugar maple
  aliases:
    - sugar maple
    - acer saccharum
hemlock:
  canonical: Hemlock
  aliases:
    - eastern hemlock
    - hemlock
    - tsuga canadensis
white pine:
  canonical: White pine
  aliases:
    - eastern white pine
    - white pine
    - pinus strobus
```

   ### 3\. Prevent infinite loops

   Any iterative estimator must have:

* A maximum age cap.
* A positive-growth check.
* A clear failure mode.

  Example:

  ```python
def integrate\_growth\_curve(species: str, circumference\_cm: float, max\_age: int = 600):
    target\_area = TreeMeasurement(circumference\_cm).basal\_area\_cm2
    cumulative\_area = 0.0
    year = current\_year()

    for age in range(1, max\_age + 1):
        growth\_rate = calculate\_growth\_rate(species, year)
        if growth\_rate <= 0:
            raise ModelError(
                f"Non-positive growth rate for {species} in {year}: {growth\_rate}"
            )
        cumulative\_area += growth\_rate
        if cumulative\_area >= target\_area:
            return age
        year -= 1

    raise ModelError(f"Target basal area not reached after {max\_age} years")
```

  ### 4\. Fix or isolate the current BAI equation

  Do not treat the current equation as canonical until it has been checked against the source table and paper.

  Create a dedicated estimator called something like:

  ```text
BaiReferenceEstimator
```

  and mark it as experimental.

  ### 5\. Add unit tests before changing behavior further

  Minimum tests:

  ```text
- circumference\_to\_dbh\_cm works.
- unknown species raises UnknownSpeciesError.
- known species aliases resolve correctly.
- estimator never loops forever.
- estimator returns wider interval or warning, not just a point estimate.
- CLI supports README examples exactly.
```

  ## Acceptance criteria

* `python tree\_age\_calculator.py "Red Spruce" 100` does not hang.
* `python tree\_age\_calculator.py "red spruce" 100` works.
* Bad species input gives a list of valid species.
* README and CLI behavior match.
* Current estimator is labeled as rough/experimental.

  \---

  # Phase 2 — Define a common estimator interface

  ## Objective

  Make it easy to swap algorithms without rewriting the CLI.

  ## Core data classes

  ```python
from dataclasses import dataclass, field
from typing import Literal

TreeContext = Literal\["forest", "yard", "street", "unknown"]

@dataclass(frozen=True)
class SiteContext:
    state: str | None = None
    county: str | None = None
    ecoregion: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    context: TreeContext = "unknown"
    elevation\_m: float | None = None

@dataclass(frozen=True)
class AgeEstimate:
    species: str
    dbh\_cm: float
    estimator\_name: str
    estimated\_age\_years: float | None
    lower\_age\_years: float | None
    upper\_age\_years: float | None
    confidence\_label: str
    warnings: list\[str] = field(default\_factory=list)
    assumptions: dict = field(default\_factory=dict)
```

  ## Estimator base class

  ```python
from abc import ABC, abstractmethod

class AgeEstimator(ABC):
    name: str

    @abstractmethod
    def estimate(
        self,
        species: str,
        measurement: TreeMeasurement,
        site: SiteContext | None = None,
    ) -> AgeEstimate:
        ...
```

  ## Estimator registry

  ```python
ESTIMATORS = {
    "growth\_factor": GrowthFactorEstimator,
    "bai\_reference": BaiReferenceEstimator,
    "fia\_age\_size": FiaAgeSizeEstimator,
    "ensemble": EnsembleEstimator,
}
```

  ## Acceptance criteria

* CLI can select an estimator with `--estimator`.
* All estimators return the same `AgeEstimate` schema.
* Tests can run estimators directly without shelling out.

  \---

  # Phase 3 — Build a conservative fallback estimator

  ## Objective

  Create a simple estimator that is not sophisticated but is stable and honest.

  ## Algorithm

  Many informal tree-age calculators use species growth factors:

  ```text
age ≈ DBH\_in\_inches × species\_growth\_factor
```

  This is crude, but useful as a fallback if no better model is available.

  ## Tasks

1. Store growth factors in a CSV or YAML file.
2. Normalize all measurements to DBH in inches for this estimator.
3. Add broad uncertainty bands.
4. Add warnings for yard/street trees.

   Example output:

   ```json
{
  "estimated\_age\_years": 65,
  "lower\_age\_years": 40,
  "upper\_age\_years": 105,
  "confidence\_label": "very rough",
  "estimator": "growth\_factor",
  "warnings": \[
    "Growth-factor estimates are crude and should be treated as order-of-magnitude estimates."
  ]
}
```

   ## Why this phase matters

   This gives you a working reference estimator while the data-driven model is being built. It also gives users an answer even when a species is missing from the more complex model.

   ## Acceptance criteria

* Supports all species in the current README.
* Always returns an uncertainty interval.
* Emits “very rough” confidence.
* Can be used as a fallback by the ensemble estimator.

  \---

  # Phase 4 — Add a cleaned-up BAI reference estimator

  ## Objective

  Preserve the spirit of the current program while preventing it from being the only model.

  ## Recommended interpretation

  Treat the existing paper-derived BAI table as a regional reference model, not a general tree-age model.

  ## Tasks

1. Move the current species table to `data/bai\_reference\_table.csv`.
2. Store units explicitly.
3. Add source metadata.
4. Implement equation variants carefully and compare them.
5. Add a notebook that plots growth rate by species and year.
6. Reject or warn on implausible curves.

   ## Validation plots

   For each species, plot:

   ```text
x-axis: year, 1950–1980
y-axis: predicted BAI
```

   The plot should make obvious if the equation has gone numerically wrong.

   ## Model warnings

   This estimator should always include warnings like:

   ```text
This estimate uses a regional-average basal-area-increment model. It does not account for suppression, release, competition, open-grown form, disease, soil compaction, or tree-specific history.
```

   ## Acceptance criteria

* BAI is positive for supported species or the estimator refuses to run.
* No species produces a zero-growth infinite loop.
* The estimator has visual regression tests or saved diagnostic plots.
* Output includes strong uncertainty language.

  \---

  # Phase 5 — Build an FIA data pipeline

  ## Objective

  Create a real empirical training dataset from Forest Inventory and Analysis data.

  ## Why FIA

  The USDA FIA DataMart provides public raw data files, standard tables, SQLite databases, FVS input files, and user guides. That makes it a better foundation for a maintainable estimator than hand-copying a single table from a paper.

  ## Important caveat

  FIA is a forest inventory system. It is excellent for forest trees, but not automatically representative of open-grown yard trees or street trees.

  ## Initial geographic scope

  Start with New England:

  ```text
CT, MA, ME, NH, RI, VT
```

  Then optionally add:

  ```text
NY, NJ, PA
```

  ## Data source strategy

  Use one of these approaches:

  ### Option A — Use FIA state SQLite databases

  Preferred for a Python project.

  Tasks:

1. Download state SQLite databases from FIA DataMart.
2. Store them outside git, e.g. `data/raw/fia/`.
3. Write a script that records download date and source.
4. Query only required tables.
5. Export a cleaned Parquet file for modeling.

   ### Option B — Use raw CSV files

   Simpler, but less convenient as the project grows.

   Tasks:

1. Download CSVs per state.
2. Load with pandas.
3. Join needed tables.
4. Save normalized Parquet.

   ### Option C — Use an existing produced tree-age dataset

   The 2025 Lu et al. study produced a tree-age dataset and describes estimating tree ages for FIA trees using diameter and other tree-level attributes. This may be the fastest way to bootstrap the project, but you should still understand the underlying assumptions.

   ## Likely FIA variables to investigate

   Verify every field against the current FIADB user guide before coding hard assumptions.

   Candidate variables:

   ```text
TREE table:
  SPCD       species code
  DIA        diameter
  HT         total height, when available
  STATUSCD   live/dead status
  INVYR      inventory year
  BHAGE      breast-height age, if available
  TOTAGE     total age, if available

PLOT table:
  STATECD
  COUNTYCD
  PLOT
  LAT
  LON
  ELEV

COND table:
  STDAGE     stand age, if available/applicable
  FORTYPCD   forest type code
  PHYSCLCD   physiographic class
  STDORGCD   stand origin
  SLOPE
  ASPECT
```

   Important: individual tree age fields are not universally populated. You will need a clear target hierarchy.

   ## Target age hierarchy

   Use the best available age target in this order:

1. Individual total age, if present and reliable.
2. Individual breast-height age, adjusted cautiously if a species-specific correction is available.
3. Site-tree age or stand-age proxy, flagged as lower quality.
4. Exclude record from supervised training if no defensible age target exists.

   Never silently mix these targets without a `target\_quality` column.

   ## Clean dataset schema

   Create one modeling table:

   ```text
species\_code
species\_common\_name
species\_scientific\_name
dbh\_cm
height\_m
age\_years
target\_type              # total\_age, breast\_height\_age, stand\_age\_proxy
state
county
ecoregion
latitude\_rounded
longitude\_rounded
elevation\_m
slope\_percent
aspect\_degrees
forest\_type\_code
stand\_origin\_code
inventory\_year
source\_database\_version
```

   ## Data quality checks

   Reject or flag records where:

* DBH is missing or nonpositive.
* Age is missing or nonpositive.
* DBH is implausibly small for age target method.
* Age is implausibly high for species without corroboration.
* Species code cannot be mapped.
* Measurement units are ambiguous.

  ## Acceptance criteria

* `make fia-data-ne` downloads or prepares New England data.
* `make fia-clean-ne` produces one cleaned modeling table.
* Data-prep script writes a report with row counts by state, species, and target type.
* No model training happens until data quality summaries are reviewed.

  \---

  # Phase 6 — Fit the first FIA age-size model

  ## Objective

  Train a data-driven model that estimates age from DBH, species, and region.

  ## Start with a deliberately simple model

  Do not start with a black-box model. First fit a transparent baseline:

  ```text
log(age) \~ species + log(DBH) + species:log(DBH) + region/ecoregion
```

  In Python terms:

  ```python
log\_age = beta0\[species] + beta1\[species] \* log\_dbh + beta\_region\[region] + error
```

  This model is simple enough to inspect and difficult enough to beat that it makes a good baseline.

  ## Candidate models

  Fit in this order:

  ### Model 1 — Species-specific log-linear model

  Inputs:

* Species.
* Log DBH.

  Pros:

* Easy to explain.
* Good baseline.

  Cons:

* Ignores site and climate.

  ### Model 2 — Species + ecoregion model

  Inputs:

* Species.
* Log DBH.
* Ecoregion or state.

  Pros:

* Captures regional differences.

  Cons:

* Sparse species-region combinations may be unstable.

  ### Model 3 — Species + size + site model

  Inputs:

* Species.
* Log DBH.
* Height, if available.
* Elevation.
* Slope/aspect.
* Forest type.
* Stand origin.

  Pros:

* More realistic.

  Cons:

* More missing-data handling.

  ### Model 4 — Quantile model or Bayesian interval model

  Purpose:

* Produce defensible uncertainty intervals directly.

  Pros:

* Better user-facing output.

  Cons:

* More modeling complexity.

  ## Train/test strategy

  Avoid random splits alone. Use several splits:

  ```text
1. Random row split.
2. Holdout by state.
3. Holdout by species.
4. Holdout by plot or county to reduce spatial leakage.
5. Holdout by inventory year if sample sizes allow.
```

  ## Metrics

  Track:

  ```text
MAE years
Median absolute error years
RMSE years
Mean absolute percentage error
Coverage of 50%, 80%, and 95% intervals
Bias by species
Bias by DBH class
Bias by state/ecoregion
```

  The interval coverage metrics are especially important. If the 80% interval only contains the true age 55% of the time, the interval is too narrow.

  ## Acceptance criteria

* Baseline model beats the crude growth-factor estimator on held-out FIA records.
* Evaluation report includes per-species and per-region error.
* Model can be serialized and loaded by the CLI.
* The estimator refuses unsupported species/regions or falls back cleanly.

  \---

  # Phase 7 — Add uncertainty intervals

  ## Objective

  Make uncertainty a first-class output.

  ## Recommended approach for v1

  Use empirical residual intervals by species and DBH class.

  Example:

1. Fit a point-estimate model.
2. On validation data, compute residuals:

   ```text
   residual = observed\_age - predicted\_age
   ```

3. Group residuals by:

   ```text
   species group × DBH class × region
   ```

4. Estimate residual quantiles.
5. Add those quantiles to future predictions.

   ## Example result calculation

   ```python
prediction = 78
residual\_p10 = -26
residual\_p90 = 41

lower = prediction + residual\_p10  # 52
upper = prediction + residual\_p90  # 119
```

   ## Fallback interval logic

   If a group has too little data:

1. Fall back from species × DBH × region.
2. To species × DBH.
3. To species.
4. To hardwood/softwood group.
5. To global residuals.

   Each fallback should add a warning.

   ## Acceptance criteria

* Every successful result has lower and upper bounds.
* Intervals widen when the model lacks local/species-specific data.
* Validation report shows empirical coverage.

  \---

  # Phase 8 — Handle yard, street, and open-grown trees

  ## Objective

  Avoid applying forest-derived models blindly to trees outside forests.

  ## Problem

  A yard maple and a forest maple with the same DBH may not be the same age. Open-grown trees often grow faster because they face less crown competition, though urban stress can complicate this.

  ## First implementation

  Add a `--context` option:

  ```bash
tree-age estimate --species "red maple" --circumference 180 --units cm --state MA --context yard
```

  Allowed values:

  ```text
forest
yard
street
unknown
```

  For v1:

* `forest`: use FIA model normally.
* `unknown`: use FIA model but warn.
* `yard`: use FIA model but warn that the true age may be lower.
* `street`: use FIA model but warn strongly; consider urban-tree model later.

  ## Later implementation

  Add an urban/open-grown modifier only after finding a credible data source. Do not invent a multiplier without validation.

  ## Acceptance criteria

* CLI asks for or accepts context.
* Result includes context-specific warnings.
* README explains forest vs yard limitations.

  \---

  # Phase 9 — Add FVS as a separate optional backend

  ## Objective

  Use Forest Vegetation Simulator ideas or data where appropriate without forcing a forward simulator into a backward age-estimation problem.

  ## Important distinction

  FVS is primarily a forest growth simulation model: it projects vegetation change over time in response to succession, disturbance, and management. That makes it useful for forward growth projections, but not automatically ideal for inferring age from current DBH.

  ## Reasonable uses

1. Compare your fitted growth curves against FVS-style diameter growth expectations.
2. Use FVS for future growth projection after age has been estimated.
3. Use FVS-derived growth rates as priors or sanity checks.

   ## Avoid initially

   Do not try to invert full FVS simulations as the primary estimator in v1. That will introduce many assumptions about stand density, competition, management history, and site index.

   ## Acceptance criteria

* FVS integration is optional.
* It does not replace the FIA age-size model.
* Documentation clearly says “forward projection,” not “ground truth age.”

  \---

  # Phase 10 — Build the CLI

  ## Objective

  Make the tool useful from the command line while preserving a clean library API.

  ## Suggested commands

  ```bash
# Estimate age
age-tree estimate \\
  --species "red maple" \\
  --circumference 180 \\
  --units cm \\
  --state MA \\
  --context yard \\
  --estimator fia\_age\_size

# List species
age-tree species list

# Explain estimator
age-tree explain --estimator fia\_age\_size

# Validate local model files
age-tree model check

# Print JSON instead of prose
age-tree estimate \\
  --species "red maple" \\
  --circumference 180 \\
  --units cm \\
  --state MA \\
  --format json
```

  ## Human-readable output

  ```text
Estimated age: 74 years
Likely range: 49–118 years
Confidence: rough
Estimator: FIA age-size model v1

Warnings:
- This model is trained primarily on forest inventory data.
- You marked the tree as yard/open-grown; true age may be lower.
- Species/site history can dominate circumference-based estimates.
```

  ## JSON output

  ```json
{
  "species": "Red maple",
  "dbh\_cm": 57.3,
  "estimated\_age\_years": 74,
  "lower\_age\_years": 49,
  "upper\_age\_years": 118,
  "confidence\_label": "rough",
  "estimator\_name": "fia\_age\_size\_v1",
  "warnings": \[
    "This model is trained primarily on forest inventory data.",
    "Yard/open-grown context may make the true age lower."
  ]
}
```

  ## Acceptance criteria

* CLI and library produce identical estimates.
* `--format json` is stable enough for downstream use.
* Help text explains measurement at breast height.
* Bad inputs produce actionable errors.

  \---

  # Phase 11 — Build validation and benchmark cases

  ## Objective

  Prevent the program from feeling plausible while being wrong.

  ## Validation sources

  Use several types of validation:

1. Held-out FIA records with age measurements.
2. Known-age planted trees, where available.
3. Published dendrochronology examples.
4. Local field examples only if age is independently known.
5. Synthetic sanity tests.

   ## Synthetic sanity tests

   Examples:

   ```text
- A 5 cm DBH tree should not estimate as 200 years old for common New England species.
- A 100 cm DBH white pine should not estimate as 15 years old.
- Age should generally increase with DBH within the same species and region.
- Uncertainty should widen for very large DBH values outside training range.
```

   ## Benchmark report

   Generate a report with:

   ```text
- Model version.
- Training data date.
- Number of training records.
- Species supported.
- Overall error metrics.
- Error by species.
- Error by DBH class.
- Error by region.
- Interval coverage.
- Known failure modes.
```

   ## Acceptance criteria

* Every release includes a model card or validation report.
* Regression tests prevent accidental narrowing of intervals.
* Monotonic sanity checks pass or exceptions are explained.

  \---

  # Phase 12 — Improve species handling

  ## Objective

  Make species input robust enough for real users.

  ## Tasks

1. Support common names.
2. Support scientific names.
3. Support fuzzy matching with confirmation.
4. Map species to FIA species codes.
5. Group rare species where necessary.

   ## Example behavior

   ```text
Input: "eastern white pine"
Resolved: White pine / Pinus strobus / FIA SPCD 129
```

   For ambiguous names:

   ```text
Input: "oak"
Error: "Oak" is ambiguous. Did you mean northern red oak, white oak, black oak, or another species?
```

   ## Acceptance criteria

* Species resolution is deterministic.
* Ambiguous names do not silently choose a species.
* Missing species fall back to genus/group only when explicitly allowed.

  \---

  # Phase 13 — Add model cards and source metadata

  ## Objective

  Make the estimator auditable.

  ## Model card contents

  For each model version, write:

  ```text
Model name
Model version
Training data source
Training data download date
States/regions included
Species included
Target age definition
Features used
Validation method
Known limitations
Appropriate use cases
Inappropriate use cases
```

  ## Example model registry

  ```yaml
fia\_age\_size\_v1:
  model\_file: models/fia\_age\_size\_v1.pkl
  training\_data: data/processed/fia\_ne\_2026\_06.parquet
  source: USDA FIA DataMart
  states: \[CT, MA, ME, NH, RI, VT]
  target\_types: \[TOTAGE, BHAGE]
  created: 2026-06-11
  interval\_method: empirical\_residual\_quantiles
```

  ## Acceptance criteria

* CLI can show model metadata.
* Every estimate includes model version.
* Model files are not detached from their data provenance.

  \---

  # Phase 14 — Optional web/app layer

  ## Objective

  Make the estimator approachable without compromising the model.

  ## Possible interfaces

1. CLI only.
2. Local web app with FastAPI.
3. Streamlit app for experimentation.
4. Static front-end calling a small API.

   ## Recommended API endpoint

   ```http
POST /estimate
```

   Request:

   ```json
{
  "species": "red maple",
  "circumference": 180,
  "units": "cm",
  "state": "MA",
  "context": "yard"
}
```

   Response:

   ```json
{
  "estimated\_age\_years": 74,
  "lower\_age\_years": 49,
  "upper\_age\_years": 118,
  "confidence\_label": "rough",
  "warnings": \["..."]
}
```

   ## Acceptance criteria

* API uses the same library code as the CLI.
* API has input validation.
* API returns warnings, not just the estimate.

  \---

  # Phase 15 — Documentation rewrite

  ## Objective

  Make the README match the actual model.

  ## README sections

1. What this program does.
2. What it cannot do.
3. How to measure circumference.
4. Supported species.
5. Supported regions.
6. Estimator types.
7. Example outputs.
8. Interpretation of uncertainty intervals.
9. Data sources.
10. Development roadmap.

    ## Replace overclaims

    Avoid:

    ```text
Calculates the age of a tree.
```

    Prefer:

    ```text
Estimates a plausible age range for a tree from species and circumference, using species- and region-specific growth data where available.
```

    Avoid:

    ```text
Adjusts growth rate based on temperature, elevation, and soil type.
```

    unless those adjustments are actually implemented and validated.

    ## Acceptance criteria

* Every README feature is covered by a test or explicitly marked planned.
* Examples run exactly as written.
* Limitations are visible near the top, not hidden at the bottom.

  \---

  # Implementation order summary

  ## Milestone 1 — Safe current program

  Deliverable:

  ```text
A stable CLI that estimates age ranges using the current/reference data without hangs or misleading exactness.
```

  Tasks:

* Normalize species names.
* Fix bad input handling.
* Add max-age limit.
* Add result object.
* Return uncertainty interval.
* Align README with actual code.

  ## Milestone 2 — Modular estimator architecture

  Deliverable:

  ```text
A library with interchangeable estimators and a stable result schema.
```

  Tasks:

* Add `AgeEstimator` base class.
* Add `TreeMeasurement`, `SiteContext`, and `AgeEstimate`.
* Add estimator registry.
* Add CLI `--estimator` option.

  ## Milestone 3 — Fallback estimator

  Deliverable:

  ```text
A crude but robust growth-factor estimator.
```

  Tasks:

* Add species growth-factor table.
* Add wide uncertainty intervals.
* Add warning system.

  ## Milestone 4 — FIA data pipeline

  Deliverable:

  ```text
A reproducible New England FIA dataset for modeling.
```

  Tasks:

* Download FIA state data.
* Join and clean required tables.
* Map species codes.
* Extract DBH, age targets, and site variables.
* Produce data quality report.

  ## Milestone 5 — FIA age-size model v1

  Deliverable:

  ```text
A trained model estimating age from species, DBH, and region.
```

  Tasks:

* Fit transparent baseline model.
* Validate by species, DBH class, and region.
* Serialize model.
* Integrate into CLI.

  ## Milestone 6 — Uncertainty model v1

  Deliverable:

  ```text
Empirical prediction intervals with coverage report.
```

  Tasks:

* Compute validation residuals.
* Build residual quantile tables.
* Add fallback interval hierarchy.
* Validate interval coverage.

  ## Milestone 7 — Model card and documentation

  Deliverable:

  ```text
A documented estimator with versioned data provenance and clear limitations.
```

  Tasks:

* Write model card.
* Rewrite README.
* Add example outputs.
* Include known failure modes.

  \---

  # Suggested near-term task list

  If you want the most direct next steps, do these in order:

1. Rename the project from `tree\_age\_calculator` to `tree\_age\_estimator`.
2. Replace the single-number return value with an `AgeEstimate` object.
3. Add species normalization and friendly errors.
4. Add `max\_age` and non-positive-growth checks.
5. Make the README honest about the current model.
6. Add a crude growth-factor fallback estimator.
7. Create a notebook that plots the current BAI growth curves by species.
8. Decide whether to keep or discard the current BAI equation after visual inspection.
9. Download New England FIA SQLite data.
10. Build a cleaned modeling table with DBH, species, location, and age target.
11. Fit the first log-age/log-DBH model.
12. Validate it against held-out records.
13. Add empirical uncertainty intervals.
14. Make the CLI default to the best available estimator and fall back safely.

    \---

    # Key risks

    ## Risk 1 — Circumference is a weak proxy for age

    Mitigation:

* Always return intervals.
* Include context warnings.
* Validate by DBH class and species.

  ## Risk 2 — FIA individual age data are sparse or inconsistent

  Mitigation:

* Track `target\_type` and `target\_quality`.
* Do not mix total age, breast-height age, and stand age silently.
* Start regionally, not nationally.

  ## Risk 3 — Yard/street trees differ from forest trees

  Mitigation:

* Add context input early.
* Warn for non-forest contexts.
* Delay urban-tree correction until credible data are available.

  ## Risk 4 — Model looks precise because code is precise

  Mitigation:

* Round estimates appropriately.
* Avoid exact planting-year claims unless the interval is narrow and justified.
* Show uncertainty prominently.

  ## Risk 5 — Species names cause silent errors

  Mitigation:

* Central species resolver.
* Alias table.
* No silent genus-level fallback unless the user opts in.

  \---

  # References and resources

* USDA Forest Service FIA DataMart: provides raw FIA data files, standard tables, SQLite databases, FVS input files, EVALIDator, state reports, load history, API EVALIDator, and FIADB user guides.
* USDA Forest Service FIADB User Guide: authoritative reference for FIADB schema, codes, and definitions.
* Lu et al. 2025, *Tree age estimation across the U.S. using forest inventory and analysis database*: useful conceptual model for deriving tree ages from FIA diameter and tree-level attributes.
* USDA Forest Service Forest Vegetation Simulator: useful for forward growth simulation and sanity checks, but not the first tool I would use for backward age inference from DBH.

  \---

  # Bottom-line recommendation

  Build the program in this order:

  ```text
safe current estimator
→ modular estimator interface
→ crude fallback model
→ FIA data pipeline
→ FIA age-size model
→ empirical uncertainty intervals
→ model cards and documentation
```

  Do not start by making the ecological model more complicated. Start by making the estimate object, error handling, data provenance, and uncertainty machinery solid. Once those are in place, improving the model becomes a contained problem rather than a rewrite.

