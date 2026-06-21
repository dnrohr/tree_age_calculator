from abc import ABC, abstractmethod

from ..measurements import TreeMeasurement
from ..result import AgeEstimate, SiteContext


class AgeEstimator(ABC):
    """Stable contract implemented by every tree age estimator."""

    name: str

    @abstractmethod
    def estimate(
        self,
        species: str,
        measurement: TreeMeasurement,
        site: SiteContext | None = None,
    ) -> AgeEstimate:
        """Return an estimate with uncertainty and model warnings."""

