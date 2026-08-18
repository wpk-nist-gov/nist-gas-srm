"""Basic model"""
# ruff:file-ignore[commented-out-code,missing-todo-link,line-contains-todo]

from datetime import UTC, datetime
from typing import Annotated, TypeAlias

from pydantic import AliasGenerator, BeforeValidator
from pydantic.alias_generators import to_pascal as to_pascal_base
from sqlalchemy import Column, DateTime
from sqlmodel import (
    VARCHAR,
    Field,
    SQLModel,
    UniqueConstraint,
)
from sqlmodel._compat import SQLModelConfig  # ruff:ignore[import-private-name]

from nist_gas_srm.core.validate import (
    validate_nan_to_none,
    validate_optional_str_to_lower,
    validate_str_to_lower,
    validate_timestamp,
)

to_pascal = AliasGenerator(
    validation_alias=to_pascal_base,
    serialization_alias=lambda x: x,
)


# * Common --------------------------------------------------------------------
class IDPrimaryKey(SQLModel):
    id: int | None = Field(default=None, primary_key=True)


class _IDPrimaryKeyPublic(SQLModel):
    id: int


class _SampleIDAndNumber(SQLModel):
    model_config = SQLModelConfig(populate_by_name=True)

    name: str = Field(index=True, validation_alias="SampleID")
    number: int = Field(validation_alias="SampleNo")


class _SampleIDAndNumberUpdate(SQLModel):
    model_config = SQLModelConfig(populate_by_name=True)

    name: str | None = None
    number: int | None = None


class SRMDataForeignKey(SQLModel):
    srmdata_id: int | None = Field(
        default=None, foreign_key="srmdata.id", ondelete="CASCADE"
    )


class _SRMDataForeignKeyUpdate(SQLModel):
    srmdata_id: int | None = None


# * Top level data (per worksheet) --------------------------------------------
class SRMDataBase(SQLModel):
    """Metadata base class"""

    __table_args__ = (
        UniqueConstraint("srm_id", "batch_id", "lot_id", name="unique_user_product"),
    )

    name: str = Field(sa_column=Column("name", VARCHAR, unique=True, index=True))
    srm_id: int = Field(index=True)
    batch_id: Annotated[
        str | None, BeforeValidator(validate_optional_str_to_lower)
    ]  # = Field(default=None, index=True)
    lot_id: Annotated[
        str, BeforeValidator(validate_str_to_lower)
    ]  # = Field(index=True)

    timestamp: Annotated[datetime, BeforeValidator(validate_timestamp)] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(UTC),
    )


class SRMDataPublic(SRMDataBase, _IDPrimaryKeyPublic):
    pass


class SRMDataCreate(SRMDataBase):
    pass


class SRMDataUpdate(SQLModel):
    name: str | None = None
    timestamp: datetime | None = None


# * Tables --------------------------------------------------------------------
# ** Ratio Data ---------------------------------------------------------------
class RatioDataBase(_SampleIDAndNumber, SRMDataForeignKey):
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
    value_g: float
    test: Annotated[str | None, BeforeValidator(validate_nan_to_none)]


class RatioDataPublic(RatioDataBase, _IDPrimaryKeyPublic):
    pass


class RatioDataCreate(RatioDataBase):
    pass


class RatioDataUpdate(_SampleIDAndNumberUpdate, _SRMDataForeignKeyUpdate):
    ratio: float | None = None
    ls_set: int | None = None
    break_set: int | None = None
    day: int | None = None
    port: int | None = None
    value_g: float
    test: Annotated[str | None, BeforeValidator(validate_nan_to_none)] = None


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
    RatioAnalysisRandomEffectsDataBase, _IDPrimaryKeyPublic
):
    pass


class RatioAnalysisRandomEffectsDataCreate(RatioAnalysisRandomEffectsDataBase):
    pass


class RatioAnalysisRandomEffectsDataUpdate(_SRMDataForeignKeyUpdate):
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
    RatioAnalysisFixedEffectsDataBase, _IDPrimaryKeyPublic
):
    pass


class RatioAnalysisFixedEffectsDataCreate(RatioAnalysisFixedEffectsDataBase):
    pass


class RatioAnalysisFixedEffectsDataUpdate(_SRMDataForeignKeyUpdate):
    estimate: float | None
    stderr: float | None
    t_value: float | None


# ** Vendor Data --------------------------------------------------------------
class VendorDataBase(_SampleIDAndNumber, SRMDataForeignKey):
    """Vendor data"""

    model_config = SQLModelConfig(
        alias_generator=to_pascal,
        populate_by_name=True,
    )

    cylinder_number: str = Field(validation_alias="CylinderNo")
    ratio: float = Field(validation_alias="VendorRatio")


class VendorDataPublic(VendorDataBase, _IDPrimaryKeyPublic):
    pass


class VendorDataCreate(VendorDataBase):
    pass


class VendorDataUpdate(_SampleIDAndNumberUpdate, _SRMDataForeignKeyUpdate):
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


class StandardsDataPublic(StandardsDataBase, _IDPrimaryKeyPublic):
    pass


