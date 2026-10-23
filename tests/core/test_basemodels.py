from typing import Any

import pytest

from nist_gas_srm.core import basemodels


@pytest.mark.parametrize(
    ("string", "expected"),
    [
        ("123", {"srm_number": 123}),
        ("123a", {"srm_number": 123, "batch": "a"}),
        ("123-b", {"srm_number": 123, "lot": "b"}),
        ("123a-b", {"srm_number": 123, "batch": "a", "lot": "b"}),
        ('{"srm_number": 123}', {"srm_number": 123}),
        ('{"srm_number": 123, "batch": "a"}', {"srm_number": 123, "batch": "a"}),
        ('{"srm_number": 123, "lot": "b"}', {"srm_number": 123, "lot": "b"}),
        (
            '{"srm_number": 123, "batch": "a", "lot": "b"}',
            {"srm_number": 123, "batch": "a", "lot": "b"},
        ),
    ],
)
def test_srmdataquery_from_string(string: str, expected: dict[str, Any]) -> None:

    assert (
        basemodels.srm.SRMQuery.from_srm_query(string).model_dump(exclude_unset=True)
        == expected
    )
