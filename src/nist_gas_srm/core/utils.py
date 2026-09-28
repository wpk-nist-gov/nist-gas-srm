"""Utilities."""

from __future__ import annotations

import enum
import itertools
import operator
import re
from collections.abc import MutableMapping
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from collections.abc import Callable, Hashable, Iterable, Mapping
    from typing import Any, Literal, TypeAlias, TypeVar

    T = TypeVar("T")


# * Dataframe/excel utils
SRM_PATTERN = re.compile(
    r"(?P<srm_id>\d+)(?P<batch_id>\w+)?(:?-(?P<lot_id>\w*))?",
    flags=re.IGNORECASE,
)

JSON_PATTERN = re.compile(r".*\{.*\}.*", flags=re.DOTALL)


def flatten_dict(
    d: MutableMapping[str, Any], parent_key: str = "", sep: str = "."
) -> dict[str, Any]:
    """Convert nested dict to flat dict."""
    items: list[tuple[str, Any]] = []
    for k, v in d.items():
        # Combine the parent key with the current key
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        # If the value is another dictionary, recurse deeper
        if isinstance(v, MutableMapping):
            items.extend(
                flatten_dict(
                    cast("MutableMapping[str, Any]", v), new_key, sep=sep
                ).items()
            )
        else:
            items.append((new_key, v))

    return dict(items)


def unflatten_dict(flat_dict: dict[str, Any], separator: str = ".") -> dict[str, Any]:
    """Convert flat dict to nested dict"""
    expanded_dict: dict[str, Any] = {}

    for flat_key, value in flat_dict.items():
        # Split the compound key into individual keys
        keys = flat_key.split(separator)
        current_level = expanded_dict

        # Traverse and build the inner dictionaries
        for key in keys[:-1]:
            if key not in current_level:
                current_level[key] = {}
            current_level = current_level[key]

        # Assign the value to the deepest key
        current_level[keys[-1]] = value

    return expanded_dict


class _Missing(enum.Enum):
    """
    Sentinel to indicate the lack of a value when ``None`` is ambiguous.

    If extending attrs, you can use ``typing.Literal[MISSING]`` to show
    that a value may be ``MISSING``.

    .. versionchanged:: 21.1.0 ``bool(MISSING)`` is now False.
    .. versionchanged:: 22.2.0 ``MISSING`` is now an ``enum.Enum`` variant.
    """

    MISSING = enum.auto()

    def __repr__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        return "MISSING"  # pragma: no cover

    def __bool__(self) -> bool:
        return False  # pragma: no cover


MISSING = _Missing.MISSING
"""
Sentinel to indicate the lack of a value when ``None`` is ambiguous.
"""

MISSING_TYPE: TypeAlias = "Literal[_Missing.MISSING]"


def get_in(
    keys: str | Iterable[Hashable],
    nested_dict: Mapping[Any, T],
    split: str | None = ".",
    default: T | MISSING_TYPE = MISSING,
    factory: Callable[[], T] | None = None,
) -> T:
    """
    >>> foo = {"a": {"b": {"c": 1}}}
    >>> get_in(["a", "b"], foo)
    {'c': 1}

    """
    from functools import reduce

    if isinstance(keys, str):
        keys = [keys]

    if split is not None:
        keys = itertools.chain.from_iterable(
            cast(
                "Iterable[Hashable]", key.split(split) if isinstance(key, str) else key
            )
            for key in keys
        )

    try:
        return cast(
            "T",
            reduce(
                cast("Callable[..., Any]", operator.getitem),
                keys,
                nested_dict,
            ),
        )
    except (KeyError, IndexError, TypeError):
        if factory is not None:
            return factory()
        if default is not MISSING:
            return default

    msg = f"Keys {keys} not found and not default or factory"
    raise ValueError(msg)
