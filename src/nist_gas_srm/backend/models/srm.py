"""Basic model"""

import logging
from typing import TYPE_CHECKING, cast

from sqlmodel import (
    Relationship,
)
from sqlmodel._compat import (  # ruff: ignore[import-private-name]
    SQLModelConfig,
)

from nist_gas_srm.core import basemodels
from nist_gas_srm.core.basemodels.keys import IDPrimaryKey

from ._fixmixin import FixMixin
from .measurements import Measurements
from .rcert import RCertData
from .standard_analysis import StandardAnalysisData

if TYPE_CHECKING:
    from sqlalchemy.orm import declared_attr


FORMAT = "[%(name)s - %(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)


class SRMData(basemodels.srm.SRMDataBase, IDPrimaryKey, FixMixin, table=True):
    """Metadata table"""

    __tablename__ = cast("declared_attr[str]", "srm_root")

    model_config = SQLModelConfig(str_to_lower=True)

    measurements: Measurements = Relationship(
        back_populates="srm_root", cascade_delete=True
    )

    rcert: RCertData = Relationship(back_populates="srm_root", cascade_delete=True)

    standard_analysis: StandardAnalysisData = Relationship(
        back_populates="srm_root", cascade_delete=True
    )
