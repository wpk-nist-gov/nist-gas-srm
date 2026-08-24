"""Create initial data from files"""
# ruff:file-ignore[magic-value-comparison,commented-out-code]

import logging
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any, cast

import pandas as pd
from sqlmodel import (
    Session,
    col,
    delete,
    select,
)

from nist_gas_srm.core import basemodels
from nist_gas_srm.core.convert import SRMRCertConverter
from nist_gas_srm.core.utils import parse_excel_filename_to_metadata

from . import crud, models
from .core.db import engine, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# * Options -------------------------------------------------------------------
def init() -> None:
    with Session(engine) as session:
        init_db(session)


def add_srm(
    session: Session,
    path: Path,
) -> None:
    srmxls = SRMRCertConverter(path)

    # do this to circumvent issues covered
    # here: https://github.com/fastapi/sqlmodel/issues/453
    srm_metadata = basemodels.SRMDataCreate(
        name=path.name,
        **parse_excel_filename_to_metadata(path.name),
    )

    _ = crud.add_srm_from_excel_obj(
        session=session, srmdata_create=srm_metadata, srmxls=srmxls
    )

    # data: dict[str, Any] = {
    #     name: list(frame_to_list_of_models(caller(srmxls), cls))
    #     for name, caller, cls in models.SRMDATA_NAME_CALLER_CLS
    # }

    # data_rcert: dict[str, Any] = {
    #     name: list(frame_to_list_of_models(caller(srmxls.rcert), cls))
    #     for name, caller, cls in models.RCERTDATA_NAME_CALLER_CLS
    # }

    # data["rcert"] = models.RCertData(**data_rcert)

    # srm = models.SRMData(**srm_metadata.model_dump(), **data)

    # # NOTE: see https://github.com/fastapi/sqlmodel/issues/254
    # session.add(srm)
    # session.commit()


def get_srm_by_name(session: Session, srm: str | models.SRMData) -> models.SRMData:
    if isinstance(srm, models.SRMData):
        return srm
    return session.exec(select(models.SRMData).where(models.SRMData.name == srm)).one()


def delete_srm(session: Session, srm: str | models.SRMData) -> None:
    srm = get_srm_by_name(session, srm)
    session.delete(srm)
    session.commit()


def delete_subtable(
    session: Session,
    srm: str | models.SRMData,
    table: type[basemodels.SRMDataForeignKey],
) -> None:
    srm = get_srm_by_name(session, srm)
    _ = session.exec(delete(table).where(col(table.srmdata_id) == srm.id))
    session.commit()


def add_srm_subtable_row(
    session: Session,
    srm: str | models.SRMData,
    obj: models.SRMSubTable,
) -> None:
    srm = get_srm_by_name(session, srm)
    obj.srmdata = srm
    session.add(obj)
    session.commit()


def get_dataframe_or_iterator_of_dataframe(
    session: Session, statement: Any, **kwargs: Any
) -> pd.DataFrame | Iterator[pd.DataFrame]:
    return cast(
        "pd.DataFrame | Iterator[pd.DataFrame]",
        pd.read_sql(
            statement,
            cast("Any", session.bind),
            **kwargs,
        ),
    )


def get_dataframe(session: Session, statement: Any, **kwargs: Any) -> pd.DataFrame:
    out = get_dataframe_or_iterator_of_dataframe(session, statement, **kwargs)
    if isinstance(out, pd.DataFrame):
        return out

    msg = "Returned an iterator for statement"
    raise ValueError(msg)


# Get direct from database
# def get_standards_data_stats(session: Session, srm_name: str) -> None:
#     statement = (
#         select(
#             StandardsData.name,
#             StandardsData.number,
#             func.avg(StandardsData.ratio),
#             (func.avg(col(StandardsData.ratio)) / func.count(col(StandardsData.ratio))),
#             # func.stddev(StandardsData.ratio),
#         )
#         .join(models.SRMData)
#         .where(models.SRMData.name == srm_name)
#         .group_by(StandardsData.name)
#     )


def main(argv: Sequence[str] | None = None) -> bool:
    from argparse import ArgumentParser

    parser = ArgumentParser()
    _ = parser.add_argument("--clean", action="store_true")
    _ = parser.add_argument("--force-add", action="store_true")
    _ = parser.add_argument("paths", nargs="+", type=Path)

    options = parser.parse_args(argv)
    paths: list[Path] = options.paths

    sqlite_file_path = Path("database.db")
    if options.clean:
        sqlite_file_path.unlink(missing_ok=True)

    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")

    if options.clean or options.force_add:
        with Session(engine) as session:
            for path in paths:
                logger.info("Path: %s", path)
                add_srm(session, path)
        return False

        new_ratio = models.RatioData.model_validate({
            "name": "abc",
            "number": "100",
            "ratio": 0.5,
            "ls_set": 100,
            "break_set": 100,
            "day": 100,
            "port": 100,
            "value_g": 0.5,
            "test": None,
        })
        with Session(engine) as session:
            add_srm_subtable_row(session, paths[0].name, new_ratio)

    # delete a subtable
    with Session(engine) as session:
        delete_subtable(session, paths[0].name, models.RatioAnalysisFixedEffectsData)

    with Session(engine) as session:
        delete_srm(session, paths[0].name)

    # with Session(engine) as session:
    #     print(
    #         get_dataframe(
    #             session=session,
    #             statement=select(RatioData)
    #             .join(models.SRMData)
    #             .where(models.SRMData.name == paths[0].name),
    #         )
    #     )

    #     print(
    #         get_dataframe(
    #             session=session,
    #             statement=select(VendorData)
    #             .join(models.SRMData)
    #             .where(models.SRMData.name == paths[0].name),
    #         )
    #     )

    # with Session(engine) as session:
    #     get_standards_data_stats(session, paths[0].name)

    # with Session(engine) as session:
    #     df = get_dataframe(
    #         session=session,
    #         statement=select_columns(
    #             StandardsData.name,
    #             StandardsData.number,
    #             StandardsData.ratio,
    #             StandardsData.concentration,
    #             StandardsData.unc,
    #         )
    #         .join(models.SRMData)
    #         .where(models.SRMData.name == paths[0].name),
    #     )

    #     from .stats import get_standards_data_stats_table

    #     print(get_standards_data_stats_table(df))

    # with Session(engine) as session:
    #     df = get_dataframe(
    #         session=session,
    #         statement=select(
    #             RatioData,
    #         )
    #         .join(models.SRMData)
    #         .where(models.SRMData.name == paths[0].name),
    #     )
    #     df = df.query("number != 100")
    #     factors = [None, "number", "port", "break_set", "day"]
    #     for factor in factors:
    #         print(factor)
    #         out = get_ratio_data_stats_table(df, factor)
    #         if factor is None:
    #             print(out)
    #         else:
    #             print(get_ratio_data_stats_table(out, factor=None, col="ave"))

    with Session(engine) as session:
        data = session.exec(
            select(models.SRMData).where(col(models.SRMData.srm_id) == 2627)
        ).all()
        logger.info("data %s", data)

    return False


if __name__ == "__main__":
    raise SystemExit(main())
