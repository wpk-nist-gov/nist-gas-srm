"""Mixin for models"""
# ruff:file-ignore[assert]

import contextlib
import re
from collections.abc import Callable, Hashable
from enum import StrEnum
from functools import cache
from operator import methodcaller
from types import UnionType
from typing import Any, ClassVar, Self, cast, get_args, get_origin

import pandas as pd
from openpyxl.workbook.workbook import Workbook
from sqlmodel import SQLModel

from .excel_utils import (
    get_frame,
    get_frame_with_len_check,
    optional_dataframe_func_wrapper,
    simple_write_to_excel,
    strip_trailing_numbers as func_strip_trailing_numbers,
)

RCERT_PATTERN = re.compile(r"^rcert\.")
STANDARD_ANALYSIS_PATTERN = re.compile(r"^standard_analysis\.")


class SheetNames(StrEnum):
    ratio = "Ratio Data"
    vendor = "Vendor Data"
    standards = "Standards Data"
    lot_standards = "Past LS"
    ratio_analysis = "Ratio Analysis"
    standard_analysis = "Std Analysis"
    rcert = "RCertification"


class SQLDataFrameInterface(SQLModel):
    dataframe_name: ClassVar[str]
    sheet_name: ClassVar[SheetNames]

    @classmethod
    @cache
    def colnames_to_dbnames(cls) -> dict[str, str]:
        out: dict[str, str] = {}
        for name, field in cls.model_fields.items():
            if (alias := field.validation_alias) is None:
                alias = name

            if alias in out:
                msg = f"repeated column name {alias}"
                raise ValueError(msg)

            if not isinstance(alias, str):
                msg = f"Unknown type {type(alias)} for alias for name {name}"
                raise TypeError(msg)
            out[alias] = name
        return out

    @classmethod
    def dbnames_to_colnames(cls) -> dict[str, str]:
        return {v: k for k, v in cls.colnames_to_dbnames().items()}

    @classmethod
    def _get_frame(
        cls,
        excelfile: pd.ExcelFile,
        strip_trailing_numbers: bool = False,
        **kwargs: Any,
    ) -> pd.DataFrame:
        out = get_frame(excelfile, sheet_name=cls.sheet_name.value, **kwargs)
        if strip_trailing_numbers:
            return out.rename(columns=func_strip_trailing_numbers)
        return out

    @classmethod
    def _get_frame_with_len_check(
        cls,
        excelfile: pd.ExcelFile,
        strip_trailing_numbers: bool = False,
        **kwargs: Any,
    ) -> pd.DataFrame:
        out = get_frame_with_len_check(
            excelfile, sheet_name=cls.sheet_name.value, **kwargs
        )
        if strip_trailing_numbers:
            return out.rename(columns=func_strip_trailing_numbers)
        return out

    @classmethod
    def _get_optional_frame(
        cls,
        excelfile: pd.ExcelFile,
        strip_trailing_numbers: bool = False,
        **kwargs: Any,
    ) -> pd.DataFrame | None:
        out = optional_dataframe_func_wrapper(
            get_frame, excelfile, sheet_name=cls.sheet_name.value, **kwargs
        )
        if out is not None and strip_trailing_numbers:
            out = out.rename(columns=func_strip_trailing_numbers)
        return out

    @classmethod
    def _get_optional_frame_with_len_check(
        cls, excelfile: pd.ExcelFile, **kwargs: Any
    ) -> pd.DataFrame | None:
        return optional_dataframe_func_wrapper(
            get_frame_with_len_check,
            excelfile,
            sheet_name=cls.sheet_name.value,
            **kwargs,
        )

    @classmethod
    def excel_to_dataframe(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        raise NotImplementedError

    @classmethod
    def dataframe_to_excel(cls, obj: pd.DataFrame, workbook: Workbook) -> None:
        """Simplest case"""
        worksheet = workbook[cls.sheet_name]
        return simple_write_to_excel(obj, worksheet=worksheet)

    @classmethod
    def dataframe_to_dicts(cls, obj: pd.DataFrame | None) -> list[dict[Hashable, Any]]:
        if obj is None:
            return []
        return obj.rename(columns=cls.colnames_to_dbnames()).to_dict(orient="records")

    @classmethod
    def dataframe_to_models(
        cls,
        obj: pd.DataFrame | None,
    ) -> list[Self]:
        return [cls.model_validate(x) for x in cls.dataframe_to_dicts(obj)]

    @classmethod
    def excel_to_dicts(cls, excelfile: pd.ExcelFile) -> list[dict[Hashable, Any]]:
        return cls.dataframe_to_dicts(cls.excel_to_dataframe(excelfile))

    @classmethod
    def excel_to_models(cls, excelfile: pd.ExcelFile) -> list[Self]:
        return cls.dataframe_to_models(cls.excel_to_dataframe(excelfile))

    @classmethod
    def dicts_to_dataframe(
        cls,
        data: list[dict[str, Any]],
        drop_colnames: list[str] | None = None,
        drop_dbnames: list[str] | None = None,
    ) -> pd.DataFrame | None:
        if not data:
            return None
        out = pd.DataFrame(data)
        if drop_dbnames:
            out = out.drop(drop_dbnames, axis=1, errors="ignore")
        out = out.rename(columns=cls.dbnames_to_colnames())
        if drop_colnames:
            return out.drop(drop_colnames, axis=1, errors="ignore")
        return out

    @classmethod
    def models_to_dataframe(
        cls,
        models: list[Self],
        drop_colnames: list[str] | None = None,
        drop_dbnames: list[str] | None = None,
    ) -> pd.DataFrame | None:
        if not models:
            return None
        return cls.dicts_to_dataframe(
            [m.model_dump() for m in models],
            drop_colnames=drop_colnames,
            drop_dbnames=drop_dbnames,
        )


def _annotation_to_model(annotation: Any, name: str) -> type[SQLModel]:
    args = get_args(annotation)
    if len(args) != 1:
        msg = f"Unknown arg {args} for {name}"
        raise ValueError(msg)

    inner_model = args[0]
    if issubclass(inner_model, SQLModel):
        return inner_model  # type: ignore[no-any-return]

    msg = f"Unknown inner model type {type(inner_model)} for {name}"
    raise TypeError(msg)


def json_to_dict_of_models(
    data: dict[str, Any], model: type[SQLModel], update: bool = False
) -> dict[str, Any]:
    """Convert json data to dict of sqlmodel objects"""

    out: dict[str, Any] = data.copy() if update else {}
    for name, field in model.model_fields.items():
        if name not in data:
            continue

        annotation: Any = field.annotation
        if annotation is None or isinstance(annotation, UnionType):
            out[name] = data[name]
        elif get_origin(annotation) is list:
            # list
            inner_model = _annotation_to_model(annotation, name)
            out[name] = [inner_model.model_validate(d) for d in data.get(name, [])]
        elif issubclass(annotation, SQLModel):
            # Recursive
            inner_model = annotation
            if v := inner_model.model_validate(
                json_to_dict_of_models(data[name], inner_model, update=update)
            ):
                out[name] = v

        else:
            # anything else
            out[name] = data[name]
    return out


def json_to_dict_of_dataframes(
    data: dict[str, Any],
    model: type[SQLModel],
    normalize: bool = True,
) -> dict[str, Any]:

    out: dict[str, Any] = {}
    for name, field in model.model_fields.items():
        if not normalize and name not in data:
            continue

        annotation: Any = field.annotation
        if annotation is None or isinstance(annotation, UnionType):
            pass
        elif get_origin(annotation) is list:
            # list
            inner_model = _annotation_to_model(annotation, name)
            if issubclass(inner_model, SQLDataFrameInterface):
                if normalize:
                    with contextlib.suppress(KeyError):
                        out[name] = pd.json_normalize(
                            data, name, ["srm_id", "batch_id", "lot_id"]
                        ).rename(columns=inner_model.dbnames_to_colnames())
                elif name in data:
                    out[name] = inner_model.dicts_to_dataframe(data[name])

        elif issubclass(annotation, SQLModel):  # pylint: disable=confusing-consecutive-elif
            # Recursive
            inner_model = annotation
            if v := json_to_dict_of_dataframes(
                data if normalize else data[name], inner_model, normalize
            ):
                out[name] = v
    return out


def _model_caller(
    caller: Callable[[type[SQLDataFrameInterface]], Any], model: type[SQLModel]
) -> dict[str, Any]:
    """Extract a dict of (nested) dataframes from excelfile"""

    out: dict[str, Any] = {}

    for name, field in model.model_fields.items():
        annotation: Any = field.annotation
        if annotation is None or isinstance(annotation, UnionType):
            pass
        elif get_origin(annotation) is list:
            # list
            inner_model = _annotation_to_model(annotation, name)
            if issubclass(inner_model, SQLDataFrameInterface):
                out[name] = caller(inner_model)
        elif issubclass(annotation, SQLModel):  # pylint: disable=confusing-consecutive-elif
            # Recursive
            inner_model = annotation
            if v := _model_caller(caller, inner_model):
                out[name] = v

    return out


def excel_to_dict_of_dataframes(
    excelfile: pd.ExcelFile,
    model: type[SQLModel],
) -> dict[str, Any]:
    """Extract a dict of (nested) dataframes from excelfile"""

    return _model_caller(
        methodcaller("excel_to_dataframe", excelfile),
        model,
    )


def excel_to_dict_of_models(
    excelfile: pd.ExcelFile,
    model: type[SQLModel],
) -> dict[str, Any]:
    return _model_caller(
        methodcaller("excel_to_models", excelfile),
        model,
    )


def excel_to_json(
    excelfile: pd.ExcelFile,
    model: type[SQLModel],
) -> dict[str, Any]:
    return _model_caller(
        methodcaller("excel_to_dicts", excelfile),
        model=model,
    )


def dict_of_dataframes_to_workbook(
    data: dict[str, Any],
    workbook: Workbook,
    model: type[SQLModel],
) -> None:

    for name, field in model.model_fields.items():
        annotation: Any = field.annotation
        if annotation is None or isinstance(annotation, UnionType):
            pass
        elif get_origin(annotation) is list:
            # list
            inner_model = _annotation_to_model(annotation, name)
            if (
                issubclass(inner_model, SQLDataFrameInterface)
                and (df := data.get(name)) is not None
            ):
                inner_model.dataframe_to_excel(df, workbook)
        elif issubclass(annotation, SQLModel):  # pylint: disable=confusing-consecutive-elif
            # Recursive
            inner_model = annotation
            dict_of_dataframes_to_workbook(data[name], workbook, inner_model)


def excel_to_dataframe_by_name(
    name: str,
    excelfile: pd.ExcelFile,
    model: type[SQLModel],
) -> pd.DataFrame | None:
    """
    Extract dataframe from excelfile by name

    Parameters
    ----------
    name : str
        Name of dataframe to extract.
    excelfile : pd.ExcelFile,
    model : SQLModel

    Returns
    pd.DataFrame, optional
        DataFrame.
    """

    prefix, sep, root = name.partition(".")

    if sep == ".":
        if (obj := model.model_fields.get(prefix)) is None:
            msg = f"model does not contain {prefix}"
            raise ValueError(msg)
        model_: Any = obj.annotation
        assert issubclass(model_, SQLModel)
        return excel_to_dataframe_by_name(root, excelfile=excelfile, model=model_)

    annotation: Any
    annotation = model.model_fields[name].annotation
    if (origin := get_origin(annotation)) is not list:
        msg = f"{name} is not a list field.  Got {origin}."
        raise ValueError(msg)

    inner_model = _annotation_to_model(annotation, name)
    assert issubclass(inner_model, SQLDataFrameInterface), (
        f"Inner class type {type(inner_model)} for {name} must be an SQLDataFrameInterface"
    )
    return inner_model.excel_to_dataframe(excelfile)


def model_to_dict_of_dataframes(
    obj: SQLModel,
    **kwargs: Any,
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, value in obj:
        if isinstance(value, list):
            if value and isinstance(v0 := value[0], SQLDataFrameInterface):  # pyright: ignore[reportUnknownVariableType]
                out[name] = v0.models_to_dataframe(
                    cast("list[SQLDataFrameInterface]", value),
                    **kwargs,
                )

        elif isinstance(value, SQLModel) and (
            v := model_to_dict_of_dataframes(value, **kwargs)
        ):
            out[name] = v
    return out
