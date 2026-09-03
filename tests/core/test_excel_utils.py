from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import pytest

from nist_gas_srm.core import excel_utils as mod

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        (
            "SRM2627a_SeriesI_CAG+CEC_CEC-RV6.4.xls",
            {
                "srm_id": "2627",
                "batch_id": "a",
                "lot_id": "I",
            },
        ),
        (
            "SRM2627_SeriesI_CAG+CEC_CEC-RV6.4.xls",
            {
                "srm_id": "2627",
                "batch_id": None,
                "lot_id": "I",
            },
        ),
    ],
)
def test_parse_excel_filename_to_metadata(name: str, expected: dict[str, str]) -> None:
    assert mod.parse_excel_filename_to_metadata(name) == expected


@pytest.mark.parametrize(
    ("rows", "params", "expected"),
    [
        ([0, 1, 2], {"lower": 1}, [True, False, False]),
        (
            range(3),
            {"upper": 1},
            [False, False, True],
        ),
        (range(3), {"include": [0, 2]}, [False, True, False]),
        (range(3), {"include": [0, 2], "upper": 1}, [False, True, True]),
    ],
)
def test_skipper(rows: list[int], params: dict[str, Any], expected: list[bool]) -> None:
    func = mod.skipper(**params)
    assert [func(x) for x in rows] == expected


@pytest.mark.parametrize(
    "df",
    [None, pd.DataFrame({"a": [1, 2, 3], "b": [1, np.nan, 3]})],
)
def test_maybe_dropna(df: pd.DataFrame | None) -> None:

    out = mod.maybe_dropna(df, how="any")

    if df is None:
        assert out is None

    else:
        assert out is not None
        pd.testing.assert_frame_equal(out, df.dropna(how="any"))


EXCEL_PATH_MARK = pytest.mark.parametrize(
    "example_excelfile_path", ["example_data.xls", "example_data.xlsx"], indirect=True
)


@EXCEL_PATH_MARK
def test_get_frame(
    example_excelfile_path: Path, example_excelfile: pd.ExcelFile
) -> None:
    a = mod.get_frame(example_excelfile, sheet_name="Ratio Data", usecols="A:I")
    b = pd.read_excel(  # pyright: ignore[reportUnknownMemberType]
        example_excelfile_path, sheet_name="Ratio Data", usecols="A:I"
    ).dropna(how="all")
    pd.testing.assert_frame_equal(a, b)


# ruff:file-ignore[commented-out-code]
# @EXCEL_PATH_MARK
# @pytest.mark.parametrize(
#     ("sheet_name", "rowx", "colx", "expected"),
#     [
#         ("Ratio Data", 16, "L", 472),
#     ]

# )
# def test_get_value_from_worksheet(
#         example_excelfile: pd.ExcelFile,
#         sheet_name: str,
#         rowx: int,
#         colx: str | int,
#         expected: Any,
# ) -> None:

#     assert mod.get_value_from_worksheet(example_excelfile, sheet_name=sheet_name, rowx=rowx, colx=colx) == expected
