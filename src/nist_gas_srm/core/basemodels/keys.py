import uuid

from sqlmodel import (
    Field,
    SQLModel,
)


# * Keys
class IDPrimaryKey(SQLModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


class IDPrimaryKeyPublic(SQLModel):
    id: uuid.UUID


# * SRM
class SRMForeignKey(SQLModel):
    srm_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        foreign_key="srm_table.id",
        nullable=False,
        ondelete="CASCADE",
        validation_alias="SRMDataID",
    )


class SRMForeignKeyUpdate(SQLModel):
    pass
    # srmdata_id: uuid.UUID  # ruff: ignore[commented-out-code]
