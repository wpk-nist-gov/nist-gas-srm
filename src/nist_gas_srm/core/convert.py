"""Convert between excel and json data"""
# ruff:file-ignore[line-contains-todo,missing-todo-link]

from __future__ import annotations

import re
from abc import abstractmethod
from enum import StrEnum
from typing import TYPE_CHECKING, Any, ClassVar, Protocol, cast, override

import pandas as pd

from . import basemodels
from .read_excel import (
    _strip_trailing_numbers,
    as_excelfile,
    get_frame,
    get_frame_with_len_check,
    maybe_dropna,
    skipper,
    validate_no_null,
)
from .utils import optional_dataframe_func_wrapper

if TYPE_CHECKING:
    from collections.abc import (
        Container,
        Hashable,
        ItemsView,
        KeysView,
        ValuesView,
    )
    from io import BytesIO
    from pathlib import Path

    from pydantic import BaseModel


RCERT_PATTERN = re.compile(r"^rcert\.")


class SheetNames(StrEnum):
    ratio = "Ratio Data"
    vendor = "Vendor Data"
    standards = "Standards Data"
    lot_standards = "Past LS"
    ratio_analysis = "Ratio Analysis"
    rcert = "RCertification"


def _get_colnames_to_dbnames_mapping(
    obj: type[BaseModel], exclude_name: Container[str] = ("srmdata_i", "rcert_id")
) -> dict[str, str]:
    out: dict[str, str] = {}
    for name, field in obj.model_fields.items():
        if name in exclude_name:
            continue

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


SRM_COLNAMES_TO_DBNAMES_MAPPER = {
    tablename: _get_colnames_to_dbnames_mapping(model)
    for tablename, model in {
        "ratios": basemodels.RatioDataCreate,
        "vendors": basemodels.VendorDataCreate,
        "standards": basemodels.StandardsDataCreate,
        "past_lot_standards": basemodels.PastLotStandardsDataCreate,
        "additional_lot_standards": basemodels.AdditionalLotStandardsDataCreate,
        "ratio_analysis_random_effects": basemodels.RatioAnalysisRandomEffectsDataCreate,
        "ratio_analysis_fixed_effects": basemodels.RatioAnalysisFixedEffectsDataCreate,
    }.items()
}

RCERT_COLNAMES_TO_DBNAMES_MAPPER = {
    tablename: _get_colnames_to_dbnames_mapping(model)
    for tablename, model in {
        "srm_values": basemodels.RCertSRMValuesCreate,
        "standards_values": basemodels.RCertStandardsValuesCreate,
        "additional_lot_standards": basemodels.RCertAdditionalLotStandardsCreate,
        "cylinder_results": basemodels.RCertCylinderResultsCreate,
        "analysis_function_coefficients": basemodels.RCertAnalysisFunctionCoefficientsCreate,
        "correlation_coefficients": basemodels.RCertCorrelationCoefficientsCreate,
        "outliers": basemodels.RCertOutliersCreate,
    }.items()
}


