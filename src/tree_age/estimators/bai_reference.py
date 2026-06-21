from dataclasses import dataclass
from datetime import date
import math

from ..errors import ModelError
from ..measurements import TreeMeasurement
from ..result import AgeEstimate, SiteContext
from ..species import resolve_species
from .base import AgeEstimator


@dataclass(frozen=True)
class BaiParameters:
    mean_bai: float
    linear_coefficient: float
    curvature_coefficient: float
    weight: float


PARAMETERS = {
    "White pine": BaiParameters(13.4, 13.6, 0.28, 0.101),
    "Hemlock": BaiParameters(9.7, 9.9, -0.07, 0.146),
    "Yellow birch": BaiParameters(8.8, 12.1, -0.27, 0.159),
    "Red spruce": BaiParameters(8.5, -5.7, -0.93, 0.160),
    "Red oak": BaiParameters(8.1, 10.8, 0.19, 0.158),
    "Sugar maple": BaiParameters(8.0, 11.7, 0.14, 0.162),
    "Balsam fir": BaiParameters(7.7, -1.5, -1.72, 0.163),
    "White ash": BaiParameters(7.6, 9.6, 0.59, 0.179),
    "American beech": BaiParameters(6.7, 25.2, 0.64, 0.203),
    "Red maple": BaiParameters(6.7, 1.8, 0.33, 0.192),
}


class BaiReferenceEstimator(AgeEstimator):
    """Experimental regional-average BAI estimator for New England species."""

    name = "bai_reference_v1"

    def __init__(self, max_age: int = 600, reference_year: int | None = None):
        if max_age <= 0:
            raise ValueError("max_age must be positive")
        self.max_age = max_age
        self.reference_year = reference_year or date.today().year

    @staticmethod
    def growth_rate(species: str, year: int) -> float:
        canonical = resolve_species(species).canonical_name
        params = PARAMETERS[canonical]
        bounded_year = min(1980, max(1950, year))
        normalized_year = bounded_year - 1965
        linear = params.linear_coefficient / 1000
        curvature = params.curvature_coefficient / 1000
        return params.mean_bai + normalized_year * linear / params.weight + (
            normalized_year**2 - 80
        ) * curvature / params.weight

    def estimate(
        self,
        species: str,
        measurement: TreeMeasurement,
        site: SiteContext | None = None,
    ) -> AgeEstimate:
        resolved = resolve_species(species)
        cumulative_area = 0.0
        age = None
        for candidate_age in range(1, self.max_age + 1):
            year = self.reference_year - candidate_age + 1
            growth = self.growth_rate(resolved.canonical_name, year)
            if not math.isfinite(growth) or growth <= 0:
                raise ModelError(
                    f"Non-positive BAI for {resolved.canonical_name} in {year}: {growth:.3f}."
                )
            cumulative_area += growth
            if cumulative_area >= measurement.basal_area_cm2:
                age = candidate_age
                break
        if age is None:
            raise ModelError(
                f"Target basal area was not reached after {self.max_age} years; "
                "the tree is outside this model's supported size range."
            )

        lower = max(1, round(age * 0.6))
        upper = max(lower + 1, round(age * 1.6))
        warnings = [
            "This is a rough estimate from a regional-average BAI model, not a measured age.",
            "The model does not account for competition, disease, soil, climate, or tree-specific growth history.",
        ]
        if site and site.context in {"yard", "street"}:
            warnings.append("Open-grown yard and street trees may be younger than this forest-derived estimate.")
        return AgeEstimate(
            species=resolved.canonical_name,
            dbh_cm=round(measurement.dbh_cm, 2),
            estimator_name=self.name,
            estimated_age_years=age,
            lower_age_years=lower,
            upper_age_years=upper,
            confidence_label="very rough",
            warnings=tuple(warnings),
            assumptions={
                "region": "New England",
                "measurement": "circumference at breast height",
                "max_age_years": self.max_age,
            },
        )
