"""Basic model"""
# ruff:file-ignore[commented-out-code,missing-todo-link,line-contains-todo]

from datetime import UTC, datetime
from operator import methodcaller
from typing import Annotated, Any, Literal, Self, TypeAlias, cast, override

import pandas as pd
from pydantic import AliasGenerator, BeforeValidator, PlainSerializer
from pydantic.alias_generators import to_pascal as to_pascal_base
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.hybrid import hybrid_property
from sqlmodel import (
    VARCHAR,
    Field,
    SQLModel,
    UniqueConstraint,
)
from sqlmodel._compat import SQLModelConfig  # ruff:ignore[import-private-name]

from nist_gas_srm.core.validate import (
    validate_nan_to_none,
    validate_optional_str_to_lower,
    validate_str_to_lower,
    validate_test_out,
    validate_timestamp,
)

from .excel_interface import SheetNames, SQLDataFrameInterface
from .utils import SRM_PATTERN, maybe_dropna, skipper, validate_no_null

# Utilities -------------------------------------------------------------------
to_pascal = AliasGenerator(
    validation_alias=to_pascal_base,
    serialization_alias=lambda x: x,
)


def _serialize_test_out(x: bool) -> Literal["OUT"] | None:
    return "OUT" if x else None


TestOutAnn = Annotated[
    bool,
    BeforeValidator(validate_test_out),
    PlainSerializer(_serialize_test_out),
    Field(validation_alias="Test"),
]
TestOutOptionalAnn = Annotated[
    bool | None,
    BeforeValidator(validate_test_out),
    PlainSerializer(_serialize_test_out),
    Field(validation_alias="Test"),
]


# * Common --------------------------------------------------------------------
class IDPrimaryKey(SQLModel):
    id: int | None = Field(default=None, primary_key=True)


class _IDPrimaryKeyPublic(SQLModel):
    id: int


class _SampleIDAndNumber(SQLModel):
    model_config = SQLModelConfig(populate_by_name=True)

    name: str = Field(index=True, validation_alias="SampleID")
    number: int = Field(validation_alias="SampleNo")


class _SampleIDAndNumberUpdate(SQLModel):
    model_config = SQLModelConfig(populate_by_name=True)

    name: str | None = None
    number: int | None = None


class SRMDataForeignKey(SQLModel):
    srmdata_id: int | None = Field(
        default=None,
        foreign_key="srmdata.id",
        ondelete="CASCADE",
        validation_alias="SRMDataID",
    )


class _SRMDataForeignKeyUpdate(SQLModel):
    srmdata_id: int | None = None


# * Top level data (per worksheet) --------------------------------------------
class SRMDataBase(SQLModel):
    """Metadata base class"""

    __table_args__ = (
        UniqueConstraint("srm_id", "batch_id", "lot_id", name="unique_user_product"),
    )

    model_config = SQLModelConfig(ignored_types=(hybrid_property,))

    name: str = Field(sa_column=Column("name", VARCHAR))
    srm_id: int = Field(index=True)
    batch_id: Annotated[str | None, BeforeValidator(validate_optional_str_to_lower)]
    lot_id: Annotated[str, BeforeValidator(validate_str_to_lower)]

    timestamp: Annotated[datetime, BeforeValidator(validate_timestamp)] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(UTC),
    )

    @hybrid_property
    def srm_string_id(self) -> str:
        return f"{self.srm_id}{self.batch_id or ''}{'-' + self.lot_id if self.lot_id else ''}"


class SRMDataPublic(SRMDataBase, _IDPrimaryKeyPublic):
    pass


class SRMDataCreate(SRMDataBase):
    pass


class SRMDataUpdate(SQLModel):
    name: str | None = None
    timestamp: datetime | None = None


