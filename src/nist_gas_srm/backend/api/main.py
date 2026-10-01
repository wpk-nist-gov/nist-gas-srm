import logging
import uuid
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
from nist_gas_srm.core.basemodels.utils import srm_params_to_srm_query
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
SRMTableIDType = Annotated[
    uuid.UUID | None, Query(title="SRM table ID", validation_alias="id")
]
SRMTableIDsType = Annotated[
    list[uuid.UUID] | None, Query(title="SRM table IDs", validation_alias="id")
]


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
        srm_query = srm_params_to_srm_query(
            srm_id=srm_id, batch_id=batch_id, lot_id=lot_id
        ).upper()
        logger.info("SRM %s exists", srm_query)
        raise HTTPException(
            status_code=400,
            detail=f"SRM {srm_query} exists.",
        )


@app.get("/")
def welcome() -> dict[str, str]:
    return {"detail": "Welcome to NIST Gas SRM database"}


@app.get("/srm/rcert/complete", response_model=basemodels.srm.SRMRCertCompletePublic)
@app.get("/srm/rcert", response_model=basemodels.srm.SRMRCertPublic)
@app.get(
    "/srm/standard-analysis/complete",
    response_model=basemodels.srm.SRMStandardAnalysisCompletePublic,
)
@app.get(
    "/srm/standard-analysis", response_model=basemodels.srm.SRMStandardAnalysisPublic
)
@app.get(
    "/srm/measurements/complete",
    response_model=basemodels.srm.SRMMeasurementsCompletePublic,
)
@app.get("/srm/measurements", response_model=basemodels.srm.SRMMeasurementsPublic)
@app.get("/srm/complete", response_model=basemodels.srm.SRMCompletePublic)
@app.get("/srm", response_model=basemodels.srm.SRMPublic)
def read_srm(
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm_query: str | None = None,
    srm_table_id: SRMTableIDType = None,
) -> models.SRMTable:
    """Get list of srms"""

    return crud.get_srm(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
        srm_query=srm_query,
        srm_table_id=srm_table_id,
    )


@app.get(
    "/srms/rcert/complete", response_model=list[basemodels.srm.SRMRCertCompletePublic]
)
@app.get("/srms/rcert", response_model=list[basemodels.srm.SRMRCertPublic])
@app.get(
    "/srms/standard-analysis/complete",
    response_model=list[basemodels.srm.SRMStandardAnalysisCompletePublic],
)
@app.get(
    "/srms/standard-analysis",
    response_model=list[basemodels.srm.SRMStandardAnalysisPublic],
)
@app.get(
    "/srms/measurements/complete",
    response_model=list[basemodels.srm.SRMMeasurementsCompletePublic],
)
@app.get(
    "/srms/measurements", response_model=list[basemodels.srm.SRMMeasurementsPublic]
)
@app.get("/srms/complete", response_model=list[basemodels.srm.SRMCompletePublic])
@app.get("/srms", response_model=list[basemodels.srm.SRMPublic])
def read_srms(
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm_query: Annotated[list[str] | None, Query()] = None,
    srm_table_id: SRMTableIDsType = None,
) -> Sequence[models.SRMTable]:
    """Get list of srms"""

    return crud.get_srms(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
        srm_query=srm_query,
        srm_table_id=srm_table_id,
    )


@app.get("/rcert/complete", response_model=basemodels.rcert.RCertCompletePublic)
@app.get("/rcert", response_model=basemodels.rcert.RCertPublic)
def read_rcert(
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm_query: str | None = None,
    srm_table_id: SRMTableIDType = None,
) -> models.RCertTable:
    """Get list of srms"""

    return crud.get_rcert(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
        srm_query=srm_query,
        srm_table_id=srm_table_id,
    )


@app.get("/rcerts/complete", response_model=list[basemodels.rcert.RCertCompletePublic])
@app.get("/rcerts", response_model=list[basemodels.rcert.RCertPublic])
def read_rcerts(
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm_query: Annotated[list[str] | None, Query()] = None,
    srm_table_id: SRMTableIDsType = None,
) -> Sequence[models.RCertTable]:
    """Get list of srms"""

    return crud.get_rcerts(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
        srm_query=srm_query,
        srm_table_id=srm_table_id,
    )


@app.get(
    "/measurement/complete",
    response_model=basemodels.measurements.MeasurementsCompletePublic,
)
@app.get("/measurement", response_model=basemodels.measurements.MeasurementsPublic)
def read_meausrement(
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm_query: str | None = None,
    srm_table_id: SRMTableIDType = None,
) -> models.Measurements:
    """Get list of srms"""

    return crud.get_measurement(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
        srm_query=srm_query,
        srm_table_id=srm_table_id,
    )


@app.get(
    "/measurements/complete",
    response_model=list[basemodels.measurements.MeasurementsCompletePublic],
)
@app.get(
    "/measurements", response_model=list[basemodels.measurements.MeasurementsPublic]
)
def read_measurements(
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm_query: Annotated[list[str] | None, Query()] = None,
    srm_table_id: SRMTableIDsType = None,
) -> Sequence[models.Measurements]:
    """Get list of srms"""

    return crud.get_measurements(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
        srm_query=srm_query,
        srm_table_id=srm_table_id,
    )


