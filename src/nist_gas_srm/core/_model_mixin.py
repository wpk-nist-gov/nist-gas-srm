"""Mixin for models"""

from collections.abc import Hashable
from enum import StrEnum
from functools import cache
from typing import Any, ClassVar, Self

import pandas as pd
from sqlmodel import SQLModel

from .read_excel import (
    _strip_trailing_numbers,
    get_frame,
    get_frame_with_len_check,
)
from .utils import optional_dataframe_func_wrapper


class SheetNames(StrEnum):
    ratio = "Ratio Data"
    vendor = "Vendor Data"
    standards = "Standards Data"
    lot_standards = "Past LS"
    ratio_analysis = "Ratio Analysis"
    rcert = "RCertification"


class SQLDataFrameInterface(SQLModel):
    _table_name: ClassVar[str]
    _sheet_name: ClassVar[SheetNames]

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
        out = get_frame(excelfile, sheet_name=cls._sheet_name.value, **kwargs)
        if strip_trailing_numbers:
            return out.rename(columns=_strip_trailing_numbers)
        return out

    @classmethod
    def _get_frame_with_len_check(
        cls,
        excelfile: pd.ExcelFile,
        strip_trailing_numbers: bool = False,
        **kwargs: Any,
    ) -> pd.DataFrame:
        out = get_frame_with_len_check(
            excelfile, sheet_name=cls._sheet_name.value, **kwargs
        )
        if strip_trailing_numbers:
            return out.rename(columns=_strip_trailing_numbers)
        return out

    @classmethod
    def _get_optional_frame(
        cls,
        excelfile: pd.ExcelFile,
        strip_trailing_numbers: bool = False,
        **kwargs: Any,
    ) -> pd.DataFrame | None:
        out = optional_dataframe_func_wrapper(
            get_frame, excelfile, sheet_name=cls._sheet_name.value, **kwargs
        )
        if out is not None and strip_trailing_numbers:
            out = out.rename(columns=_strip_trailing_numbers)
        return out

    @classmethod
    def _get_optional_frame_with_len_check(
        cls, excelfile: pd.ExcelFile, **kwargs: Any
    ) -> pd.DataFrame | None:
        return optional_dataframe_func_wrapper(
            get_frame_with_len_check,
            excelfile,
            sheet_name=cls._sheet_name.value,
            **kwargs,
        )

    @classmethod
    def excel_to_dataframe(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        raise NotImplementedError

    @classmethod
    def dataframe_to_excel(cls, obj: pd.DataFrame, excelfile: pd.ExcelFile) -> None:
        raise NotImplementedError

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
    def dicts_to_dataframe(cls, data: list[dict[Hashable, Any]]) -> pd.DataFrame | None:
        if not data:
            return None
        return pd.DataFrame(data).rename(columns=cls.dbnames_to_colnames())
