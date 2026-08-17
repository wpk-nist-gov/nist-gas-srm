from collections.abc import AsyncGenerator, Generator, Sequence
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import AfterValidator
from sqlmodel import Session, create_engine, select

from ._model import SRMDataComplete, SRMDataPublic, StandardsDataPublic
from .core.validate import validate_optional_str_to_lower
from .model import SRMData, StandardsData, create_db_and_tables

_OptStrAsLower = Annotated[str | None, AfterValidator(validate_optional_str_to_lower)]

sqlite_file_path = Path("database.db")
sqlite_url = f"sqlite:///{sqlite_file_path}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:  # ruff:ignore[unused-function-argument]
    # 1. Startup: Code here runs BEFORE the application starts accepting requests
    create_db_and_tables(engine)

    yield  # The application runs while paused here

    # 2. Shutdown: Code here runs AFTER the application finishes handling requests


app = FastAPI(lifespan=lifespan)


def get_session() -> Generator[Session]:
    with Session(engine) as session:
        yield session


SessionDepends = Annotated[Session, Depends(get_session)]


@app.get("/srm/", response_model=list[SRMDataPublic])
def read_srms(*, session: SessionDepends) -> Sequence[SRMData]:
    """Get all SRMs"""
    return session.exec(select(SRMData)).all()


@app.get("/srm/index/{index}", response_model=SRMDataPublic)
def read_srm_index(*, session: SessionDepends, index: int) -> SRMData:
    """Get single SRM"""
    if (data := session.get(SRMData, index)) is None:
        raise HTTPException(status_code=404, detail=f"srm with {index=} not found")
    return data


@app.get("/srm/{srm_id}", response_model=list[SRMDataPublic])
def read_srm(
    *,
    session: SessionDepends,
    srm_id: int,
    batch_id: _OptStrAsLower = None,
    lot_id: _OptStrAsLower = None,
) -> Sequence[SRMData]:

    query = select(SRMData).where(SRMData.srm_id == srm_id)

    if batch_id:
        query = query.where(SRMData.batch_id == batch_id)
    if lot_id:
        query = query.where(SRMData.lot_id == lot_id)

    return session.exec(query).all()


@app.get("/srm-complete/{srm_id}", response_model=list[SRMDataComplete])
def read_srm_complete(
    *,
    session: SessionDepends,
    srm_id: int,
    batch_id: _OptStrAsLower = None,
    lot_id: _OptStrAsLower = None,
) -> Sequence[SRMData]:

    query = select(SRMData).where(SRMData.srm_id == srm_id)

    if batch_id:
        query = query.where(SRMData.batch_id == batch_id)
    if lot_id:
        query = query.where(SRMData.lot_id == lot_id)

    return session.exec(query).all()


@app.get("/standards/{srm_id}", response_model=list[StandardsDataPublic])
def read_srm_standards(
    *,
    session: SessionDepends,
    srm_id: int,
    batch_id: _OptStrAsLower = None,
    lot_id: _OptStrAsLower = None,
) -> list[StandardsData]:

    query = select(SRMData).where(SRMData.srm_id == srm_id)

    if batch_id:
        query = query.where(SRMData.batch_id == batch_id)
    if lot_id:
        query = query.where(SRMData.lot_id == lot_id)

    return session.exec(query).one().standards


# @app.get("/ratios/{srm_id}", response_model=RatioDataPublic)
# def read_ratios(
#         srm_id: int,
#         batch_id: _OptStrAsLower = None,  # ruff:ignore[commented-out-code]
#         lot_id: _OptStrAsLower = None,  # ruff:ignore[commented-out-code]
# ) -> Sequence[RatioData]:
#     with Session(engine) as session:
#         pass


# @app.get(f"/srm/{srm_id}")
# def read_ratio_data() -> None:
#     pass
