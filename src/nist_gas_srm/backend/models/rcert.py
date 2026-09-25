import logging
from typing import TYPE_CHECKING, Optional, TypeAlias, cast  # pyright: ignore[reportDeprecated]

from sqlmodel import (
    Relationship,
)
from sqlmodel._compat import (  # ruff: ignore[import-private-name]
    SQLModelConfig,
)

from nist_gas_srm.core.basemodels import rcert as rcertmodels
from nist_gas_srm.core.basemodels.keys import IDPrimaryKey

from ._fixmixin import FixMixin

if TYPE_CHECKING:
    from sqlalchemy.orm import declared_attr

    from .srm import SRMData


FORMAT = "[%(name)s - %(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)


class RCertData(rcertmodels.RCertBase, IDPrimaryKey, FixMixin, table=True):
    """R Certified values"""

    __tablename__ = cast("declared_attr[str]", "rcert_root")

    model_config = SQLModelConfig(str_to_lower=True)

    srm_root: Optional["SRMData"] = Relationship(back_populates="rcert")  # pyright: ignore[reportDeprecated]

    srm_values: list["SRMValues"] = Relationship(
        back_populates="rcert_root", cascade_delete=True
    )
    standards_values: list["StandardsValues"] = Relationship(
        back_populates="rcert_root", cascade_delete=True
    )
    additional_lot_standards: list["AdditionalLotStandards"] = Relationship(
        back_populates="rcert_root", cascade_delete=True
    )
    cylinder_results: list["CylinderResults"] = Relationship(
        back_populates="rcert_root", cascade_delete=True
    )
    analysis_function_coefficients: list["AnalysisFunctionCoefficients"] = Relationship(
        back_populates="rcert_root", cascade_delete=True
    )
    correlation_coefficients: list["CorrelationCoefficients"] = Relationship(
        back_populates="rcert_root", cascade_delete=True
    )
    outliers: list["Outliers"] = Relationship(
        back_populates="rcert_root", cascade_delete=True
    )


class SRMValues(rcertmodels.SRMValuesBase, IDPrimaryKey, table=True):
    __tablename__ = cast("declared_attr[str]", "rcert_srm_values")

    rcert_root: RCertData | None = Relationship(back_populates="srm_values")


class StandardsValues(rcertmodels.StandardsValuesBase, IDPrimaryKey, table=True):
    __tablename__ = cast("declared_attr[str]", "rcert_standards_values")
    rcert_root: RCertData | None = Relationship(back_populates="standards_values")


class AdditionalLotStandards(
    rcertmodels.AdditionalLotStandardsBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "rcert_additional_lot_standards")

    rcert_root: RCertData | None = Relationship(
        back_populates="additional_lot_standards"
    )


class CylinderResults(rcertmodels.CylinderResultsBase, IDPrimaryKey, table=True):
    __tablename__ = cast("declared_attr[str]", "rcert_cylinder_results")
    rcert_root: RCertData | None = Relationship(back_populates="cylinder_results")


class AnalysisFunctionCoefficients(
    rcertmodels.AnalysisFunctionCoefficientsBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "rcert_analysis_function_coefficients")
    rcert_root: RCertData | None = Relationship(
        back_populates="analysis_function_coefficients"
    )


class CorrelationCoefficients(
    rcertmodels.CorrelationCoefficientsBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "rcert_correlation_coefficients")
    rcert_root: RCertData | None = Relationship(
        back_populates="correlation_coefficients"
    )


class Outliers(rcertmodels.OutliersBase, IDPrimaryKey, table=True):
    __tablename__ = cast("declared_attr[str]", "rcert_outliers")
    rcert_root: RCertData | None = Relationship(back_populates="outliers")


RCertSubTable: TypeAlias = (
    SRMValues
    | StandardsValues
    | AdditionalLotStandards
    | CylinderResults
    | AnalysisFunctionCoefficients
    | CorrelationCoefficients
    | Outliers
)
