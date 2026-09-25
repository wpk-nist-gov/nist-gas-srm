"""Basic model"""

import logging
from typing import TYPE_CHECKING, Any, TypeAlias, cast

from pydantic import model_validator
from sqlmodel import (
    Relationship,
    SQLModel,
    select,
)
from sqlmodel._compat import (  # ruff: ignore[import-private-name]
    SQLModelConfig,
    get_relationship_to,
)
from sqlmodel.sql._expression_select_cls import Select, SelectOfScalar

from nist_gas_srm.core.basemodels import (
    AdditionalLotStandardsDataBase,
    IDPrimaryKey,
    PastLotStandardsDataBase,
    RatioAnalysisFixedEffectsDataBase,
    RatioAnalysisRandomEffectsDataBase,
    RatioDataBase,
    RCertAdditionalLotStandardsBase,
    RCertAnalysisFunctionCoefficientsBase,
    RCertBase,
    RCertCorrelationCoefficientsBase,
    RCertCylinderResultsBase,
    RCertOutliersBase,
    RCertSRMValuesBase,
    RCertStandardsValuesBase,
    SRMDataBase,
    StandardAnalysisBase,
    StandardAnalysisGenLineEvalBase,
    StandardAnalysisGenLineParamsBase,
    StandardAnalysisGenLineSolutionBase,
    StandardAnalysisParamsBase,
    StandardsDataBase,
    VendorDataBase,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import declared_attr


FORMAT = "[%(name)s - %(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)


# Sql Models ------------------------------------------------------------------
class _FixMixin(SQLModel):
    # see https://github.com/fastapi/sqlmodel/issues/293
    @model_validator(mode="before")
    @classmethod
    def convert_relationships(cls, model: Any) -> Any:
        for rel_name, rel_info in cls.__sqlmodel_relationships__.items():
            if (attr := getattr(model, rel_name, None)) is None:
                continue

            # use sqlmodel internal function to get class
            ann = cls.__annotations__[rel_name].__args__[0]
            rel_class_name = get_relationship_to(
                name=rel_name, rel_info=rel_info, annotation=ann
            )

            # might be type or string depending on how it was declared
            rel_class: Any = (
                rel_class_name
                if isinstance(rel_class_name, type)
                else globals()[rel_class_name]
            )

            # convert attribute(s) with their model's validator
            items: Any
            if isinstance(attr, list):
                items = [rel_class.model_validate(item) for item in attr]  # pyright: ignore[reportUnknownVariableType]
                setattr(model, rel_name, items)
            else:
                item = rel_class.model_validate(attr)
                setattr(model, rel_name, item)

        return model


class SRMData(SRMDataBase, IDPrimaryKey, _FixMixin, table=True):
    """Metadata table"""

    model_config = SQLModelConfig(str_to_lower=True)

    ratios: list["RatioData"] = Relationship(
        back_populates="srmdata", cascade_delete=True
    )
    vendors: list["VendorData"] = Relationship(
        back_populates="srmdata", cascade_delete=True
    )
    standards: list["StandardsData"] = Relationship(
        back_populates="srmdata", cascade_delete=True
    )
    past_lot_standards: list["PastLotStandardsData"] = Relationship(
        back_populates="srmdata",
        cascade_delete=True,
    )
    additional_lot_standards: list["AdditionalLotStandardsData"] = Relationship(
        back_populates="srmdata",
        cascade_delete=True,
    )
    ratio_analysis_random_effects: list["RatioAnalysisRandomEffectsData"] = (
        Relationship(
            back_populates="srmdata",
            cascade_delete=True,
        )
    )
    ratio_analysis_fixed_effects: list["RatioAnalysisFixedEffectsData"] = Relationship(
        back_populates="srmdata",
        cascade_delete=True,
    )

    rcert: "RCertData" = Relationship(back_populates="srmdata", cascade_delete=True)

    standard_analysis: "StandardAnalysisData" = Relationship(
        back_populates="srmdata", cascade_delete=True
    )


# * subtables
class RatioData(RatioDataBase, IDPrimaryKey, table=True):
    """Ratio Data table"""

    __tablename__ = cast("declared_attr[str]", "srm_ratios")

    srmdata: SRMData | None = Relationship(back_populates="ratios")


class RatioAnalysisRandomEffectsData(
    RatioAnalysisRandomEffectsDataBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "srm_ratio_analysis_random_effects")

    srmdata: SRMData | None = Relationship(
        back_populates="ratio_analysis_random_effects"
    )


class RatioAnalysisFixedEffectsData(
    RatioAnalysisFixedEffectsDataBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "srm_ratio_analysis_fixed_effects")
    srmdata: SRMData | None = Relationship(
        back_populates="ratio_analysis_fixed_effects"
    )


class VendorData(VendorDataBase, IDPrimaryKey, table=True):
    """Vendor data table"""

    __tablename__ = cast("declared_attr[str]", "srm_vendors")

    srmdata: SRMData | None = Relationship(back_populates="vendors")


class StandardsData(StandardsDataBase, IDPrimaryKey, table=True):
    """Standards data table"""

    __tablename__ = cast("declared_attr[str]", "srm_standards")

    srmdata: SRMData | None = Relationship(back_populates="standards")


class PastLotStandardsData(PastLotStandardsDataBase, IDPrimaryKey, table=True):
    """Past lot standards table"""

    __tablename__ = cast("declared_attr[str]", "srm_past_lot_standards")

    srmdata: SRMData | None = Relationship(back_populates="past_lot_standards")


class AdditionalLotStandardsData(
    AdditionalLotStandardsDataBase, IDPrimaryKey, table=True
):
    """Additional lot standards table"""

    __tablename__ = cast("declared_attr[str]", "srm_additional_lot_standards")

    srmdata: SRMData | None = Relationship(back_populates="additional_lot_standards")


# * Standard analysis
class StandardAnalysisData(StandardAnalysisBase, IDPrimaryKey, _FixMixin, table=True):
    """Standard analysis data"""

    __tablename__ = cast("declared_attr[str]", "standard_analysis_data")

    model_config = SQLModelConfig(str_to_lower=True)
    srmdata: SRMData | None = Relationship(back_populates="standard_analysis")

    params: list["StandardAnalysisParamsData"] = Relationship(
        back_populates="standard_analysis_data",
        cascade_delete=True,
    )
    genline_params: list["StandardAnalysisGenLineParamsData"] = Relationship(
        back_populates="standard_analysis_data",
        cascade_delete=True,
    )
    genline_solution: list["StandardAnalysisGenLineSolutionData"] = Relationship(
        back_populates="standard_analysis_data",
        cascade_delete=True,
    )

    genline_eval: list["StandardAnalysisGenLineEvalData"] = Relationship(
        back_populates="standard_analysis_data",
        cascade_delete=True,
    )


class StandardAnalysisParamsData(StandardAnalysisParamsBase, IDPrimaryKey, table=True):
    __tablename__ = cast("declared_attr[str]", "standard_analysis_params")
    standard_analysis_data: StandardAnalysisData | None = Relationship(
        back_populates="params"
    )


class StandardAnalysisGenLineParamsData(
    StandardAnalysisGenLineParamsBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "standard_analysis_genline_params")
    standard_analysis_data: StandardAnalysisData | None = Relationship(
        back_populates="genline_params"
    )


class StandardAnalysisGenLineSolutionData(
    StandardAnalysisGenLineSolutionBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "standard_analysis_genline_solution")
    standard_analysis_data: StandardAnalysisData | None = Relationship(
        back_populates="genline_solution"
    )


class StandardAnalysisGenLineEvalData(
    StandardAnalysisGenLineEvalBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "standard_analysis_genline_eval")
    standard_analysis_data: StandardAnalysisData | None = Relationship(
        back_populates="genline_eval"
    )


# * RCert
class RCertData(RCertBase, IDPrimaryKey, _FixMixin, table=True):
    """R Certified values"""

    model_config = SQLModelConfig(str_to_lower=True)

    srmdata: SRMData | None = Relationship(back_populates="rcert")

    srm_values: list["RCertSRMValues"] = Relationship(
        back_populates="rcertdata", cascade_delete=True
    )
    standards_values: list["RCertStandardsValues"] = Relationship(
        back_populates="rcertdata", cascade_delete=True
    )
    additional_lot_standards: list["RCertAdditionalLotStandards"] = Relationship(
        back_populates="rcertdata", cascade_delete=True
    )
    cylinder_results: list["RCertCylinderResults"] = Relationship(
        back_populates="rcertdata", cascade_delete=True
    )
    analysis_function_coefficients: list["RCertAnalysisFunctionCoefficients"] = (
        Relationship(back_populates="rcertdata", cascade_delete=True)
    )
    correlation_coefficients: list["RCertCorrelationCoefficients"] = Relationship(
        back_populates="rcertdata", cascade_delete=True
    )
    outliers: list["RCertOutliers"] = Relationship(
        back_populates="rcertdata", cascade_delete=True
    )


class RCertSRMValues(RCertSRMValuesBase, IDPrimaryKey, table=True):
    __tablename__ = cast("declared_attr[str]", "rcert_srm_values")

    rcertdata: RCertData | None = Relationship(back_populates="srm_values")


class RCertStandardsValues(RCertStandardsValuesBase, IDPrimaryKey, table=True):
    __tablename__ = cast("declared_attr[str]", "rcert_standards_values")
    rcertdata: RCertData | None = Relationship(back_populates="standards_values")


class RCertAdditionalLotStandards(
    RCertAdditionalLotStandardsBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "rcert_additional_lot_standards")

    rcertdata: RCertData | None = Relationship(
        back_populates="additional_lot_standards"
    )


class RCertCylinderResults(RCertCylinderResultsBase, IDPrimaryKey, table=True):
    __tablename__ = cast("declared_attr[str]", "rcert_cylinder_results")
    rcertdata: RCertData | None = Relationship(back_populates="cylinder_results")


class RCertAnalysisFunctionCoefficients(
    RCertAnalysisFunctionCoefficientsBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "rcert_analysis_function_coefficients")
    rcertdata: RCertData | None = Relationship(
        back_populates="analysis_function_coefficients"
    )


class RCertCorrelationCoefficients(
    RCertCorrelationCoefficientsBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "rcert_correlation_coefficients")
    rcertdata: RCertData | None = Relationship(
        back_populates="correlation_coefficients"
    )


class RCertOutliers(RCertOutliersBase, IDPrimaryKey, table=True):
    __tablename__ = cast("declared_attr[str]", "rcert_outliers")
    rcertdata: RCertData | None = Relationship(back_populates="outliers")


# Useful type aliases
SRMSubTable: TypeAlias = (
    RatioData
    | VendorData
    | StandardsData
    | RatioAnalysisRandomEffectsData
    | RatioAnalysisFixedEffectsData
    | PastLotStandardsData
    | AdditionalLotStandardsData
)

StandardAnalysisSubTable: TypeAlias = (
    StandardAnalysisParamsData
    | StandardAnalysisGenLineParamsData
    | StandardAnalysisGenLineSolutionData
    | StandardAnalysisGenLineEvalData
)

RCertSubTable: TypeAlias = (
    RCertSRMValues
    | RCertStandardsValues
    | RCertAdditionalLotStandards
    | RCertCylinderResults
    | RCertAnalysisFunctionCoefficients
    | RCertCorrelationCoefficients
    | RCertOutliers
)


# * Utils ---------------------------------------------------------------------
def select_columns(*columns: Any) -> Select[Any] | SelectOfScalar[Any]:
    """For typing purposes"""
    return cast("Select[Any] | SelectOfScalar[Any]", select(*columns))
