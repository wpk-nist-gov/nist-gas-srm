"""srm models"""
# ruff:file-ignore[manual-from-import]
# pylint: disable=abstract-method

from datetime import UTC, datetime
from typing import (
    Annotated,
    Any,
    Self,
)

from pydantic import BeforeValidator
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.hybrid import hybrid_property
from sqlmodel import (
    VARCHAR,
    Field,
    SQLModel,
    UniqueConstraint,
)
from sqlmodel._compat import SQLModelConfig  # ruff:ignore[import-private-name]

import nist_gas_srm.core.basemodels.measurements as measurements
import nist_gas_srm.core.basemodels.rcert as rcert
import nist_gas_srm.core.basemodels.standard_analysis as stdanal
from nist_gas_srm.core.utils import JSON_PATTERN, SRM_PATTERN
from nist_gas_srm.core.validate import (
    validate_timestamp,
)

from .keys import IDPrimaryKeyPublic
from .utils import (
    LowerString,
    OptionalLowerString,
)


class SRMBase(SQLModel):
    """Metadata base class"""

    __table_args__ = (
        UniqueConstraint("srm_id", "batch_id", "lot_id", name="unique_user_product"),
    )

    model_config = SQLModelConfig(ignored_types=(hybrid_property,))

    name: str | None = Field(sa_column=Column("name", VARCHAR), default=None)
    note: str | None = Field(sa_column=Column("note", VARCHAR), default=None)
    units: str = "ppm"

    srm_id: int = Field(index=True)
    batch_id: OptionalLowerString
    lot_id: LowerString

    timestamp: Annotated[datetime, BeforeValidator(validate_timestamp)] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(UTC),
    )

    @hybrid_property
    def srm_string_id(self) -> str:
        return f"{self.srm_id}{self.batch_id or ''}{'-' + self.lot_id if self.lot_id else ''}"


class SRMPublic(SRMBase, IDPrimaryKeyPublic):
    pass


class SRMCreate(SRMBase):
    pass


class SRMUpdate(SQLModel):
    name: str | None = None
    timestamp: datetime | None = None


class SRMQuery(SQLModel):
    srm_id: int | None = None
    batch_id: OptionalLowerString = None
    lot_id: OptionalLowerString = None

    @classmethod
    def from_string(cls, string: str) -> Self:
        """
        Match patterns like:

        "{srm_id}{batch_id}-{lot_id}" with batch/lot optional

        or

        '{"srm_id": ...., "batch_id": ..., "lot_id": ...}'

        """

        if (m := JSON_PATTERN.match(string)) is not None:
            return cls.model_validate_json(string)

        if (m := SRM_PATTERN.match(string)) is not None:
            return cls.model_validate({
                k: v for k, v in m.groupdict().items() if v is not None
            })
        return cls()

    @classmethod
    def from_params_exclude_none(cls, **kwargs: Any) -> Self:
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        return cls.model_validate(kwargs)


class SRMCompletePublic(SRMPublic):
    measurements: measurements.MeasurementsCompletePublic
    standard_analysis: stdanal.StandardAnalysisCompletePublic
    rcert: rcert.RCertCompletePublic


class SRMCompleteCreate(SRMCreate):
    measurements: measurements.MeasurementsCompleteCreate
    standard_analysis: stdanal.StandardAnalysisCompleteCreate
    rcert: rcert.RCertCompleteCreate


# measurements only
class SRMMeasurementsCompletePublic(SRMPublic):
    measurements: measurements.MeasurementsCompletePublic


class SRMMeasurementsCompleteCreate(SRMCreate):
    measurements: measurements.MeasurementsCompleteCreate


# standard_analysis only
class SRMStandardAnalysisCompletePublic(SRMPublic):
    standard_analysis: stdanal.StandardAnalysisCompletePublic


class SRMStandardAnalysisCompleteCreate(SRMCreate):
    standard_analysis: stdanal.StandardAnalysisCompleteCreate


# rcert only
class SRMRCertCompletePublic(SRMPublic):
    rcert: rcert.RCertCompletePublic


class SRMRCertCompleteCreate(SRMCreate):
    rcert: rcert.RCertCompleteCreate


# Single publics
class SRMRMeasurementsPublic(SRMPublic):
    measurements: measurements.MeasurementsPublic


class SRMStandardAnalysisPublic(SRMPublic):
    standard_analysis: stdanal.StandardAnalysisPublic


class SRMRCertPublic(SRMPublic):
    rcert: rcert.RCertPublic
