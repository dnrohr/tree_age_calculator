import csv
from importlib.resources import files

from ..measurements import TreeMeasurement
from ..result import AgeEstimate, SiteContext
from ..species import resolve_species
from .base import AgeEstimator


def load_growth_factors() -> dict[str, float]:
    resource = files("tree_age.data").joinpath("growth_factors.csv")
    with resource.open("r", encoding="utf-8", newline="") as handle:
        return {
            row["species"]: float(row["growth_factor"])
            for row in csv.DictReader(handle)
        }


class GrowthFactorEstimator(AgeEstimator):
    """Conservative fallback using age ~= DBH inches * species factor."""

    name = "growth_factor_v1"

    def __init__(self) -> None:
        self.growth_factors = load_growth_factors()

    def estimate(
        self,
        species: str,
        measurement: TreeMeasurement,
        site: SiteContext | None = None,
    ) -> AgeEstimate:
        resolved = resolve_species(species)
        factor = self.growth_factors[resolved.canonical_name]
        point = max(1, int(measurement.dbh_inches * factor + 0.5))
        lower = max(1, round(point * 0.6))
        upper = max(lower + 1, round(point * 1.7))
        warnings = [
            "Growth-factor estimates are crude rules of thumb, not measured ages.",
            "Actual growth varies substantially with site, competition, climate, health, and tree history.",
        ]
        if site and site.context in {"yard", "street"}:
            warnings.append("Open-grown yard and street trees may be younger than this estimate.")
        return AgeEstimate(
            species=resolved.canonical_name,
            dbh_cm=round(measurement.dbh_cm, 2),
            estimator_name=self.name,
            estimated_age_years=point,
            lower_age_years=lower,
            upper_age_years=upper,
            confidence_label="very rough",
            warnings=tuple(warnings),
            assumptions={
                "formula": "DBH in inches multiplied by species growth factor",
                "growth_factor": factor,
                "measurement": "circumference at breast height",
            },
        )
