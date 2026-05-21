"""Basic model"""

# ruff: noqa: T201

import logging
from collections.abc import Iterator, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any, cast

import pandas as pd
from pydantic import BeforeValidator
from pydantic.alias_generators import to_pascal
from sqlalchemy import Column, DateTime, Engine
from sqlmodel import (
    VARCHAR,
    Field,
    Relationship,
    Session,
    SQLModel,
    col,
    create_engine,
    delete,
    select,
)
from sqlmodel._compat import SQLModelConfig  # noqa: PLC2701
from sqlmodel.sql._expression_select_cls import Select, SelectOfScalar

from nist_gas_srm.stats import get_ratio_data_stats_table

from .core.validate import validate_nan_to_none
from .read_excel import (
    SRMExcelFile,
    frame_to_list_of_models,
)

FORMAT = "[%(name)s - %(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)


# * Utils


def select_columns(*columns: Any) -> Select[Any] | SelectOfScalar[Any]:
    """For typing purposes"""
    return cast("Select[Any] | SelectOfScalar[Any]", select(*columns))


# * Common --------------------------------------------------------------------
class _IDPrimaryKey(SQLModel):
    id: int | None = Field(default=None, primary_key=True)


class _IDPrimaryKeyPublic(SQLModel):
    id: int


class _SampleIDAndNumber(SQLModel):
    model_config = SQLModelConfig(populate_by_name=True)

    name: str = Field(index=True, alias="SampleID")
    number: int = Field(alias="SampleNo")


class _SampleIDAndNumberUpdate(SQLModel):
    model_config = SQLModelConfig(populate_by_name=True)

    name: str | None = None
    number: int | None = None


class _SRMDataForeignKey(SQLModel):
    srmdata_id: int | None = Field(
        default=None, foreign_key="srmdata.id", ondelete="CASCADE"
    )


class _SRMDataForeignKeyUpdate(SQLModel):
    srmdata_id: int | None = None


# * Top level data (per worksheet) --------------------------------------------
class SRMDataBase(SQLModel):
    """Metadata base class"""

    name: str = Field(sa_column=Column("name", VARCHAR, unique=True, index=True))
    timestamp: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(UTC),
    )


class SRMData(SRMDataBase, _IDPrimaryKey, table=True):
    """Metadata table"""

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


class SRMDataPublic(SRMDataBase, _IDPrimaryKeyPublic):
    pass


class SRMDataCreate(SRMDataBase):
    pass


class SRMDataUpdate(SQLModel):
    name: str | None = None
    timestamp: datetime | None = None


# * Tables --------------------------------------------------------------------
# ** Ratio Data ---------------------------------------------------------------
class RatioDataBase(_SampleIDAndNumber, _SRMDataForeignKey):
    """Ratio data base class"""

    model_config = SQLModelConfig(alias_generator=to_pascal, populate_by_name=True)

    ratio: float
    ls_set: int = Field(alias="LSSet")
    break_set: int
    day: int
    port: int
    value_g: float
    test: Annotated[str | None, BeforeValidator(validate_nan_to_none)]


class RatioData(RatioDataBase, _IDPrimaryKey, table=True):
    """Ratio Data table"""

    srmdata: SRMData | None = Relationship(back_populates="ratios")


class RatioDataPublic(RatioDataBase, _IDPrimaryKeyPublic):
    pass


class RatioDataCreate(RatioDataBase):
    pass


class RatioDataUpdate(_SampleIDAndNumberUpdate, _SRMDataForeignKeyUpdate):
    ratio: float | None = None
    ls_set: int | None = None
    break_set: int | None = None
    day: int | None = None
    port: int | None = None
    value_g: float
    test: Annotated[str | None, BeforeValidator(validate_nan_to_none)] = None


# ** Ratio Analysis -----------------------------------------------------------
class RatioAnalysisRandomEffectsDataBase(_SRMDataForeignKey):
    model_config = SQLModelConfig(alias_generator=to_pascal, populate_by_name=True)

    groups: str
    name: Annotated[str | None, BeforeValidator(validate_nan_to_none)]
    stddev: float = Field(alias="Std Dev")
    count: Annotated[int | None, BeforeValidator(validate_nan_to_none)] = Field(
        alias="No"
    )


