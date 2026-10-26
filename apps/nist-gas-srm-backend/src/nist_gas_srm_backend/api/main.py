# ruff:file-ignore[commented-out-code]
# pylint: disable=duplicate-code

import logging
import uuid
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated, Any, TypeVar

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
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlmodel import Session, SQLModel

from nist_gas_srm import basemodels, excel
from nist_gas_srm.basemodels.utils import srm_params_to_srm_query
from nist_gas_srm.core.typing import SubTableType

from .. import crud, models
from ..core.db import engine, init_db

FORMAT = "[%(name)s - %(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)

DataModelT = TypeVar("DataModelT", bound=SQLModel)
DataModelT2 = TypeVar("DataModelT2", bound=SQLModel)


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
SRMTableIDMultType = Annotated[
    list[uuid.UUID] | None, Query(title="SRM table IDs", validation_alias="id")
]
SRMQueryType = Annotated[str | None, Query(title="General query")]
SRMQueryMultType = Annotated[list[str] | None, Query(title="General query")]


def _raise_if_srms_exist(
    session: Session,
    srm_number: int,
    batch: str | None,
    lot: str | None,
) -> None:
    if crud.get_srms(
        session=session,
        srm_number=srm_number,
        batch=batch,
        lot=lot,
    ):
        srm_query = srm_params_to_srm_query(
            srm_number=srm_number, batch=batch, lot=lot
        ).upper()
        logger.info("SRM %s exists", srm_query)
        raise HTTPException(
            status_code=400,
            detail=f"SRM {srm_query} exists.",
        )


@app.get("/")
def welcome() -> dict[str, str]:
    return {"detail": "Welcome to NIST Gas SRM database"}


# @app.get(
#     "/srms/rcert/single",
#     response_model=basemodels.srm.SRMRCertCompletePublic,
# )
# @app.get(
#     "/srm/standard-analysis/single",
#     response_model=basemodels.srm.SRMStandardAnalysisCompletePublic,
# )
# @app.get(
#     "/srm/measurements/single",
#     response_model=basemodels.srm.SRMMeasurementsCompletePublic,
# )
# @app.get(
#     "/srms/single",
#     response_model=basemodels.srm.SRMCompletePublic,
# )
# def read_srm(
#     *,
#     session: SessionDepends,
#     srm_number: int | None = None,
#     batch: str | None = None,
#     lot: str | None = None,
#     srm_query: SRMQueryType = None,
#     srm_table_id: SRMTableIDType = None,
# ) -> models.SRMTable:
#     """Get list of srms"""

#     return crud.get_srm(
#         session=session,
#         srm_number=srm_number,
#         batch=batch,
#         lot=lot,
#         srm_query=srm_query,
#         srm_table_id=srm_table_id,
#     )


# @app.get(
#     "/srms/rcert/complete",
#     response_model=list[basemodels.srm.SRMRCertCompletePublic],
# )
# @app.get(
#     "/srms/rcert",
#     response_model=list[basemodels.srm.SRMRCertPublic],
# )
# @app.get(
#     "/srms/standard-analysis/complete",
#     response_model=list[basemodels.srm.SRMStandardAnalysisCompletePublic],
# )
# @app.get(
#     "/srms/standard-analysis",
#     response_model=list[basemodels.srm.SRMStandardAnalysisPublic],
# )
# @app.get(
#     "/srms/measurements/complete",
#     response_model=list[basemodels.srm.SRMMeasurementsCompletePublic],
# )
# @app.get(
#     "/srms/measurements",
#     response_model=list[basemodels.srm.SRMMeasurementsPublic],
# )
# @app.get(
#     "/srms/complete",
#     response_model=list[basemodels.srm.SRMCompletePublic],
# )
# @app.get(
#     "/srms",
#     response_model=list[basemodels.srm.SRMPublic],
# )
# def read_srms(
#     *,
#     session: SessionDepends,
#     srm_number: int | None = None,
#     batch: str | None = None,
#     lot: str | None = None,
#     srm_query: SRMQueryMultType = None,
#     srm_table_id: SRMTableIDMultType = None,
#     one: bool = False,
# ) -> Sequence[models.SRMTable]:
#     """Get list of srms"""

