"""srm models"""
# ruff:file-ignore[manual-from-import]
# pylint: disable=abstract-method

from collections.abc import Iterable
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


class FromSRMQuery(SQLModel):
    @classmethod
    def from_srm_query(cls, srm_query: str | Self) -> Self:
        """
        Match patterns like:

        "{srm_id}{batch_id}-{lot_id}" with batch/lot optional

        or

        '{"srm_id": ...., "batch_id": ..., "lot_id": ...}'

        """

        if not isinstance(srm_query, str):
            return srm_query

        if (m := JSON_PATTERN.match(srm_query)) is not None:
            return cls.model_validate_json(srm_query)

        if (m := SRM_PATTERN.match(srm_query)) is not None:
            return cls.model_validate({
                k: v for k, v in m.groupdict().items() if v is not None
            })
        return cls()

    @classmethod
    def from_srm_queries(cls, srm_queries: Iterable[str | Self]) -> list[Self]:
        if isinstance(srm_queries, str):
            srm_queries = [srm_queries]
        return [cls.from_srm_query(srm_query) for srm_query in srm_queries]

    @classmethod
    def from_params_exclude_none(cls, **kwargs: Any) -> Self:
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        return cls.model_validate(kwargs)


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
    batch_id: OptionalLowerString = None
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


class SRMCreate(SRMBase, FromSRMQuery):
    pass


class SRMUpdate(SQLModel):
    name: str | None = None
    timestamp: datetime | None = None


class SRMQuery(FromSRMQuery):
    srm_id: int | None = None
    batch_id: OptionalLowerString = None
    lot_id: OptionalLowerString = None


# * Public combinations
class SRMCompletePublic(SRMPublic):
    measurements: measurements.MeasurementsCompletePublic
    standard_analysis: stdanal.StandardAnalysisCompletePublic
    rcert: rcert.RCertCompletePublic


class SRMMeasurementsCompletePublic(SRMPublic):
    measurements: measurements.MeasurementsCompletePublic


class SRMStandardAnalysisCompletePublic(SRMPublic):
    standard_analysis: stdanal.StandardAnalysisCompletePublic


class SRMRCertCompletePublic(SRMPublic):
    rcert: rcert.RCertCompletePublic


class SRMMeasurementsPublic(SRMPublic):
    measurements: measurements.MeasurementsPublic


class SRMStandardAnalysisPublic(SRMPublic):
    standard_analysis: stdanal.StandardAnalysisPublic


class SRMRCertPublic(SRMPublic):
    rcert: rcert.RCertPublic


# * Create combinations
class SRMCompleteCreate(SRMCreate):
    measurements: measurements.MeasurementsCompleteCreate
    standard_analysis: stdanal.StandardAnalysisCompleteCreate
    rcert: rcert.RCertCompleteCreate


class SRMMeasurementsCompleteCreate(SRMCreate):
    measurements: measurements.MeasurementsCompleteCreate


class SRMStandardAnalysisCompleteCreate(SRMCreate):
    standard_analysis: stdanal.StandardAnalysisCompleteCreate


class SRMRCertCompleteCreate(SRMCreate):
    rcert: rcert.RCertCompleteCreate


class SRMMeasurementsCreate(SRMCreate):
    measurements: measurements.MeasurementsCreate


class SRMStandardAnalysisCreate(SRMCreate):
    standard_analysis: stdanal.StandardAnalysisCreate


class SRMRCertCreate(SRMCreate):
    rcert: rcert.RCertCreate
