"""
Top level API (:mod:`nist_gas_srm`)
======================================================
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

try:  # noqa: RUF067
    __version__ = _version("nist-gas-srm")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "999"


__author__ = """William P. Krekelberg"""