#     try:
#         return crud.get_srms(
#             session=session,
#             srm_number=srm_number,
#             batch=batch,
#             lot=lot,
#             srm_query=srm_query,
#             srm_table_id=srm_table_id,
#             one=one,
#         )
#     except MultipleResultsFound as e:
#         raise HTTPException(status_code=409, detail="Multiple records found") from e
#     except NoResultFound as e:
#         raise HTTPException(status_code=409, detail="No record found") from e


# class EnvelopeMultWrapper(Generic[DataModelT, DataModelT2]):
#     def __init__(
#         self, model: type[DataModelT], model_complete: type[DataModelT2]
#     ) -> None:
#         self._model = model
#         self._model_complete = model_complete

#     def __call__(
#         self,
#         *,
#         session: SessionDepends,
#         srm_number: int | None = None,
#         batch: str | None = None,
#         lot: str | None = None,
#         srm_query: SRMQueryMultType = None,
#         srm_table_id: SRMTableIDMultType = None,
#         complete: bool = False,
#         one: bool = False,
#     ) -> (
#         basemodels.results.ResponseEnvelopeMult[list[DataModelT]]
#         | basemodels.results.ResponseEnvelopeMult[list[DataModelT2]]
#     ):

#         with catch_single_record_errors():
#             data_db = crud.get_srms(
#                 session=session,
#                 srm_number=srm_number,
#                 batch=batch,
#                 lot=lot,
#                 srm_query=srm_query,
#                 srm_table_id=srm_table_id,
#                 one=one,
#             )
#             model = self._model_complete if complete else self._model

#             params: dict[str, Any] = {
#                 "message": "Hello",
#                 "data": [model.model_validate(d) for d in data_db],
#             }

#             return basemodels.results.ResponseEnvelopeMult(**params)


# _: Any = app.get("/envelopes")(
#     EnvelopeMultWrapper(basemodels.srm.SRMPublic, basemodels.srm.SRMCompletePublic)
# )
# _ = app.get("/envelopes/measurements")(
#     EnvelopeMultWrapper(
#         basemodels.srm.SRMMeasurementsPublic,
#         basemodels.srm.SRMMeasurementsCompletePublic,
#     )
# )
# _ = app.get("/envelopes/standard-analysis")(
#     EnvelopeMultWrapper(
#         basemodels.srm.SRMStandardAnalysisPublic,
#         basemodels.srm.SRMStandardAnalysisCompletePublic,
#     )
# )
# _ = app.get("/envelopes/rcerts")(
#     EnvelopeMultWrapper(
#         basemodels.srm.SRMRCertPublic, basemodels.srm.SRMRCertCompletePublic
#     )
# )


# class EnvelopeWrapper(Generic[DataModelT, DataModelT2]):
#     def __init__(
#         self, model: type[DataModelT], model_complete: type[DataModelT2]
#     ) -> None:
#         self._model = model
#         self._model_complete = model_complete

#     def __call__(
#         self,
#         *,
#         session: SessionDepends,
#         srm_query_or_id: str,
#         complete: bool = True,
#     ) -> (
#         basemodels.results.ResponseEnvelope[DataModelT]
#         | basemodels.results.ResponseEnvelope[DataModelT2]
#     ):
#         srm_table_id: uuid.UUID | None = None
#         srm_query: str | None = None
#         try:
#             srm_table_id = uuid.UUID(srm_query_or_id)
#         except ValueError:
#             srm_query = srm_query_or_id

#         with catch_single_record_errors():
#             data_db = crud.get_srm(
#                 session=session,
#                 srm_query=srm_query,
#                 srm_table_id=srm_table_id,
#             )
#             model = self._model_complete if complete else self._model

#             params: dict[str, Any] = {
#                 "message": "Hello",
#                 "data": model.model_validate(data_db),
#             }

#             return basemodels.results.ResponseEnvelope(**params)


# _ = app.get("/envelopes/{srm_query_or_id}")(
#     EnvelopeWrapper(basemodels.srm.SRMPublic, basemodels.srm.SRMCompletePublic)
# )


@contextmanager
def catch_single_record_errors() -> Generator[None]:
    try:
        yield
    except MultipleResultsFound as e:
        raise HTTPException(status_code=400, detail="Multiple records found") from e
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail="No record found") from e


