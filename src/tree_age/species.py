from dataclasses import dataclass
import re

from .errors import UnknownSpeciesError


@dataclass(frozen=True)
class Species:
    canonical_name: str
    scientific_name: str
    aliases: tuple[str, ...] = ()


SPECIES = (
    Species("White pine", "Pinus strobus", ("eastern white pine",)),
    Species("Hemlock", "Tsuga canadensis", ("eastern hemlock",)),
    Species("Yellow birch", "Betula alleghaniensis"),
    Species("Red spruce", "Picea rubens"),
    Species("Red oak", "Quercus rubra", ("northern red oak",)),
    Species("Sugar maple", "Acer saccharum"),
    Species("Balsam fir", "Abies balsamea"),
    Species("White ash", "Fraxinus americana"),
    Species("American beech", "Fagus grandifolia"),
    Species("Red maple", "Acer rubrum"),
)


def _key(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().casefold())


_LOOKUP = {
    _key(name): species
    for species in SPECIES
    for name in (species.canonical_name, species.scientific_name, *species.aliases)
}


def resolve_species(value: str) -> Species:
    try:
        return _LOOKUP[_key(value)]
    except KeyError as exc:
        valid = ", ".join(species.canonical_name for species in SPECIES)
        raise UnknownSpeciesError(
            f"Unknown species {value!r}. Supported species: {valid}."
        ) from exc

