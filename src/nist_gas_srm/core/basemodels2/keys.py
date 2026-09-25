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
class SRMDataForeignKey(SQLModel):
    srm_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        foreign_key="srm_root.id",
        nullable=False,
        ondelete="CASCADE",
        validation_alias="SRMDataID",
    )


class SRMDataForeignKeyUpdate(SQLModel):
    pass
    # srmdata_id: uuid.UUID  # ruff: ignore[commented-out-code]


# * standard analysis
class StandardAnalysisForeignKey(SQLModel):
    standard_analysis_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        nullable=False,
        foreign_key="standard_analysis_root.id",
        ondelete="CASCADE",
    )
