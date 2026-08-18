"""Basic crud operations"""

from collections.abc import Sequence
from typing import Any

from sqlmodel import Session, select

from . import _models as pmodels, models, read_excel


def create_srm(
    *, session: Session, srmdata_create: pmodels.SRMDataCreate
) -> models.SRMData:
    obj = models.SRMData.model_validate(srmdata_create)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


def update_srm(
    *, session: Session, db_srmdata: models.SRMData, srmdata_in: pmodels.SRMDataUpdate
) -> models.SRMData:
    srmdata_data = srmdata_in.model_dump(exclude_unset=True)

    _ = db_srmdata.sqlmodel_update(srmdata_data)
    session.add(db_srmdata)
    session.commit()
    session.refresh(db_srmdata)
    return db_srmdata


def get_srm(
    *,
    session: Session,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
) -> models.SRMData:
    """Get single srm"""

    query = select(models.SRMData)

    if srm_id is not None:
        query = query.where(models.SRMData.srm_id == srm_id)
    if batch_id is not None:
        query = query.where(models.SRMData.batch_id == batch_id)
    if lot_id is not None:
        query = query.where(models.SRMData.lot_id == lot_id)

    return session.exec(query).one()


def get_srms(
    *,
    session: Session,
    srm_id: int | None,
    batch_id: str | None = None,
    lot_id: str | None = None,
) -> Sequence[models.SRMData]:
    """Get multiple srm"""

    query = select(models.SRMData)

    if srm_id is not None:
        query = query.where(models.SRMData.srm_id == srm_id)
    if batch_id is not None:
        query = query.where(models.SRMData.batch_id == batch_id)
    if lot_id is not None:
        query = query.where(models.SRMData.lot_id == lot_id)

    return session.exec(query).all()


def get_rcert(
    *,
    session: Session,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
) -> models.RCertData:

    return get_srm(
        session=session, srm_id=srm_id, batch_id=batch_id, lot_id=lot_id
    ).rcert


def get_rcerts(
    *,
    session: Session,
    srm_id: int | None = None,
    batch_id: str | None = None,
    lot_id: str | None = None,
) -> Sequence[models.RCertData]:

    return [
        _.rcert
        for _ in get_srms(
            session=session, srm_id=srm_id, batch_id=batch_id, lot_id=lot_id
        )
    ]


def add_srm_item(
    *,
    session: Session,
    srm: models.SRMData,
    obj: models.SRMSubTable,
) -> None:
    """Add raw data item (row)."""
    obj.srmdata = srm
    session.add(obj)
    session.commit()


def add_rcert_item(
    *,
    session: Session,
    srm: models.SRMData,
    obj: models.RCertSubTable,
) -> None:
    """Add rcert item (row)."""
    obj.rcertdata = srm.rcert
    session.add(obj)
    session.commit()


def create_srm_item(
    *,
    session: Session,
    srmdata_id: int,
    item_in: pmodels.SRMSubTableCreate,
    cls: type[models.SRMSubTable],
) -> models.SRMSubTable:

    db_item = cls.model_validate(item_in, update={"srmdata_id": srmdata_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


def create_rcert_item(
    *,
    session: Session,
    rcert_id: int,
    item_in: pmodels.RCertSubTableCreate,
    cls: type[models.RCertSubTable],
) -> models.RCertSubTable:
    db_item = cls.model_validate(item_in, update={"rcert_id": rcert_id})
    session.add(db_item)
    session.refresh(db_item)
    return db_item


def add_srm_from_excel_obj(
    *,
    session: Session,
    srmdata_create: pmodels.SRMDataCreate,
    srmxls: read_excel.SRMExcelFile,
) -> models.SRMData:

    data: dict[str, Any] = {
        name: list(read_excel.frame_to_list_of_models(caller(srmxls), cls))
        for name, caller, cls in models.SRMDATA_NAME_CALLER_CLS
    }

    data_rcert: dict[str, Any] = {
        name: list(read_excel.frame_to_list_of_models(caller(srmxls.rcert), cls))
        for name, caller, cls in models.RCERTDATA_NAME_CALLER_CLS
    }

    data["rcert"] = models.RCertData(**data_rcert)

    srm = models.SRMData(**srmdata_create.model_dump(), **data)
    session.add(srm)
    session.commit()
    session.refresh(srm)
    return srm


def delete_srm(*, session: Session, srm: models.SRMData) -> None:
    session.delete(srm)
    session.commit()
