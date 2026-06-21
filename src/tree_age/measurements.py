from dataclasses import dataclass
import math


@dataclass(frozen=True)
class TreeMeasurement:
    circumference_cm: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.circumference_cm) or self.circumference_cm <= 0:
            raise ValueError("Circumference must be a positive, finite number.")

    @property
    def dbh_cm(self) -> float:
        return self.circumference_cm / math.pi

    @property
    def dbh_inches(self) -> float:
        return self.dbh_cm / 2.54

    @property
    def radius_cm(self) -> float:
        return self.circumference_cm / (2 * math.pi)

    @property
    def basal_area_cm2(self) -> float:
        return math.pi * self.radius_cm**2