class StandardsDataCreate(StandardsDataBase):
    pass


class StandardsDataUpdate(_SampleIDAndNumberUpdate, _SRMDataForeignKeyUpdate):
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


class PastLotStandardsDataPublic(PastLotStandardsDataBase, _IDPrimaryKeyPublic):
    pass


class PastLotStandardsDataCreate(PastLotStandardsDataBase):
    pass


class PastLotStandardsDataUpdate(_SampleIDAndNumberUpdate, _SRMDataForeignKeyUpdate):
    name: str | None = None
    number: int | None = None
    ratio: float | None = None
    past_conc: float | None = None
    pred_conc: float | None = None


class AdditionalLotStandardsDataBase(SRMDataForeignKey):
    """AdditionalLotStandards"""

    model_config = SQLModelConfig(populate_by_name=True)
    name: str = Field(validation_alias="ID")
    number: int = Field(validation_alias="LS#")
    ratio: float = Field(validation_alias="Ratio")


class AdditionalLotStandardsDataPublic(
    AdditionalLotStandardsDataBase, _IDPrimaryKeyPublic
):
    pass


class AdditionalLotStandardsDataCreate(AdditionalLotStandardsDataBase):
    pass


class AdditionalLotStandardsDataUpdate(
    _SampleIDAndNumberUpdate, _SRMDataForeignKeyUpdate
):
    name: str | None = None
    number: int | None = None
    ratio: float | None = None


# * RCertification -----------------------------------------------------------
class RCertForeignKey(SQLModel):
    rcert_id: int | None = Field(
        default=None, foreign_key="rcertdata.id", ondelete="CASCADE"
    )


class _RCertForeignKeyUpdate(SQLModel):
    rcert_id: int | None = None


# ** RCert
class RCertBase(SRMDataForeignKey):
    """Points back to srmdata"""


class RCertPublic(RCertBase, _IDPrimaryKeyPublic):
    pass


class RCertCreate(RCertBase):
    pass


class RCertUpdate(_SRMDataForeignKeyUpdate):
    pass


# ** SRMValues
# Each of these point back to rcert
class RCertSRMValuesBase(RCertForeignKey):
    """RCert.srm_values"""

    name: str
    value: Annotated[float | None, BeforeValidator(validate_nan_to_none)]


class RCertSRMValuesPublic(RCertSRMValuesBase, _IDPrimaryKeyPublic):
    pass


class RCertSRMValuesCreate(RCertSRMValuesBase):
    pass


class RCertSRMValuesUpdate(_RCertForeignKeyUpdate):
    name: str | None = None
    value: float | None = None


# ** Standard Values
class RCertStandardsValuesBase(RCertForeignKey):
    """Rcert.standards_values"""

    model_config = SQLModelConfig(populate_by_name=True)

    primary_standard: int = Field(validation_alias="Primary Standards")
    value: float = Field(validation_alias="Value")
    uncert: float = Field(validation_alias="Uncert (k=2)")
    predicted: float = Field(validation_alias="Predicted")
    predicted_uncert: float = Field(validation_alias="Predicted Uncert (k=2)")


class RCertStandardsValuesPublic(RCertStandardsValuesBase, _IDPrimaryKeyPublic):
    pass


class RCertStandardsValuesCreate(RCertStandardsValuesBase):
    pass


class RCertStandardsValuesUpdate(_RCertForeignKeyUpdate):
    value: float | None = None
    uncert: float | None = None
    predicted: float | None = None
    predicted_uncert: float | None = None


# ** Additional lot standards
class RCertAdditionalLotStandardsBase(RCertForeignKey):
    model_config = SQLModelConfig(populate_by_name=True)

    name: str = Field(validation_alias="Additional LSs")
    number: int = Field(validation_alias="LS #")

    value: float = Field(validation_alias="Value")
    uncert: float = Field(validation_alias="Uncert")
    uncert_ci95: float = Field(validation_alias="95% CI")  # 95 % confidence interval


class RCertAdditionalLotStandardsPublic(
    RCertAdditionalLotStandardsBase, _IDPrimaryKeyPublic
):
    pass


class RCertAdditionalLotStandardsCreate(RCertAdditionalLotStandardsBase):
    pass


class RCertAdditionalLotStandardsUpdate(_RCertForeignKeyUpdate):
    name: str | None = None
    number: int | None = None
    value: float | None = None
    uncert: float | None = None
    uncert_ci95: float | None = None


# ** Cylinder results
class RCertCylinderResultsBase(RCertForeignKey):
    model_config = SQLModelConfig(alias_generator=to_pascal, populate_by_name=True)

    name: str = Field(validation_alias="Sample")
    value: float
    uncert: float
    uncert_ci95: float = Field(validation_alias="95% CI")


class RCertCylinderResultsPublic(RCertCylinderResultsBase, _IDPrimaryKeyPublic):
    model_config = SQLModelConfig(populate_by_name=True)


class RCertCylinderResultsCreate(RCertCylinderResultsBase):
    pass


class RCertCylinderResultsUpdate(_RCertForeignKeyUpdate):
    name: str | None = None
    value: float | None = None
    uncert: float | None = None
    uncert_ci95: float | None = None