@app.get("/srms")
def get_srms(
    *,
    session: SessionDepends,
    srm_number: int | None = None,
    batch: str | None = None,
    lot: str | None = None,
    srm_query: SRMQueryMultType = None,
    srm_table_id: SRMTableIDMultType = None,
    complete: bool = False,
    subtable: SubTableType = None,
    one: bool = False,
) -> basemodels.results.ResponseEnvelopeMult[list[basemodels.srm.SRMPublicTypes]]:

    with catch_single_record_errors():
        data_db = crud.get_srms(
            session=session,
            srm_number=srm_number,
            batch=batch,
            lot=lot,
            srm_query=srm_query,
            srm_table_id=srm_table_id,
            one=one,
        )
        model = basemodels.srm.PUBLIC_TYPES_COMPLETE_SUBTABLE_MAPPING[
            subtable, complete
        ]

        return basemodels.results.ResponseEnvelopeMult(
            message="Hello there",
            data=[model.model_validate(d) for d in data_db],
        )


# Delete
@app.delete("/srms")
def delete_srm(
    *,
    session: SessionDepends,
    srm_number: int | None = None,
    batch: str | None = None,
    lot: str | None = None,
    srm_query: SRMQueryType = None,
    srm_table_id: SRMTableIDType = None,
) -> basemodels.Message:

    srm = crud.get_srm(
        session=session,
        srm_number=srm_number,
        batch=batch,
        lot=lot,
        srm_query=srm_query,
        srm_table_id=srm_table_id,
    )

    crud.delete_srm(session=session, srm=srm)
    return basemodels.Message(message=f"SRM {srm.srm_string_id} deleted successfully")


# @app.get("/rcerts/single", response_model=basemodels.rcert.RCertCompletePublic)
# def read_rcert(
#     *,
#     session: SessionDepends,
#     srm_number: int | None = None,
#     batch: str | None = None,
#     lot: str | None = None,
#     srm_query: SRMQueryType = None,
#     srm_table_id: SRMTableIDType = None,
# ) -> models.RCertTable:
#     """Get list of srms"""

#     return crud.get_rcert(
#         session=session,
#         srm_number=srm_number,
#         batch=batch,
#         lot=lot,
#         srm_query=srm_query,
#         srm_table_id=srm_table_id,
#     )


# @app.get("/rcerts", response_model=list[basemodels.rcert.RCertCompletePublic])
# def read_rcerts(
#     *,
#     session: SessionDepends,
#     srm_number: int | None = None,
#     batch: str | None = None,
#     lot: str | None = None,
#     srm_query: SRMQueryMultType = None,
#     srm_table_id: SRMTableIDMultType = None,
#     one: bool = False,
# ) -> Sequence[models.RCertTable]:
#     """Get list of srms"""

#     return crud.get_rcerts(
#         session=session,
#         srm_number=srm_number,
#         batch=batch,
#         lot=lot,
#         srm_query=srm_query,
#         srm_table_id=srm_table_id,
#         one=one,
#     )


# @app.get(
#     "/measurements/single",
#     response_model=basemodels.measurements.MeasurementsCompletePublic,
# )
# def read_meauserement(
#     *,
#     session: SessionDepends,
#     srm_number: int | None = None,
#     batch: str | None = None,
#     lot: str | None = None,
#     srm_query: SRMQueryType = None,
#     srm_table_id: SRMTableIDType = None,
# ) -> models.Measurements:
#     """Get list of srms"""

#     return crud.get_measurement(
#         session=session,
#         srm_number=srm_number,
#         batch=batch,
#         lot=lot,
#         srm_query=srm_query,
#         srm_table_id=srm_table_id,
#     )


# @app.get(
#     "/measurements",
#     response_model=list[basemodels.measurements.MeasurementsCompletePublic],
# )
# def read_measurements(
#     *,
#     session: SessionDepends,
#     srm_number: int | None = None,
#     batch: str | None = None,
#     lot: str | None = None,
#     srm_query: SRMQueryMultType = None,
#     srm_table_id: SRMTableIDMultType = None,
#     one: bool = False,
# ) -> Sequence[models.Measurements]:
#     """Get list of srms"""

#     return crud.get_measurements(
#         session=session,
#         srm_number=srm_number,
#         batch=batch,
#         lot=lot,
#         srm_query=srm_query,
#         srm_table_id=srm_table_id,
#         one=one,
#     )


