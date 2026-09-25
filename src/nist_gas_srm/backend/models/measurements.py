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
    ratios: list["MeasurementsRatios"] = Relationship(
        back_populates="measurements", cascade_delete=True
    )
    vendors: list["MeasurementsVendors"] = Relationship(
        back_populates="measurements", cascade_delete=True
    )
    standards: list["MeasurementsStandards"] = Relationship(
        back_populates="measurements", cascade_delete=True
    )
    past_lot_standards: list["MeasurementsPastLotStandards"] = Relationship(
        back_populates="measurements",
        cascade_delete=True,
    )
    additional_lot_standards: list["MeasurementsAdditionalLotStandards"] = Relationship(
        back_populates="measurements",
        cascade_delete=True,
    )
    ratio_analysis_random_effects: list["MeasurementsRatioAnalysisRandomEffects"] = (
        Relationship(
            back_populates="measurements",
            cascade_delete=True,
        )
    )
    ratio_analysis_fixed_effects: list["MeasurementsRatioAnalysisFixedEffects"] = (
        Relationship(
            back_populates="measurements",
            cascade_delete=True,
        )
    )


# * subtables
class MeasurementsRatios(
    basemodels.measurements.MeasurementsRatiosBase, IDPrimaryKey, table=True
):
    """Ratio Data table"""

    __tablename__ = cast("declared_attr[str]", "measurements_ratios")

    measurements: Measurements | None = Relationship(back_populates="ratios")


class MeasurementsRatioAnalysisRandomEffects(
    basemodels.measurements.MeasurementsRatioAnalysisRandomEffectsBase,
    IDPrimaryKey,
    table=True,
):
    __tablename__ = cast(
        "declared_attr[str]", "measurements_ratio_analysis_random_effects"
    )

    measurements: Measurements | None = Relationship(
        back_populates="ratio_analysis_random_effects"
    )


class MeasurementsRatioAnalysisFixedEffects(
    basemodels.measurements.MeasurementsRatioAnalysisFixedEffectsBase,
    IDPrimaryKey,
    table=True,
):
    __tablename__ = cast(
        "declared_attr[str]", "measurements_ratio_analysis_fixed_effects"
    )
    measurements: Measurements | None = Relationship(
        back_populates="ratio_analysis_fixed_effects"
    )


class MeasurementsVendors(
    basemodels.measurements.MeasurementsVendorsBase, IDPrimaryKey, table=True
):
    """Vendor data table"""

    __tablename__ = cast("declared_attr[str]", "measurements_vendors")

    measurements: Measurements | None = Relationship(back_populates="vendors")


class MeasurementsStandards(
    basemodels.measurements.MeasurementsStandardsBase, IDPrimaryKey, table=True
):
    """Standards data table"""

    __tablename__ = cast("declared_attr[str]", "measurements_standards")

    measurements: Measurements | None = Relationship(back_populates="standards")


class MeasurementsPastLotStandards(
    basemodels.measurements.MeasurementsPastLotStandardsBase, IDPrimaryKey, table=True
):
    """Past lot standards table"""

    __tablename__ = cast("declared_attr[str]", "measurements_past_lot_standards")

    measurements: Measurements | None = Relationship(
        back_populates="past_lot_standards"
    )


class MeasurementsAdditionalLotStandards(
    basemodels.measurements.MeasurementsAdditionalLotStandardsBase,
    IDPrimaryKey,
    table=True,
):
    """Additional lot standards table"""

    __tablename__ = cast("declared_attr[str]", "measurements_additional_lot_standards")

    measurements: Measurements | None = Relationship(
        back_populates="additional_lot_standards"
    )


MeasurementsSubTableType: TypeAlias = (
    MeasurementsRatios
    | MeasurementsVendors
    | MeasurementsStandards
    | MeasurementsRatioAnalysisRandomEffects
    | MeasurementsRatioAnalysisFixedEffects
    | MeasurementsPastLotStandards
    | MeasurementsAdditionalLotStandards
)
