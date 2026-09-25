# ruff:file-ignore[commented-out-code]

import uuid
from typing import (
    Annotated,
    TypeAlias,
    cast,
)

import pandas as pd
from openpyxl import Workbook
from pydantic import BeforeValidator
from sqlmodel import (
    Field,
    SQLModel,
)
from sqlmodel._compat import SQLModelConfig  # ruff:ignore[import-private-name]

from nist_gas_srm.core import excel_interface
from nist_gas_srm.core.excel_utils import (
    simple_write_to_excel,
)
from nist_gas_srm.core.typing_compat import override
from nist_gas_srm.core.validate import (
    validate_nan_to_none,
)

from .keys import (
    IDPrimaryKeyPublic,
    SRMForeignKey,
    SRMForeignKeyUpdate,
)
from .utils import (
    to_pascal,
)


# * Keys
class MeasurementsForeignKey(SQLModel):
    measurements_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        nullable=False,
        foreign_key="measurements.id",
        ondelete="CASCADE",
    )


class _MeasurementsForeignKeyUpdate(SQLModel):
    pass


# root table
class MeasurementsBase(SRMForeignKey, SQLModel):
    pass


class MeasurementsPublic(MeasurementsBase, IDPrimaryKeyPublic):
    pass


class MeasurementsCreate(MeasurementsBase):
    pass


class MeasurementsUpdate(SRMForeignKeyUpdate):
    pass


# * Subtables -----------------------------------------------------------------
# ** Utils
class SampleIDAndNumber(SQLModel):
    model_config = SQLModelConfig(populate_by_name=True)

    name: str = Field(index=True, validation_alias="SampleID")
    number: int = Field(validation_alias="SampleNo")


class SampleIDAndNumberUpdate(SQLModel):
    model_config = SQLModelConfig(populate_by_name=True)

    name: str | None = None
    number: int | None = None


# ** Ratio Data
class MeasurementsRatiosBase(SampleIDAndNumber, MeasurementsForeignKey):
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


class MeasurementsRatiosPublic(MeasurementsRatiosBase, IDPrimaryKeyPublic):
    pass


class MeasurementsRatiosCreate(
    MeasurementsRatiosBase, excel_interface.SQLDataFrameInterface
):
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


class MeasurementsRatiosUpdate(SampleIDAndNumberUpdate, _MeasurementsForeignKeyUpdate):
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
class MeasurementsVendorsBase(SampleIDAndNumber, MeasurementsForeignKey):
    """Vendor data"""

    model_config = SQLModelConfig(
        alias_generator=to_pascal,
        populate_by_name=True,
    )

    cylinder_number: str = Field(validation_alias="CylinderNo")
    ratio: float = Field(validation_alias="VendorRatio")


class MeasurementsVendorsPublic(MeasurementsVendorsBase, IDPrimaryKeyPublic):
    pass


class MeasurementsVendorsCreate(
    MeasurementsVendorsBase, excel_interface.SQLDataFrameInterface
):
    dataframe_name = "vendors"
    sheet_name = excel_interface.SheetNames.vendor

    @override
    @classmethod
    def excel_to_dataframe(cls, excelfile: pd.ExcelFile) -> pd.DataFrame | None:
        return cls._get_frame(excelfile, usecols="A:D")


class MeasurementsVendorsUpdate(SampleIDAndNumberUpdate, _MeasurementsForeignKeyUpdate):
    cylinder_number: str | None = None
    ratio: float | None = None


# ** Standards Data -----------------------------------------------------------
class MeasurementsStandardsBase(MeasurementsForeignKey):
    """Standards Data"""

    model_config = SQLModelConfig(populate_by_name=True)

    name: str = Field(validation_alias="StandardID")
    number: int = Field(validation_alias="StandardNo")
    ratio: float = Field(validation_alias="SRatio")
    concentration: float = Field(validation_alias="SConc")
    uncert: float = Field(validation_alias="Sunc")


class MeasurementsStandardsPublic(MeasurementsStandardsBase, IDPrimaryKeyPublic):
    pass


class MeasurementsStandardsCreate(
    MeasurementsStandardsBase, excel_interface.SQLDataFrameInterface
):
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


class MeasurementsStandardsUpdate(
    SampleIDAndNumberUpdate, _MeasurementsForeignKeyUpdate
):
    name: str | None = None
    number: int | None = None
    ratio: float | None = None
    concentration: float | None = None
    uncert: float | None = None


# ** Past lot standards -------------------------------------------------------
class MeasurementsPastLotStandardsBase(MeasurementsForeignKey):
    """Past lot standards"""

    model_config = SQLModelConfig(populate_by_name=True)
    name: str = Field(validation_alias="LS ID")
    number: int = Field(validation_alias="LS#")
    ratio: float = Field(validation_alias="Ratio")
    value: float = Field(validation_alias="Past Conc")


