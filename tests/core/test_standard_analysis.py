from __future__ import annotations

from typing import TYPE_CHECKING, cast

import numpy as np
import pytest

from nist_gas_srm.core import standard_analysis

if TYPE_CHECKING:
    from numpy.typing import ArrayLike

    from nist_gas_srm.core.standard_analysis import NDArray1DFloat64, NDArrayFloat64

rng = np.random.default_rng()


@pytest.fixture(params=[(), (1, 2, 3)])
def shape(request: pytest.FixtureRequest) -> tuple[int, ...]:
    return cast("tuple[int, ...]", request.param)


@pytest.fixture(params=range(1, 4))
def degree(request: pytest.FixtureRequest) -> int:
    return cast("int", request.param)


@pytest.fixture
def x(shape: tuple[int, ...]) -> NDArrayFloat64:
    return rng.random(shape)


@pytest.fixture
def ux(shape: tuple[int, ...]) -> NDArrayFloat64:
    return rng.random(shape)


@pytest.fixture
def beta(degree: int) -> NDArray1DFloat64:
    return rng.random(degree + 1)


@pytest.fixture
def cov_beta(degree: int) -> NDArrayFloat64:
    v = rng.random((degree + 1, degree + 1))
    return v @ v.T


def test__polynomial_func(beta: NDArray1DFloat64, x: NDArrayFloat64) -> None:
    np.testing.assert_allclose(
        np.polynomial.Polynomial(beta)(x),
        standard_analysis._polynomial_func(x, beta),
    )


def eval_x(
    y: ArrayLike,
    uy: ArrayLike,
    beta: NDArrayFloat64,
    cov_beta: NDArrayFloat64,
    degree: int | None = None,
) -> tuple[NDArrayFloat64, NDArrayFloat64]:
    """
    evaluate X from polynomaial of form

    For testing purposes only.  This is a copy of excel vba code.

    x = a[0] * y ** degree + a[1] * y**(degree -1) + ... + a[k] * y ** (degree -k ) + ... + a[degree]
    """
    y = np.asarray(y, dtype=np.float64)
    uy = np.asarray(uy, dtype=np.float64)

    a = np.flip(beta)
    siga = np.flip(cov_beta)

    a = np.asarray(a, dtype=np.float64)
    siga = np.asarray(siga, dtype=np.float64)

    if degree is None:
        degree = len(a) - 1

    match degree:
        case 1:
            x = y * a[0] + a[1]
            ux = np.sqrt(
                (a[0] * uy) ** 2 + siga[1, 1] + (y**2 * siga[0, 0]) + 2 * y * siga[1, 0]
            )

        case 2:
            x = a[0] * y * y + a[1] * y + a[2]
            t = (
                (a[1] + 2 * a[0] * y) ** 2 * uy**2
                + siga[2, 2]
                + (siga[1, 1] * y**2)
                + (siga[0, 0] * y**4)
                + (2 * y * siga[2, 1])
                + (2 * siga[2, 0] * y**2)
                + (2 * siga[1, 0] * y**3)
            )
            ux = np.sqrt(t)
        case 3:
            x = a[0] * y**3 + a[1] * y**2 + a[2] * y + a[3]
            t = (
                ((a[2] + 2 * y * a[1] + 3 * y**2 * a[0]) * uy) ** 2
                + siga[3, 3]
                + (siga[2, 2] * y**2)
                + (siga[1, 1] * y**4)
                + (siga[0, 0] * y**6)
                + 2 * y * siga[3, 2]
                + 2 * y**2 * siga[3, 1]
                + 2 * y**3 * siga[3, 0]
                + 2 * y**3 * siga[2, 1]
                + 2 * y**4 * siga[2, 0]
                + 2 * y**5 * siga[1, 0]
            )
            ux = np.sqrt(t)

        case _:
            msg = f"Degree {degree} not supported"
            raise NotImplementedError(msg)

    return x, ux


def test_eval_polynomail_error(
    x: NDArrayFloat64,
    ux: NDArrayFloat64,
    beta: NDArrayFloat64,
    cov_beta: NDArrayFloat64,
) -> None:
    y, uy = standard_analysis.eval_polynomial_error(
        x,
        ux,
        beta,
        cov_beta,
    )
    yy, uyy = eval_x(x, ux, beta, cov_beta)

    np.testing.assert_allclose(y, yy)
    np.testing.assert_allclose(uy, uyy)
