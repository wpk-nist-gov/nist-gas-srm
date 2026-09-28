"""Perform 'standard' analysis."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

import numpy as np
import odrpack
import pandas as pd

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

    from numpy.typing import ArrayLike, NDArray
    from odrpack.result import OdrResult

    NDArrayFloat64 = NDArray[np.float64]
    NDArrayAny = NDArray[Any]
    NDArray1DFloat64 = np.ndarray[tuple[int], np.dtype[np.float64]]

FIT_NAME_DEGREE_MAPPING: dict[str, int] = {
    "GENLINE - Linear (y=b0+b1*x)": 1,
    "GENLINE - Quadratic (y=b0+b1*x+b2*x2)": 2,
    "GENLINE - Cubic (y=b0+b1*x+b2*x2+b3*x3)": 3,
}


def _collapse_columns(average_standards: pd.DataFrame) -> pd.DataFrame:
    out = average_standards.copy()
    out.columns = [
        column[0] if column[-1] == "mean" else "_".join(column)
        for column in average_standards.columns
    ]
    return out


def stderr(x: Any, max_n: int | None = None, ddof: int = 1) -> Any:
    # print("norm", np.sqrt
    cnt = np.count_nonzero(x)

    if max_n is not None:
        cnt = min(cnt, np.int64(max_n))

    return np.std(x, ddof=ddof) / np.sqrt(cnt)


def get_average_frame(
    df: pd.DataFrame,
    group_cols: Sequence[str],
    collapse: bool = True,
    max_n: int | None = None,
    ddof: int = 1,
) -> pd.DataFrame:
    if not isinstance(group_cols, str):
        group_cols = list(group_cols)
    out = df.groupby(group_cols).agg([
        "mean",
        "std",
        partial(stderr, max_n=max_n, ddof=ddof),
    ])
    if collapse:
        return out.pipe(_collapse_columns)
    return out


def get_average_standards_frame(
    df: pd.DataFrame,
    group_cols: Sequence[str] = ("StandardNo", "StandardID"),
    psm_uncert: float | None = None,
    concentration_name: str = "SConc",
    max_n: int | None = None,
    ddof: int = 1,
) -> pd.DataFrame:
    out = get_average_frame(df, group_cols, max_n=max_n, ddof=ddof)

    if psm_uncert is not None:
        key = f"{concentration_name}_stderr"
        out[key] = out[concentration_name] * psm_uncert
    return out


def get_average_additional_lot_standards_frame(
    df: pd.DataFrame,
    ratio_name: str = "Ratio",
    lot_number_name: str = "LS#",
    assumed_ratio_value: float = 1.0,
    assumed_ratio_stderr: float = 0.0,
    max_n: int | None = None,
    ddof: int = 1,
) -> pd.DataFrame:

    ratio_stderr_name = f"{ratio_name}_stderr"

    out = get_average_frame(
        df[[lot_number_name, ratio_name]],
        group_cols=lot_number_name,
        max_n=max_n,
        ddof=ddof,
    ).reset_index()[[lot_number_name, ratio_name, ratio_stderr_name]]

    ref = pd.DataFrame([
        {
            lot_number_name: 1,
            ratio_name: assumed_ratio_value,
            ratio_stderr_name: assumed_ratio_stderr,
        }
    ])
    return pd.concat((ref, out), ignore_index=True)


def eval_polynomial_error(
    x: ArrayLike, ux: ArrayLike, beta: ArrayLike, cov_beta: ArrayLike
) -> tuple[NDArrayFloat64, NDArrayFloat64]:
    """
    evaluate polynmial and error for polynmial of form

    y = beta[0] + beta[1] * x ** 1 + ...
    """

    from uncertainties import correlated_values, unumpy  # pyright: ignore[reportMissingTypeStubs, reportUnknownVariableType]

    x, ux, beta, cov_beta = (
        np.asarray(_, dtype=np.float64) for _ in (x, ux, beta, cov_beta)
    )

    beta_uncert: Any = correlated_values(beta, cov_beta)
    x_uncert: Any = unumpy.uarray(x, ux)  # pyright: ignore[reportUnknownMemberType]

    y = _polynomial_func(x_uncert, beta_uncert)

    return unumpy.nominal_values(y), unumpy.std_devs(y)  # pyright: ignore[reportUnknownMemberType]


def _polynomial_func(
    x: NDArrayFloat64, beta: Sequence[Any] | NDArray1DFloat64
) -> NDArrayFloat64:
    """"""
    result: NDArrayFloat64 = np.zeros_like(x)
    for coefficient in reversed(beta):
        result = result * x + coefficient
    return result


def fit_standards_data(
    average_standards: pd.DataFrame,
    ratio_name: str = "SRatio",
    concentration_name: str = "SConc",
    beta0: Sequence[float] | None = None,
    degree: int = 1,
    **kwargs: Any,
) -> OdrResult:

    kwargs.setdefault("ndigit", 8)
    kwargs.setdefault("maxit", 100)

    p_x = average_standards[ratio_name].to_numpy()
    p_sx = average_standards[f"{ratio_name}_stderr"].to_numpy()
    p_y = average_standards[concentration_name].to_numpy()
    p_sy = average_standards[f"{concentration_name}_stderr"]

    if beta0 is None:
        beta0 = [1.0] * (degree + 1)

    return odrpack.odr_fit(
        _polynomial_func,
        p_x,
        p_y,
        beta0=np.array(beta0),
        weight_x=p_sx**-2,
        weight_y=p_sy**-2,
        **kwargs,
    )


def fit_to_params(
    fit: OdrResult,
) -> pd.DataFrame:

    n = len(fit.beta)
    beta_stderr = np.sqrt(np.diag(fit.cov_beta))

    params = [
        {"name": f"b{i}", "value": value, "stderr": stderr}
        for i, (value, stderr) in enumerate(zip(fit.beta, beta_stderr, strict=True))
    ]

    from itertools import combinations

    params.extend([
        {"name": f"cov(b{i}, b{j})", "stderr": fit.cov_beta[i, j]}
        for i, j in combinations(range(n), 2)
    ])

    params.append({"name": "rms residual error", "stderr": np.sqrt(fit.res_var)})

    return pd.DataFrame(params)


def solution_table(
    average_standards: pd.DataFrame,
    fit: OdrResult,
    ratio_name: str = "SRatio",
    concentration_name: str = "SConc",
) -> pd.DataFrame:

    out = (
        average_standards[[ratio_name, concentration_name]]
        .rename(
            columns={
                ratio_name: "X",
                concentration_name: "Y",
            }
        )
        .reset_index(drop=True)
    )

    out["X-solution"] = fit.xplusd
    out["Y-solution"] = fit.yest

    x_stderr = average_standards[f"{ratio_name}_stderr"].to_numpy()
    y_stderr = average_standards[f"{concentration_name}_stderr"].to_numpy()

    pass_test = (np.abs(fit.delta) < 2 * x_stderr) & (np.abs(fit.eps) < 2 * y_stderr)

    out["uTest"] = np.where(pass_test, "PASS", "FAIL")

    return out


def eval_table(
    average_additional_lot_standards: pd.DataFrame,
    beta: NDArrayFloat64,
    cov_beta: NDArrayFloat64,
    ratio_name: str = "Ratio",
) -> pd.DataFrame:

    y, yerr = eval_polynomial_error(
        average_additional_lot_standards[ratio_name].to_numpy(),
        average_additional_lot_standards[f"{ratio_name}_stderr"].to_numpy(),
        beta=beta,
        cov_beta=cov_beta,
    )

    return average_additional_lot_standards.assign(
        Yeval=y,
        uYeval=yerr,
    )
