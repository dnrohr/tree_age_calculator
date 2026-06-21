from dataclasses import dataclass
import re

from .errors import UnknownSpeciesError


@dataclass(frozen=True)
class Species:
    canonical_name: str
    scientific_name: str
    fia_code: int
    aliases: tuple[str, ...] = ()


SPECIES = (
    Species("White pine", "Pinus strobus", 129, ("eastern white pine",)),
    Species("Hemlock", "Tsuga canadensis", 261, ("eastern hemlock",)),
    Species("Yellow birch", "Betula alleghaniensis", 371),
    Species("Red spruce", "Picea rubens", 97),
    Species("Red oak", "Quercus rubra", 833, ("northern red oak",)),
    Species("Sugar maple", "Acer saccharum", 318),
    Species("Balsam fir", "Abies balsamea", 12),
    Species("White ash", "Fraxinus americana", 541),
    Species("American beech", "Fagus grandifolia", 531),
    Species("Red maple", "Acer rubrum", 316),
)


def _key(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().casefold())


_LOOKUP = {
    _key(name): species
    for species in SPECIES
    for name in (species.canonical_name, species.scientific_name, *species.aliases)
}


def resolve_species(value: str) -> Species:
    ambiguous = {
        "oak": "Oak is ambiguous; specify northern red oak or another species.",
        "maple": "Maple is ambiguous; specify red maple, sugar maple, or another species.",
        "pine": "Pine is ambiguous; specify eastern white pine or another species.",
    }
    if _key(value) in ambiguous:
        raise UnknownSpeciesError(ambiguous[_key(value)])
    try:
        return _LOOKUP[_key(value)]
    except KeyError as exc:
        from difflib import get_close_matches

        valid_names = [species.canonical_name for species in SPECIES]
        valid = ", ".join(valid_names)
        matches = get_close_matches(value, valid_names, n=3, cutoff=0.55)
        suggestion = f" Did you mean {', '.join(matches)}?" if matches else ""
        raise UnknownSpeciesError(
            f"Unknown species {value!r}.{suggestion} Supported species: {valid}."
        ) from exc