class MeasurementsPastLotStandardsPublic(
    MeasurementsPastLotStandardsBase, IDPrimaryKeyPublic
):
    pass


class MeasurementsPastLotStandardsCreate(
    MeasurementsPastLotStandardsBase, excel_interface.SQLDataFrameInterface
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


class MeasurementsPastLotStandardsUpdate(
    SampleIDAndNumberUpdate, _MeasurementsForeignKeyUpdate
):
    name: str | None = None
    number: int | None = None
    ratio: float | None = None
    past_conc: float | None = None
    pred_conc: float | None = None


# ** Additional lot standards -------------------------------------------------
class MeasurementsAdditionalLotStandardsBase(MeasurementsForeignKey):
    """MeasurementsAdditionalLotStandards"""

    model_config = SQLModelConfig(populate_by_name=True)
    name: str = Field(validation_alias="ID")
    number: int = Field(validation_alias="LS#")
    ratio: float = Field(validation_alias="Ratio")


class MeasurementsAdditionalLotStandardsPublic(
    MeasurementsAdditionalLotStandardsBase, IDPrimaryKeyPublic
):
    pass


class MeasurementsAdditionalLotStandardsCreate(
    MeasurementsAdditionalLotStandardsBase, excel_interface.SQLDataFrameInterface
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


class MeasurementsAdditionalLotStandardsUpdate(
    SampleIDAndNumberUpdate, _MeasurementsForeignKeyUpdate
):
    name: str | None = None
    number: int | None = None
    ratio: float | None = None


# ** Ratio Analysis -----------------------------------------------------------
class MeasurementsRatioAnalysisRandomEffectsBase(MeasurementsForeignKey):
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


class MeasurementsRatioAnalysisRandomEffectsPublic(
    MeasurementsRatioAnalysisRandomEffectsBase, IDPrimaryKeyPublic
):
    pass


class MeasurementsRatioAnalysisRandomEffectsCreate(
    MeasurementsRatioAnalysisRandomEffectsBase, excel_interface.SQLDataFrameInterface
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


class MeasurementsRatioAnalysisRandomEffectsUpdate(_MeasurementsForeignKeyUpdate):
    groups: str | None
    name: str | None
    stddev: float | None
    count: int | None


class MeasurementsRatioAnalysisFixedEffectsBase(MeasurementsForeignKey):
    model_config = SQLModelConfig(
        alias_generator=to_pascal,
        populate_by_name=True,
    )

    estimate: float
    stderr: float = Field(validation_alias="Std Error")
    t_value: float = Field(validation_alias="t value")


class MeasurementsRatioAnalysisFixedEffectsPublic(
    MeasurementsRatioAnalysisFixedEffectsBase, IDPrimaryKeyPublic
):
    pass


class MeasurementsRatioAnalysisFixedEffectsCreate(
    MeasurementsRatioAnalysisFixedEffectsBase, excel_interface.SQLDataFrameInterface
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


class MeasurementsRatioAnalysisFixedEffectsUpdate(_MeasurementsForeignKeyUpdate):
    estimate: float | None
    stderr: float | None
    t_value: float | None


MeasurementsSubTableCreateType: TypeAlias = (
    MeasurementsRatiosCreate
    | MeasurementsVendorsCreate
    | MeasurementsStandardsCreate
    | MeasurementsRatioAnalysisRandomEffectsCreate
    | MeasurementsRatioAnalysisFixedEffectsCreate
    | MeasurementsPastLotStandardsCreate
    | MeasurementsAdditionalLotStandardsCreate
)


# * Complete ------------------------------------------------------------------
class MeasurementsCompletePublic(MeasurementsPublic):
    ratios: list[MeasurementsRatiosPublic] = []
    vendors: list[MeasurementsVendorsPublic] = []
    standards: list[MeasurementsStandardsPublic] = []
    past_lot_standards: list[MeasurementsPastLotStandardsPublic] = []
    additional_lot_standards: list[MeasurementsAdditionalLotStandardsPublic] = []
    ratio_analysis_random_effects: list[
        MeasurementsRatioAnalysisRandomEffectsPublic
    ] = []
    ratio_analysis_fixed_effects: list[MeasurementsRatioAnalysisFixedEffectsPublic] = []


class MeasurementsCompleteCreate(MeasurementsCreate):
    ratios: list[MeasurementsRatiosCreate] = []
    vendors: list[MeasurementsVendorsCreate] = []
    standards: list[MeasurementsStandardsCreate] = []
    past_lot_standards: list[MeasurementsPastLotStandardsCreate] = []
    additional_lot_standards: list[MeasurementsAdditionalLotStandardsCreate] = []
    ratio_analysis_random_effects: list[
        MeasurementsRatioAnalysisRandomEffectsCreate
    ] = []
    ratio_analysis_fixed_effects: list[MeasurementsRatioAnalysisFixedEffectsCreate] = []
