from ..errors import ModelError
from ..measurements import TreeMeasurement
from ..result import AgeEstimate, SiteContext
from .base import AgeEstimator
from .fia_age_size import FiaAgeSizeEstimator
from .growth_factor import GrowthFactorEstimator


class EnsembleEstimator(AgeEstimator):
    """Prefer the empirical model and fall back explicitly when unsupported."""

    name = "ensemble_v1"

    def __init__(self) -> None:
        self.primary = FiaAgeSizeEstimator()
        self.fallback = GrowthFactorEstimator()

    def estimate(
        self,
        species: str,
        measurement: TreeMeasurement,
        site: SiteContext | None = None,
    ) -> AgeEstimate:
        try:
            return self.primary.estimate(species, measurement, site)
        except ModelError:
            result = self.fallback.estimate(species, measurement, site)
            return AgeEstimate(
                species=result.species,
                dbh_cm=result.dbh_cm,
                estimator_name=f"{self.name} -> {result.estimator_name}",
                estimated_age_years=result.estimated_age_years,
                lower_age_years=result.lower_age_years,
                upper_age_years=result.upper_age_years,
                confidence_label=result.confidence_label,
                warnings=(
                    "The empirical FIA model does not support this species; the growth-factor fallback was used.",
                    *result.warnings,
                ),
                assumptions={**result.assumptions, "fallback_used": True},
            )
