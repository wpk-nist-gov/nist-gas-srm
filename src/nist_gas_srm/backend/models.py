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

from nist_gas_srm.core import basemodels
from nist_gas_srm.core.basemodels.keys import IDPrimaryKey

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


class SRMData(basemodels.srm.SRMDataBase, IDPrimaryKey, _FixMixin, table=True):
    """Metadata table"""

    __tablename__ = cast("declared_attr[str]", "srm_root")

    model_config = SQLModelConfig(str_to_lower=True)

    ratios: list["RatioData"] = Relationship(
        back_populates="srm_root", cascade_delete=True
    )
    vendors: list["VendorData"] = Relationship(
        back_populates="srm_root", cascade_delete=True
    )
    standards: list["StandardsData"] = Relationship(
        back_populates="srm_root", cascade_delete=True
    )
    past_lot_standards: list["PastLotStandardsData"] = Relationship(
        back_populates="srm_root",
        cascade_delete=True,
    )
    additional_lot_standards: list["AdditionalLotStandardsData"] = Relationship(
        back_populates="srm_root",
        cascade_delete=True,
    )
    ratio_analysis_random_effects: list["RatioAnalysisRandomEffectsData"] = (
        Relationship(
            back_populates="srm_root",
            cascade_delete=True,
        )
    )
    ratio_analysis_fixed_effects: list["RatioAnalysisFixedEffectsData"] = Relationship(
        back_populates="srm_root",
        cascade_delete=True,
    )

    rcert: "RCertData" = Relationship(back_populates="srm_root", cascade_delete=True)

    standard_analysis: "StandardAnalysisData" = Relationship(
        back_populates="srm_root", cascade_delete=True
    )


# * subtables
class RatioData(basemodels.srm.RatioDataBase, IDPrimaryKey, table=True):
    """Ratio Data table"""

    __tablename__ = cast("declared_attr[str]", "srm_ratios")

    srm_root: SRMData | None = Relationship(back_populates="ratios")


class RatioAnalysisRandomEffectsData(
    basemodels.srm.RatioAnalysisRandomEffectsDataBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "srm_ratio_analysis_random_effects")

    srm_root: SRMData | None = Relationship(
        back_populates="ratio_analysis_random_effects"
    )


class RatioAnalysisFixedEffectsData(
    basemodels.srm.RatioAnalysisFixedEffectsDataBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "srm_ratio_analysis_fixed_effects")
    srm_root: SRMData | None = Relationship(
        back_populates="ratio_analysis_fixed_effects"
    )


class VendorData(basemodels.srm.VendorDataBase, IDPrimaryKey, table=True):
    """Vendor data table"""

    __tablename__ = cast("declared_attr[str]", "srm_vendors")

    srm_root: SRMData | None = Relationship(back_populates="vendors")


class StandardsData(basemodels.srm.StandardsDataBase, IDPrimaryKey, table=True):
    """Standards data table"""

    __tablename__ = cast("declared_attr[str]", "srm_standards")

    srm_root: SRMData | None = Relationship(back_populates="standards")


class PastLotStandardsData(
    basemodels.srm.PastLotStandardsDataBase, IDPrimaryKey, table=True
):
    """Past lot standards table"""

    __tablename__ = cast("declared_attr[str]", "srm_past_lot_standards")

    srm_root: SRMData | None = Relationship(back_populates="past_lot_standards")


class AdditionalLotStandardsData(
    basemodels.srm.AdditionalLotStandardsDataBase, IDPrimaryKey, table=True
):
    """Additional lot standards table"""

    __tablename__ = cast("declared_attr[str]", "srm_additional_lot_standards")

    srm_root: SRMData | None = Relationship(back_populates="additional_lot_standards")


# * Standard analysis
class StandardAnalysisData(
    basemodels.standard_analysis.StandardAnalysisBase,
    IDPrimaryKey,
    _FixMixin,
    table=True,
):
    """Standard analysis data"""

    __tablename__ = cast("declared_attr[str]", "standard_analysis_root")

    model_config = SQLModelConfig(str_to_lower=True)
    srm_root: SRMData | None = Relationship(back_populates="standard_analysis")

    params: list["StandardAnalysisParamsData"] = Relationship(
        back_populates="standard_analysis_root",
        cascade_delete=True,
    )
    genline_params: list["StandardAnalysisGenLineParamsData"] = Relationship(
        back_populates="standard_analysis_root",
        cascade_delete=True,
    )
    genline_solution: list["StandardAnalysisGenLineSolutionData"] = Relationship(
        back_populates="standard_analysis_root",
        cascade_delete=True,
    )

    genline_eval: list["StandardAnalysisGenLineEvalData"] = Relationship(
        back_populates="standard_analysis_root",
        cascade_delete=True,
    )


