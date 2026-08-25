"""
Read excel files (:mod:`~nist_gas_srm.read_excel`)
==================================================
"""

from __future__ import annotations

from datetime import UTC, datetime
from functools import cached_property
from typing import TYPE_CHECKING, ClassVar, cast

import pandas as pd

if TYPE_CHECKING:
    from collections.abc import Hashable, Iterator
    from io import BytesIO
    from pathlib import Path
    from typing import Any, TypeVar

    from pydantic import BaseModel

    _Model = TypeVar("_Model", bound=BaseModel)


from .utils import (
    as_excelfile,
    get_frame,
    get_frame_with_len_check,
    get_value_from_worksheet,
    maybe_dropna,
    skipper,
    strip_trailing_numbers as func_strip_trailing_numbers,
    validate_no_null,
)


class _Sheet:
    ratio: str = "Ratio Data"
    vendor: str = "Vendor Data"
    standards: str = "Standards Data"
    lot_standards: str = "Past LS"
    ratio_analysis: str = "Ratio Analysis"
    rcert: str = "RCertification"


class _SRMExcelFileBase:
    sheet: ClassVar[type[_Sheet]] = _Sheet

    def __init__(self, path_or_excelfile: Path | BytesIO | pd.ExcelFile) -> None:
        with as_excelfile(path_or_excelfile) as excelfile:
            self.excelfile = excelfile

    # *  Ratio Analysis
    def _get_optional_frame(
        self, sheet_name: str, usecols: str, **kwargs: Any
    ) -> pd.DataFrame | None:
        if sheet_name in self.excelfile.sheet_names:
            df = get_frame(
                self.excelfile,
                sheet_name,
                usecols=usecols,
                **kwargs,
            )
            return None if df.empty else df.rename(columns=func_strip_trailing_numbers)
        return None


class _RCertification(_SRMExcelFileBase):
    def analysis_date(self) -> datetime | None:
        if value := get_value_from_worksheet(
            self.excelfile, self.sheet.rcert, rowx=43, colx="B"
        ):
            return datetime.strptime(value, "%B %d %Y").astimezone(UTC)
        return None

    def srm_values_excel(self) -> pd.DataFrame | None:
        # relative_uncertainty <- confidence_level / value
        # effective k <- confidence_level / uncertainty
        return self._get_optional_frame(
            self.sheet.rcert,
            usecols="A:B",
            header=None,
            skiprows=skipper(include={47, 48, 49, 52, 53, 54, 55}),
            names=["name", "value"],
        )

    def srm_values(self) -> pd.DataFrame | None:
        # NOTE: to convert back to stacked data
        # use pd.melt(out, var_name="name", value_name="value")
        if (df := self.srm_values_excel()) is None:
            return df
        new = cast(
            "pd.DataFrame",
            pd.pivot(df.assign(dummy=0).set_index("dummy"), columns="name")["value"],
        )
        return new.rename_axis(columns=None, index=None)

    def standards_values(self) -> pd.DataFrame | None:
        out = self._get_optional_frame(
            self.sheet.rcert,
            usecols="A:E",
            skiprows=skipper(lower=58, upper=68),
        )

        if out is not None:
            columns = list(out.columns)
            columns[-1] = "Predicted " + columns[-1]
            out.columns = columns

            out = maybe_dropna(out, how="all", subset=out.columns[1:])

        return out

    def additional_lot_standards(self) -> pd.DataFrame | None:
        return self._get_optional_frame(
            self.sheet.rcert, usecols="A:E", skiprows=skipper(lower=71, upper=75)
        )

    def cylinder_results(self) -> pd.DataFrame | None:
        return self._get_optional_frame(
            self.sheet.rcert,
            usecols="M:P",
            skiprows=46,
        )

    def analysis_function_coefficients(self) -> pd.DataFrame | None:
        out = maybe_dropna(
            self._get_optional_frame(
                self.sheet.rcert,
                usecols="G:H",
                skiprows=skipper(lower=46, upper=50),
                names=["value", "uncert"],
            ),
            how="all",
        )
        if out is not None:
            out = out.assign(order=range(len(out)))
        return out

    def correlation_coefficients(self) -> pd.DataFrame | None:
        out = self._get_optional_frame(
            self.sheet.rcert,
            usecols="G:J",
            skiprows=skipper(lower=52, upper=56),
        )
        out = maybe_dropna(out, how="all")

        if out is not None:
            out = out.assign(order=range(len(out)))

        return maybe_dropna(out, how="all", axis=1)

    def correlation_coefficients_flat(self) -> pd.DataFrame | None:

        if (df := self.correlation_coefficients()) is None:
            return df

        return pd.melt(
            df.rename(columns=lambda x: x if x == "order" else int(x[1:])),
            id_vars="order",
            var_name="order_other",
        )

    @staticmethod
    def stack_flat_correlation_coefficients(df: pd.DataFrame) -> pd.DataFrame:
        return (
            pd
            .pivot(df, columns="order_other", index="order", values="value")
            .rename_axis(columns=None)
            .reset_index()
        )

    def outliers(self) -> pd.DataFrame | None:
        return self._get_optional_frame(
            self.sheet.rcert,
            usecols="A:D",
            skiprows=78,
        )

    def params(self) -> pd.Series | None:
        out = self._get_optional_frame(
            self.sheet.ratio,
            usecols="J:K",
            skiprows=skipper(lower=24, upper=25),
            header=None,
            names=["parameter", "value"],
        )

        if out is not None:
            return out.assign(
                parameter=lambda x: x.parameter.str.replace(r"\s*=\s*", "", regex=True)
            ).set_index("parameter")["value"]
        return out


