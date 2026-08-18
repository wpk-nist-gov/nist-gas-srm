# ruff:file-ignore[commented-out-code]
from collections.abc import AsyncGenerator, Generator, Sequence
from contextlib import asynccontextmanager
from io import BytesIO
from typing import Annotated, Any

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from pydantic import AfterValidator, ValidationError
from sqlmodel import Session

from nist_gas_srm.backend import crud, models
from nist_gas_srm.backend.core.db import engine, init_db
from nist_gas_srm.core import basemodels
from nist_gas_srm.core.read_excel import SRMExcelFile
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


def _raise_if_srms_exist(
    session: Session,
    srm_id: int | None = None,
    batch_id: _OptStrAsLower = None,
    lot_id: _OptStrAsLower = None,
) -> None:
    if crud.get_srms(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
    ):
        raise HTTPException(
            status_code=400,
            detail=f"SRM with {srm_id=}, {batch_id=}, {lot_id=} exists.",
        )


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


@app.get("/srm/complete/", response_model=basemodels.SRMDataPublicComplete)
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


@app.get("/srms/complete/", response_model=list[basemodels.SRMDataPublicComplete])
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


@app.get("/srmrcert/complete/", response_model=basemodels.SRMRCertPublicComplete)
def read_srmrcert_complete(
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


@app.get("/srmrcerts/complete/", response_model=list[basemodels.SRMRCertPublicComplete])
def read_srmrcerts_complete(
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


@app.get("/rcert/complete", response_model=basemodels.RCertPublicComplete)
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


@app.get("/rcerts/complete", response_model=list[basemodels.RCertPublicComplete])
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


@app.get(
    "/rcert/cylinder-results/",
    response_model=list[basemodels.RCertCylinderResultsPublic],
)
def read_rcerts_cylinder_results(
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: _OptStrAsLower = None,
    lot_id: _OptStrAsLower = None,
) -> Sequence[models.RCertCylinderResults]:
    """Get list of srms"""

    return crud.get_rcert(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
    ).cylinder_results


@app.post("/srm/", response_model=basemodels.SRMDataPublic)
def create_srm(
    *, session: SessionDepends, srmdata_in: basemodels.SRMDataCreate
) -> models.SRMData:
    db_srmdata = models.SRMData.model_validate(srmdata_in, update={"id": 0})
    session.add(db_srmdata)
    session.commit()
    session.refresh(db_srmdata)
    return db_srmdata


@app.post("/upload-excel/", response_model=basemodels.SRMDataPublic)
async def create_upload_file(
    *,
    session: SessionDepends,
    srmdata_in: Annotated[
        str, Form()
    ] = '{"name": "string", "srm_id": 0, "batch_id": null, "lot_id": "string", "timestamp": null}',
    file: Annotated[UploadFile, File()],
) -> Any:  # models.SRMData:

    try:
        srmdata_create = basemodels.SRMDataCreate.model_validate_json(srmdata_in)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors()) from e

    _raise_if_srms_exist(
        session=session,
        srm_id=srmdata_create.srm_id,
        batch_id=srmdata_create.batch_id,
        lot_id=srmdata_create.lot_id,
    )

    if file.filename is None or not file.filename.endswith(".xls"):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Please upload an Excel file."
        )

    # 2. Read the file contents into memory
    contents = await file.read()

    try:
        # 3. Load the byte stream into a Pandas DataFrame
        srmxls = SRMExcelFile(BytesIO(contents))
        return crud.add_srm_from_excel_obj(
            session=session, srmdata_create=srmdata_create, srmxls=srmxls
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing Excel file: {e!s}",
        ) from e


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
