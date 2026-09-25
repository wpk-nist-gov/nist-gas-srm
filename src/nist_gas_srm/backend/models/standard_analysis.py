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

    params: list["Params"] = Relationship(
        back_populates="standard_analysis_table",
        cascade_delete=True,
    )
    genline_params: list["GenLineParams"] = Relationship(
        back_populates="standard_analysis_table",
        cascade_delete=True,
    )
    genline_solution: list["GenLineSolution"] = Relationship(
        back_populates="standard_analysis_table",
        cascade_delete=True,
    )

    genline_eval: list["GenLineEval"] = Relationship(
        back_populates="standard_analysis_table",
        cascade_delete=True,
    )


class Params(stdanal.ParamsBase, IDPrimaryKey, table=True):
    __tablename__ = cast("declared_attr[str]", "standard_analysis_params")
    standard_analysis_table: StandardAnalysisTable | None = Relationship(
        back_populates="params"
    )


class GenLineParams(stdanal.GenLineParamsBase, IDPrimaryKey, table=True):
    __tablename__ = cast("declared_attr[str]", "standard_analysis_genline_params")
    standard_analysis_table: StandardAnalysisTable | None = Relationship(
        back_populates="genline_params"
    )


class GenLineSolution(stdanal.GenLineSolutionBase, IDPrimaryKey, table=True):
    __tablename__ = cast("declared_attr[str]", "standard_analysis_genline_solution")
    standard_analysis_table: StandardAnalysisTable | None = Relationship(
        back_populates="genline_solution"
    )


class GenLineEval(stdanal.GenLineEvalBase, IDPrimaryKey, table=True):
    __tablename__ = cast("declared_attr[str]", "standard_analysis_genline_eval")
    standard_analysis_table: StandardAnalysisTable | None = Relationship(
        back_populates="genline_eval"
    )


StandardAnalysisSubTableType: TypeAlias = (
    Params | GenLineParams | GenLineSolution | GenLineEval
)
