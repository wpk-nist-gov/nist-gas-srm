"""srm models"""
# ruff:file-ignore[commented-out-code]
# pylint: disable=abstract-method

from datetime import UTC, datetime
from typing import (
    Annotated,
    Any,
    Self,
    TypeAlias,
    cast,
)

import pandas as pd
from openpyxl import Workbook
from pydantic import BeforeValidator
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.hybrid import hybrid_property
from sqlmodel import (
    VARCHAR,
    Field,
    SQLModel,
    UniqueConstraint,
)
from sqlmodel._compat import SQLModelConfig  # ruff:ignore[import-private-name]

from nist_gas_srm.core import excel_interface
from nist_gas_srm.core.excel_utils import (
    simple_write_to_excel,
)
from nist_gas_srm.core.typing_compat import override
from nist_gas_srm.core.utils import JSON_PATTERN, SRM_PATTERN
from nist_gas_srm.core.validate import (
    validate_nan_to_none,
    validate_timestamp,
)

from .keys import IDPrimaryKeyPublic, SRMDataForeignKey, SRMDataForeignKeyUpdate
from .utils import (
    LowerString,
    OptionalLowerString,
    to_pascal,
)


class SampleIDAndNumber(SQLModel):
    model_config = SQLModelConfig(populate_by_name=True)

    name: str = Field(index=True, validation_alias="SampleID")
    number: int = Field(validation_alias="SampleNo")


class SampleIDAndNumberUpdate(SQLModel):
    model_config = SQLModelConfig(populate_by_name=True)

    name: str | None = None
    number: int | None = None


class SRMDataBase(SQLModel):
    """Metadata base class"""

    __table_args__ = (
        UniqueConstraint("srm_id", "batch_id", "lot_id", name="unique_user_product"),
    )

    model_config = SQLModelConfig(ignored_types=(hybrid_property,))

    name: str | None = Field(sa_column=Column("name", VARCHAR), default=None)
    note: str | None = Field(sa_column=Column("note", VARCHAR), default=None)
    units: str = "ppm"

    srm_id: int = Field(index=True)
    batch_id: OptionalLowerString
    lot_id: LowerString

    timestamp: Annotated[datetime, BeforeValidator(validate_timestamp)] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(UTC),
    )

    @hybrid_property
    def srm_string_id(self) -> str:
        return f"{self.srm_id}{self.batch_id or ''}{'-' + self.lot_id if self.lot_id else ''}"


class SRMDataPublic(SRMDataBase, IDPrimaryKeyPublic):
    pass


class SRMDataCreate(SRMDataBase):
    pass


class SRMDataUpdate(SQLModel):
    name: str | None = None
    timestamp: datetime | None = None


class SRMDataQuery(SQLModel):
    srm_id: int | None = None
    batch_id: OptionalLowerString = None
    lot_id: OptionalLowerString = None

    @classmethod
    def from_string(cls, string: str) -> Self:
        """
        Match patterns like:

        "{srm_id}{batch_id}-{lot_id}" with batch/lot optional

        or

        '{"srm_id": ...., "batch_id": ..., "lot_id": ...}'

        """

        if (m := JSON_PATTERN.match(string)) is not None:
            return cls.model_validate_json(string)

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
class RatioDataBase(SampleIDAndNumber, SRMDataForeignKey):
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


class RatioDataPublic(RatioDataBase, IDPrimaryKeyPublic):
    pass


