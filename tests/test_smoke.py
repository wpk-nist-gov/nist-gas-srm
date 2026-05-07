"""Smoke test for package"""

from nist_gas_srm import __version__


def _main() -> int:
    assert isinstance(__version__, str)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
