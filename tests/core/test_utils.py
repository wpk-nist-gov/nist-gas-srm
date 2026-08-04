from __future__ import annotations

import pytest

from nist_gas_srm.core import utils as mod


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
