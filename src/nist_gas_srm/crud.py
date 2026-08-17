"""Basic crud operations"""

from collections.abc import Sequence

from sqlmodel import Session, select

from . import _models as pmodels, models


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


def get_srms(
    *,
    session: Session,
    srm_id: int,
    batch_id: str | None = None,
    lot_id: str | None = None,
) -> Sequence[models.SRMData]:
    """Get multiple srm"""

    query = select(models.SRMData).where(models.SRMData.srm_id == srm_id)

    if batch_id:
        query = query.where(models.SRMData.batch_id == batch_id)
    if lot_id:
        query = query.where(models.SRMData.lot_id == lot_id)

    return session.exec(query).all()


def get_srm(
    *,
    session: Session,
    srm_id: int,
    batch_id: str | None = None,
    lot_id: str | None = None,
) -> models.SRMData:
    """Get single srm"""

    query = select(models.SRMData).where(models.SRMData.srm_id == srm_id)

    if batch_id:
        query = query.where(models.SRMData.batch_id == batch_id)
    if lot_id:
        query = query.where(models.SRMData.lot_id == lot_id)

    return session.exec(query).one()


def add_srm_subtable_row(
    *,
    session: Session,
    srm: models.SRMData,
    obj: models.RatioData
    | models.VendorData
    | models.StandardsData
    | models.RatioAnalysisRandomEffectsData
    | models.RatioAnalysisFixedEffectsData
    | models.PastLotStandardsData
    | models.AdditionalLotStandardsData,
) -> None:
    obj.srmdata = srm
    session.add(obj)
    session.commit()


def add_rcert_subtable_row(
    *,
    session: Session,
    srm: models.SRMData,
    obj: models.RCertSRMValues
    | models.RCertStandardsValues
    | models.RCertAdditionalLotStandards
    | models.RCertCylinderResults
    | models.RCertAnalysisFunctionCoefficients
    | models.RCertCorrelationCoefficients
    | models.RCertOutliers,
) -> None:
    obj.rcertdata = srm.rcert
    session.add(obj)
    session.commit()


# ruff:file-ignore[commented-out-code]
# def add_srm_from_excel_obj(
#     *,
#     session: Session,
#     srmdata_create: pmodels.SRMDataCreate,
#     srmxls: read_excel.SRMExcelFile,
# ) -> None:

#     data: dict[str, Any] = srmdata_create.model_dump()
#     for key, attr, cls in [
#             ("ratios", "ratio_data", models.RatioData),
#             ("vendords", "vendor_data", models.VendorData),
#             ("standards", "standards_data", models.StandardsData),
#             ("ratio_analysis_random_effects", "ratio_analysis_random_effects", models.RatioAnalysisRandomEffectsData),
#             ("ratio_analysis_fixed_effects", "ratio_analysis_fixed_effects", models.RatioAnalysisFixedEffectsData),
#             ("past_lot_standards", "past_lot_standards", models.PastLotStandardsData),
#             ("additional_lot_standards", "additional_lot_standards", models.AdditionalLotStandardsData),
#     ]:

#         data[key] = list(read_excel.frame_to_list_of_models())