class DataProtocol(Protocol):
    sheet_name: ClassVar[SheetNames]
    table_name: ClassVar[str]
    _mapper: ClassVar[dict[str, dict[str, str]]] = SRM_COLNAMES_TO_DBNAMES_MAPPER
    _model: type[BaseModel] | None
    _excelfile: pd.ExcelFile | None

    def __init__(
        self, xls: pd.ExcelFile | None = None, model: type[BaseModel] | None = None
    ) -> None:
        self._excelfile = xls
        self._model = model

    @property
    def excelfile(self) -> pd.ExcelFile:
        if self._excelfile is None:
            msg = "Must pass xls during creation"
            raise ValueError(msg)
        return self._excelfile

    @property
    def colnames_to_dbnames(self) -> dict[str, str]:
        return self._mapper[self.table_name]

    @property
    def dbnames_to_colnames(self) -> dict[str, str]:
        return {v: k for k, v in self.colnames_to_dbnames.items()}

    @property
    def columns(self) -> list[str]:
        return list(self.dbnames_to_colnames.values())

    @property
    def dbnames(self) -> list[str]:
        return list(self.dbnames_to_colnames.keys())

    def _get_frame(self, **kwargs: Any) -> pd.DataFrame:
        return get_frame(self.excelfile, sheet_name=self.sheet_name.value, **kwargs)

    def _get_frame_with_len_check(self, **kwargs: Any) -> pd.DataFrame:
        return get_frame_with_len_check(
            self.excelfile, sheet_name=self.sheet_name.value, **kwargs
        )

    def _get_optional_frame(
        self, strip_trailing_numbers: bool = False, **kwargs: Any
    ) -> pd.DataFrame | None:
        out = optional_dataframe_func_wrapper(
            get_frame, self.excelfile, sheet_name=self.sheet_name.value, **kwargs
        )
        if out is not None and strip_trailing_numbers:
            out = out.rename(columns=_strip_trailing_numbers)
        return out

    def _get_optional_frame_with_len_check(self, **kwargs: Any) -> pd.DataFrame | None:
        return optional_dataframe_func_wrapper(
            get_frame_with_len_check,
            self.excelfile,
            sheet_name=self.sheet_name.value,
            **kwargs,
        )

    @abstractmethod
    def excel_to_dataframe(self) -> pd.DataFrame | None: ...

    def dataframe_to_excel(self, obj: pd.DataFrame) -> None:
        raise NotImplementedError

    def normalize_dataframe_names(
        self, obj: pd.DataFrame | None
    ) -> pd.DataFrame | None:
        if obj is None:
            return obj
        return obj.rename(columns=self.colnames_to_dbnames)

    def dataframe_to_dicts(self, obj: pd.DataFrame | None) -> list[dict[Hashable, Any]]:
        if obj is None:
            return []
        return obj.rename(columns=self.colnames_to_dbnames).to_dict(orient="records")

    def _validate_model(self, model: type[BaseModel] | None) -> type[BaseModel]:
        if (model := model if model is not None else self._model) is None:
            msg = "Must pass model to method or set model in init."
            raise ValueError(msg)
        return model

    def dataframe_to_models(
        self,
        obj: pd.DataFrame | None,
        model: type[BaseModel] | None = None,
    ) -> list[BaseModel]:
        model = self._validate_model(model)
        return [model.model_validate(x) for x in self.dataframe_to_dicts(obj)]

    def excel_to_dicts(self) -> list[dict[Hashable, Any]]:
        return self.dataframe_to_dicts(self.excel_to_dataframe())

    def excel_to_models(self, cls: type[BaseModel] | None = None) -> list[BaseModel]:
        return self.dataframe_to_models(self.excel_to_dataframe(), cls)

    def dicts_to_dataframe(
        self, data: list[dict[Hashable, Any]]
    ) -> pd.DataFrame | None:
        if not data:
            return None
        return pd.DataFrame(data).rename(columns=self.dbnames_to_colnames)


class RatioData(DataProtocol):
    table_name = "ratios"
    sheet_name = SheetNames.ratio

    @override
    def excel_to_dataframe(self) -> pd.DataFrame | None:
        out = self._get_frame_with_len_check(
            usecols="A:I",
            rowx=16,
            colx="L",
        )

        _ = validate_no_null(out.drop(columns="Test"))
        return out


class VendorData(DataProtocol):
    table_name = "vendors"
    sheet_name = SheetNames.vendor

    @override
    def excel_to_dataframe(self) -> pd.DataFrame | None:
        return self._get_frame(usecols="A:D")


class StandardsData(DataProtocol):
    table_name = "standards"
    sheet_name = SheetNames.standards

    @override
    def excel_to_dataframe(self) -> pd.DataFrame | None:
        return self._get_frame_with_len_check(
            usecols="A:E",
            rowx=1,
            colx="H",
        )