class StandardAnalysisParamsData(
    basemodels.standard_analysis.ParamsBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "standard_analysis_params")
    standard_analysis_root: StandardAnalysisData | None = Relationship(
        back_populates="params"
    )


class StandardAnalysisGenLineParamsData(
    basemodels.standard_analysis.GenLineParamsBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "standard_analysis_genline_params")
    standard_analysis_root: StandardAnalysisData | None = Relationship(
        back_populates="genline_params"
    )


class StandardAnalysisGenLineSolutionData(
    basemodels.standard_analysis.GenLineSolutionBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "standard_analysis_genline_solution")
    standard_analysis_root: StandardAnalysisData | None = Relationship(
        back_populates="genline_solution"
    )


class StandardAnalysisGenLineEvalData(
    basemodels.standard_analysis.GenLineEvalBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "standard_analysis_genline_eval")
    standard_analysis_root: StandardAnalysisData | None = Relationship(
        back_populates="genline_eval"
    )


# * RCert
class RCertData(basemodels.rcert.RCertBase, IDPrimaryKey, _FixMixin, table=True):
    """R Certified values"""

    __tablename__ = cast("declared_attr[str]", "rcert_root")

    model_config = SQLModelConfig(str_to_lower=True)

    srm_root: SRMData | None = Relationship(back_populates="rcert")

    srm_values: list["RCertSRMValues"] = Relationship(
        back_populates="rcert_root", cascade_delete=True
    )
    standards_values: list["RCertStandardsValues"] = Relationship(
        back_populates="rcert_root", cascade_delete=True
    )
    additional_lot_standards: list["RCertAdditionalLotStandards"] = Relationship(
        back_populates="rcert_root", cascade_delete=True
    )
    cylinder_results: list["RCertCylinderResults"] = Relationship(
        back_populates="rcert_root", cascade_delete=True
    )
    analysis_function_coefficients: list["RCertAnalysisFunctionCoefficients"] = (
        Relationship(back_populates="rcert_root", cascade_delete=True)
    )
    correlation_coefficients: list["RCertCorrelationCoefficients"] = Relationship(
        back_populates="rcert_root", cascade_delete=True
    )
    outliers: list["RCertOutliers"] = Relationship(
        back_populates="rcert_root", cascade_delete=True
    )


class RCertSRMValues(basemodels.rcert.SRMValuesBase, IDPrimaryKey, table=True):
    __tablename__ = cast("declared_attr[str]", "rcert_srm_values")

    rcert_root: RCertData | None = Relationship(back_populates="srm_values")


class RCertStandardsValues(
    basemodels.rcert.StandardsValuesBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "rcert_standards_values")
    rcert_root: RCertData | None = Relationship(back_populates="standards_values")


class RCertAdditionalLotStandards(
    basemodels.rcert.AdditionalLotStandardsBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "rcert_additional_lot_standards")

    rcert_root: RCertData | None = Relationship(
        back_populates="additional_lot_standards"
    )


class RCertCylinderResults(
    basemodels.rcert.CylinderResultsBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "rcert_cylinder_results")
    rcert_root: RCertData | None = Relationship(back_populates="cylinder_results")


class RCertAnalysisFunctionCoefficients(
    basemodels.rcert.AnalysisFunctionCoefficientsBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "rcert_analysis_function_coefficients")
    rcert_root: RCertData | None = Relationship(
        back_populates="analysis_function_coefficients"
    )


class RCertCorrelationCoefficients(
    basemodels.rcert.CorrelationCoefficientsBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "rcert_correlation_coefficients")
    rcert_root: RCertData | None = Relationship(
        back_populates="correlation_coefficients"
    )


class RCertOutliers(basemodels.rcert.OutliersBase, IDPrimaryKey, table=True):
    __tablename__ = cast("declared_attr[str]", "rcert_outliers")
    rcert_root: RCertData | None = Relationship(back_populates="outliers")


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
