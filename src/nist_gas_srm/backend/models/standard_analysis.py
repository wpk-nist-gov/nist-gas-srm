import logging
from typing import TYPE_CHECKING, Optional, TypeAlias, cast  # pyright: ignore[reportDeprecated]

from sqlmodel import (
    Relationship,
)
from sqlmodel._compat import (  # ruff: ignore[import-private-name]
    SQLModelConfig,
)

from nist_gas_srm.core.basemodels import standard_analysis as stdanal
from nist_gas_srm.core.basemodels.keys import IDPrimaryKey

from ._fixmixin import FixMixin

if TYPE_CHECKING:
    from sqlalchemy.orm import declared_attr

    from .srm import SRMTable


FORMAT = "[%(name)s - %(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)


# * Standard analysis
class StandardAnalysisTable(
    stdanal.StandardAnalysisBase,
    IDPrimaryKey,
    FixMixin,
    table=True,
):
    """Standard analysis data"""

    __tablename__ = cast("declared_attr[str]", "standard_analysis_table")

    model_config = SQLModelConfig(str_to_lower=True)
    srm_table: Optional["SRMTable"] = Relationship(back_populates="standard_analysis")  # pyright: ignore[reportDeprecated]

    params: list["StandardAnalysisParams"] = Relationship(
        back_populates="standard_analysis_table",
        cascade_delete=True,
    )
    genline_params: list["StandardAnalysisGenLineParams"] = Relationship(
        back_populates="standard_analysis_table",
        cascade_delete=True,
    )
    genline_solution: list["StandardAnalysisGenLineSolution"] = Relationship(
        back_populates="standard_analysis_table",
        cascade_delete=True,
    )

    genline_eval: list["StandardAnalysisGenLineEval"] = Relationship(
        back_populates="standard_analysis_table",
        cascade_delete=True,
    )


class StandardAnalysisParams(
    stdanal.StandardAnalysisParamsBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "standard_analysis_params")
    standard_analysis_table: StandardAnalysisTable | None = Relationship(
        back_populates="params"
    )


class StandardAnalysisGenLineParams(
    stdanal.StandardAnalysisGenLineParamsBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "standard_analysis_genline_params")
    standard_analysis_table: StandardAnalysisTable | None = Relationship(
        back_populates="genline_params"
    )


class StandardAnalysisGenLineSolution(
    stdanal.StandardAnalysisGenLineSolutionBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "standard_analysis_genline_solution")
    standard_analysis_table: StandardAnalysisTable | None = Relationship(
        back_populates="genline_solution"
    )


class StandardAnalysisGenLineEval(
    stdanal.StandardAnalysisGenLineEvalBase, IDPrimaryKey, table=True
):
    __tablename__ = cast("declared_attr[str]", "standard_analysis_genline_eval")
    standard_analysis_table: StandardAnalysisTable | None = Relationship(
        back_populates="genline_eval"
    )


StandardAnalysisSubTableType: TypeAlias = (
    StandardAnalysisParams
    | StandardAnalysisGenLineParams
    | StandardAnalysisGenLineSolution
    | StandardAnalysisGenLineEval
)
