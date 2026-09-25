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

    from .srm import SRMTable


FORMAT = "[%(name)s - %(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)


class RCertTable(rcertmodels.RCertBase, IDPrimaryKey, FixMixin, table=True):
    """R Certified values"""

    __tablename__ = cast("declared_attr[str]", "rcert_table")

    model_config = SQLModelConfig(str_to_lower=True)

    srm_table: Optional["SRMTable"] = Relationship(back_populates="rcert")  # pyright: ignore[reportDeprecated]

    srm_values: list["RCertSRMValues"] = Relationship(
        back_populates="rcert_table", cascade_delete=True
    )
    standards_values: list["RCertStandardsValues"] = Relationship(
        back_populates="rcert_table", cascade_delete=True
    )
    additional_lot_standards: list["RCertAdditionalLotStandards"] = Relationship(
        back_populates="rcert_table", cascade_delete=True
    )
    cylinder_results: list["RCertCylinderResults"] = Relationship(
        back_populates="rcert_table", cascade_delete=True
    )
    analysis_function_coefficients: list["RCertAnalysisFunctionCoefficients"] = (
        Relationship(back_populates="rcert_table", cascade_delete=True)
    )
    correlation_coefficients: list["RCertCorrelationCoefficients"] = Relationship(
        back_populates="rcert_table", cascade_delete=True
    )
    outliers: list["RCertOutliers"] = Relationship(
        back_populates="rcert_table", cascade_delete=True
    )


class RCertSRMValues(rcertmodels.RCertSRMValuesBase, IDPrimaryKey, table=True):
    __tablename__ = cast("declared_attr[str]", "rcert_srm_values")

    rcert_table: RCertTable | None = Relationship(back_populates="srm_values")


class RCertStandardsValues(
    rcertmodels.RCertStandardsValuesBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "rcert_standards_values")
    rcert_table: RCertTable | None = Relationship(back_populates="standards_values")


class RCertAdditionalLotStandards(
    rcertmodels.RCertAdditionalLotStandardsBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "rcert_additional_lot_standards")

    rcert_table: RCertTable | None = Relationship(
        back_populates="additional_lot_standards"
    )


class RCertCylinderResults(
    rcertmodels.RCertCylinderResultsBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "rcert_cylinder_results")
    rcert_table: RCertTable | None = Relationship(back_populates="cylinder_results")


class RCertAnalysisFunctionCoefficients(
    rcertmodels.RCertAnalysisFunctionCoefficientsBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "rcert_analysis_function_coefficients")
    rcert_table: RCertTable | None = Relationship(
        back_populates="analysis_function_coefficients"
    )


class RCertCorrelationCoefficients(
    rcertmodels.RCertCorrelationCoefficientsBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "rcert_correlation_coefficients")
    rcert_table: RCertTable | None = Relationship(
        back_populates="correlation_coefficients"
    )


class RCertOutliers(rcertmodels.RCertOutliersBase, IDPrimaryKey, table=True):
    __tablename__ = cast("declared_attr[str]", "rcert_outliers")
    rcert_table: RCertTable | None = Relationship(back_populates="outliers")


RCertSubTableType: TypeAlias = (
    RCertSRMValues
    | RCertStandardsValues
    | RCertAdditionalLotStandards
    | RCertCylinderResults
    | RCertAnalysisFunctionCoefficients
    | RCertCorrelationCoefficients
    | RCertOutliers
)