# ** Analysis function coefficients
class RCertAnalysisFunctionCoefficientsBase(RCertForeignKey):
    order: int
    value: float
    uncert: float


class RCertAnalysisFunctionCoefficientsPublic(
    RCertAnalysisFunctionCoefficientsBase, _IDPrimaryKeyPublic
):
    pass


class RCertAnalysisFunctionCoefficientsCreate(RCertAnalysisFunctionCoefficientsBase):
    pass


class RCertAnalysisFunctionCoefficientsUpdate(_RCertForeignKeyUpdate):
    order: int | None = None
    value: float | None = None
    uncert: float | None = None


# ** Correlation coefficients
class RCertCorrelationCoefficientsBase(RCertForeignKey):
    order: int
    order_other: int
    value: float


class RCertCorrelationCoefficientsPublic(
    RCertCorrelationCoefficientsBase, _IDPrimaryKeyPublic
):
    pass


class RCertCorrelationCoefficientsCreate(RCertCorrelationCoefficientsBase):
    pass


class RCertCorrelationCoefficientsUpdate(_RCertForeignKeyUpdate):
    order: int | None = None
    order_other: int | None = None
    value: float | None = None


# ** outliers
class RCertOutliersBase(RCertForeignKey):
    model_config = SQLModelConfig(
        alias_generator=to_pascal,
        populate_by_name=True,
    )
    name: str = Field(validation_alias="SampleID")
    ratio: float
    # TODO(wpk): make this a bool with where test == "OUT"
    test: Annotated[str | None, BeforeValidator(validate_nan_to_none)]
    value: float


class RCertOutliersPublic(RCertOutliersBase, _IDPrimaryKeyPublic):
    pass


class RCertOutliersCreate(RCertOutliersBase):
    pass


class RCertOutliersUpdate(_RCertForeignKeyUpdate):
    name: str | None = None
    # TODO(wpk): make this a bool with where test == "OUT"
    test: Annotated[str | None, BeforeValidator(validate_nan_to_none)] = None
    ratio: float | None = None
    value: float | None = None


# * "Complete" data
# ** Public
class RCertPublicComplete(_IDPrimaryKeyPublic):
    srm_values: list[RCertSRMValuesPublic] = []
    standards_values: list[RCertStandardsValuesPublic] = []
    additional_lot_standards: list[RCertAdditionalLotStandardsPublic] = []
    cylinder_results: list[RCertCylinderResultsPublic] = []
    analysis_function_coefficients: list[RCertAnalysisFunctionCoefficientsPublic] = []
    correlation_coefficients: list[RCertCorrelationCoefficientsPublic] = []
    outliers: list[RCertOutliersPublic] = []


class SRMDataPublicComplete(SRMDataBase, _IDPrimaryKeyPublic):
    ratios: list[RatioDataPublic] = []
    vendors: list[VendorDataPublic] = []
    standards: list[StandardsDataPublic] = []
    past_lot_standards: list[PastLotStandardsDataPublic] = []
    additional_lot_standards: list[AdditionalLotStandardsDataPublic] = []
    ratio_analysis_random_effects: list[RatioAnalysisRandomEffectsDataPublic] = []
    ratio_analysis_fixed_effects: list[RatioAnalysisFixedEffectsDataPublic] = []


class SRMRCertPublicComplete(SRMDataPublicComplete):
    rcert: RCertPublicComplete


# ** Create
class RCertCreateComplete:
    pass


# Useful typealiases
SRMSubTableCreate: TypeAlias = (
    RatioDataCreate
    | VendorDataCreate
    | StandardsDataCreate
    | RatioAnalysisRandomEffectsDataCreate
    | RatioAnalysisFixedEffectsDataCreate
    | PastLotStandardsDataCreate
    | AdditionalLotStandardsDataCreate
)

RCertSubTableCreate: TypeAlias = (
    RCertSRMValuesCreate
    | RCertStandardsValuesCreate
    | RCertAdditionalLotStandardsCreate
    | RCertCylinderResultsCreate
    | RCertAnalysisFunctionCoefficientsCreate
    | RCertCorrelationCoefficientsCreate
    | RCertOutliersCreate
)

# class RCertificationDataBase(SRMDataForeignKey):

#     timestamp: datetime = Field
#     srm_value: float
#     srm_uncertainty: float
#     srm_cl_95: float
#     srm_rel_uncert: float
#     srm_effective_k: float
#     ls_value: float
#     ls_uncertainty: float
#     ls_cl_95: float
#     ls_rel_uncert: float


# class _CertifiedDataForeignKey(SQLModel):
#     certified_id: int | None = Field(
#         default=None, foreign_key="certifieddata.id", ondelete="CASCADE",
#     )


# class _CertifiedDataForeignKeyUpdate(SQLModel):
#     certified_id: int | None = None


# class _CertifiedDataBase(_CertifiedDataForeignKey):
#     value: float
#     uncertainty: float
#     confidence_level_95: float

#     # relative_uncertainty <- confidence_level_95 / value
#     # effective k <- confidence_level_95 / uncertainty
