import csv
from importlib.resources import files
import json
import math

from ..errors import ModelError
from ..measurements import TreeMeasurement
from ..result import AgeEstimate, SiteContext
from ..species import resolve_species
from .base import AgeEstimator


class UrbanSugarMapleEstimator(AgeEstimator):
    """Published Northeast urban sugar-maple DBH-to-age equation."""

    name = "urban_sugar_maple_v1"

    def __init__(self) -> None:
        coefficient_resource = files("tree_age.data").joinpath("urban_tree_northeast_sugar_maple.csv")
        with coefficient_resource.open(encoding="utf-8", newline="") as handle:
            self.parameters = next(csv.DictReader(handle))
        metadata_resource = files("tree_age.data").joinpath(
            "urban_tree_northeast_sugar_maple_metadata.json"
        )
        with metadata_resource.open(encoding="utf-8") as handle:
            self.metadata = json.load(handle)

    def estimate(
        self,
        species: str,
        measurement: TreeMeasurement,
        site: SiteContext | None = None,
    ) -> AgeEstimate:
        resolved = resolve_species(species)
        if resolved.canonical_name != "Sugar maple":
            raise ModelError(f"{self.name} supports Sugar maple only.")

        dbh = measurement.dbh_cm
        intercept = float(self.parameters["intercept"])
        coefficient = float(self.parameters["coefficient"])
        mse = float(self.parameters["mse"])
        sigma = float(self.parameters["sigma"])
        log_center = intercept + coefficient * math.log(math.log(dbh + 1) + mse / 2)
        point_value = math.exp(log_center)
        z80 = 1.2815515655446004
        lower_value = math.exp(log_center - z80 * sigma)
        upper_value = math.exp(log_center + z80 * sigma)
        point = max(1, round(point_value))
        lower = max(1, min(point, round(lower_value)))
        upper = max(point + 1, round(upper_value))

        warnings = [
            "This model represents planted urban trees; age means years since planting.",
            "The Northeast sugar-maple age equation is based on only 16 observations.",
            "Massachusetts was not sampled directly; the published Northeast regional equation is being transferred.",
        ]
        context = site.context if site else "unknown"
        if context == "forest":
            warnings.append("Forest context is outside this urban model's intended domain; prefer fia_age_size.")
        elif context == "unknown":
            warnings.append("Growing context is unknown; use this model only for yard, park, or street trees.")
        raw_min = float(self.parameters["regional_raw_dbh_min_cm"])
        raw_max = float(self.parameters["regional_raw_dbh_max_cm"])
        outside_dbh_range = not raw_min <= dbh <= raw_max
        if outside_dbh_range:
            half_width = max(point - lower, upper - point)
            lower = max(1, point - round(half_width * 1.5))
            upper = point + round(half_width * 1.5)
            warnings.append("DBH is outside the Northeast regional raw sample range; interval widened.")

        return AgeEstimate(
            species=resolved.canonical_name,
            dbh_cm=round(dbh, 2),
            estimator_name=self.name,
            estimated_age_years=point,
            lower_age_years=lower,
            upper_age_years=upper,
            confidence_label="very rough",
            warnings=tuple(warnings),
            assumptions={
                "model_version": "1.0.0",
                "source": "USDA Forest Service Urban Tree Database",
                "source_doi": self.metadata["doi"],
                "source_region": self.parameters["region"],
                "source_sample_size": int(self.parameters["n"]),
                "adjusted_r2": float(self.parameters["adjusted_r2"]),
                "age_definition": "years since planted",
                "dbh_outside_regional_raw_range": outside_dbh_range,
            },
        )
