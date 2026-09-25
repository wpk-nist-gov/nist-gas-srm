import logging
from typing import TYPE_CHECKING, Optional, TypeAlias, cast  # pyright: ignore[reportDeprecated]

from sqlmodel import (
    Relationship,
)

from nist_gas_srm.core import basemodels
from nist_gas_srm.core.basemodels.keys import IDPrimaryKey

from ._fixmixin import FixMixin

if TYPE_CHECKING:
    from sqlalchemy.orm import declared_attr

    from .srm import SRMTable


FORMAT = "[%(name)s - %(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)


class Measurements(
    basemodels.measurements.MeasurementsBase, IDPrimaryKey, FixMixin, table=True
):
    __tablename__ = cast("declared_attr[str]", "measurements")

    srm_table: Optional["SRMTable"] = Relationship(back_populates="measurements")  # pyright: ignore[reportDeprecated]
    ratios: list["RatioData"] = Relationship(
        back_populates="measurements", cascade_delete=True
    )
    vendors: list["VendorData"] = Relationship(
        back_populates="measurements", cascade_delete=True
    )
    standards: list["StandardsData"] = Relationship(
        back_populates="measurements", cascade_delete=True
    )
    past_lot_standards: list["PastLotStandards"] = Relationship(
        back_populates="measurements",
        cascade_delete=True,
    )
    additional_lot_standards: list["AdditionalLotStandards"] = Relationship(
        back_populates="measurements",
        cascade_delete=True,
    )
    ratio_analysis_random_effects: list["RatioAnalysisRandomEffects"] = Relationship(
        back_populates="measurements",
        cascade_delete=True,
    )
    ratio_analysis_fixed_effects: list["RatioAnalysisFixedEffects"] = Relationship(
        back_populates="measurements",
        cascade_delete=True,
    )


# * subtables
class RatioData(basemodels.measurements.RatioDataBase, IDPrimaryKey, table=True):
    """Ratio Data table"""

    __tablename__ = cast("declared_attr[str]", "measurements_ratios")

    measurements: Measurements | None = Relationship(back_populates="ratios")


class RatioAnalysisRandomEffects(
    basemodels.measurements.RatioAnalysisRandomEffectsBase, IDPrimaryKey, table=True
):
    __tablename__ = cast(
        "declared_attr[str]", "measurements_ratio_analysis_random_effects"
    )

    measurements: Measurements | None = Relationship(
        back_populates="ratio_analysis_random_effects"
    )


class RatioAnalysisFixedEffects(
    basemodels.measurements.RatioAnalysisFixedEffectsBase, IDPrimaryKey, table=True
):
    __tablename__ = cast(
        "declared_attr[str]", "measurements_ratio_analysis_fixed_effects"
    )
    measurements: Measurements | None = Relationship(
        back_populates="ratio_analysis_fixed_effects"
    )


class VendorData(basemodels.measurements.VendorDataBase, IDPrimaryKey, table=True):
    """Vendor data table"""

    __tablename__ = cast("declared_attr[str]", "measurements_vendors")

    measurements: Measurements | None = Relationship(back_populates="vendors")


class StandardsData(
    basemodels.measurements.StandardsDataBase, IDPrimaryKey, table=True
):
    """Standards data table"""

    __tablename__ = cast("declared_attr[str]", "measurements_standards")

    measurements: Measurements | None = Relationship(back_populates="standards")


class PastLotStandards(
    basemodels.measurements.PastLotStandardsBase, IDPrimaryKey, table=True
):
    """Past lot standards table"""

    __tablename__ = cast("declared_attr[str]", "measurements_past_lot_standards")

    measurements: Measurements | None = Relationship(
        back_populates="past_lot_standards"
    )


class AdditionalLotStandards(
    basemodels.measurements.AdditionalLotStandardsBase, IDPrimaryKey, table=True
):
    """Additional lot standards table"""

    __tablename__ = cast("declared_attr[str]", "measurements_additional_lot_standards")

    measurements: Measurements | None = Relationship(
        back_populates="additional_lot_standards"
    )


MeasurementsSubTableType: TypeAlias = (
    RatioData
    | VendorData
    | StandardsData
    | RatioAnalysisRandomEffects
    | RatioAnalysisFixedEffects
    | PastLotStandards
    | AdditionalLotStandards
)
