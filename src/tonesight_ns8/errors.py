"""Project exceptions for ToneSight NS8 package modules."""

from __future__ import annotations


class InvalidInput(ValueError):
    """Raised when strict input validation fails."""


class UnknownFamily(ValueError):
    """Raised when family identifier is unknown."""


class InvalidTaxonomy(ValueError):
    """Raised when taxonomy structure or values are invalid."""


class UnknownToneLabel(KeyError):
    """Raised when a requested tone label is not in taxonomy."""

