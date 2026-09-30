from typing import Annotated, Literal

from pydantic import AliasGenerator, BeforeValidator, PlainSerializer, StringConstraints
from pydantic.alias_generators import to_pascal as to_pascal_base
from sqlmodel import (
    Field,
)

from nist_gas_srm.core.validate import (
    validate_test_out,
)

# * Utilities
to_pascal = AliasGenerator(
    validation_alias=to_pascal_base,
    serialization_alias=lambda x: x,
)


def _serialize_test_out(x: bool) -> Literal["OUT"] | None:
    return "OUT" if x else None


TestOutAnn = Annotated[
    bool,
    BeforeValidator(validate_test_out),
    PlainSerializer(_serialize_test_out),
    Field(validation_alias="Test"),
]
TestOutOptionalAnn = Annotated[
    bool | None,
    BeforeValidator(validate_test_out),
    PlainSerializer(_serialize_test_out),
    Field(validation_alias="Test"),
]
LowerString = Annotated[str, StringConstraints(min_length=1, to_lower=True)]
OptionalLowerString = Annotated[
    str | None, StringConstraints(min_length=1, to_lower=True)
]


def srm_params_to_srm_query(
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
) -> str:

    return f"{srm_id}{batch_id or ''}{'-' + lot_id if lot_id else ''}"
