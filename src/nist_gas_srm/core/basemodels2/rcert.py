"""RCertification model"""
# ruff:file-ignore[commented-out-code,missing-todo-link,line-contains-todo]
# pylint: disable=abstract-method

import uuid
from typing import Annotated, TypeAlias, cast

import pandas as pd
from openpyxl import Workbook
from pydantic import BeforeValidator
from sqlmodel import (
    Field,
    SQLModel,
)
from sqlmodel._compat import SQLModelConfig  # ruff:ignore[import-private-name]

from nist_gas_srm.core.excel_interface import SheetNames, SQLDataFrameInterface
from nist_gas_srm.core.excel_utils import (
    maybe_dropna,
    simple_write_to_excel,
    skipper,
)
from nist_gas_srm.core.typing_compat import override
from nist_gas_srm.core.validate import (
    validate_nan_to_none,
)

from .keys import (
    IDPrimaryKeyPublic,
    SRMDataForeignKey,
    SRMDataForeignKeyUpdate,
)
from .utils import (
    TestOutAnn,
    TestOutOptionalAnn,
    to_pascal,
)


# * RCertification -----------------------------------------------------------
class RCertForeignKey(SQLModel):
    rcert_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        nullable=False,
        foreign_key="rcert_root.id",
        ondelete="CASCADE",
    )


class _RCertForeignKeyUpdate(SQLModel):
    # rcert_id: uuid.UUID
    pass


# ** RCert
# NOTE(wpk): include SQLModel here to make linter happy
class RCertBase(SRMDataForeignKey, SQLModel):
    """Points back to srm_root"""


class RCertPublic(RCertBase, IDPrimaryKeyPublic):
    pass


class RCertCreate(RCertBase):
    pass


class RCertUpdate(SRMDataForeignKeyUpdate):
    pass


# ** SRMValues
# Each of these point back to rcert
class SRMValuesBase(RCertForeignKey):
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


class SRMValuesPublic(SRMValuesBase, IDPrimaryKeyPublic):
    pass


class SRMValuesCreate(SRMValuesBase, SQLDataFrameInterface):
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

    @override
    @classmethod
    def dataframe_to_excel(cls, obj: pd.DataFrame, workbook: Workbook) -> None:
        """Simplest case"""
        if obj.empty:
            return
        keys = [k for k in cls.colnames_to_dbnames() if k != "rcert_id"]
        df = obj[keys].T.reset_index()
        simple_write_to_excel(
            df,
            worksheet=workbook[cls.sheet_name],
            start=(48, "A"),
            fill_from=(48, "A"),
            header=False,
            rows=[48, 49, 50, 53, 54, 55, 56],
        )


class SRMValuesUpdate(_RCertForeignKeyUpdate):
    value: float | None = None
    uncert: float | None = None
    uncert_ci95: float | None = None
    uhistorical: Annotated[float | None, BeforeValidator(validate_nan_to_none)] = None

    ls_value: float | None = None
    ls_uncert: float | None = None
    ls_uncert_ci95: float | None = None


# ** Standard Values
class StandardsValuesBase(RCertForeignKey):
    """Rcert.standards_values"""

    model_config = SQLModelConfig(populate_by_name=True)

    primary_standard: int = Field(validation_alias="Primary Standards")
    value: float = Field(validation_alias="Value")
    uncert: float = Field(validation_alias="Uncert (k=2)")
    predicted: float = Field(validation_alias="Predicted")
    predicted_uncert: float = Field(validation_alias="Predicted Uncert (k=2)")


class StandardsValuesPublic(StandardsValuesBase, IDPrimaryKeyPublic):
    pass


class StandardsValuesCreate(StandardsValuesBase, SQLDataFrameInterface):
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

    @override
    @classmethod
    def dataframe_to_excel(cls, obj: pd.DataFrame, workbook: Workbook) -> None:
        """Simplest case"""
        simple_write_to_excel(
            obj,
            worksheet=workbook[cls.sheet_name],
            start=(60, "A"),
            fill_from=(60, "B"),
            header=False,
        )


