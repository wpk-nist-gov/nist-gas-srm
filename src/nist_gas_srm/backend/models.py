"""Basic model"""

import logging
from operator import methodcaller
from typing import Any, TypeAlias, cast

from sqlmodel import (
    Relationship,
    select,
)
from sqlmodel._compat import SQLModelConfig  # ruff:ignore[import-private-name]
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
    StandardsDataBase,
    VendorDataBase,
)

FORMAT = "[%(name)s - %(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)


# Sql Models ------------------------------------------------------------------
class SRMData(SRMDataBase, IDPrimaryKey, table=True):
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


# * subtables
class RatioData(RatioDataBase, IDPrimaryKey, table=True):
    """Ratio Data table"""

    srmdata: SRMData | None = Relationship(back_populates="ratios")


class RatioAnalysisRandomEffectsData(
    RatioAnalysisRandomEffectsDataBase, IDPrimaryKey, table=True
):
    srmdata: SRMData | None = Relationship(
        back_populates="ratio_analysis_random_effects"
    )


class RatioAnalysisFixedEffectsData(
    RatioAnalysisFixedEffectsDataBase, IDPrimaryKey, table=True
):
    srmdata: SRMData | None = Relationship(
        back_populates="ratio_analysis_fixed_effects"
    )


class VendorData(VendorDataBase, IDPrimaryKey, table=True):
    """Vendor data table"""

    srmdata: SRMData | None = Relationship(back_populates="vendors")


class StandardsData(StandardsDataBase, IDPrimaryKey, table=True):
    """Standards data table"""

    srmdata: SRMData | None = Relationship(back_populates="standards")


class PastLotStandardsData(PastLotStandardsDataBase, IDPrimaryKey, table=True):
    """Past lot standards table"""

    srmdata: SRMData | None = Relationship(back_populates="past_lot_standards")


class AdditionalLotStandardsData(
    AdditionalLotStandardsDataBase, IDPrimaryKey, table=True
):
    """Additional lot standards table"""

    srmdata: SRMData | None = Relationship(back_populates="additional_lot_standards")


# * RCert
class RCertData(RCertBase, IDPrimaryKey, table=True):
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
    rcertdata: RCertData | None = Relationship(back_populates="srm_values")


class RCertStandardsValues(RCertStandardsValuesBase, IDPrimaryKey, table=True):
    rcertdata: RCertData | None = Relationship(back_populates="standards_values")


class RCertAdditionalLotStandards(
    RCertAdditionalLotStandardsBase, IDPrimaryKey, table=True
):
    rcertdata: RCertData | None = Relationship(
        back_populates="additional_lot_standards"
    )


class RCertCylinderResults(RCertCylinderResultsBase, IDPrimaryKey, table=True):
    model_config = SQLModelConfig(populate_by_name=True, serialize_by_alias=False)
    rcertdata: RCertData | None = Relationship(back_populates="cylinder_results")


class RCertAnalysisFunctionCoefficients(
    RCertAnalysisFunctionCoefficientsBase, IDPrimaryKey, table=True
):
    rcertdata: RCertData | None = Relationship(
        back_populates="analysis_function_coefficients"
    )


class RCertCorrelationCoefficients(
    RCertCorrelationCoefficientsBase, IDPrimaryKey, table=True
):
    rcertdata: RCertData | None = Relationship(
        back_populates="correlation_coefficients"
    )


class RCertOutliers(RCertOutliersBase, IDPrimaryKey, table=True):
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

RCertSubTable: TypeAlias = (
    RCertSRMValues
    | RCertStandardsValues
    | RCertAdditionalLotStandards
    | RCertCylinderResults
    | RCertAnalysisFunctionCoefficients
    | RCertCorrelationCoefficients
    | RCertOutliers
)


# * name/getter/cls triples
SRMDATA_NAME_CALLER_CLS = [
    (name, methodcaller(name if attr is None else attr), cls)
    for name, attr, cls in [
        ("ratios", "ratio_data", RatioData),
        ("vendords", "vendor_data", VendorData),
        ("standards", "standards_data", StandardsData),
        ("ratio_analysis_random_effects", None, RatioAnalysisRandomEffectsData),
        (
            "ratio_analysis_fixed_effects",
            "ratio_analysis_fixed_effects_intercept",
            RatioAnalysisFixedEffectsData,
        ),
        ("past_lot_standards", None, PastLotStandardsData),
        ("additional_lot_standards", None, AdditionalLotStandardsData),
    ]
]


RCERTDATA_NAME_CALLER_CLS = [
    (name, methodcaller(name if attr is None else attr), cls)
    for name, attr, cls in [
        ("srm_values", None, RCertSRMValues),
        ("standards_values", None, RCertStandardsValues),
        ("additional_lot_standards", None, RCertAdditionalLotStandards),
        ("cylinder_results", None, RCertCylinderResults),
        ("analysis_function_coefficients", None, RCertAnalysisFunctionCoefficients),
        (
            "correlation_coefficients",
            "correlation_coefficients_flat",
            RCertCorrelationCoefficients,
        ),
        ("outliers", None, RCertOutliers),
    ]
]


# * Utils ---------------------------------------------------------------------
def select_columns(*columns: Any) -> Select[Any] | SelectOfScalar[Any]:
    """For typing purposes"""
    return cast("Select[Any] | SelectOfScalar[Any]", select(*columns))
