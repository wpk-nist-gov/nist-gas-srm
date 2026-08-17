"""Basic model"""

# ruff:file-ignore[commented-out-code]

# ruff:file-ignore[print]
import logging
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any, cast

import pandas as pd
from sqlalchemy import Engine
from sqlmodel import (
    Relationship,
    Session,
    SQLModel,
    col,
    create_engine,
    delete,
    select,
)
from sqlmodel._compat import SQLModelConfig  # ruff:ignore[import-private-name]
from sqlmodel.sql._expression_select_cls import Select, SelectOfScalar

# from ._model import (
#     AdditionalLotStandardsData as AdditionalLotStandardsData,
#     PastLotStandardsData as PastLotStandardsData,
#     RatioAnalysisFixedEffectsData as RatioAnalysisFixedEffectsData,
#     RatioAnalysisRandomEffectsData as RatioAnalysisRandomEffectsData,
#     RatioData as RatioData,
#     SRMData as SRMData,
#     SRMDataCreate,
#     SRMDataForeignKey,
#     StandardsData as StandardsData,
#     VendorData as VendorData,
# )
from ._model import (
    AdditionalLotStandardsDataBase,
    IDPrimaryKey,
    PastLotStandardsDataBase,
    RatioAnalysisFixedEffectsDataBase,
    RatioAnalysisRandomEffectsDataBase,
    RatioDataBase,
    SRMDataBase,
    SRMDataCreate,
    SRMDataForeignKey,
    StandardsDataBase,
    VendorDataBase,
)
from .core.utils import parse_excel_filename_to_metadata
from .read_excel import (
    SRMExcelFile,
    frame_to_list_of_models,
)

FORMAT = "[%(name)s - %(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)


# Sql Models ------------------------------------------------------------------
class SRMData(SRMDataBase, IDPrimaryKey, table=True):
    """Metadata table"""

    model_config = SQLModelConfig(str_to_lower=True)

    ratios: list["RatioData"] = Relationship(
        back_populates="srmdata", cascade_delete=True
    )
    vendors: list["VendorData"] = Relationship(
        back_populates="srmdata", cascade_delete=True
    )
    standards: list["StandardsData"] = Relationship(
        back_populates="srmdata", cascade_delete=True
    )
    past_lot_standards: list["PastLotStandardsData"] = Relationship(
        back_populates="srmdata",
        cascade_delete=True,
    )
    additional_lot_standards: list["AdditionalLotStandardsData"] = Relationship(
        back_populates="srmdata",
        cascade_delete=True,
    )
    ratio_analysis_random_effects: list["RatioAnalysisRandomEffectsData"] = (
        Relationship(
            back_populates="srmdata",
            cascade_delete=True,
        )
    )
    ratio_analysis_fixed_effects: list["RatioAnalysisFixedEffectsData"] = Relationship(
        back_populates="srmdata",
        cascade_delete=True,
    )


# * subtables
class RatioData(RatioDataBase, IDPrimaryKey, table=True):
    """Ratio Data table"""

    srmdata: SRMData | None = Relationship(back_populates="ratios")


class RatioAnalysisRandomEffectsData(
    RatioAnalysisRandomEffectsDataBase, IDPrimaryKey, table=True
):
    srmdata: SRMData | None = Relationship(
        back_populates="ratio_analysis_random_effects"
    )


class RatioAnalysisFixedEffectsData(
    RatioAnalysisFixedEffectsDataBase, IDPrimaryKey, table=True
):
    srmdata: SRMData | None = Relationship(
        back_populates="ratio_analysis_fixed_effects"
    )


class VendorData(VendorDataBase, IDPrimaryKey, table=True):
    """Vendor data table"""

    srmdata: SRMData | None = Relationship(back_populates="vendors")


class StandardsData(StandardsDataBase, IDPrimaryKey, table=True):
    """Standards data table"""

    srmdata: SRMData | None = Relationship(back_populates="standards")


class PastLotStandardsData(PastLotStandardsDataBase, IDPrimaryKey, table=True):
    """Past lot standards table"""

    srmdata: SRMData | None = Relationship(back_populates="past_lot_standards")


class AdditionalLotStandardsData(
    AdditionalLotStandardsDataBase, IDPrimaryKey, table=True
):
    """Additional lot standards table"""

    srmdata: SRMData | None = Relationship(back_populates="additional_lot_standards")


# * Utils ---------------------------------------------------------------------
def select_columns(*columns: Any) -> Select[Any] | SelectOfScalar[Any]:
    """For typing purposes"""
    return cast("Select[Any] | SelectOfScalar[Any]", select(*columns))


# * Options -------------------------------------------------------------------
def create_db_and_tables(engine: Engine) -> None:
    SQLModel.metadata.create_all(engine)