class StandardsValuesUpdate(_RCertForeignKeyUpdate):
    value: float | None = None
    uncert: float | None = None
    predicted: float | None = None
    predicted_uncert: float | None = None


# ** Additional lot standards
class AdditionalLotStandardsBase(RCertForeignKey):
    model_config = SQLModelConfig(populate_by_name=True)

    name: str = Field(validation_alias="Additional LSs")
    number: int = Field(validation_alias="LS #")

    value: float = Field(validation_alias="Value")
    uncert: float = Field(validation_alias="Uncert")
    uncert_ci95: float = Field(validation_alias="95% CI")  # 95 % confidence interval


class AdditionalLotStandardsPublic(AdditionalLotStandardsBase, IDPrimaryKeyPublic):
    pass


class AdditionalLotStandardsCreate(AdditionalLotStandardsBase, SQLDataFrameInterface):
    dataframe_name = "rcert.additional_lot_standards"
    sheet_name = SheetNames.rcert

    @override
    @classmethod
    def excel_to_dataframe(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        return cls._get_optional_frame(
            excelfile, usecols="A:E", skiprows=skipper(lower=71, upper=75)
        )

    @override
    @classmethod
    def dataframe_to_excel(cls, obj: pd.DataFrame, workbook: Workbook) -> None:
        """Simplest case"""
        simple_write_to_excel(
            obj,
            worksheet=workbook[cls.sheet_name],
            start=(73, "A"),
            fill_from=(73, "B"),
            header=False,
        )


class AdditionalLotStandardsUpdate(_RCertForeignKeyUpdate):
    name: str | None = None
    number: int | None = None
    value: float | None = None
    uncert: float | None = None
    uncert_ci95: float | None = None


# ** Cylinder results
class CylinderResultsBase(RCertForeignKey):
    model_config = SQLModelConfig(alias_generator=to_pascal, populate_by_name=True)

    name: str = Field(validation_alias="Sample")
    value: float
    uncert: float
    uncert_ci95: float = Field(validation_alias="95% CI")


class CylinderResultsPublic(CylinderResultsBase, IDPrimaryKeyPublic):
    model_config = SQLModelConfig(populate_by_name=True)


class CylinderResultsCreate(CylinderResultsBase, SQLDataFrameInterface):
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

    @override
    @classmethod
    def dataframe_to_excel(cls, obj: pd.DataFrame, workbook: Workbook) -> None:
        """Simplest case"""
        simple_write_to_excel(
            obj,
            worksheet=workbook[cls.sheet_name],
            start=(48, "M"),
            fill_from=(47, "M"),
            header=False,
            extra_fill_columns=["Q", "R", "S", "T", "U"],
        )


class CylinderResultsUpdate(_RCertForeignKeyUpdate):
    name: str | None = None
    value: float | None = None
    uncert: float | None = None
    uncert_ci95: float | None = None


# ** Analysis function coefficients
class AnalysisFunctionCoefficientsBase(RCertForeignKey):
    order: int
    value: float
    uncert: float


class AnalysisFunctionCoefficientsPublic(
    AnalysisFunctionCoefficientsBase, IDPrimaryKeyPublic
):
    pass


class AnalysisFunctionCoefficientsCreate(
    AnalysisFunctionCoefficientsBase, SQLDataFrameInterface
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

    @override
    @classmethod
    def dataframe_to_excel(cls, obj: pd.DataFrame, workbook: Workbook) -> None:
        """Simplest case"""
        simple_write_to_excel(
            obj.drop("order", axis=1),
            worksheet=workbook[cls.sheet_name],
            start=(48, "G"),
            fill_from=(48, "G"),
            header=False,
        )


class AnalysisFunctionCoefficientsUpdate(_RCertForeignKeyUpdate):
    order: int | None = None
    value: float | None = None
    uncert: float | None = None


# ** Correlation coefficients
class CorrelationCoefficientsBase(RCertForeignKey):
    order: int
    order_other: int
    value: float


class CorrelationCoefficientsPublic(CorrelationCoefficientsBase, IDPrimaryKeyPublic):
    pass


class CorrelationCoefficientsCreate(CorrelationCoefficientsBase, SQLDataFrameInterface):
    dataframe_name = "rcert.correlation_coefficients"
    sheet_name = SheetNames.rcert

    @classmethod
    def excel_to_dataframe_matrix(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        out = cls._get_optional_frame(
            excelfile,
            usecols="G:J",
            skiprows=skipper(lower=52, upper=56),
        )

        if (out := maybe_dropna(out, how="all")) is not None:
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

    @override
    @classmethod
    def dataframe_to_excel(cls, obj: pd.DataFrame, workbook: Workbook) -> None:
        """Simplest case"""
        df = pd.pivot(obj, index="order", columns="order_other")
        simple_write_to_excel(
            df,
            worksheet=workbook[cls.sheet_name],
            start=(54, "G"),
            fill_from=(54, "G"),
            header=False,
        )


class CorrelationCoefficientsUpdate(_RCertForeignKeyUpdate):
    order: int | None = None
    order_other: int | None = None
    value: float | None = None


# ** outliers
class OutliersBase(RCertForeignKey):
    model_config = SQLModelConfig(
        alias_generator=to_pascal,
        populate_by_name=True,
    )
    name: str = Field(validation_alias="SampleID")
    ratio: float
    # TODO(wpk): make this a bool with where test == "OUT"
    test_out: TestOutAnn
    value: float


class OutliersPublic(OutliersBase, IDPrimaryKeyPublic):
    pass


class OutliersCreate(OutliersBase, SQLDataFrameInterface):
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

    @override
    @classmethod
    def dataframe_to_excel(cls, obj: pd.DataFrame, workbook: Workbook) -> None:
        """Simplest case"""
        simple_write_to_excel(
            obj,
            worksheet=workbook[cls.sheet_name],
            start=(80, "A"),
            fill_from=(80, "A"),
            header=False,
        )


class OutliersUpdate(_RCertForeignKeyUpdate):
    name: str | None = Field(validation_alias="Test", default=None)
    # TODO(wpk): make this a bool with where test == "OUT"
    test_out: TestOutOptionalAnn = None
    ratio: float | None = None
    value: float | None = None


RCertSubTableCreate: TypeAlias = (
    SRMValuesCreate
    | StandardsValuesCreate
    | AdditionalLotStandardsCreate
    | CylinderResultsCreate
    | AnalysisFunctionCoefficientsCreate
    | CorrelationCoefficientsCreate
    | OutliersCreate
)


# * Complete
class CompletePublic(RCertPublic):
    srm_values: list[SRMValuesPublic] = []
    standards_values: list[StandardsValuesPublic] = []
    additional_lot_standards: list[AdditionalLotStandardsPublic] = []
    cylinder_results: list[CylinderResultsPublic] = []
    analysis_function_coefficients: list[AnalysisFunctionCoefficientsPublic] = []
    correlation_coefficients: list[CorrelationCoefficientsPublic] = []
    outliers: list[OutliersPublic] = []


class CompleteCreate(RCertCreate):
    srm_values: list[SRMValuesCreate] = []
    standards_values: list[StandardsValuesCreate] = []
    additional_lot_standards: list[AdditionalLotStandardsCreate] = []
    cylinder_results: list[CylinderResultsCreate] = []
    analysis_function_coefficients: list[AnalysisFunctionCoefficientsCreate] = []
    correlation_coefficients: list[CorrelationCoefficientsCreate] = []
    outliers: list[OutliersCreate] = []
