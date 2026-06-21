class TreeAgeError(Exception):
    """Base exception for expected estimator failures."""


class UnknownSpeciesError(TreeAgeError):
    """Raised when a species name cannot be resolved."""


class ModelError(TreeAgeError):
    """Raised when an estimator cannot produce a defensible result."""