def add_srm(
    session: Session,
    path: Path,
) -> None:
    srmxls = SRMExcelFile(path)

    # do this to circumvent issues covered
    # here: https://github.com/fastapi/sqlmodel/issues/453
    srm_metadata = SRMDataCreate(
        name=path.name,
        **parse_excel_filename_to_metadata(path.name),
    )

    srm = SRMData(
        **srm_metadata.model_dump(),
        ratios=list(frame_to_list_of_models(srmxls.ratio_data(), RatioData)),
        vendors=list(frame_to_list_of_models(srmxls.vendor_data(), VendorData)),
        standards=list(frame_to_list_of_models(srmxls.standards_data(), StandardsData)),
        ratio_analysis_random_effects=list(
            frame_to_list_of_models(
                srmxls.ratio_analysis_random_effects(), RatioAnalysisRandomEffectsData
            )
        ),
        ratio_analysis_fixed_effects=list(
            frame_to_list_of_models(
                srmxls.ratio_analysis_fixed_effects_intercept(),
                RatioAnalysisFixedEffectsData,
            )
        ),
        past_lot_standards=list(
            frame_to_list_of_models(srmxls.past_lot_standards(), PastLotStandardsData)
        ),
        additional_lot_standards=list(
            frame_to_list_of_models(
                srmxls.additional_lot_standards(), AdditionalLotStandardsData
            )
        ),
    )

    # NOTE: see https://github.com/fastapi/sqlmodel/issues/254
    session.add(srm)
    session.commit()


def get_srm_by_name(session: Session, srm: str | SRMData) -> SRMData:
    if isinstance(srm, SRMData):
        return srm
    return session.exec(select(SRMData).where(SRMData.name == srm)).one()


def delete_srm(session: Session, srm: str | SRMData) -> None:
    srm = get_srm_by_name(session, srm)
    session.delete(srm)
    session.commit()


def delete_subtable(
    session: Session, srm: str | SRMData, table: type[SRMDataForeignKey]
) -> None:
    srm = get_srm_by_name(session, srm)
    _ = session.exec(delete(table).where(col(table.srmdata_id) == srm.id))
    session.commit()


def add_srm_subtable_row(
    session: Session,
    srm: str | SRMData,
    obj: RatioData
    | VendorData
    | StandardsData
    | PastLotStandardsData
    | AdditionalLotStandardsData,
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
#         .join(SRMData)
#         .where(SRMData.name == srm_name)
#         .group_by(StandardsData.name)
#     )


def main(argv: Sequence[str] | None = None) -> bool:
    from argparse import ArgumentParser

    parser = ArgumentParser()
    _ = parser.add_argument("--clean", action="store_true")
    _ = parser.add_argument("paths", nargs="+", type=Path)

    options = parser.parse_args(argv)
    paths: list[Path] = options.paths

    sqlite_file_path = Path("database.db")
    sqlite_url = f"sqlite:///{sqlite_file_path}"

    engine = create_engine(sqlite_url, echo=True)

    if options.clean:
        sqlite_file_path.unlink(missing_ok=True)

    create_db_and_tables(engine)

    if options.clean:
        with Session(engine) as session:
            for path in paths:
                logger.info("Path: %s", path)
                add_srm(session, path)

        new_ratio = RatioData.model_validate({
            "name": "abc",
            "number": 100,
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
    # with Session(engine) as session:
    #     delete_subtable(session, paths[0].name, RatioAnalysisFixedEffectsData)

    # with Session(engine) as session:
    #     delete_srm(session, paths[0].name)

    # with Session(engine) as session:
    #     print(
    #         get_dataframe(
    #             session=session,
    #             statement=select(RatioData)
    #             .join(SRMData)
    #             .where(SRMData.name == paths[0].name),
    #         )
    #     )

    #     print(
    #         get_dataframe(
    #             session=session,
    #             statement=select(VendorData)
    #             .join(SRMData)
    #             .where(SRMData.name == paths[0].name),
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
    #         .join(SRMData)
    #         .where(SRMData.name == paths[0].name),
    #     )

    #     from .stats import get_standards_data_stats_table

    #     print(get_standards_data_stats_table(df))

    # with Session(engine) as session:
    #     df = get_dataframe(
    #         session=session,
    #         statement=select(
    #             RatioData,
    #         )
    #         .join(SRMData)
    #         .where(SRMData.name == paths[0].name),
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
        data = session.exec(select(SRMData).where(col(SRMData.srm_id) == 2627)).all()  # ruff:ignore[magic-value-comparison]
        print(data)

    return False


if __name__ == "__main__":
    raise SystemExit(main())