class SRMExcelFile(_SRMExcelFileBase):
    """Interface to SRM excel file"""

    @cached_property
    def rcert(self) -> _RCertification:
        return _RCertification(self.excelfile)

    def ratio_data(self, **kwargs: Any) -> pd.DataFrame:
        df = get_frame_with_len_check(
            self.excelfile, self.sheet.ratio, usecols="A:I", rowx=16, colx="L", **kwargs
        )
        _ = validate_no_null(df.drop(columns="Test"))
        return df

    def vendor_data(self, **kwargs: Any) -> pd.DataFrame:
        return get_frame(
            self.excelfile, sheet_name=self.sheet.vendor, usecols="A:D", **kwargs
        )

    def standards_data(self, **kwargs: Any) -> pd.DataFrame:
        df = get_frame_with_len_check(
            self.excelfile,
            self.sheet.standards,
            usecols="A:E",
            rowx=1,
            colx="H",
            **kwargs,
        )
        return validate_no_null(df)

    def past_lot_standards(self, **kwargs: Any) -> pd.DataFrame:
        return get_frame(
            self.excelfile,
            self.sheet.lot_standards,
            usecols="A:F",
            skiprows=1,
            **kwargs,
        ).rename(columns=func_strip_trailing_numbers)

    def additional_lot_standards(self, **kwargs: Any) -> pd.DataFrame:
        return get_frame(
            self.excelfile,
            self.sheet.lot_standards,
            usecols="H:J",
            skiprows=1,
            **kwargs,
        ).rename(columns=func_strip_trailing_numbers)

    def ratio_analysis_random_effects(self, **kwargs: Any) -> pd.DataFrame | None:
        return self._get_optional_frame(
            self.sheet.ratio_analysis, usecols="X:Y,AA,AC", skiprows=1, **kwargs
        )

    def ratio_analysis_fixed_effects_intercept(
        self, **kwargs: Any
    ) -> pd.DataFrame | None:
        return self._get_optional_frame(
            self.sheet.ratio_analysis, usecols="AD:AF", skiprows=1, **kwargs
        )


def frame_to_list_of_dicts(df: pd.DataFrame | None) -> list[dict[Hashable, Any]]:

    return [] if df is None else df.to_dict(orient="records")


def frame_to_list_of_models(
    df: pd.DataFrame | None, cls: type[_Model]
) -> Iterator[_Model]:
    """Convert dataframe to iterator of models"""
    return (
        cls.model_validate(data)
        for data in ([] if df is None else df.to_dict(orient="records"))
    )


def list_of_models_to_frame(models: list[BaseModel]) -> pd.DataFrame:
    """Convert list of models to dataframe"""
    return pd.DataFrame(m.model_dump() for m in models)
