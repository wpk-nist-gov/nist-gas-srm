"""Validation routines."""

from __future__ import annotations

from math import isnan
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


def validate_nan_to_none(x: Any) -> Any:
    """Convert possible nan value to None"""
    if x is None or isinstance(x, str):
        return x

    try:
        if isnan(x):
            return None
    except TypeError:
        pass
    return x


def validate_str_to_lower(x: str) -> str:
    return x.lower()


def validate_optional_str_to_lower(x: str | None) -> str | None:
    if x is None:
        return x
    return x.lower()
