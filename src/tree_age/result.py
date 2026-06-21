from dataclasses import asdict, dataclass, field
import json
from typing import Literal

TreeContext = Literal["forest", "yard", "street", "unknown"]


@dataclass(frozen=True)
class SiteContext:
    state: str | None = None
    context: TreeContext = "unknown"
    elevation_m: float | None = None


@dataclass(frozen=True)
class AgeEstimate:
    species: str
    dbh_cm: float
    estimator_name: str
    estimated_age_years: int
    lower_age_years: int
    upper_age_years: int
    confidence_label: str
    warnings: tuple[str, ...] = field(default_factory=tuple)
    assumptions: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["warnings"] = list(self.warnings)
        return value

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