class RatioAnalysisRandomEffectsData(
    RatioAnalysisRandomEffectsDataBase, _IDPrimaryKey, table=True
):
    srmdata: SRMData | None = Relationship(
        back_populates="ratio_analysis_random_effects"
    )


class RatioAnalysisRandomEffectsDataPublic(
    RatioAnalysisRandomEffectsDataBase, _IDPrimaryKeyPublic
):
    pass


class RatioAnalysisRandomEffectsDataUpdate(_SRMDataForeignKeyUpdate):
    groups: str | None
    name: str | None
    stddev: float | None
    count: int | None


class RatioAnalysisFixedEffectsDataBase(_SRMDataForeignKey):
    model_config = SQLModelConfig(alias_generator=to_pascal, populate_by_name=True)

    estimate: float
    stderr: float = Field(alias="Std Error")
    t_value: float = Field(alias="t value")


class RatioAnalysisFixedEffectsData(
    RatioAnalysisFixedEffectsDataBase, _IDPrimaryKey, table=True
):
    srmdata: SRMData | None = Relationship(
        back_populates="ratio_analysis_fixed_effects"
    )


class RatioAnalysisFixedEffectsDataPublic(
    RatioAnalysisFixedEffectsDataBase, _IDPrimaryKeyPublic
):
    pass


class RatioAnalysisFixedEffectsDataUpdate(_SRMDataForeignKeyUpdate):
    estimate: float | None
    stderr: float | None
    t_value: float | None


# ** Vendor Data --------------------------------------------------------------
class VendorDataBase(_SampleIDAndNumber, _SRMDataForeignKey):
    """Vendor data"""

    model_config = SQLModelConfig(alias_generator=to_pascal, populate_by_name=True)

    cylinder_number: str = Field(alias="CylinderNo")
    ratio: float = Field(alias="VendorRatio")


class VendorData(VendorDataBase, _IDPrimaryKey, table=True):
    """Vendor data table"""

    srmdata: SRMData | None = Relationship(back_populates="vendors")


class VendorDataPublic(VendorDataBase, _IDPrimaryKeyPublic):
    pass


class VendorDataCreate(VendorDataBase):
    pass


class VendorDataUpdate(_SampleIDAndNumberUpdate, _SRMDataForeignKeyUpdate):
    cylinder_number: str | None = None
    ratio: float | None = None


# ** Standards Data -----------------------------------------------------------
class StandardsDataBase(_SRMDataForeignKey):
    """Standards Data"""

    name: str = Field(alias="StandardID")
    number: int = Field(alias="StandardNo")
    ratio: float = Field(alias="SRatio")
    concentration: float = Field(alias="SConc")
    unc: float = Field(alias="Sunc")
    uncert: float = Field(alias="Suncert")


class StandardsData(StandardsDataBase, _IDPrimaryKey, table=True):
    """Standards data table"""

    srmdata: SRMData | None = Relationship(back_populates="standards")


class StandardsDataPublic(StandardsDataBase, _IDPrimaryKeyPublic):
    pass


class StandardsDataCreate(StandardsDataBase):
    pass


class StandardsDataUpdate(_SampleIDAndNumberUpdate, _SRMDataForeignKeyUpdate):
    name: str | None = None
    number: int | None = None
    ratio: float | None = None
    concentration: float | None = None
    unc: float | None = None
    uncert: float | None = None


# ** Past lot standards -------------------------------------------------------
class PastLotStandardsDataBase(_SRMDataForeignKey):
    """Past lot standards"""

    name: str = Field(alias="LS ID")
    number: int = Field(alias="LS#")
    ratio: float = Field(alias="Ratio")
    past_conc: float = Field(alias="Past Conc")
    pred_conc: float = Field(alias="Pred Conc")


class PastLotStandardsData(PastLotStandardsDataBase, _IDPrimaryKey, table=True):
    """Past lot standards table"""

    srmdata: SRMData | None = Relationship(back_populates="past_lot_standards")