class PastLotStandards(DataProtocol):
    table_name = "past_lot_standards"
    sheet_name = SheetNames.lot_standards

    @override
    def excel_to_dataframe(self) -> pd.DataFrame | None:
        return self._get_frame(
            usecols="A:F", skiprows=1, strip_trailing_numbers=True
        ).rename(columns=_strip_trailing_numbers)


class AdditionalLotStandards(DataProtocol):
    table_name = "additional_lot_standards"
    sheet_name = SheetNames.lot_standards

    @override
    def excel_to_dataframe(self) -> pd.DataFrame | None:
        return self._get_frame(
            usecols="H:J",
            skiprows=1,
        ).rename(columns=_strip_trailing_numbers)


class RatioAnalysisRandomEffects(DataProtocol):
    table_name = "ratio_analysis_random_effects"
    sheet_name = SheetNames.ratio_analysis

    @override
    def excel_to_dataframe(self) -> pd.DataFrame | None:
        return self._get_optional_frame(
            usecols="X:Y,AA,AC",
            skiprows=1,
            strip_trailing_numbers=True,
        )


class RatioAnalysisFixedEffects(DataProtocol):
    table_name = "ratio_analysis_fixed_effects"
    sheet_name = SheetNames.ratio_analysis

    @override
    def excel_to_dataframe(self) -> pd.DataFrame | None:
        return self._get_optional_frame(
            usecols="AD:AF",
            skiprows=1,
            strip_trailing_numbers=True,
        )


# * RCert
class RCertDataProtocol(DataProtocol):
    _mapper = RCERT_COLNAMES_TO_DBNAMES_MAPPER


class RCertSRMValues(RCertDataProtocol):
    table_name = "srm_values"
    sheet_name = SheetNames.rcert

    def excel_to_dataframe_transposed(self) -> pd.DataFrame | None:
        return self._get_optional_frame(
            usecols="A:B",
            header=None,
            skiprows=skipper(include={47, 48, 49, 52, 53, 54, 55}),
            names=["name", "value"],
        )

    @override
    def excel_to_dataframe(self) -> pd.DataFrame | None:
        if (df := self.excel_to_dataframe_transposed()) is None:
            return df
        new = cast(
            "pd.DataFrame",
            pd.pivot(df.assign(dummy=0).set_index("dummy"), columns="name")["value"],
        )
        return new.rename_axis(columns=None, index=None)

    # TODO(wpk): transpose output


class RCertStandardsValues(RCertDataProtocol):
    table_name = "standards_values"
    sheet_name = SheetNames.rcert

    @override
    def excel_to_dataframe(self) -> pd.DataFrame | None:
        out = self._get_optional_frame(
            usecols="A:E",
            skiprows=skipper(lower=58, upper=68),
        )

        if out is not None:
            out = out.rename(columns=_strip_trailing_numbers)
            columns = list(out.columns)
            columns[-1] = "Predicted " + columns[-1]
            out.columns = columns

            out = maybe_dropna(out, how="all", subset=out.columns[1:])

        return out


class RCertAdditionalLotStandards(RCertDataProtocol):
    table_name = "additional_lot_standards"
    sheet_name = SheetNames.rcert

    @override
    def excel_to_dataframe(self) -> pd.DataFrame | None:
        return self._get_optional_frame(
            usecols="A:E", skiprows=skipper(lower=71, upper=75)
        )


class RCertCylinderResults(RCertDataProtocol):
    table_name = "cylinder_results"
    sheet_name = SheetNames.rcert

    @override
    def excel_to_dataframe(self) -> pd.DataFrame | None:
        return self._get_optional_frame(
            usecols="M:P",
            skiprows=46,
            strip_trailing_numbers=True,
        )


