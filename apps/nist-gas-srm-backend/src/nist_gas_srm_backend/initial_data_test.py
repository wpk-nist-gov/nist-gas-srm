"""Create initial data from files"""
# pylint: disable=duplicate-code

import json
import logging
from collections.abc import Sequence
from pathlib import Path

import pandas as pd
from sqlmodel import (
    Session,
)

from nist_gas_srm import basemodels

from . import crud
from .core.db import engine, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# * Options ----------------------------------------------------------------------------
def init() -> None:
    with Session(engine) as session:
        init_db(session)


def add_srm(
    session: Session,
    srm_query: str,
    path: Path,
) -> None:
    excelfile = pd.ExcelFile(path)

    # do this to circumvent issues covered
    # here: https://github.com/fastapi/sqlmodel/issues/453
    srm_metadata = basemodels.srm.SRMCreate.from_srm_query(srm_query)

    _ = crud.add_srm_from_excel_obj(
        session=session,
        srmdata_create=srm_metadata,
        excelfile=excelfile,
    )


def main(argv: Sequence[str] | None = None) -> bool:
    from argparse import ArgumentParser

    parser = ArgumentParser()
    _ = parser.add_argument("--clean", action="store_true")
    _ = parser.add_argument("path", type=Path)

    options = parser.parse_args(argv)
    path: Path = options.path

    sqlite_file_path = Path("database.db")
    if options.clean:
        sqlite_file_path.unlink(missing_ok=True)

    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")

    if options.clean or options.force_add:
        with Session(engine) as session:
            for srm_query in (
                "2627-I",
                "2627a-I",
                "26271-J",
                "22A-a",
                "22A-b",
                "22B-a",
                "22-a",
                json.dumps({
                    "srm_number": 123,
                    "lot": "hello",
                    "units": "ppb",
                    "note": "other",
                }),
            ):
                logger.info("Path: %s", path)
                add_srm(session, srm_query=srm_query, path=path)

    return False


if __name__ == "__main__":
    raise SystemExit(main())
