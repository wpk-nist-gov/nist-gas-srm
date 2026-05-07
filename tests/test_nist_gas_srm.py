"""Tests for `nist-gas-srm` package."""

from __future__ import annotations

import re

import pytest

from nist_gas_srm import example_function


def test_version() -> None:
    from nist_gas_srm import __version__

    assert isinstance(__version__, str)
    assert re.match(r"^\d+\.\d+\.\d+.*$", __version__) is not None


@pytest.fixture
def response() -> tuple[int, int]:
    return 1, 2


def test_example_function(response: tuple[int, int]) -> None:
    expected = 3
    assert example_function(*response) == expected
