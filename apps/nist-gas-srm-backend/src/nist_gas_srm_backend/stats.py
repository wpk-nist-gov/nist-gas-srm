from __future__ import annotations

from math import sqrt

import pandas as pd


def get_standards_data_stats_table(
    df: pd.DataFrame, count_max: int = 1, psm_uncert: float | None = 0.002
) -> pd.DataFrame:
    """
    Calculate common stats for standards data

    Parameters
    ----------
    df : pd.DataFrame
        Standards data.
    count_max : int
        Max count used in uncertainty analysis.

    """

    def _calc_stderr(g: pd.Series) -> float:
        return g.std() / sqrt(min(count_max, g.count()))

    grouped = df.groupby("name")

    g = grouped.ratio

    header = grouped[["number", "concentration"]].first()

    calculated = g.agg(ratio_ave="mean", ratio_stderr=_calc_stderr)

    if psm_uncert is not None:
        header["concentration_uncert"] = header["concentration"] * psm_uncert
    else:
        calculated["concentration_uncert"] = grouped["unc"].first()

    return header.merge(calculated, left_index=True, right_index=True).sort_values(
        "number"
    )


def get_ratio_data_stats_table(
    df: pd.DataFrame, factor: str | None, col: str = "ratio"
) -> pd.DataFrame:
    """Calculate stats for ratio data"""
    g = df[[col]] if factor is None else df.groupby(factor)[col]
    return pd.DataFrame({
        "ave": g.mean(),
        "std": g.std(),
        "sem": g.sem(),
        "count": g.count(),
    })
