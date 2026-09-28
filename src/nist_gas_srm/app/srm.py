"""View existing data"""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import streamlit as st

from nist_gas_srm.app._utils import (
    FASTAPI_URL,
    get_all_srms,
)
from nist_gas_srm.client import crud
from nist_gas_srm.core import basemodels, excel_interface

if TYPE_CHECKING:
    from typing import Any


def get_data(srm_query: list[str]) -> dict[str, Any]:
    with httpx.Client(base_url=FASTAPI_URL) as client:
        response = crud.get_srms(
            client,
            srm_query=srm_query,
            complete=True,
        )
        dataframes = excel_interface.json_to_dict_of_dataframes(
            response.json(),
            model=basemodels.srm.SRMMeasurementsCompleteCreate,
            normalize=True,
        )
        return excel_interface.clean_normalized_dataframe(dataframes)


srms = st.multiselect(
    "SRM",
    get_all_srms(),
    accept_new_options=True,
)
