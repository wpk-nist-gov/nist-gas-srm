"""Create initial data from files"""
# ruff:file-ignore[commented-out-code]

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
from nist_gas_srm.core.basemodels.keys import SRMForeignKey
from nist_gas_srm.core.excel_utils import parse_excel_filename_to_metadata

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
    excelfile = pd.ExcelFile(path)

    # do this to circumvent issues covered
    # here: https://github.com/fastapi/sqlmodel/issues/453
    srm_metadata = basemodels.srm.SRMCreate(
        name=path.name,
        **parse_excel_filename_to_metadata(path.name),
    )

    _ = crud.add_srm_from_excel_obj(
        session=session,
        srmdata_create=srm_metadata,
        excelfile=excelfile,
    )


def get_srm_by_name(session: Session, srm: str | models.SRMTable) -> models.SRMTable:
    if isinstance(srm, models.SRMTable):
        return srm
    return session.exec(
        select(models.SRMTable).where(models.SRMTable.name == srm)
    ).one()


def delete_srm(session: Session, srm: str | models.SRMTable) -> None:
    srm = get_srm_by_name(session, srm)
    session.delete(srm)
    session.commit()


def delete_subtable(
    session: Session,
    srm: str | models.SRMTable,
    table: type[SRMForeignKey],
) -> None:
    srm = get_srm_by_name(session, srm)
    _ = session.exec(delete(table).where(col(table.srm_id) == srm.id))
    session.commit()


def add_srm_subtable_row(
    session: Session,
    srm: str | models.SRMTable,
    obj: models.measurements.MeasurementsSubTableType,
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
#             MeasurementsStandards.name,
#             MeasurementsStandards.number,
#             func.avg(MeasurementsStandards.ratio),
#             (func.avg(col(MeasurementsStandards.ratio)) / func.count(col(MeasurementsStandards.ratio))),
#             # func.stddev(MeasurementsStandards.ratio),
#         )
#         .join(models.SRMTable)
#         .where(models.SRMTable.name == srm_name)
#         .group_by(MeasurementsStandards.name)
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

    #     new_ratio = models.MeasurementsRatios.model_validate({
    #         "name": "abc",
    #         "number": "100",
    #         "ratio": 0.5,
    #         "ls_set": 100,
    #         "break_set": 100,
    #         "day": 100,
    #         "port": 100,
    #         "value_g": 0.5,
    #         "test": None,
    #     })
    #     with Session(engine) as session:
    #         add_srm_subtable_row(session, paths[0].name, new_ratio)

    # # delete a subtable
    # with Session(engine) as session:
    #     delete_subtable(session, paths[0].name, models.MeasurementsRatioAnalysisFixedEffects)

    # with Session(engine) as session:
    #     delete_srm(session, paths[0].name)

    # with Session(engine) as session:
    #     print(
    #         get_dataframe(
    #             session=session,
    #             statement=select(MeasurementsRatios)
    #             .join(models.SRMTable)
    #             .where(models.SRMTable.name == paths[0].name),
    #         )
    #     )

    #     print(
    #         get_dataframe(
    #             session=session,
    #             statement=select(MeasurementsVendors)
    #             .join(models.SRMTable)
    #             .where(models.SRMTable.name == paths[0].name),
    #         )
    #     )

    # with Session(engine) as session:
    #     get_standards_data_stats(session, paths[0].name)

    # with Session(engine) as session:
    #     df = get_dataframe(
    #         session=session,
    #         statement=select_columns(
    #             MeasurementsStandards.name,
    #             MeasurementsStandards.number,
    #             MeasurementsStandards.ratio,
    #             MeasurementsStandards.concentration,
    #             MeasurementsStandards.unc,
    #         )
    #         .join(models.SRMTable)
    #         .where(models.SRMTable.name == paths[0].name),
    #     )

    #     from .stats import get_standards_data_stats_table

    #     print(get_standards_data_stats_table(df))

    # with Session(engine) as session:
    #     df = get_dataframe(
    #         session=session,
    #         statement=select(
    #             MeasurementsRatios,
    #         )
    #         .join(models.SRMTable)
    #         .where(models.SRMTable.name == paths[0].name),
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

    # with Session(engine) as session:
    #     data = session.exec(
    #         select(models.SRMTable).where(col(models.SRMTable.srm_id) == 2627)
    #     ).all()
    #     logger.info("data %s", data)

    return False


if __name__ == "__main__":
    raise SystemExit(main())