class SRMDataQuery(SQLModel):
    srm_id: int | None = None
    batch_id: Annotated[str | None, BeforeValidator(validate_optional_str_to_lower)] = (
        None
    )
    lot_id: Annotated[str | None, BeforeValidator(validate_optional_str_to_lower)] = (
        None
    )

    @classmethod
    def from_string(cls, string: str) -> Self:
        if (m := SRM_PATTERN.match(string)) is not None:
            return cls.model_validate({
                k: v for k, v in m.groupdict().items() if v is not None
            })
        return cls()

    @classmethod
    def from_params_exclude_none(cls, **kwargs: Any) -> Self:
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        return cls.model_validate(kwargs)


# * Tables --------------------------------------------------------------------
# ** Ratio Data ---------------------------------------------------------------
class RatioDataBase(_SampleIDAndNumber, SRMDataForeignKey):
    """Ratio data base class"""

    model_config = SQLModelConfig(
        alias_generator=to_pascal,
        populate_by_name=True,
    )

    ratio: float
    ls_set: int = Field(validation_alias="LSSet")
    break_set: int
    day: int
    port: int
    value_g: float
    test_out: TestOutAnn


class RatioDataPublic(RatioDataBase, _IDPrimaryKeyPublic):
    pass


class RatioDataCreate(RatioDataBase, SQLDataFrameInterface):
    dataframe_name = "ratios"
    sheet_name = SheetNames.ratio

    @override
    @classmethod
    def excel_to_dataframe(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        out = cls._get_frame_with_len_check(
            excelfile,
            usecols="A:I",
            rowx=16,
            colx="L",
        )

        _ = validate_no_null(out.drop(columns="Test"))
        return out


class RatioDataUpdate(_SampleIDAndNumberUpdate, _SRMDataForeignKeyUpdate):
    model_config = SQLModelConfig(
        alias_generator=to_pascal,
        populate_by_name=True,
    )
    ratio: float | None = None
    ls_set: int | None = None
    break_set: int | None = None
    day: int | None = None
    port: int | None = None
    value_g: float | None = None
    test_out: TestOutOptionalAnn = None


# ** Vendor Data --------------------------------------------------------------
class VendorDataBase(_SampleIDAndNumber, SRMDataForeignKey):
    """Vendor data"""

    model_config = SQLModelConfig(
        alias_generator=to_pascal,
        populate_by_name=True,
    )

    cylinder_number: str = Field(validation_alias="CylinderNo")
    ratio: float = Field(validation_alias="VendorRatio")


class VendorDataPublic(VendorDataBase, _IDPrimaryKeyPublic):
    pass


class VendorDataCreate(VendorDataBase, SQLDataFrameInterface):
    dataframe_name = "vendors"
    sheet_name = SheetNames.vendor

    @override
    @classmethod
    def excel_to_dataframe(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        return cls._get_frame(excelfile, usecols="A:D")


class VendorDataUpdate(_SampleIDAndNumberUpdate, _SRMDataForeignKeyUpdate):
    cylinder_number: str | None = None
    ratio: float | None = None


# ** Standards Data -----------------------------------------------------------
class StandardsDataBase(SRMDataForeignKey):
    """Standards Data"""

    model_config = SQLModelConfig(populate_by_name=True)

    name: str = Field(validation_alias="StandardID")
    number: int = Field(validation_alias="StandardNo")
    ratio: float = Field(validation_alias="SRatio")
    concentration: float = Field(validation_alias="SConc")
    uncert: float = Field(validation_alias="Sunc")


class StandardsDataPublic(StandardsDataBase, _IDPrimaryKeyPublic):
    pass


class StandardsDataCreate(StandardsDataBase, SQLDataFrameInterface):
    dataframe_name = "standards"
    sheet_name = SheetNames.standards

    @override
    @classmethod
    def excel_to_dataframe(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        return cls._get_frame_with_len_check(
            excelfile,
            usecols="A:E",
            rowx=1,
            colx="H",
        )


class StandardsDataUpdate(_SampleIDAndNumberUpdate, _SRMDataForeignKeyUpdate):
    name: str | None = None
    number: int | None = None
    ratio: float | None = None
    concentration: float | None = None
    uncert: float | None = None


# ** Past lot standards -------------------------------------------------------
class PastLotStandardsDataBase(SRMDataForeignKey):
    """Past lot standards"""

    model_config = SQLModelConfig(populate_by_name=True)
    name: str = Field(validation_alias="LS ID")
    number: int = Field(validation_alias="LS#")
    ratio: float = Field(validation_alias="Ratio")
    value: float = Field(validation_alias="Past Conc")


class PastLotStandardsDataPublic(PastLotStandardsDataBase, _IDPrimaryKeyPublic):
    pass


class PastLotStandardsDataCreate(PastLotStandardsDataBase, SQLDataFrameInterface):
    dataframe_name = "past_lot_standards"
    sheet_name = SheetNames.lot_standards

    @override
    @classmethod
    def excel_to_dataframe(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        return cls._get_frame(
            excelfile,
            strip_trailing_numbers=True,
            usecols="A:F",
            skiprows=1,
        )


class PastLotStandardsDataUpdate(_SampleIDAndNumberUpdate, _SRMDataForeignKeyUpdate):
    name: str | None = None
    number: int | None = None
    ratio: float | None = None
    past_conc: float | None = None
    pred_conc: float | None = None


# ** Additional lot standards -------------------------------------------------
class AdditionalLotStandardsDataBase(SRMDataForeignKey):
    """AdditionalLotStandards"""

    model_config = SQLModelConfig(populate_by_name=True)
    name: str = Field(validation_alias="ID")
    number: int = Field(validation_alias="LS#")
    ratio: float = Field(validation_alias="Ratio")


class AdditionalLotStandardsDataPublic(
    AdditionalLotStandardsDataBase, _IDPrimaryKeyPublic
):
    pass


class AdditionalLotStandardsDataCreate(
    AdditionalLotStandardsDataBase, SQLDataFrameInterface
):
    dataframe_name = "additional_lot_standards"
    sheet_name = SheetNames.lot_standards

    @override
    @classmethod
    def excel_to_dataframe(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        return cls._get_frame(
            excelfile,
            strip_trailing_numbers=True,
            usecols="H:J",
            skiprows=1,
        )


class AdditionalLotStandardsDataUpdate(
    _SampleIDAndNumberUpdate, _SRMDataForeignKeyUpdate
):
    name: str | None = None
    number: int | None = None
    ratio: float | None = None


# ** Ratio Analysis -----------------------------------------------------------
class RatioAnalysisRandomEffectsDataBase(SRMDataForeignKey):
    model_config = SQLModelConfig(
        alias_generator=to_pascal,
        populate_by_name=True,
    )

    groups: str
    name: Annotated[str | None, BeforeValidator(validate_nan_to_none)]
    stddev: float = Field(validation_alias="Std Dev")
    count: Annotated[int | None, BeforeValidator(validate_nan_to_none)] = Field(
        alias="No"
    )


class RatioAnalysisRandomEffectsDataPublic(
    RatioAnalysisRandomEffectsDataBase, _IDPrimaryKeyPublic
):
    pass


class RatioAnalysisRandomEffectsDataCreate(
    RatioAnalysisRandomEffectsDataBase, SQLDataFrameInterface
):
    dataframe_name = "ratio_analysis_random_effects"
    sheet_name = SheetNames.ratio_analysis

    @override
    @classmethod
    def excel_to_dataframe(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        return cls._get_optional_frame(
            excelfile,
            usecols="X:Y,AA,AC",
            skiprows=1,
            strip_trailing_numbers=True,
        )


class RatioAnalysisRandomEffectsDataUpdate(_SRMDataForeignKeyUpdate):
    groups: str | None
    name: str | None
    stddev: float | None
    count: int | None


class RatioAnalysisFixedEffectsDataBase(SRMDataForeignKey):
    model_config = SQLModelConfig(
        alias_generator=to_pascal,
        populate_by_name=True,
    )

    estimate: float
    stderr: float = Field(validation_alias="Std Error")
    t_value: float = Field(validation_alias="t value")


class RatioAnalysisFixedEffectsDataPublic(
    RatioAnalysisFixedEffectsDataBase, _IDPrimaryKeyPublic
):
    pass


class RatioAnalysisFixedEffectsDataCreate(
    RatioAnalysisFixedEffectsDataBase, SQLDataFrameInterface
):
    dataframe_name = "ratio_analysis_fixed_effects"
    sheet_name = SheetNames.ratio_analysis

    @override
    @classmethod
    def excel_to_dataframe(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        return cls._get_optional_frame(
            excelfile,
            usecols="AD:AF",
            skiprows=1,
            strip_trailing_numbers=True,
        )


class RatioAnalysisFixedEffectsDataUpdate(_SRMDataForeignKeyUpdate):
    estimate: float | None
    stderr: float | None
    t_value: float | None


# * RCertification -----------------------------------------------------------
class RCertForeignKey(SQLModel):
    rcert_id: int | None = Field(
        default=None, foreign_key="rcertdata.id", ondelete="CASCADE"
    )


class _RCertForeignKeyUpdate(SQLModel):
    rcert_id: int | None = None


# ** RCert
class RCertBase(SRMDataForeignKey):
    """Points back to srmdata"""


class RCertPublic(RCertBase, _IDPrimaryKeyPublic):
    pass


class RCertCreate(RCertBase):
    pass


class RCertUpdate(_SRMDataForeignKeyUpdate):
    pass


# ** SRMValues
# Each of these point back to rcert
class RCertSRMValuesBase(RCertForeignKey):
    """RCert.srm_values"""

    model_config = SQLModelConfig(populate_by_name=True)

    value: float = Field(validation_alias="SRM Value")
    uncert: float = Field(validation_alias="SRM uncertainty")
    uncert_ci95: float = Field(validation_alias="SRM 95 % C.L.")
    uhistorical: Annotated[float | None, BeforeValidator(validate_nan_to_none)] = Field(
        validation_alias="uHistorical"
    )

    ls_value: float = Field(validation_alias="LS Value")
    ls_uncert: float = Field(validation_alias="LS uncertainty")
    ls_uncert_ci95: float = Field(validation_alias="LS 95 % C.L.")


class RCertSRMValuesPublic(RCertSRMValuesBase, _IDPrimaryKeyPublic):
    pass


class RCertSRMValuesCreate(RCertSRMValuesBase, SQLDataFrameInterface):
    dataframe_name = "rcert.srm_values"
    sheet_name = SheetNames.rcert

    @classmethod
    def excel_to_dataframe_transposed(
        cls, excelfile: pd.ExcelFile
    ) -> pd.DataFrame | None:
        return cls._get_optional_frame(
            excelfile,
            usecols="A:B",
            header=None,
            skiprows=skipper(include={47, 48, 49, 52, 53, 54, 55}),
            names=["name", "value"],
        )

    @override
    @classmethod
    def excel_to_dataframe(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        if (df := cls.excel_to_dataframe_transposed(excelfile)) is None:
            return df
        new = cast(
            "pd.DataFrame",
            pd.pivot(df.assign(dummy=0).set_index("dummy"), columns="name")["value"],
        )
        return new.rename_axis(columns=None, index=None)


class RCertSRMValuesUpdate(_RCertForeignKeyUpdate):
    value: float | None = None
    uncert: float | None = None
    uncert_ci95: float | None = None
    uhistorical: Annotated[float | None, BeforeValidator(validate_nan_to_none)] = None

    ls_value: float | None = None
    ls_uncert: float | None = None
    ls_uncert_ci95: float | None = None


# ** Standard Values
class RCertStandardsValuesBase(RCertForeignKey):
    """Rcert.standards_values"""

    model_config = SQLModelConfig(populate_by_name=True)

    primary_standard: int = Field(validation_alias="Primary Standards")
    value: float = Field(validation_alias="Value")
    uncert: float = Field(validation_alias="Uncert (k=2)")
    predicted: float = Field(validation_alias="Predicted")
    predicted_uncert: float = Field(validation_alias="Predicted Uncert (k=2)")


class RCertStandardsValuesPublic(RCertStandardsValuesBase, _IDPrimaryKeyPublic):
    pass


class RCertStandardsValuesCreate(RCertStandardsValuesBase, SQLDataFrameInterface):
    dataframe_name = "rcert.standards_values"
    sheet_name = SheetNames.rcert

    @override
    @classmethod
    def excel_to_dataframe(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        out = cls._get_optional_frame(
            excelfile,
            strip_trailing_numbers=True,
            usecols="A:E",
            skiprows=skipper(lower=58, upper=68),
        )

        if out is not None:
            columns = list(out.columns)
            columns[-1] = "Predicted " + columns[-1]
            out.columns = columns

            out = maybe_dropna(out, how="all", subset=out.columns[1:])

        return out


class RCertStandardsValuesUpdate(_RCertForeignKeyUpdate):
    value: float | None = None
    uncert: float | None = None
    predicted: float | None = None
    predicted_uncert: float | None = None


# ** Additional lot standards
class RCertAdditionalLotStandardsBase(RCertForeignKey):
    model_config = SQLModelConfig(populate_by_name=True)

    name: str = Field(validation_alias="Additional LSs")
    number: int = Field(validation_alias="LS #")

    value: float = Field(validation_alias="Value")
    uncert: float = Field(validation_alias="Uncert")
    uncert_ci95: float = Field(validation_alias="95% CI")  # 95 % confidence interval


class RCertAdditionalLotStandardsPublic(
    RCertAdditionalLotStandardsBase, _IDPrimaryKeyPublic
):
    pass


class RCertAdditionalLotStandardsCreate(
    RCertAdditionalLotStandardsBase, SQLDataFrameInterface
):
    dataframe_name = "rcert.additional_lot_standards"
    sheet_name = SheetNames.rcert

    @override
    @classmethod
    def excel_to_dataframe(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        return cls._get_optional_frame(
            excelfile, usecols="A:E", skiprows=skipper(lower=71, upper=75)
        )


class RCertAdditionalLotStandardsUpdate(_RCertForeignKeyUpdate):
    name: str | None = None
    number: int | None = None
    value: float | None = None
    uncert: float | None = None
    uncert_ci95: float | None = None


# ** Cylinder results
class RCertCylinderResultsBase(RCertForeignKey):
    model_config = SQLModelConfig(alias_generator=to_pascal, populate_by_name=True)

    name: str = Field(validation_alias="Sample")
    value: float
    uncert: float
    uncert_ci95: float = Field(validation_alias="95% CI")


class RCertCylinderResultsPublic(RCertCylinderResultsBase, _IDPrimaryKeyPublic):
    model_config = SQLModelConfig(populate_by_name=True)


class RCertCylinderResultsCreate(RCertCylinderResultsBase, SQLDataFrameInterface):
    dataframe_name = "rcert.cylinder_results"
    sheet_name = SheetNames.rcert

    @override
    @classmethod
    def excel_to_dataframe(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        return cls._get_optional_frame(
            excelfile,
            usecols="M:P",
            skiprows=46,
            strip_trailing_numbers=True,
        )


class RCertCylinderResultsUpdate(_RCertForeignKeyUpdate):
    name: str | None = None
    value: float | None = None
    uncert: float | None = None
    uncert_ci95: float | None = None


# ** Analysis function coefficients
class RCertAnalysisFunctionCoefficientsBase(RCertForeignKey):
    order: int
    value: float
    uncert: float


class RCertAnalysisFunctionCoefficientsPublic(
    RCertAnalysisFunctionCoefficientsBase, _IDPrimaryKeyPublic
):
    pass


class RCertAnalysisFunctionCoefficientsCreate(
    RCertAnalysisFunctionCoefficientsBase, SQLDataFrameInterface
):
    dataframe_name = "rcert.analysis_function_coefficients"
    sheet_name = SheetNames.rcert

    @override
    @classmethod
    def excel_to_dataframe(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        out = maybe_dropna(
            cls._get_optional_frame(
                excelfile,
                usecols="G:H",
                skiprows=skipper(lower=46, upper=50),
                names=["value", "uncert"],
            ),
            how="all",
        )
        if out is not None:
            out = out.assign(order=range(len(out)))
        return out


class RCertAnalysisFunctionCoefficientsUpdate(_RCertForeignKeyUpdate):
    order: int | None = None
    value: float | None = None
    uncert: float | None = None


# ** Correlation coefficients
class RCertCorrelationCoefficientsBase(RCertForeignKey):
    order: int
    order_other: int
    value: float


class RCertCorrelationCoefficientsPublic(
    RCertCorrelationCoefficientsBase, _IDPrimaryKeyPublic
):
    pass


class RCertCorrelationCoefficientsCreate(
    RCertCorrelationCoefficientsBase, SQLDataFrameInterface
):
    dataframe_name = "rcert.correlation_coefficients"
    sheet_name = SheetNames.rcert

    @classmethod
    def excel_to_dataframe_matrix(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        out = cls._get_optional_frame(
            excelfile,
            usecols="G:J",
            skiprows=skipper(lower=52, upper=56),
        )
        out = maybe_dropna(out, how="all")

        if out is not None:
            out = out.assign(order=range(len(out)))

        return maybe_dropna(out, how="all", axis=1)

    @override
    @classmethod
    def excel_to_dataframe(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:

        if (df := cls.excel_to_dataframe_matrix(excelfile)) is None:
            return df

        return pd.melt(
            df.rename(columns=lambda x: x if x == "order" else int(x[1:])),
            id_vars="order",
            var_name="order_other",
        )


class RCertCorrelationCoefficientsUpdate(_RCertForeignKeyUpdate):
    order: int | None = None
    order_other: int | None = None
    value: float | None = None


# ** outliers
class RCertOutliersBase(RCertForeignKey):
    model_config = SQLModelConfig(
        alias_generator=to_pascal,
        populate_by_name=True,
    )
    name: str = Field(validation_alias="SampleID")
    ratio: float
    # TODO(wpk): make this a bool with where test == "OUT"
    test_out: TestOutAnn
    value: float


class RCertOutliersPublic(RCertOutliersBase, _IDPrimaryKeyPublic):
    pass


class RCertOutliersCreate(RCertOutliersBase, SQLDataFrameInterface):
    dataframe_name = "rcert.outliers"
    sheet_name = SheetNames.rcert

    @override
    @classmethod
    def excel_to_dataframe(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        return cls._get_optional_frame(
            excelfile,
            usecols="A:D",
            skiprows=78,
        )


class RCertOutliersUpdate(_RCertForeignKeyUpdate):
    name: str | None = Field(validation_alias="Test", default=None)
    # TODO(wpk): make this a bool with where test == "OUT"
    test_out: TestOutOptionalAnn = None
    ratio: float | None = None
    value: float | None = None


# * "Complete" data
# ** Public
class RCertPublicComplete(RCertPublic):
    srm_values: list[RCertSRMValuesPublic] = []
    standards_values: list[RCertStandardsValuesPublic] = []
    additional_lot_standards: list[RCertAdditionalLotStandardsPublic] = []
    cylinder_results: list[RCertCylinderResultsPublic] = []
    analysis_function_coefficients: list[RCertAnalysisFunctionCoefficientsPublic] = []
    correlation_coefficients: list[RCertCorrelationCoefficientsPublic] = []
    outliers: list[RCertOutliersPublic] = []


class SRMDataPublicComplete(SRMDataPublic):
    ratios: list[RatioDataPublic] = []
    vendors: list[VendorDataPublic] = []
    standards: list[StandardsDataPublic] = []
    past_lot_standards: list[PastLotStandardsDataPublic] = []
    additional_lot_standards: list[AdditionalLotStandardsDataPublic] = []
    ratio_analysis_random_effects: list[RatioAnalysisRandomEffectsDataPublic] = []
    ratio_analysis_fixed_effects: list[RatioAnalysisFixedEffectsDataPublic] = []


class SRMRCertPublicComplete(SRMDataPublicComplete):
    rcert: RCertPublicComplete


# ** Create
class RCertCreateComplete(RCertCreate):
    srm_values: list[RCertSRMValuesCreate] = []
    standards_values: list[RCertStandardsValuesCreate] = []
    additional_lot_standards: list[RCertAdditionalLotStandardsCreate] = []
    cylinder_results: list[RCertCylinderResultsCreate] = []
    analysis_function_coefficients: list[RCertAnalysisFunctionCoefficientsCreate] = []
    correlation_coefficients: list[RCertCorrelationCoefficientsCreate] = []
    outliers: list[RCertOutliersCreate] = []


class SRMDataCreateComplete(SRMDataCreate):
    ratios: list[RatioDataCreate] = []
    vendors: list[VendorDataCreate] = []
    standards: list[StandardsDataCreate] = []
    past_lot_standards: list[PastLotStandardsDataCreate] = []
    additional_lot_standards: list[AdditionalLotStandardsDataCreate] = []
    ratio_analysis_random_effects: list[RatioAnalysisRandomEffectsDataCreate] = []
    ratio_analysis_fixed_effects: list[RatioAnalysisFixedEffectsDataCreate] = []


class SRMRCertCreateComplete(SRMDataCreateComplete):
    rcert: RCertCreateComplete


# create_map = {
#     "ratios": RatioDataCreate,

# }

# * name/getter/cls triples
SRMDATA_NAME_CALLER_MAPPING = {
    name: methodcaller(name if attr is None else attr)
    for name, attr in {
        "ratios": "ratio_data",
        "vendors": "vendor_data",
        "standards": "standards_data",
        "ratio_analysis_random_effects": None,
        "ratio_analysis_fixed_effects": "ratio_analysis_fixed_effects_intercept",
        "past_lot_standards": None,
        "additional_lot_standards": None,
    }.items()
}


RCERTDATA_NAME_CALLER_MAPPING = {
    name: methodcaller(name if attr is None else attr)
    for name, attr in {
        "srm_values": None,
        "standards_values": None,
        "additional_lot_standards": None,
        "cylinder_results": None,
        "analysis_function_coefficients": None,
        "correlation_coefficients": "correlation_coefficients_flat",
        "outliers": None,
    }.items()
}


# * Useful typealiases
SRMSubTableCreate: TypeAlias = (
    RatioDataCreate
    | VendorDataCreate
    | StandardsDataCreate
    | RatioAnalysisRandomEffectsDataCreate
    | RatioAnalysisFixedEffectsDataCreate
    | PastLotStandardsDataCreate
    | AdditionalLotStandardsDataCreate
)

RCertSubTableCreate: TypeAlias = (
    RCertSRMValuesCreate
    | RCertStandardsValuesCreate
    | RCertAdditionalLotStandardsCreate
    | RCertCylinderResultsCreate
    | RCertAnalysisFunctionCoefficientsCreate
    | RCertCorrelationCoefficientsCreate
    | RCertOutliersCreate
)


# class RCertificationDataBase(SRMDataForeignKey):

#     timestamp: datetime = Field
#     srm_value: float
#     srm_uncertainty: float
#     srm_cl_95: float
#     srm_rel_uncert: float
#     srm_effective_k: float
#     ls_value: float
#     ls_uncertainty: float
#     ls_cl_95: float
#     ls_rel_uncert: float


# class _CertifiedDataForeignKey(SQLModel):
#     certified_id: int | None = Field(
#         default=None, foreign_key="certifieddata.id", ondelete="CASCADE",
#     )


# class _CertifiedDataForeignKeyUpdate(SQLModel):
#     certified_id: int | None = None


# class _CertifiedDataBase(_CertifiedDataForeignKey):
#     value: float
#     uncertainty: float
#     confidence_level_95: float

#     # relative_uncertainty <- confidence_level_95 / value
#     # effective k <- confidence_level_95 / uncertainty
