from typing import Any

import pytest

from nist_gas_srm.core import basemodels


@pytest.mark.parametrize(
    ("string", "expected"),
    [
        ("123", {"srm_id": 123}),
        ("123a", {"srm_id": 123, "batch_id": "a"}),
        ("123-b", {"srm_id": 123, "lot_id": "b"}),
        ("123a-b", {"srm_id": 123, "batch_id": "a", "lot_id": "b"}),
        ('{"srm_id": 123}', {"srm_id": 123}),
        ('{"srm_id": 123, "batch_id": "a"}', {"srm_id": 123, "batch_id": "a"}),
        ('{"srm_id": 123, "lot_id": "b"}', {"srm_id": 123, "lot_id": "b"}),
        (
            '{"srm_id": 123, "batch_id": "a", "lot_id": "b"}',
            {"srm_id": 123, "batch_id": "a", "lot_id": "b"},
        ),
    ],
)
def test_srmdataquery_from_string(string: str, expected: dict[str, Any]) -> None:

    assert (
        basemodels.srm.SRMQuery.from_string(string).model_dump(exclude_unset=True)
        == expected
    )
