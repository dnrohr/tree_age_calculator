"""Tree age estimation with explicit uncertainty."""

from .estimators import AgeEstimator, BaiReferenceEstimator, EnsembleEstimator, FiaAgeSizeEstimator, GrowthFactorEstimator, get_estimator
from .measurements import TreeMeasurement
from .result import AgeEstimate, SiteContext

__all__ = [
    "AgeEstimate",
    "AgeEstimator",
    "BaiReferenceEstimator",
    "GrowthFactorEstimator",
    "FiaAgeSizeEstimator",
    "EnsembleEstimator",
    "SiteContext",
    "TreeMeasurement",
    "get_estimator",
]
__version__ = "1.0.0"