# @app.get(
#     "/standard-analysis/complete",
#     response_model=basemodels.standard_analysis.StandardAnalysisCompletePublic,
# )
# @app.get(
#     "/standard-analysis",
#     response_model=basemodels.standard_analysis.StandardAnalysisPublic,
# )
# def read_standard_analysis(
#     *,
#     session: SessionDepends,
#     srm_number: int | None = None,
#     batch: str | None = None,
#     lot: str | None = None,
#     srm_query: SRMQueryType = None,
#     srm_table_id: SRMTableIDType = None,

# ) -> models.StandardAnalysisTable:
#     """Get list of srms"""

#     return crud.get_standard_analysis(
#         session=session,
#         srm_number=srm_number,
#         batch=batch,
#         lot=lot,
#         srm_query=srm_query,
#         srm_table_id=srm_table_id,
#     )


# @app.get(
#     "/standard-analyses",
#     response_model=list[basemodels.standard_analysis.StandardAnalysisCompletePublic],
# )
# def read_standard_analyses(
#     *,
#     session: SessionDepends,
#     srm_number: int | None = None,
#     batch: str | None = None,
#     lot: str | None = None,
#     srm_query: SRMQueryMultType = None,
#     srm_table_id: SRMTableIDMultType = None,
#     one: bool = False,
# ) -> Sequence[models.StandardAnalysisTable]:
#     """Get list of srms"""

#     return crud.get_standard_analyses(
#         session=session,
#         srm_number=srm_number,
#         batch=batch,
#         lot=lot,
#         srm_query=srm_query,
#         srm_table_id=srm_table_id,
#         one=one,
#     )


# @app.get(
#     "/rcert/cylinder-results",
#     response_model=list[basemodels.rcert.RCertCylinderResultsPublic],
# )
# def read_rcerts_cylinder_results(
#     *,
#     session: SessionDepends,
#     srm_number: int | None = None,
#     batch: str | None = None,
#     lot: str | None = None,
# ) -> Sequence[models.rcert.RCertCylinderResults]:
#     """Get list of srms"""

#     return crud.get_rcert(
#         session=session,
#         srm_number=srm_number,
#         batch=batch,
#         lot=lot,
#     ).cylinder_results


@app.post("/srms", response_model=basemodels.srm.SRMPublic)
def create_srm(
    *,
    session: SessionDepends,
    srmdata_in: basemodels.srm.SRMCreate,
) -> models.SRMTable:
    return crud.add_srm_from_create(session=session, srmdata_in=srmdata_in)


@app.post("/srms/complete", response_model=basemodels.srm.SRMPublic)
def create_srm_complete(
    *,
    session: SessionDepends,
    srmdata_in: basemodels.srm.SRMCompleteCreate,
) -> models.SRMTable:
    return crud.add_srm_from_create(session=session, srmdata_in=srmdata_in)


@app.post("/srms/measurements", response_model=basemodels.srm.SRMPublic)
def create_srm_measurements(
    *,
    session: SessionDepends,
    srmdata_in: basemodels.srm.SRMMeasurementsCreate,
) -> models.SRMTable:
    return crud.add_srm_from_create(session=session, srmdata_in=srmdata_in)


@app.post("/srms/measurements/complete", response_model=basemodels.srm.SRMPublic)
def create_srm_measurements_complete(
    *,
    session: SessionDepends,
    srmdata_in: basemodels.srm.SRMMeasurementsCompleteCreate,
) -> models.SRMTable:
    return crud.add_srm_from_create(session=session, srmdata_in=srmdata_in)


@app.post("/srms/standard-analysis", response_model=basemodels.srm.SRMPublic)
def create_srm_standard_analysis(
    *,
    session: SessionDepends,
    srmdata_in: basemodels.srm.SRMStandardAnalysisCreate,
) -> models.SRMTable:
    return crud.add_srm_from_create(session=session, srmdata_in=srmdata_in)


@app.post("/srms/standard-analysis/complete", response_model=basemodels.srm.SRMPublic)
def create_srm_standard_analysis_complete(
    *,
    session: SessionDepends,
    srmdata_in: basemodels.srm.SRMStandardAnalysisCompleteCreate,
) -> models.SRMTable:
    return crud.add_srm_from_create(session=session, srmdata_in=srmdata_in)


