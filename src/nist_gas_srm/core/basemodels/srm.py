"""srm models"""
# ruff:file-ignore[manual-from-import]

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import (
    Annotated,
    Any,
    Self,
    TypeAlias,
)

from pydantic import BeforeValidator
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.hybrid import hybrid_property
from sqlmodel import (
    VARCHAR,
    Field,
    SQLModel,
    UniqueConstraint,
    col,
)
from sqlmodel._compat import SQLModelConfig  # ruff:ignore[import-private-name]

# pylint: disable=consider-using-from-import
import nist_gas_srm.core.basemodels.measurements as measurements
import nist_gas_srm.core.basemodels.rcert as rcert
import nist_gas_srm.core.basemodels.standard_analysis as stdanal
from nist_gas_srm.core.missing import MISSING
from nist_gas_srm.core.typing import SubTableType
from nist_gas_srm.core.utils import JSON_PATTERN, SRM_PATTERN
from nist_gas_srm.core.validate import (
    validate_like_string,
    validate_timestamp,
)

from .keys import IDPrimaryKeyPublic
from .utils import (
    LowerString,
    OptionalLowerString,
    srm_params_to_srm_query,
)


class Message(SQLModel):
    """Generic message"""

    message: str


class FromSRMQuery(SQLModel):
    @classmethod
    def from_srm_query(cls, srm_query: str | Self) -> Self:
        """
        Match patterns like:

        "{srm_number}{batch}-{lot}" with batch/lot optional

        or

        '{"srm_number": ...., "batch": ..., "lot": ...}'

        """

        if not isinstance(srm_query, str):
            return srm_query

        if JSON_PATTERN.match(srm_query) is not None:
            return cls.model_validate_json(srm_query)

        if (m := SRM_PATTERN.match(srm_query)) is not None:
            return cls.model_validate({
                k: v for k, v in m.groupdict().items() if v is not None
            })
        return cls()

    @classmethod
    def validate_srm_query_maybe_like(
        cls, srm_query: str | Self
    ) -> tuple[bool, str | Self]:

        if not isinstance(srm_query, str):
            return False, srm_query

        if JSON_PATTERN.match(srm_query) is not None:
            return False, cls.model_validate_json(srm_query)

        return validate_like_string(srm_query)

    @classmethod
    def from_srm_queries(cls, srm_queries: Iterable[str | Self]) -> list[Self]:
        if isinstance(srm_queries, str):
            srm_queries = [srm_queries]
        return [cls.from_srm_query(srm_query) for srm_query in srm_queries]

    @classmethod
    def from_params_exclude_none(cls, **kwargs: Any) -> Self:
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        return cls.model_validate(kwargs)

    @classmethod
    def from_params_exclude_missing(cls, **kwargs: Any) -> Self:
        kwargs = {k: v for k, v in kwargs.items() if v is not MISSING}
        return cls.model_validate(kwargs)


class SRMBase(SQLModel):
    """Metadata base class"""

    __table_args__ = (
        UniqueConstraint("srm_number", "batch", "lot", name="unique_user_product"),
    )

    model_config = SQLModelConfig(ignored_types=(hybrid_property,))

    description: str | None = Field(
        sa_column=Column("description", VARCHAR), default=None
    )
    units: str = "ppm"

    srm_number: int = Field(index=True)
    batch: OptionalLowerString = None
    lot: LowerString
    revision: str | None = None

    timestamp: Annotated[datetime, BeforeValidator(validate_timestamp)] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(UTC),
    )

    @hybrid_property
    def srm_string_id(self) -> str:
        return srm_params_to_srm_query(
            srm_number=self.srm_number, batch=self.batch, lot=self.lot
        )

    @srm_string_id.inplace.expression
    @classmethod
    def _srm_string_id_expression(cls) -> Any:
        from sqlalchemy import String, func

        return func.concat(
            func.cast(col(cls.srm_number), String),
            func.coalesce(cls.batch, ""),
            func.concat("-", cls.lot),
        )


class SRMPublic(SRMBase, IDPrimaryKeyPublic):
    pass


class SRMCreate(SRMBase, FromSRMQuery):
    pass


class SRMUpdate(SQLModel):
    name: str | None = None
    timestamp: datetime | None = None


class SRMQuery(FromSRMQuery):
    srm_number: int | None = None
    batch: OptionalLowerString = None
    lot: OptionalLowerString = None


class SRMQueryFuzzy(SQLModel):
    srm_number: int | str | None = None
    batch: OptionalLowerString = None
    lot: OptionalLowerString = None


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


SRMPublicTypes: TypeAlias = (
    SRMPublic
    | SRMCompletePublic
    | SRMMeasurementsPublic
    | SRMMeasurementsCompletePublic
    | SRMStandardAnalysisPublic
    | SRMStandardAnalysisCompletePublic
    | SRMRCertPublic
    | SRMRCertCompletePublic
)


PUBLIC_TYPES_COMPLETE_SUBTABLE_MAPPING: dict[
    tuple[SubTableType, bool], type[SRMPublicTypes]
] = {
    (None, False): SRMPublic,
    (None, True): SRMCompletePublic,
    ("measurements", False): SRMMeasurementsPublic,
    ("measurements", True): SRMMeasurementsCompletePublic,
    ("standard-analysis", False): SRMStandardAnalysisPublic,
    ("standard-analysis", True): SRMStandardAnalysisCompletePublic,
    ("rcert", False): SRMRCertPublic,
    ("rcert", True): SRMRCertCompletePublic,
}