class PastLotStandardsDataPublic(PastLotStandardsDataBase, _IDPrimaryKeyPublic):
    pass


class PastLogStandardsDataCreate(PastLotStandardsDataBase):
    pass


class PastLotStandardsDataUpdate(_SampleIDAndNumberUpdate, _SRMDataForeignKeyUpdate):
    name: str | None = None
    number: int | None = None
    ratio: float | None = None
    past_conc: float | None = None
    pred_conc: float | None = None


class AdditionalLotStandardsDataBase(_SRMDataForeignKey):
    """AdditionalLotStandards"""

    name: str = Field(alias="ID")
    number: int = Field(alias="LS#")
    ratio: float = Field(alias="Ratio")


class AdditionalLotStandardsData(
    AdditionalLotStandardsDataBase, _IDPrimaryKey, table=True
):
    """Additional lot standards table"""

    srmdata: SRMData | None = Relationship(back_populates="additional_lot_standards")


class AdditionalLotStandardsDataPublic(
    AdditionalLotStandardsDataBase, _IDPrimaryKeyPublic
):
    pass


class AdditionalLogStandardsDataCreate(AdditionalLotStandardsDataBase):
    pass


class AdditionalLotStandardsDataUpdate(
    _SampleIDAndNumberUpdate, _SRMDataForeignKeyUpdate
):
    name: str | None = None
    number: int | None = None
    ratio: float | None = None


# * RCertification -----------------------------------------------------------
# ruff: noqa: ERA001
# class RCertificationDataBase(_SRMDataForeignKey):

#     timestamp: datetime = Field

#     srm_value: float
#     srm_uncertainty: float
#     srm_cl_95: float
#     srm_rel_uncert: float
#     srm_effective_k: float
#     ls_value: float
#     ls_uncertainty: float
#     ls_cl_95: float
#     ls_rel_uncert: float


# class _CertifiedDataForeignKey(SQLModel):
#     certified_id: int | None = Field(
#         default=None, foreign_key="certifieddata.id", ondelete="CASCADE",
#     )


# class _CertifiedDataForeignKeyUpdate(SQLModel):
#     certified_id: int | None = None


# class _CertifiedDataBase(_CertifiedDataForeignKey):
#     value: float
#     uncertainty: float
#     confidence_level_95: float

#     # relative_uncertainty <- confidence_level_95 / value
#     # effective k <- confidence_level_95 / uncertainty


# * Options -------------------------------------------------------------------
sqlite_file_path = Path("database.db")
sqlite_url = f"sqlite:///{sqlite_file_path}"

engine = create_engine(sqlite_url, echo=True)


def create_db_and_tables(engine: Engine) -> None:
    SQLModel.metadata.create_all(engine)


def add_srm(session: Session, path: Path) -> None:
    srmxls = SRMExcelFile(path)
    srm = SRMData(
        name=path.name,
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


def get_srm(session: Session, srm: str | SRMData) -> SRMData:
    if isinstance(srm, SRMData):
        return srm
    return session.exec(select(SRMData).where(SRMData.name == srm)).one()


def delete_srm(session: Session, srm: str | SRMData) -> None:
    srm = get_srm(session, srm)
    session.delete(srm)
    session.commit()


def delete_subtable(
    session: Session, srm: str | SRMData, table: type[_SRMDataForeignKey]
) -> None:
    srm = get_srm(session, srm)
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
    srm = get_srm(session, srm)
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

    with Session(engine) as session:
        df = get_dataframe(
            session=session,
            statement=select(
                RatioData,
            )
            .join(SRMData)
            .where(SRMData.name == paths[0].name),
        )
        df = df.query("number != 100")
        factors = [None, "number", "port", "break_set", "day"]
        for factor in factors:
            print(factor)
            out = get_ratio_data_stats_table(df, factor)
            if factor is None:
                print(out)
            else:
                print(get_ratio_data_stats_table(out, factor=None, col="ave"))

    return False


if __name__ == "__main__":
    raise SystemExit(main())