@app.post("/srms/rcert", response_model=basemodels.srm.SRMPublic)
def create_srm_rcert(
    *,
    session: SessionDepends,
    srmdata_in: basemodels.srm.SRMRCertCreate,
) -> models.SRMTable:
    return crud.add_srm_from_create(session=session, srmdata_in=srmdata_in)


@app.post("/srms/rcert/complete", response_model=basemodels.srm.SRMPublic)
def create_srm_rcert_complete(
    *,
    session: SessionDepends,
    srmdata_in: basemodels.srm.SRMRCertCompleteCreate,
) -> models.SRMTable:
    return crud.add_srm_from_create(session=session, srmdata_in=srmdata_in)


@app.post("/srms/files", response_model=basemodels.srm.SRMPublic)
async def create_upload_file(
    *,
    session: SessionDepends,
    srm_query: Annotated[
        str, Form()
    ] = '{"name": "string", "srm_number": 0, "batch": null, "lot": "string", "timestamp": null}',
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
        srm_number=srmdata_create.srm_number,
        batch=srmdata_create.batch,
        lot=srmdata_create.lot,
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
        with excel.utils.as_excelfile(BytesIO(contents)) as excelfile:
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
@app.get("/srms/files")
async def download_excel(
    background_tasks: BackgroundTasks,
    *,
    session: SessionDepends,
    srm_number: int | None = None,
    batch: str | None = None,
    lot: str | None = None,
    srm_query: SRMQueryType = None,
    srm_table_id: SRMTableIDType = None,
) -> FileResponse:

    with catch_single_record_errors():
        srmdata = basemodels.srm.SRMCompleteCreate.model_validate(
            crud.get_srm(
                session=session,
                srm_number=srm_number,
                batch=batch,
                lot=lot,
                srm_query=srm_query,
                srm_table_id=srm_table_id,
            )
        )

    # convert to dict of dataframes
    data = excel.interface.model_to_dict_of_dataframes(
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
        f"SRM{srmdata.srm_number}{srmdata.batch or ''}-{srmdata.lot}".upper() + ".xlsx"
    )

    # convert to excel file

    with TemporaryDirectory(delete=False) as d:
        file_path = Path(d) / filename

        logger.info("hello %s", file_path)

        with excel.utils.xlsx_manager(excel.template.template_xlsx) as workbook:
            excel.interface.dict_of_dataframes_to_workbook(
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


# fmt: off
@app.get("/srms/{srm_query_or_id}")
def get_srm_single(
    *,
    session: SessionDepends,
    srm_query_or_id: str,
    complete: bool = False,
    subtable: SubTableType = None,
) -> (
    basemodels.results.ResponseEnvelope[basemodels.srm.SRMPublic]
    | basemodels.results.ResponseEnvelope[basemodels.srm.SRMCompletePublic]
    | basemodels.results.ResponseEnvelope[basemodels.srm.SRMMeasurementsPublic]
    | basemodels.results.ResponseEnvelope[basemodels.srm.SRMMeasurementsCompletePublic]
    | basemodels.results.ResponseEnvelope[basemodels.srm.SRMStandardAnalysisPublic]
    | basemodels.results.ResponseEnvelope[basemodels.srm.SRMStandardAnalysisCompletePublic]
    | basemodels.results.ResponseEnvelope[basemodels.srm.SRMRCertPublic]
    | basemodels.results.ResponseEnvelope[basemodels.srm.SRMRCertCompletePublic]
    # fmt: on
):

    srm_table_id: uuid.UUID | None = None
    srm_query: str | None = None
    try:
        srm_table_id = uuid.UUID(srm_query_or_id)
    except ValueError:
        srm_query = srm_query_or_id

    with catch_single_record_errors():
        data_db = crud.get_srm(
            session=session,
            srm_query=srm_query,
            srm_table_id=srm_table_id,
        )
        model = basemodels.srm.PUBLIC_TYPES_COMPLETE_SUBTABLE_MAPPING[
            subtable, complete
        ]

        params: dict[str, Any] = {
            "message": "Hello",
            "data": model.model_validate(data_db),
        }
        return basemodels.results.ResponseEnvelope(**params)
