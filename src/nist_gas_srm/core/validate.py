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

    try:  # pylint: disable=too-many-try-statements
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
    return validate_str_to_lower(x)


def validate_timestamp(x: str | None) -> str:
    if x is None:
        from datetime import UTC, datetime

        return str(datetime.now(UTC))

    return x


def validate_test_out(x: Any) -> Any:  # ruff: ignore[too-many-return-statements]
    if x is None:
        return False

    if isinstance(x, str):
        if x.lower() == "out":
            return True
        if x.lower() == "in":
            return False
        return x

    if isinstance(x, bool):
        return x

    try:  # pylint: disable=too-many-try-statements)
        if isnan(x):
            return False
    except TypeError:
        pass

    return x
