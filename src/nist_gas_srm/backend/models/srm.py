"""Basic model"""

import logging
from typing import TYPE_CHECKING, TypeAlias, cast

from sqlmodel import (
    Relationship,
)
from sqlmodel._compat import (  # ruff: ignore[import-private-name]
    SQLModelConfig,
)

from nist_gas_srm.core import basemodels
from nist_gas_srm.core.basemodels.keys import IDPrimaryKey

from ._fixmixin import FixMixin
from .rcert import RCertData
from .standard_analysis import StandardAnalysisData

if TYPE_CHECKING:
    from sqlalchemy.orm import declared_attr


FORMAT = "[%(name)s - %(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)


class SRMData(basemodels.srm.SRMDataBase, IDPrimaryKey, FixMixin, table=True):
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

    rcert: RCertData = Relationship(back_populates="srm_root", cascade_delete=True)

    standard_analysis: StandardAnalysisData = Relationship(
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


SRMSubTable: TypeAlias = (
    RatioData
    | VendorData
    | StandardsData
    | RatioAnalysisRandomEffectsData
    | RatioAnalysisFixedEffectsData
    | PastLotStandardsData
    | AdditionalLotStandardsData
)
