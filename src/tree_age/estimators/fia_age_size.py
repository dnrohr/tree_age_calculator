from importlib.resources import files
import json
import math
from pathlib import Path

from ..errors import ModelError
from ..measurements import TreeMeasurement
from ..result import AgeEstimate, SiteContext
from ..species import resolve_species
from .base import AgeEstimator


class FiaAgeSizeEstimator(AgeEstimator):
    name = "fia_age_size_v1"

    def __init__(self, model_path: Path | None = None) -> None:
        if model_path is None:
            resource = files("tree_age.data").joinpath("fia_age_size_v1.json")
            with resource.open(encoding="utf-8") as handle:
                self.model = json.load(handle)
        else:
            self.model = json.loads(model_path.read_text(encoding="utf-8"))

    def estimate(
        self,
        species: str,
        measurement: TreeMeasurement,
        site: SiteContext | None = None,
    ) -> AgeEstimate:
        resolved = resolve_species(species)
        try:
            parameters = self.model["species_models"][resolved.canonical_name]
        except KeyError as exc:
            supported = ", ".join(sorted(self.model["species_models"]))
            raise ModelError(
                f"{self.name} does not support {resolved.canonical_name}. Supported species: {supported}."
            ) from exc
        state = site.state.upper() if site and site.state else None
        state_offset = parameters["state_offsets"].get(state, 0.0)
        point_value = math.exp(
            parameters["intercept"]
            + parameters["log_dbh_slope"] * math.log(measurement.dbh_cm)
            + state_offset
        )
        point = max(1, round(point_value))
        lower = max(1, round(point * 0.6))
        upper = max(lower + 1, round(point * 1.6))
        warnings = [
            "This baseline is trained on selected FIA site trees, not a random sample of all trees.",
            "Its current interval is conservative and heuristic, not yet coverage-calibrated.",
        ]
        trained_states = self.model["metadata"]["states"]
        if state and state not in trained_states:
            warnings.append(f"State {state} was not represented in training; no state adjustment was applied.")
        if site and site.context in {"yard", "street"}:
            warnings.append("FIA is forest-derived; open-grown yard and street trees may be younger.")
        return AgeEstimate(
            species=resolved.canonical_name,
            dbh_cm=round(measurement.dbh_cm, 2),
            estimator_name=self.name,
            estimated_age_years=point,
            lower_age_years=lower,
            upper_age_years=upper,
            confidence_label="rough",
            warnings=tuple(warnings),
            assumptions={
                "model_version": self.model["metadata"]["model_version"],
                "training_states": trained_states,
                "state_adjustment": state if state in parameters["state_offsets"] else None,
            },
        )
