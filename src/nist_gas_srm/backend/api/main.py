# ruff:file-ignore[commented-out-code]

from collections.abc import AsyncGenerator, Generator, Sequence
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from pydantic import AfterValidator
from sqlmodel import Session

from nist_gas_srm.backend import _models as basemodels, crud, models
from nist_gas_srm.backend.core.db import engine, init_db
from nist_gas_srm.core.validate import validate_optional_str_to_lower

_OptStrAsLower = Annotated[str | None, AfterValidator(validate_optional_str_to_lower)]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:  # ruff:ignore[unused-function-argument]
    # 1. Startup: Code here runs BEFORE the application starts accepting requests
    with Session(engine) as session:
        init_db(session)

    yield  # The application runs while paused here

    # 2. Shutdown: Code here runs AFTER the application finishes handling requests


app = FastAPI(lifespan=lifespan)


def get_session() -> Generator[Session]:
    with Session(engine) as session:
        yield session


SessionDepends = Annotated[Session, Depends(get_session)]


@app.get("/")
def welcome() -> dict[str, str]:
    return {"detail": "Welcome to NIST Gas SRM database"}


@app.get("/srm/", response_model=basemodels.SRMDataPublic)
def read_srm(
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: _OptStrAsLower = None,
    lot_id: _OptStrAsLower = None,
) -> models.SRMData:
    """Get list of srms"""

    return crud.get_srm(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
    )


@app.get("/srms/", response_model=list[basemodels.SRMDataPublic])
def read_srms(
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: _OptStrAsLower = None,
    lot_id: _OptStrAsLower = None,
) -> Sequence[models.SRMData]:
    """Get list of srms"""
    return crud.get_srms(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
    )


@app.get("/srms/complete/", response_model=list[basemodels.SRMDataComplete])
def read_srms_complete(
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: _OptStrAsLower = None,
    lot_id: _OptStrAsLower = None,
) -> Sequence[models.SRMData]:

    return crud.get_srms(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
    )


@app.get("/srm/complete/", response_model=basemodels.SRMDataComplete)
def read_srm_complete(
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: _OptStrAsLower = None,
    lot_id: _OptStrAsLower = None,
) -> models.SRMData:
    return crud.get_srm(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
    )


@app.get("/rcert/", response_model=basemodels.RCertPublic)
def read_rcert(
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: _OptStrAsLower = None,
    lot_id: _OptStrAsLower = None,
) -> models.RCertData:
    """Get list of srms"""

    return crud.get_rcert(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
    )


@app.get("/rcerts/", response_model=list[basemodels.RCertPublic])
def read_rcerts(
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: _OptStrAsLower = None,
    lot_id: _OptStrAsLower = None,
) -> Sequence[models.RCertData]:
    """Get list of srms"""

    return crud.get_rcerts(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
    )


@app.get("/rcert/complete", response_model=basemodels.RCertComplete)
def read_rcert_complete(
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: _OptStrAsLower = None,
    lot_id: _OptStrAsLower = None,
) -> models.RCertData:
    """Get list of srms"""

    return crud.get_rcert(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
    )


@app.get("/rcerts/", response_model=list[basemodels.RCertComplete])
def read_rcerts_complete(
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: _OptStrAsLower = None,
    lot_id: _OptStrAsLower = None,
) -> Sequence[models.RCertData]:
    """Get list of srms"""

    return crud.get_rcerts(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
    )


# @app.get("/standards/{srm_id}", response_model=list[StandardsDataPublic])
# def read_srm_standards(
#     *,
#     session: SessionDepends,
#     srm_id: int,
#     batch_id: _OptStrAsLower = None,
#     lot_id: _OptStrAsLower = None,
# ) -> list[StandardsData]:

#     query = select(models.SRMData).where(models.SRMData.srm_id == srm_id)

#     if batch_id:
#         query = query.where(models.SRMData.batch_id == batch_id)
#     if lot_id:
#         query = query.where(models.SRMData.lot_id == lot_id)

#     return session.exec(query).one().standards


# @app.get("/ratios/{srm_id}", response_model=RatioDataPublic)
# def read_ratios(
#         srm_id: int,
#         batch_id: _OptStrAsLower = None,
#         lot_id: _OptStrAsLower = None,
# ) -> Sequence[RatioData]:
#     with Session(engine) as session:
#         pass


# @app.get(f"/srm/{srm_id}")
# def read_ratio_data() -> None:
#     pass
