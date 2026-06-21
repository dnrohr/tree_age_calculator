from collections.abc import Callable

from ..errors import ModelError
from .base import AgeEstimator
from .bai_reference import BaiReferenceEstimator
from .growth_factor import GrowthFactorEstimator

EstimatorFactory = Callable[[], AgeEstimator]

ESTIMATORS: dict[str, EstimatorFactory] = {
    "bai_reference": BaiReferenceEstimator,
    "growth_factor": GrowthFactorEstimator,
}


def get_estimator(name: str) -> AgeEstimator:
    try:
        return ESTIMATORS[name]()
    except KeyError as exc:
        valid = ", ".join(sorted(ESTIMATORS))
        raise ModelError(f"Unknown estimator {name!r}. Available estimators: {valid}.") from exc
