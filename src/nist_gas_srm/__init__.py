"""
Top level API (:mod:`nist_gas_srm`)
======================================================
"""

from importlib.metadata import PackageNotFoundError, version as _version

from . import basemodels, excel

try:  # ruff:ignore[non-empty-init-module]
    __version__ = _version("nist-gas-srm")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "999"


__author__ = """William P. Krekelberg"""

__all__ = [
    "basemodels",
    "excel",
]
