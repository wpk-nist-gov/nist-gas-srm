from __future__ import annotations

from math import nan
from unittest.mock import patch

import numpy as np
import pytest

from nist_gas_srm.core import validate


@pytest.mark.parametrize(
    ("x", "expected"),
    [
        (None, None),
        ("hello", "hello"),
        (1.0, 1.0),
        (1, 1),
        (np.nan, None),
        (nan, None),
    ],
)
def test_validate_nan_to_none(x: object, expected: object) -> None:
    assert validate.validate_nan_to_none(x) == expected


@pytest.mark.parametrize(
    ("x", "expected"),
    [
        ("Hello", "hello"),
        ("ABC", "abc"),
        ("abc", "abc"),
        (None, None),
    ],
)
def test_validate_str_to_lower_optional(x: str, expected: str) -> None:
    assert validate.validate_optional_str_to_lower(x) == expected


@pytest.mark.parametrize(
    ("x", "expected"),
    [
        ("foo", "foo"),
        (None, "bar"),
    ],
)
def test_validate_timestamp(x: str, expected: str) -> None:
    import datetime

    with patch.object(datetime, "datetime", autospec=True) as mock:
        mock.now.return_value = "bar"
        assert validate.validate_timestamp(x) == expected


@pytest.mark.parametrize(
    ("x", "expected"),
    [
        ("OUT", True),
        ("Out", True),
        ("out", True),
        ("in", False),
        ("IN", False),
        (True, True),
        (False, False),
        (None, False),
        (nan, False),
        (np.nan, False),
    ],
)
def test_validate_test_out(x: object, expected: object) -> None:
    assert validate.validate_test_out(x) == expected
