from collections.abc import Sequence
from typing import Generic, TypeVar

from sqlmodel import SQLModel

DataModelT = TypeVar("DataModelT", bound=SQLModel)
DataModelsT = TypeVar("DataModelsT", bound=Sequence[SQLModel])


class ResponseEnvelope(SQLModel, Generic[DataModelT]):
    success: bool = True
    message: str | None = None
    data: DataModelT | None = None


class ResponseEnvelopeMult(SQLModel, Generic[DataModelsT]):
    success: bool = True
    message: str | None = None
    data: DataModelsT | None = None
