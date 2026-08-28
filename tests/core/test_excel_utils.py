from __future__ import annotations

import pandas as pd
import pytest

from nist_gas_srm.core import excel_utils as mod


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
    "example_excelfile", ["example_data.xls", "example_data.xlsx"], indirect=True
)
def test_get_frame(example_excelfile: pd.ExcelFile) -> None:
    a = mod.get_frame(example_excelfile, sheet_name="Ratio Data", usecols="A:I")
    b = pd.read_excel(example_excelfile, sheet_name="Ratio Data", usecols="A:I").dropna(  # pyright: ignore[reportUnknownMemberType]
        how="all"
    )
    pd.testing.assert_frame_equal(a, b)
