from __future__ import annotations

import re
from contextlib import contextmanager
from functools import partial
from typing import TYPE_CHECKING, cast

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from collections.abc import Callable, Container, Generator
    from io import BytesIO
    from pathlib import Path
    from typing import Any, TypeVar

    T = TypeVar("T")

EXCEL_FILENAME_PATTERN = re.compile(
    r"srm(?P<srm_id>\d+)(?P<batch_id>\w*)_Series(?P<lot_id>\w*)_(.*).xls",
    flags=re.IGNORECASE,
)

strip_trailing_numbers = partial(re.compile(r"\.[1-9]+").sub, "")


def skipper(
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


def maybe_dropna(df: pd.DataFrame | None, **kwargs: Any) -> pd.DataFrame | None:
    if df is not None:
        return cast("pd.DataFrame | None", df.dropna(**kwargs))
    return df


def get_frame(
    io: Any,
    sheet_name: str,
    **kwargs: Any,
) -> pd.DataFrame:
    return pd.read_excel(io, sheet_name=sheet_name, **kwargs).dropna(how="all")  # pyright: ignore[reportUnknownMemberType]


def validate_no_null(x: T) -> T:
    if np.any(pd.isnull(cast("np.ndarray[Any, Any]", x))):
        msg = "Null values found"
        raise ValueError(msg)
    return x


def get_value_from_worksheet(
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
def as_excelfile(
    path_or_excelfile: Path | BytesIO | pd.ExcelFile,
) -> Generator[pd.ExcelFile]:
    if isinstance(path_or_excelfile, pd.ExcelFile):
        yield path_or_excelfile
    else:
        yield pd.ExcelFile(path_or_excelfile)


def get_frame_with_len_check(
    path_or_excelfile: Path | BytesIO | pd.ExcelFile,
    sheet_name: str,
    usecols: str,
    rowx: int,
    colx: int | str,
    require_check: bool = True,
    **kwargs: Any,
) -> pd.DataFrame:

    with as_excelfile(path_or_excelfile) as xls:
        df = get_frame(xls, sheet_name=sheet_name, usecols=usecols, **kwargs)

        if require_check:
            if (
                val := get_value_from_worksheet(
                    xls, sheet_name=sheet_name, rowx=rowx, colx=colx
                )
            ) is None:
                msg = "No check value found"
                raise ValueError(msg)

            if (check := int(val)) != len(df):
                msg = f"Wrong check shape {check=} != {len(df)}"
                raise ValueError(msg)

    return df


def parse_excel_filename_to_metadata(name: str) -> dict[str, Any]:
    """
    Parse an excel filename to parameters
    """
    if (m := EXCEL_FILENAME_PATTERN.match(name)) is None:
        msg = f"Unable to parse ids from {name}"
        raise ValueError(msg)

    out = m.groupdict().copy()
    if not out["batch_id"]:
        out["batch_id"] = None

    return out


def optional_dataframe_func_wrapper(
    func: Callable[..., pd.DataFrame],
    xls: pd.ExcelFile,
    sheet_name: str,
    **kwargs: Any,
) -> pd.DataFrame | None:

    if sheet_name in xls.sheet_names:
        df = func(
            xls,
            sheet_name,
            **kwargs,
        )
        return None if df.empty else df
    return None
