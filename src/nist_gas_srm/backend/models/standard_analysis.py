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

    from .srm import SRMData


FORMAT = "[%(name)s - %(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)


# * Standard analysis
class StandardAnalysisData(
    stdanal.StandardAnalysisBase,
    IDPrimaryKey,
    FixMixin,
    table=True,
):
    """Standard analysis data"""

    __tablename__ = cast("declared_attr[str]", "standard_analysis_root")

    model_config = SQLModelConfig(str_to_lower=True)
    srm_root: Optional["SRMData"] = Relationship(back_populates="standard_analysis")  # pyright: ignore[reportDeprecated]

    params: list["ParamsData"] = Relationship(
        back_populates="standard_analysis_root",
        cascade_delete=True,
    )
    genline_params: list["GenLineParamsData"] = Relationship(
        back_populates="standard_analysis_root",
        cascade_delete=True,
    )
    genline_solution: list["GenLineSolutionData"] = Relationship(
        back_populates="standard_analysis_root",
        cascade_delete=True,
    )

    genline_eval: list["GenLineEvalData"] = Relationship(
        back_populates="standard_analysis_root",
        cascade_delete=True,
    )


class ParamsData(stdanal.ParamsBase, IDPrimaryKey, table=True):
    __tablename__ = cast("declared_attr[str]", "standard_analysis_params")
    standard_analysis_root: StandardAnalysisData | None = Relationship(
        back_populates="params"
    )


class GenLineParamsData(stdanal.GenLineParamsBase, IDPrimaryKey, table=True):
    __tablename__ = cast("declared_attr[str]", "standard_analysis_genline_params")
    standard_analysis_root: StandardAnalysisData | None = Relationship(
        back_populates="genline_params"
    )


class GenLineSolutionData(stdanal.GenLineSolutionBase, IDPrimaryKey, table=True):
    __tablename__ = cast("declared_attr[str]", "standard_analysis_genline_solution")
    standard_analysis_root: StandardAnalysisData | None = Relationship(
        back_populates="genline_solution"
    )


class GenLineEvalData(stdanal.GenLineEvalBase, IDPrimaryKey, table=True):
    __tablename__ = cast("declared_attr[str]", "standard_analysis_genline_eval")
    standard_analysis_root: StandardAnalysisData | None = Relationship(
        back_populates="genline_eval"
    )


StandardAnalysisSubTable: TypeAlias = (
    ParamsData | GenLineParamsData | GenLineSolutionData | GenLineEvalData
)