class RCertAnalysisFunctionCoefficients(RCertDataProtocol):
    table_name = "analysis_function_coefficients"
    sheet_name = SheetNames.rcert

    @override
    def excel_to_dataframe(self) -> pd.DataFrame | None:
        out = maybe_dropna(
            self._get_optional_frame(
                usecols="G:H",
                skiprows=skipper(lower=46, upper=50),
                names=["value", "uncert"],
            ),
            how="all",
        )
        if out is not None:
            out = out.assign(order=range(len(out)))
        return out


class RCertCorrelationCoefficients(RCertDataProtocol):
    table_name = "correlation_coefficients"
    sheet_name = SheetNames.rcert

    def excel_to_dataframe_matrix(self) -> pd.DataFrame | None:
        out = self._get_optional_frame(
            usecols="G:J",
            skiprows=skipper(lower=52, upper=56),
        )
        out = maybe_dropna(out, how="all")

        if out is not None:
            out = out.assign(order=range(len(out)))

        return maybe_dropna(out, how="all", axis=1)

    @override
    def excel_to_dataframe(self) -> pd.DataFrame | None:

        if (df := self.excel_to_dataframe_matrix()) is None:
            return df

        return pd.melt(
            df.rename(columns=lambda x: x if x == "order" else int(x[1:])),
            id_vars="order",
            var_name="order_other",
        )

    # TODO(wpk): stack frame output


class RCertOutliers(RCertDataProtocol):
    table_name = "outliers"
    sheet_name = SheetNames.rcert

    @override
    def excel_to_dataframe(self) -> pd.DataFrame | None:
        return self._get_optional_frame(
            usecols="A:D",
            skiprows=78,
        )


class _CollectionConverter:
    _classes: ClassVar[tuple[type[DataProtocol], ...]]

    def __init__(
        self,
        path_or_excelfile: Path | BytesIO | pd.ExcelFile,
        model_mapper: dict[str, type[BaseModel]] | None = None,
    ) -> None:

        if model_mapper is None:
            model_mapper = {}
        with as_excelfile(path_or_excelfile) as excelfile:
            self.excelfile = excelfile

            self._objs: dict[str, DataProtocol] = {
                v.table_name: v(self.excelfile, model=model_mapper.get(v.table_name))
                for v in self._classes
            }

    def __getitem__(self, key: str) -> DataProtocol:
        return self._objs[key]

    def keys(self) -> KeysView[str]:
        return self._objs.keys()

    def values(self) -> ValuesView[str]:
        return cast("ValuesView[str]", self._objs.values())

    def items(self) -> ItemsView[str, DataProtocol]:
        return self._objs.items()

    def model_dump(self) -> dict[str, Any]:
        return {k: v.excel_to_dicts() for k, v in self.items()}


class _RCertConverter(_CollectionConverter):
    _classes = (
        RCertSRMValues,
        RCertStandardsValues,
        RCertAdditionalLotStandards,
        RCertCylinderResults,
        RCertAnalysisFunctionCoefficients,
        RCertCorrelationCoefficients,
        RCertOutliers,
    )


class _SRMConverter(_CollectionConverter):
    _classes = (
        RatioData,
        VendorData,
        StandardsData,
        PastLotStandards,
        AdditionalLotStandards,
        RatioAnalysisRandomEffects,
        RatioAnalysisFixedEffects,
    )


class SRMRCertConverter(_SRMConverter):
    def __init__(
        self,
        path_or_excelfile: Path | BytesIO | pd.ExcelFile,
        model_mapper: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(path_or_excelfile, model_mapper)
        self.rcert = _RCertConverter(
            path_or_excelfile, (model_mapper or {}).get("rcert", {})
        )

    @override
    def model_dump(self) -> dict[str, Any]:
        out = super().model_dump()
        out["rcert"] = self.rcert.model_dump()
        return out

    @override
    def __getitem__(self, key: str) -> DataProtocol:
        if key.startswith("rcert."):
            return self.rcert[RCERT_PATTERN.sub("", key)]
        return super().__getitem__(key)
