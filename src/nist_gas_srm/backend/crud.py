"""Basic crud operations"""

from collections.abc import Iterable, Sequence

import pandas as pd
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import Session, SQLModel, and_ as sql_and_, or_ as sql_or_, select

from nist_gas_srm.core import basemodels, excel_interface  # , read_excel

from . import models


def create_srm(
    *, session: Session, srmdata_create: basemodels.srm.SRMCreate
) -> models.SRMTable:
    obj = models.SRMTable.model_validate(srmdata_create)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


def update_srm(
    *,
    session: Session,
    db_srmdata: models.SRMTable,
    srmdata_in: basemodels.srm.SRMUpdate,
) -> models.SRMTable:
    srmdata_data = srmdata_in.model_dump(exclude_unset=True)

    _ = db_srmdata.sqlmodel_update(srmdata_data)
    session.add(db_srmdata)
    session.commit()
    session.refresh(db_srmdata)
    return db_srmdata


def _get_sql_and_from_model(
    query: basemodels.srm.SRMQuery,
    model: type[SQLModel] = models.SRMTable,
) -> ColumnElement[bool]:
    return sql_and_(
        *(
            getattr(model, attr) == value
            for attr, value in query.model_dump(exclude_unset=True).items()
        )
    )


def _get_where_from_srm_query(
    srm_query: str | basemodels.srm.SRMQuery | Iterable[basemodels.srm.SRMQuery | str],
) -> ColumnElement[bool]:

    if isinstance(srm_query, str):
        srm_query = basemodels.srm.SRMQuery.from_srm_query(srm_query)

    if isinstance(srm_query, basemodels.srm.SRMQuery):
        where_ = _get_sql_and_from_model(srm_query)

    else:
        srm_query = basemodels.srm.SRMQuery.from_srm_queries(srm_query)
        where_ = sql_or_(*(_get_sql_and_from_model(obj) for obj in srm_query))
    return where_


def _get_srm_result(
    *,
    session: Session,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm_query: str
    | basemodels.srm.SRMQuery
    | Sequence[basemodels.srm.SRMQuery | str]
    | None = None,
) -> ScalarResult[models.SRMTable]:

    query = select(models.SRMTable)
    if srm_query is not None:
        where_ = _get_where_from_srm_query(srm_query)
        query = query.where(where_)
        return session.exec(query)
    srm_query = basemodels.srm.SRMQuery.from_params_exclude_none(
        srm_id=srm_id, batch_id=batch_id, lot_id=lot_id
    )
    if srm_query.model_dump(exclude_unset=True):
        where_ = _get_where_from_srm_query(srm_query)
        query = query.where(where_)

    return session.exec(query)


def get_srm(
    *,
    session: Session,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm_query: basemodels.srm.SRMQuery | str | None = None,
) -> models.SRMTable:
    """Get single srm"""

    return _get_srm_result(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
        srm_query=srm_query,
    ).one()


def get_srms(
    *,
    session: Session,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm_query: Sequence[basemodels.srm.SRMQuery | str] | None = None,
) -> Sequence[models.SRMTable]:
    """Get multiple srm"""
    return _get_srm_result(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
        srm_query=srm_query,
    ).all()


def get_rcert(
    *,
    session: Session,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm_query: basemodels.srm.SRMQuery | str | None = None,
) -> models.RCertTable:

    return get_srm(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
        srm_query=srm_query,
    ).rcert


def get_rcerts(
    *,
    session: Session,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm_query: Sequence[basemodels.srm.SRMQuery | str] | None = None,
) -> Sequence[models.RCertTable]:

    return [
        _.rcert
        for _ in get_srms(
            session=session,
            srm_id=srm_id,
            batch_id=batch_id,
            lot_id=lot_id,
            srm_query=srm_query,
        )
    ]


def get_measurement(
    *,
    session: Session,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm_query: basemodels.srm.SRMQuery | str | None = None,
) -> models.Measurements:

    return get_srm(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
        srm_query=srm_query,
    ).measurements


def get_measurements(
    *,
    session: Session,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm_query: Sequence[basemodels.srm.SRMQuery | str] | None = None,
) -> Sequence[models.Measurements]:

    return [
        _.measurements
        for _ in get_srms(
            session=session,
            srm_id=srm_id,
            batch_id=batch_id,
            lot_id=lot_id,
            srm_query=srm_query,
        )
    ]


