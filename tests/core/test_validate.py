from __future__ import annotations

from contextlib import nullcontext
from math import nan
from typing import TYPE_CHECKING
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from nist_gas_srm.core import validate

if TYPE_CHECKING:
    from typing import Any


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


@pytest.mark.parametrize(
    ("x", "expected"),
    [
        ([1, 1, 1, None], pytest.raises(ValueError, match="Null values found")),
        (
            [1, 2, 3],
            nullcontext([1, 2, 3]),
        ),
        (np.ones(3), nullcontext(np.ones(3))),
        (
            np.array([1.0, 2.0, np.nan]),
            pytest.raises(ValueError, match="Null values found"),
        ),
        (
            pd.DataFrame({"a": [1, 2, 3]}),
            nullcontext(pd.DataFrame({"a": [1, 2, 3]})),
        ),
        (
            pd.DataFrame({"a": [1, 2, None]}),
            pytest.raises(ValueError, match="Null values found"),
        ),
    ],
)
def test_validate_no_null(x: Any, expected: Any) -> None:
    with expected as e:
        np.testing.assert_allclose(validate.validate_no_null(x), e)
