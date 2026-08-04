"""Utilities."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

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
