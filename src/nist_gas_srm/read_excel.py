"""
Read excel files (:mod:`~nist_gas_srm.read_excel`)
==================================================
"""

from __future__ import annotations

import re
from contextlib import contextmanager
from datetime import UTC, datetime
from functools import cached_property, partial
from typing import TYPE_CHECKING, ClassVar, cast

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from collections.abc import Callable, Container, Generator, Iterator
    from io import BytesIO
    from pathlib import Path
    from typing import Any, TypeVar

    from pydantic import BaseModel

    T = TypeVar("T")

    _Model = TypeVar("_Model", bound=BaseModel)


_strip_trailing_numbers = partial(re.compile(r"\.[1-9]+").sub, "")


def _skipper(
    lower: int | None = None,
    upper: int | None = None,
    include: Container[int] | None = None,
) -> Callable[[int], bool]:
    def func(x: int) -> bool:
        return (
            (lower is not None and x < lower)
            or (upper is not None and x > upper)
            or (include is not None and x not in include)
        )

    return func


def _maybe_dropna(df: pd.DataFrame | None, **kwargs: Any) -> pd.DataFrame | None:
    if df is not None:
        return cast("pd.DataFrame | None", df.dropna(**kwargs))
    return df


def _get_frame(
    io: Any,
    sheet_name: str,
    **kwargs: Any,
) -> pd.DataFrame:
    return pd.read_excel(io, sheet_name=sheet_name, **kwargs).dropna(how="all")  # pyright: ignore[reportUnknownMemberType]


def _validate_no_null(x: T) -> T:
    if np.any(pd.isnull(cast("np.ndarray[Any, Any]", x))):
        msg = "Null values found"
        raise ValueError(msg)
    return x


def _get_value_from_worksheet(
    xls: pd.ExcelFile, sheet_name: str, rowx: int, colx: int | str
) -> Any:
    if isinstance(colx, str):
        colx = ord(colx.lower()) - ord("a")

    book: Any = xls.book  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
    engine = cast("str | None", getattr(xls, "engine", None))
    if engine == "xlrd":
        return book.sheet_by_name(sheet_name).cell_value(rowx=rowx, colx=colx)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

    if engine == "calamine":
        return book.get_sheet_by_name(sheet_name).to_python(skip_empty_area=False)[  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
            rowx
        ][colx]

    msg = f"Unknown engine={engine}"
    raise ValueError(msg)


@contextmanager
def _as_excelfile(
    path_or_excelfile: Path | BytesIO | pd.ExcelFile,
) -> Generator[pd.ExcelFile]:
    if isinstance(path_or_excelfile, pd.ExcelFile):
        yield path_or_excelfile
    else:
        yield pd.ExcelFile(path_or_excelfile)


def _get_frame_with_len_check(
    path_or_excelfile: Path | BytesIO | pd.ExcelFile,
    sheet_name: str,
    usecols: str,
    rowx: int,
    colx: int | str,
    require_check: bool = True,
    **kwargs: Any,
) -> pd.DataFrame:

    with _as_excelfile(path_or_excelfile) as xls:
        df = _get_frame(xls, sheet_name=sheet_name, usecols=usecols, **kwargs)

        if require_check:
            if (
                val := _get_value_from_worksheet(
                    xls, sheet_name=sheet_name, rowx=rowx, colx=colx
                )
            ) is None:
                msg = "No check value found"
                raise ValueError(msg)

            check = int(val)
            if check != len(df):
                msg = f"Wrong check shape {check=} != {len(df)}"
                raise ValueError(msg)

    return df


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
        with _as_excelfile(path_or_excelfile) as excelfile:
            self.excelfile = excelfile

    # *  Ratio Analysis
    def _get_optional_frame(
        self, sheet_name: str, usecols: str, **kwargs: Any
    ) -> pd.DataFrame | None:
        if sheet_name in self.excelfile.sheet_names:
            df = _get_frame(
                self.excelfile,
                sheet_name,
                usecols=usecols,
                **kwargs,
            )
            return None if df.empty else df.rename(columns=_strip_trailing_numbers)
        return None


class _RCertification(_SRMExcelFileBase):
    def analysis_date(self) -> datetime | None:
        if value := _get_value_from_worksheet(
            self.excelfile, self.sheet.rcert, rowx=43, colx="B"
        ):
            return datetime.strptime(value, "%B %d %Y").astimezone(UTC)
        return None

    def srm_values(self) -> pd.DataFrame | None:
        # relative_uncertainty <- confidence_level / value
        # effective k <- confidence_level / uncertainty
        return self._get_optional_frame(
            self.sheet.rcert,
            usecols="A:B",
            header=None,
            skiprows=_skipper(include={47, 48, 49, 52, 53, 54, 55}),
            names=["name", "value"],
        )

    def standards_values(self) -> pd.DataFrame | None:
        return _maybe_dropna(
            self._get_optional_frame(
                self.sheet.rcert,
                usecols="B:E",
                skiprows=_skipper(lower=58, upper=68),
            ),
            how="all",
        )

    def additional_lot_standards(self) -> pd.DataFrame | None:
        return self._get_optional_frame(
            self.sheet.rcert, usecols="A:E", skiprows=_skipper(lower=71, upper=75)
        )

    def cylinder_results(self) -> pd.DataFrame | None:
        return self._get_optional_frame(
            self.sheet.rcert,
            usecols="M:P",
            skiprows=47,
            header=None,
            names=["name", "value", "uncert", "confidence_level_95"],
        )

    def analysis_function_coefficients(self) -> pd.DataFrame | None:
        return _maybe_dropna(
            self._get_optional_frame(
                self.sheet.rcert,
                usecols="G:H",
                skiprows=_skipper(lower=46, upper=50),
            ),
            how="all",
        )

    def correlation_coefficients(self) -> pd.DataFrame | None:
        out = self._get_optional_frame(
            self.sheet.rcert,
            usecols="G:J",
            skiprows=_skipper(lower=52, upper=56),
        )
        out = _maybe_dropna(out, how="all")
        return _maybe_dropna(out, how="all", axis=1)

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
            skiprows=_skipper(lower=24, upper=25),
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
        df = _get_frame_with_len_check(
            self.excelfile, self.sheet.ratio, usecols="A:I", rowx=16, colx="L", **kwargs
        )
        _ = _validate_no_null(df.drop(columns="Test"))
        return df

    def vendor_data(self, **kwargs: Any) -> pd.DataFrame:
        return _get_frame(
            self.excelfile, sheet_name=self.sheet.vendor, usecols="A:D", **kwargs
        )

    def standards_data(self, **kwargs: Any) -> pd.DataFrame:
        df = _get_frame_with_len_check(
            self.excelfile,
            self.sheet.standards,
            usecols="A:F",
            rowx=1,
            colx="H",
            **kwargs,
        )
        return _validate_no_null(df)

    def past_lot_standards(self, **kwargs: Any) -> pd.DataFrame:
        return _get_frame(
            self.excelfile,
            self.sheet.lot_standards,
            usecols="A:F",
            skiprows=1,
            **kwargs,
        ).rename(columns=_strip_trailing_numbers)

    def additional_lot_standards(self, **kwargs: Any) -> pd.DataFrame:
        return _get_frame(
            self.excelfile,
            self.sheet.lot_standards,
            usecols="H:J",
            skiprows=1,
            **kwargs,
        ).rename(columns=_strip_trailing_numbers)

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
