"""Basic model"""

from datetime import UTC, datetime
from typing import Annotated

from pydantic import BeforeValidator
from pydantic.alias_generators import to_pascal
from sqlalchemy import Column, DateTime
from sqlmodel import (
    VARCHAR,
    Field,
    SQLModel,
)
from sqlmodel._compat import SQLModelConfig  # ruff:ignore[import-private-name]

from .core.validate import (
    validate_nan_to_none,
    validate_optional_str_to_lower,
    validate_str_to_lower,
)


# * Common --------------------------------------------------------------------
class IDPrimaryKey(SQLModel):
    id: int | None = Field(default=None, primary_key=True)


class _IDPrimaryKeyPublic(SQLModel):
    id: int


class _SampleIDAndNumber(SQLModel):
    model_config = SQLModelConfig(populate_by_name=True)

    name: str = Field(index=True, alias="SampleID")
    number: int = Field(alias="SampleNo")


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

    name: str = Field(sa_column=Column("name", VARCHAR, unique=True, index=True))
    srm_id: int = Field(index=True)
    batch_id: Annotated[
        str | None, BeforeValidator(validate_optional_str_to_lower)
    ]  # = Field(default=None, index=True)
    lot_id: Annotated[
        str, BeforeValidator(validate_str_to_lower)
    ]  # = Field(index=True)

    timestamp: datetime = Field(
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

    model_config = SQLModelConfig(alias_generator=to_pascal, populate_by_name=True)

    ratio: float
    ls_set: int = Field(alias="LSSet")
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
    model_config = SQLModelConfig(alias_generator=to_pascal, populate_by_name=True)

    groups: str
    name: Annotated[str | None, BeforeValidator(validate_nan_to_none)]
    stddev: float = Field(alias="Std Dev")
    count: Annotated[int | None, BeforeValidator(validate_nan_to_none)] = Field(
        alias="No"
    )


class RatioAnalysisRandomEffectsDataPublic(
    RatioAnalysisRandomEffectsDataBase, _IDPrimaryKeyPublic
):
    pass


class RatioAnalysisRandomEffectsDataUpdate(_SRMDataForeignKeyUpdate):
    groups: str | None
    name: str | None
    stddev: float | None
    count: int | None


class RatioAnalysisFixedEffectsDataBase(SRMDataForeignKey):
    model_config = SQLModelConfig(alias_generator=to_pascal, populate_by_name=True)

    estimate: float
    stderr: float = Field(alias="Std Error")
    t_value: float = Field(alias="t value")


class RatioAnalysisFixedEffectsDataPublic(
    RatioAnalysisFixedEffectsDataBase, _IDPrimaryKeyPublic
):
    pass


class RatioAnalysisFixedEffectsDataUpdate(_SRMDataForeignKeyUpdate):
    estimate: float | None
    stderr: float | None
    t_value: float | None


# ** Vendor Data --------------------------------------------------------------
class VendorDataBase(_SampleIDAndNumber, SRMDataForeignKey):
    """Vendor data"""

    model_config = SQLModelConfig(alias_generator=to_pascal, populate_by_name=True)

    cylinder_number: str = Field(alias="CylinderNo")
    ratio: float = Field(alias="VendorRatio")


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

    name: str = Field(alias="StandardID")
    number: int = Field(alias="StandardNo")
    ratio: float = Field(alias="SRatio")
    concentration: float = Field(alias="SConc")
    unc: float = Field(alias="Sunc")
    uncert: float = Field(alias="Suncert")


class StandardsDataPublic(StandardsDataBase, _IDPrimaryKeyPublic):
    pass


class StandardsDataCreate(StandardsDataBase):
    pass


class StandardsDataUpdate(_SampleIDAndNumberUpdate, _SRMDataForeignKeyUpdate):
    name: str | None = None
    number: int | None = None
    ratio: float | None = None
    concentration: float | None = None
    unc: float | None = None
    uncert: float | None = None


# ** Past lot standards -------------------------------------------------------
class PastLotStandardsDataBase(SRMDataForeignKey):
    """Past lot standards"""

    name: str = Field(alias="LS ID")
    number: int = Field(alias="LS#")
    ratio: float = Field(alias="Ratio")
    past_conc: float = Field(alias="Past Conc")
    pred_conc: float = Field(alias="Pred Conc")


class PastLotStandardsDataPublic(PastLotStandardsDataBase, _IDPrimaryKeyPublic):
    pass


class PastLogStandardsDataCreate(PastLotStandardsDataBase):
    pass


class PastLotStandardsDataUpdate(_SampleIDAndNumberUpdate, _SRMDataForeignKeyUpdate):
    name: str | None = None
    number: int | None = None
    ratio: float | None = None
    past_conc: float | None = None
    pred_conc: float | None = None


class AdditionalLotStandardsDataBase(SRMDataForeignKey):
    """AdditionalLotStandards"""

    name: str = Field(alias="ID")
    number: int = Field(alias="LS#")
    ratio: float = Field(alias="Ratio")


class AdditionalLotStandardsDataPublic(
    AdditionalLotStandardsDataBase, _IDPrimaryKeyPublic
):
    pass


class AdditionalLogStandardsDataCreate(AdditionalLotStandardsDataBase):
    pass


class AdditionalLotStandardsDataUpdate(
    _SampleIDAndNumberUpdate, _SRMDataForeignKeyUpdate
):
    name: str | None = None
    number: int | None = None
    ratio: float | None = None


# * RCertification -----------------------------------------------------------
# ruff:file-ignore[commented-out-code]
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