@app.get(
    "/standard-analysis/complete",
    response_model=basemodels.standard_analysis.StandardAnalysisCompletePublic,
)
@app.get(
    "/standard-analysis",
    response_model=basemodels.standard_analysis.StandardAnalysisPublic,
)
def read_standard_analysis(
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm_query: str | None = None,
    srm_table_id: SRMTableIDType = None,
) -> models.StandardAnalysisTable:
    """Get list of srms"""

    return crud.get_standard_analysis(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
        srm_query=srm_query,
        srm_table_id=srm_table_id,
    )


@app.get(
    "/standard-analyses/complete",
    response_model=list[basemodels.standard_analysis.StandardAnalysisCompletePublic],
)
@app.get(
    "/standard-analyses",
    response_model=list[basemodels.standard_analysis.StandardAnalysisPublic],
)
def read_standard_analyses(
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm_query: Annotated[list[str] | None, Query()] = None,
    srm_table_id: SRMTableIDsType = None,
) -> Sequence[models.StandardAnalysisTable]:
    """Get list of srms"""

    return crud.get_standard_analyses(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
        srm_query=srm_query,
        srm_table_id=srm_table_id,
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


@app.post("/srm/measurements", response_model=basemodels.srm.SRMPublic)
def create_srm_measurements(
    *,
    session: SessionDepends,
    srmdata_in: basemodels.srm.SRMMeasurementsCreate,
) -> models.SRMTable:
    return crud.add_srm_from_create(session=session, srmdata_in=srmdata_in)


@app.post("/srm/measurements/complete", response_model=basemodels.srm.SRMPublic)
def create_srm_measurements_complete(
    *,
    session: SessionDepends,
    srmdata_in: basemodels.srm.SRMMeasurementsCompleteCreate,
) -> models.SRMTable:
    return crud.add_srm_from_create(session=session, srmdata_in=srmdata_in)


@app.post("/srm/standard-analysis", response_model=basemodels.srm.SRMPublic)
def create_srm_standard_analysis(
    *,
    session: SessionDepends,
    srmdata_in: basemodels.srm.SRMStandardAnalysisCreate,
) -> models.SRMTable:
    return crud.add_srm_from_create(session=session, srmdata_in=srmdata_in)


@app.post("/srm/standard-analysis/complete", response_model=basemodels.srm.SRMPublic)
def create_srm_standard_analysis_complete(
    *,
    session: SessionDepends,
    srmdata_in: basemodels.srm.SRMStandardAnalysisCompleteCreate,
) -> models.SRMTable:
    return crud.add_srm_from_create(session=session, srmdata_in=srmdata_in)


@app.post("/srm/rcert", response_model=basemodels.srm.SRMPublic)
def create_srm_rcert(
    *,
    session: SessionDepends,
    srmdata_in: basemodels.srm.SRMRCertCreate,
) -> models.SRMTable:
    return crud.add_srm_from_create(session=session, srmdata_in=srmdata_in)


@app.post("/srm/rcert/complete", response_model=basemodels.srm.SRMPublic)
def create_srm_rcert_complete(
    *,
    session: SessionDepends,
    srmdata_in: basemodels.srm.SRMRCertCompleteCreate,
) -> models.SRMTable:
    return crud.add_srm_from_create(session=session, srmdata_in=srmdata_in)


# Delete
@app.delete("/srm")
def delete_srm(
    *,
    session: SessionDepends,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm_query: str | None = None,
    srm_table_id: SRMTableIDType = None,
) -> basemodels.Message:

    srm = crud.get_srm(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
        srm_query=srm_query,
        srm_table_id=srm_table_id,
    )

    crud.delete_srm(session=session, srm=srm)
    return basemodels.Message(message=f"SRM {srm.srm_string_id} deleted successfully")


@app.post("/upload-excel", response_model=basemodels.srm.SRMPublic)
async def create_upload_file(
    *,
    session: SessionDepends,
    srm_query: Annotated[
        str, Form()
    ] = '{"name": "string", "srm_id": 0, "batch_id": null, "lot_id": "string", "timestamp": null}',
    file: Annotated[UploadFile, File()],
) -> Any:  # models.SRMTable:

    logger.info("srm_query %s %s", srm_query, type(srm_query))

    try:
        srmdata_create = basemodels.srm.SRMCreate.from_srm_query(srm_query)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors()) from e

    logger.info("srmdata_create %s", srmdata_create)

    _raise_if_srms_exist(
        session=session,
        srm_id=srmdata_create.srm_id,
        batch_id=srmdata_create.batch_id,
        lot_id=srmdata_create.lot_id,
    )

    if file.filename is None or not file.filename.endswith(".xls"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an Excel file.",
        )

    # 2. Read the file contents into memory
    contents = await file.read()

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
            detail=f"Error processing Excel file: {e!s}",
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
    srm_query: str | None = None,
    srm_table_id: SRMTableIDType = None,
) -> FileResponse:

    srmdata = basemodels.srm.SRMCompleteCreate.model_validate(
        crud.get_srm(
            session=session,
            srm_id=srm_id,
            batch_id=batch_id,
            lot_id=lot_id,
            srm_query=srm_query,
            srm_table_id=srm_table_id,
        )
    )

    # convert to dict of dataframes
    data = model_to_dict_of_dataframes(
        srmdata,
        drop_dbnames=[
            "srm_table_id",
            "measurements_id",
            "standard_analysis_id",
            "rcert_id",
        ],
    )

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

        logger.info("hello %s", file_path)

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