def get_standard_analysis(
    *,
    session: Session,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm_query: basemodels.srm.SRMQuery | str | None = None,
) -> models.StandardAnalysisTable:

    return get_srm(
        session=session,
        srm_id=srm_id,
        batch_id=batch_id,
        lot_id=lot_id,
        srm_query=srm_query,
    ).standard_analysis


def get_standard_analyses(
    *,
    session: Session,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
    srm_query: Sequence[basemodels.srm.SRMQuery | str] | None = None,
) -> Sequence[models.StandardAnalysisTable]:

    return [
        _.standard_analysis
        for _ in get_srms(
            session=session,
            srm_id=srm_id,
            batch_id=batch_id,
            lot_id=lot_id,
            srm_query=srm_query,
        )
    ]


def add_srm_item(
    *,
    session: Session,
    srm: models.SRMTable,
    obj: models.measurements.MeasurementsSubTableType,
) -> None:
    """Add raw data item (row)."""
    obj.srmdata = srm
    session.add(obj)
    session.commit()


def add_rcert_item(
    *,
    session: Session,
    srm: models.SRMTable,
    obj: models.rcert.RCertSubTableType,
) -> None:
    """Add rcert item (row)."""
    obj.rcertdata = srm.rcert
    session.add(obj)
    session.commit()


def create_srm_item(
    *,
    session: Session,
    srmdata_id: int,
    item_in: basemodels.measurements.MeasurementsSubTableCreateType,
    cls: type[models.measurements.MeasurementsSubTableType],
) -> models.measurements.MeasurementsSubTableType:

    db_item = cls.model_validate(item_in, update={"srmdata_id": srmdata_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


def create_rcert_item(
    *,
    session: Session,
    rcert_id: int,
    item_in: basemodels.rcert.RCertSubTableCreateType,
    cls: type[models.rcert.RCertSubTableType],
) -> models.rcert.RCertSubTableType:
    db_item = cls.model_validate(item_in, update={"rcert_id": rcert_id})
    session.add(db_item)
    session.refresh(db_item)
    return db_item


# ruff:file-ignore[commented-out-code]
# the "other" way of doing it.  Have a hack that seems to work for now below
# def add_srm_from_excel_obj(
#     *,
#     session: Session,
#     srmdata_create: basemodels.srm.SRMCreate,
#     srmxls: read_excel.SRMExcelFile,
# ) -> models.SRMTable:

#     data: dict[str, Any] = {
#         name: list(read_excel.frame_to_list_of_models(caller(srmxls), cls))
#         for name, caller, cls in models.SRMDATA_NAME_CALLER_CLS
#     }

#     data_rcert: dict[str, Any] = {
#         name: list(read_excel.frame_to_list_of_models(caller(srmxls.rcert), cls))
#         for name, caller, cls in models.RCERTDATA_NAME_CALLER_CLS
#     }

#     data["rcert"] = models.RCertTable(**data_rcert)

#     srm = models.SRMTable(**srmdata_create.model_dump(), **data)
#     session.add(srm)
#     session.commit()
#     session.refresh(srm)
#     return srm


def add_srm_from_excel_obj(
    *,
    session: Session,
    srmdata_create: basemodels.srm.SRMCreate,
    excelfile: pd.ExcelFile,
) -> models.SRMTable:

    data = excel_interface.excel_to_json(
        excelfile,
        model=basemodels.srm.SRMCompleteCreate,
    )
    data.update(srmdata_create.model_dump())

    srmdata_in = basemodels.srm.SRMCompleteCreate.model_validate(data)
    return add_srm_from_create(session=session, srmdata_in=srmdata_in)


def add_srm_from_create(
    *,
    session: Session,
    srmdata_in: basemodels.srm.SRMCreate,
) -> models.SRMTable:

    # NOTE: this only works with the _FixMixin in models.py
    # see https://github.com/fastapi/sqlmodel/issues/293
    srm = models.SRMTable.model_validate(srmdata_in)
    session.add(srm)
    session.commit()
    session.refresh(srm)
    return srm


def delete_srm(*, session: Session, srm: models.SRMTable) -> None:
    session.delete(srm)
    session.commit()