class RatioDataCreate(RatioDataBase, excel_interface.SQLDataFrameInterface):
    dataframe_name = "ratios"
    sheet_name = excel_interface.SheetNames.ratio

    @override
    @classmethod
    def excel_to_dataframe(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        return cls._get_frame_with_len_check(
            excelfile,
            usecols="A:G",
            rowx=16,
            colx="L",
        )


class RatioDataUpdate(SampleIDAndNumberUpdate, SRMDataForeignKeyUpdate):
    model_config = SQLModelConfig(
        alias_generator=to_pascal,
        populate_by_name=True,
    )
    ratio: float | None = None
    ls_set: int | None = None
    break_set: int | None = None
    day: int | None = None
    port: int | None = None


# ** Vendor Data --------------------------------------------------------------
class VendorDataBase(SampleIDAndNumber, SRMDataForeignKey):
    """Vendor data"""

    model_config = SQLModelConfig(
        alias_generator=to_pascal,
        populate_by_name=True,
    )

    cylinder_number: str = Field(validation_alias="CylinderNo")
    ratio: float = Field(validation_alias="VendorRatio")


class VendorDataPublic(VendorDataBase, IDPrimaryKeyPublic):
    pass


class VendorDataCreate(VendorDataBase, excel_interface.SQLDataFrameInterface):
    dataframe_name = "vendors"
    sheet_name = excel_interface.SheetNames.vendor

    @override
    @classmethod
    def excel_to_dataframe(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        return cls._get_frame(excelfile, usecols="A:D")


class VendorDataUpdate(SampleIDAndNumberUpdate, SRMDataForeignKeyUpdate):
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


class StandardsDataPublic(StandardsDataBase, IDPrimaryKeyPublic):
    pass


class StandardsDataCreate(StandardsDataBase, excel_interface.SQLDataFrameInterface):
    dataframe_name = "standards"
    sheet_name = excel_interface.SheetNames.standards

    @override
    @classmethod
    def excel_to_dataframe(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        return cls._get_frame_with_len_check(
            excelfile,
            usecols="A:E",
            rowx=1,
            colx="H",
        )

    @override
    @classmethod
    def dataframe_to_excel(cls, obj: pd.DataFrame, workbook: Workbook) -> None:
        super().dataframe_to_excel(obj, workbook)
        cls.dataframe_to_excel_std_analysis(obj, workbook)

    @classmethod
    def dataframe_to_excel_std_analysis(
        cls,
        obj: pd.DataFrame,
        workbook: Workbook,
        sheet_name: str = "Std Analysis",
        alpha: float = 0.05,
    ) -> None:
        import statsmodels.formula.api as smf  # pyright: ignore[reportMissingTypeStubs]
        from statsmodels.stats.api import (  # pyright: ignore[reportMissingTypeStubs]
            anova_lm,  # pyright: ignore[reportUnknownVariableType]
        )

        model = smf.ols(formula="SRatio ~ SConc", data=obj)  # pyright: ignore[reportUnknownMemberType]
        res = model.fit()  # pyright: ignore[reportUnknownMemberType]

        regression_table = pd.DataFrame.from_dict(
            {
                "Multiple R": res.rsquared**0.5,
                "R square": res.rsquared,
                "Adjusted R square": res.rsquared_adj,
                "Standard Error": res.scale**0.5,
                "Observations": res.nobs,
            },
            orient="index",
            columns=["values"],
        )

        worksheet = workbook[sheet_name]

        simple_write_to_excel(
            regression_table,
            worksheet=worksheet,
            start=(13, "B"),
            fill_from=None,
            header=False,
        )

        # anova
        anova_table = cast("pd.DataFrame", anova_lm(res, typ=1))
        simple_write_to_excel(
            anova_table,
            worksheet=worksheet,
            start=(21, "B"),
            fill_from=None,
            header=False,
        )

        # coefficients
        coefficients_table = pd.DataFrame({
            "Coefficients": res.params,
            "Standard Error": res.bse,
            "t Stat": res.tvalues,
            "P-value": res.pvalues,
        })

        coefficients_table[["Lower", "Upper"]] = res.conf_int(alpha)
        simple_write_to_excel(
            coefficients_table,
            worksheet=worksheet,
            start=(26, "B"),
            fill_from=None,
            header=False,
        )

        # residuals
        residuals_table = pd.DataFrame({
            "Observation": range(1, len(obj) + 1),
            "Predicted Y": res.fittedvalues,
            "Residuals": res.resid,
        })
        simple_write_to_excel(
            residuals_table,
            worksheet=worksheet,
            start=(34, "A"),
            fill_from=None,
            header=False,
        )


class StandardsDataUpdate(SampleIDAndNumberUpdate, SRMDataForeignKeyUpdate):
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


class PastLotStandardsDataPublic(PastLotStandardsDataBase, IDPrimaryKeyPublic):
    pass


class PastLotStandardsDataCreate(
    PastLotStandardsDataBase, excel_interface.SQLDataFrameInterface
):
    dataframe_name = "past_lot_standards"
    sheet_name = excel_interface.SheetNames.lot_standards

    @override
    @classmethod
    def excel_to_dataframe(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        return cls._get_frame(
            excelfile,
            strip_trailing_numbers=True,
            usecols="A:F",
            skiprows=1,
        )

    @override
    @classmethod
    def dataframe_to_excel(cls, obj: pd.DataFrame, workbook: Workbook) -> None:
        """Simplest case"""
        simple_write_to_excel(
            obj,
            worksheet=workbook[cls.sheet_name],
            start=(3, 1),
            fill_from=(3, 1),
            header=False,
        )


class PastLotStandardsDataUpdate(SampleIDAndNumberUpdate, SRMDataForeignKeyUpdate):
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
    AdditionalLotStandardsDataBase, IDPrimaryKeyPublic
):
    pass


class AdditionalLotStandardsDataCreate(
    AdditionalLotStandardsDataBase, excel_interface.SQLDataFrameInterface
):
    dataframe_name = "additional_lot_standards"
    sheet_name = excel_interface.SheetNames.lot_standards

    @override
    @classmethod
    def excel_to_dataframe(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        return cls._get_frame(
            excelfile,
            strip_trailing_numbers=True,
            usecols="H:J",
            skiprows=1,
        )

    @override
    @classmethod
    def dataframe_to_excel(cls, obj: pd.DataFrame, workbook: Workbook) -> None:
        """Simplest case"""
        simple_write_to_excel(
            obj,
            worksheet=workbook[cls.sheet_name],
            start=(3, "H"),
            fill_from=(3, "H"),
            header=False,
        )


class AdditionalLotStandardsDataUpdate(
    SampleIDAndNumberUpdate, SRMDataForeignKeyUpdate
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
    RatioAnalysisRandomEffectsDataBase, IDPrimaryKeyPublic
):
    pass


class RatioAnalysisRandomEffectsDataCreate(
    RatioAnalysisRandomEffectsDataBase, excel_interface.SQLDataFrameInterface
):
    dataframe_name = "ratio_analysis_random_effects"
    sheet_name = excel_interface.SheetNames.ratio_analysis

    @override
    @classmethod
    def excel_to_dataframe(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        return cls._get_optional_frame(
            excelfile,
            usecols="X:Y,AA,AC",
            skiprows=1,
            strip_trailing_numbers=True,
        )

    @override
    @classmethod
    def dataframe_to_excel(cls, obj: pd.DataFrame, workbook: Workbook) -> None:
        """Simplest case"""
        if obj.empty:
            return
        start_row = 3
        simple_write_to_excel(
            obj,
            worksheet=workbook[cls.sheet_name],
            start=(start_row, "X"),
            fill_from=None,
            header=False,
            columns=["X", "Y", "AA", "AC"],
        )

        # # insert formulas
        # column_variance = validate_column("Z")
        # column_relative = validate_column("AB")
        # norm = f"SUM($Z${start_row}:$Z${start_row + len(obj) - 1})"
        # for row in range(start_row, len(obj) + start_row):
        #     cell = worksheet.cell(row=row, column=column_variance)
        #     cell.value = f"=AA{row}^2"

        #     cell = worksheet.cell(row=row, column=column_relative)
        #     cell.value = f"=Z{row} / {norm}"


class RatioAnalysisRandomEffectsDataUpdate(SRMDataForeignKeyUpdate):
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
    RatioAnalysisFixedEffectsDataBase, IDPrimaryKeyPublic
):
    pass


class RatioAnalysisFixedEffectsDataCreate(
    RatioAnalysisFixedEffectsDataBase, excel_interface.SQLDataFrameInterface
):
    dataframe_name = "ratio_analysis_fixed_effects"
    sheet_name = excel_interface.SheetNames.ratio_analysis

    @override
    @classmethod
    def excel_to_dataframe(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        return cls._get_optional_frame(
            excelfile,
            usecols="AD:AF",
            skiprows=1,
            strip_trailing_numbers=True,
        )

    @override
    @classmethod
    def dataframe_to_excel(cls, obj: pd.DataFrame, workbook: Workbook) -> None:
        """Simplest case"""
        simple_write_to_excel(
            obj,
            worksheet=workbook[cls.sheet_name],
            start=(3, "AD"),
            fill_from=None,
            header=False,
        )


class RatioAnalysisFixedEffectsDataUpdate(SRMDataForeignKeyUpdate):
    estimate: float | None
    stderr: float | None
    t_value: float | None


SRMSubTableCreate: TypeAlias = (
    RatioDataCreate
    | VendorDataCreate
    | StandardsDataCreate
    | RatioAnalysisRandomEffectsDataCreate
    | RatioAnalysisFixedEffectsDataCreate
    | PastLotStandardsDataCreate
    | AdditionalLotStandardsDataCreate
)


# * Complete
class CompletePublic(SRMDataPublic):
    ratios: list[RatioDataPublic] = []
    vendors: list[VendorDataPublic] = []
    standards: list[StandardsDataPublic] = []
    past_lot_standards: list[PastLotStandardsDataPublic] = []
    additional_lot_standards: list[AdditionalLotStandardsDataPublic] = []
    ratio_analysis_random_effects: list[RatioAnalysisRandomEffectsDataPublic] = []
    ratio_analysis_fixed_effects: list[RatioAnalysisFixedEffectsDataPublic] = []


class CompleteCreate(SRMDataCreate):
    ratios: list[RatioDataCreate] = []
    vendors: list[VendorDataCreate] = []
    standards: list[StandardsDataCreate] = []
    past_lot_standards: list[PastLotStandardsDataCreate] = []
    additional_lot_standards: list[AdditionalLotStandardsDataCreate] = []
    ratio_analysis_random_effects: list[RatioAnalysisRandomEffectsDataCreate] = []
    ratio_analysis_fixed_effects: list[RatioAnalysisFixedEffectsDataCreate] = []
