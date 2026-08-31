from collections.abc import AsyncGenerator, Generator, Sequence
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import AfterValidator, ValidationError
from sqlmodel import Session

from nist_gas_srm.backend import crud, models
from nist_gas_srm.backend.core.db import engine, init_db
from nist_gas_srm.core import basemodels
from nist_gas_srm.core.excel_utils import as_excelfile
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


@app.get("/srmrcert/complete", response_model=basemodels.SRMRCertPublicComplete)
@app.get("/srm/complete", response_model=basemodels.SRMDataPublicComplete)
@app.get("/srm", response_model=basemodels.SRMDataPublic)
def read_srm(
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: _OptStrAsLower = None,
    lot_id: _OptStrAsLower = None,
    srm: str | None = None,
) -> models.SRMData:
    """Get list of srms"""

    return crud.get_srm(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
        srm_query=srm,
    )


@app.get("/srmrcerts/complete", response_model=list[basemodels.SRMRCertPublicComplete])
@app.get("/srms/complete", response_model=list[basemodels.SRMDataPublicComplete])
@app.get("/srms", response_model=list[basemodels.SRMDataPublic])
def read_srms(
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: _OptStrAsLower = None,
    lot_id: _OptStrAsLower = None,
    srm: Annotated[list[str] | None, Query()] = None,
) -> Sequence[models.SRMData]:
    """Get list of srms"""

    return crud.get_srms(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
        srm_query=srm,
    )


@app.get("/rcert/complete", response_model=basemodels.RCertPublicComplete)
@app.get("/rcert", response_model=basemodels.RCertPublic)
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


@app.get("/rcerts/complete", response_model=list[basemodels.RCertPublicComplete])
@app.get("/rcerts", response_model=list[basemodels.RCertPublic])
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


@app.get(
    "/rcert/cylinder-results",
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


@app.post("/srm", response_model=basemodels.SRMDataPublic)
def create_srm(
    *,
    session: SessionDepends,
    srmdata_in: basemodels.SRMDataCreate,
) -> models.SRMData:
    return crud.add_srm_from_create(session=session, srmdata_in=srmdata_in)


@app.post("/srm/complete", response_model=basemodels.SRMDataPublic)
def create_srm_complete(
    *,
    session: SessionDepends,
    srmdata_in: basemodels.SRMDataCreateComplete,
) -> models.SRMData:
    return crud.add_srm_from_create(session=session, srmdata_in=srmdata_in)


@app.post("/srmrcert/complete", response_model=basemodels.SRMDataPublic)
def create_srmrcert_complete(
    *,
    session: SessionDepends,
    srmdata_in: basemodels.SRMRCertCreateComplete,
) -> models.SRMData:
    return crud.add_srm_from_create(session=session, srmdata_in=srmdata_in)


@app.post("/upload-excel", response_model=basemodels.SRMDataPublic)
async def create_upload_file(
    *,
    session: SessionDepends,
    srmdata_in: Annotated[
        str, Form()
    ] = '{"name": "string", "srm_id": 0, "batch_id": null, "lot_id": "string", "timestamp": null}',
    uploadfile: Annotated[UploadFile, File()],
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

    if uploadfile.filename is None or not uploadfile.filename.endswith(".xls"):
        raise HTTPException(
            status_code=400,
            detail="Invalid uploadfile type. Please upload an Excel uploadfile.",
        )

    # 2. Read the uploadfile contents into memory
    contents = await uploadfile.read()

    try:  # pylint: disable=too-many-try-statements
        # 3. Load the byte stream into a Pandas DataFrame
        with as_excelfile(BytesIO(contents)) as excelfile:
            return crud.add_srm_from_excel_obj(
                session=session,
                srmdata_create=srmdata_create,
                excelfile=excelfile,
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing Excel uploadfile: {e!s}",
        ) from e


# Just for demo purposes
@app.get("/download-excel")
async def download_excel() -> FileResponse:
    # Path to the file stored on your server
    file_path = (
        Path(__file__).parent
        / "../../../../tmp/data/SRM2627a_SeriesI_CAG+CEC_CEC-RV6.4.xls"
    )

    if not file_path.exists():
        raise HTTPException(status_code=400, detail="Error generating excel file")

    # Explicitly set the custom name the user sees when saving
    display_filename = "monthly_report.xlsx"

    # Official MIME type for modern .xlsx Excel files
    excel_media_type = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    return FileResponse(
        path=file_path, filename=display_filename, media_type=excel_media_type
    )
