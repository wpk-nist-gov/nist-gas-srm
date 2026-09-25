import logging
from collections.abc import AsyncGenerator, Generator, Sequence
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated, Any

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import FileResponse
from pydantic import ValidationError
from sqlmodel import Session

from nist_gas_srm.backend import crud, models
from nist_gas_srm.backend.core.db import engine, init_db
from nist_gas_srm.core import basemodels
from nist_gas_srm.core.excel_interface import (
    dict_of_dataframes_to_workbook,
    model_to_dict_of_dataframes,
)
from nist_gas_srm.core.excel_utils import as_excelfile

FORMAT = "[%(name)s - %(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)


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
    batch_id: str | None = None,
    lot_id: str | None = None,
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


@app.get("/srmrcert/complete", response_model=basemodels.srm.SRMCompletePublic)
@app.get("/srm/complete", response_model=basemodels.srm.SRMCompletePublic)
@app.get("/srm", response_model=basemodels.srm.SRMPublic)
def read_srm(
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm: str | None = None,
) -> models.SRMTable:
    """Get list of srms"""

    return crud.get_srm(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
        srm_query=srm,
    )


@app.get("/srmrcerts/complete", response_model=list[basemodels.srm.SRMCompletePublic])
@app.get("/srms/complete", response_model=list[basemodels.srm.SRMCompletePublic])
@app.get("/srms", response_model=list[basemodels.srm.SRMPublic])
def read_srms(
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm: Annotated[list[str] | None, Query()] = None,
) -> Sequence[models.SRMTable]:
    """Get list of srms"""

    return crud.get_srms(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
        srm_query=srm,
    )


@app.get("/rcert/complete", response_model=basemodels.rcert.RCertCompletePublic)
@app.get("/rcert", response_model=basemodels.rcert.RCertPublic)
def read_rcert(
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm: str | None = None,
) -> models.RCertTable:
    """Get list of srms"""

    return crud.get_rcert(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
        srm_query=srm,
    )


@app.get("/rcerts/complete", response_model=list[basemodels.rcert.RCertCompletePublic])
@app.get("/rcerts", response_model=list[basemodels.rcert.RCertPublic])
def read_rcerts(
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm: Annotated[list[str] | None, Query()] = None,
) -> Sequence[models.RCertTable]:
    """Get list of srms"""

    return crud.get_rcerts(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
        srm_query=srm,
    )


@app.get(
    "/rcert/cylinder-results",
    response_model=list[basemodels.rcert.RCertCylinderResultsPublic],
)
def read_rcerts_cylinder_results(
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
) -> Sequence[models.rcert.RCertCylinderResults]:
    """Get list of srms"""

    return crud.get_rcert(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
    ).cylinder_results


@app.post("/srm", response_model=basemodels.srm.SRMPublic)
def create_srm(
    *,
    session: SessionDepends,
    srmdata_in: basemodels.srm.SRMCreate,
) -> models.SRMTable:
    return crud.add_srm_from_create(session=session, srmdata_in=srmdata_in)


@app.post("/srm/complete", response_model=basemodels.srm.SRMPublic)
def create_srm_complete(
    *,
    session: SessionDepends,
    srmdata_in: basemodels.srm.SRMCompleteCreate,
) -> models.SRMTable:
    return crud.add_srm_from_create(session=session, srmdata_in=srmdata_in)


@app.post("/srmrcert/complete", response_model=basemodels.srm.SRMPublic)
def create_srmrcert_complete(
    *,
    session: SessionDepends,
    srmdata_in: basemodels.srm.SRMCompleteCreate,
) -> models.SRMTable:
    return crud.add_srm_from_create(session=session, srmdata_in=srmdata_in)


@app.post("/upload-excel", response_model=basemodels.srm.SRMPublic)
async def create_upload_file(
    *,
    session: SessionDepends,
    srmdata_in: Annotated[
        str, Form()
    ] = '{"name": "string", "srm_id": 0, "batch_id": null, "lot_id": "string", "timestamp": null}',
    uploadfile: Annotated[UploadFile, File()],
) -> Any:  # models.SRMTable:

    try:
        srmdata_create = basemodels.srm.SRMCreate.model_validate_json(srmdata_in)
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


def remove_file(path: Path) -> None:
    """Deletes the temporary file after the response is sent."""
    path.unlink()
    logger.info("delete path %s", path)


# Just for demo purposes
@app.get("/download-excel")
async def download_excel(
    background_tasks: BackgroundTasks,
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm: str | None = None,
) -> FileResponse:

    srmdata = basemodels.srm.SRMCompleteCreate.model_validate(
        crud.get_srm(
            session=session,
            srm_id=srm_id,
            batch_id=batch_id,
            lot_id=lot_id,
            srm_query=srm,
        )
    )

    # convert to dict of dataframes
    data = model_to_dict_of_dataframes(srmdata, drop_dbnames=["srmdata_id", "rcert_id"])

    # filename
    filename = (
        f"SRM{srmdata.srm_id}{srmdata.batch_id or ''}-{srmdata.lot_id}".upper()
        + ".xlsx"
    )

    # convert to excel file
    from nist_gas_srm.core.excel_template import template_xlsx
    from nist_gas_srm.core.excel_utils import xlsx_manager

    with TemporaryDirectory(delete=False) as d:
        file_path = Path(d) / filename

        with xlsx_manager(template_xlsx) as workbook:
            dict_of_dataframes_to_workbook(
                data,
                workbook,
                model=basemodels.srm.SRMCompleteCreate,
            )

        workbook.save(file_path)

        if not file_path.exists():
            raise HTTPException(status_code=400, detail="Error generating excel file")

        logger.info("file path %s", file_path)
        background_tasks.add_task(remove_file, file_path)

        # Official MIME type for modern .xlsx Excel files
        excel_media_type = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        return FileResponse(
            path=file_path, filename=filename, media_type=excel_media_type
        )
