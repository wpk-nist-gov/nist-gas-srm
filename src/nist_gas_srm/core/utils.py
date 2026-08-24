"""Utilities."""

from __future__ import annotations

import re
from collections.abc import Callable, MutableMapping
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from typing import Any

    import pandas as pd

EXCEL_FILENAME_PATTERN = re.compile(
    r"srm(?P<srm_id>\d+)(?P<batch_id>\w*)_Series(?P<lot_id>\w*)_(.*).xls",
    flags=re.IGNORECASE,
)


def parse_excel_filename_to_metadata(name: str) -> dict[str, Any]:
    """
    Parse an excel filename to parameters
    """
    if (m := EXCEL_FILENAME_PATTERN.match(name)) is None:
        msg = f"Unable to parse ids from {name}"
        raise ValueError(msg)

    out = m.groupdict().copy()
    if not out["batch_id"]:
        out["batch_id"] = None

    return out


def optional_dataframe_func_wrapper(
    func: Callable[..., pd.DataFrame],
    xls: pd.ExcelFile,
    sheet_name: str,
    **kwargs: Any,
) -> pd.DataFrame | None:

    if sheet_name in xls.sheet_names:
        df = func(
            xls,
            sheet_name,
            **kwargs,
        )
        return None if df.empty else df
    return None


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
