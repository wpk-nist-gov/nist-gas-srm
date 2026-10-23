"""Create initial data from files"""

import logging
from collections.abc import Sequence
from pathlib import Path

import pandas as pd
from sqlmodel import (
    Session,
)

from nist_gas_srm.core import basemodels
from nist_gas_srm.core.excel.utils import parse_excel_filename_to_metadata

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
    path: Path,
) -> None:
    excelfile = pd.ExcelFile(path)

    # do this to circumvent issues covered
    # here: https://github.com/fastapi/sqlmodel/issues/453
    srm_metadata = basemodels.srm.SRMCreate(
        description=path.name,
        **parse_excel_filename_to_metadata(path.name),
    )

    _ = crud.add_srm_from_excel_obj(
        session=session,
        srmdata_create=srm_metadata,
        excelfile=excelfile,
    )


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


if __name__ == "__main__":
    raise SystemExit(main())
