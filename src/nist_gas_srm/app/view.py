"""View existing data"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import httpx
import streamlit as st

from nist_gas_srm.app._utils import (
    FASTAPI_URL,
    TABLEGROUP_DBNAMES_TABLENAMES_MAPPING,
    get_all_srms,
)
from nist_gas_srm.client import crud
from nist_gas_srm.core import basemodels, excel_interface
from nist_gas_srm.core.utils import get_in

if TYPE_CHECKING:
    from typing import Any

    import pandas as pd


def get_data(srm_query: list[str]) -> dict[str, Any]:
    with httpx.Client(base_url=FASTAPI_URL) as client:
        response = crud.get_srms(
            client,
            srm_query=srm_query,
            complete=True,
        )
        dataframes = excel_interface.json_to_dict_of_dataframes(
            response.json(),
            model=basemodels.srm.SRMCompleteCreate,
            normalize=True,
        )
        return excel_interface.clean_normalized_dataframe(dataframes)


srms = st.multiselect(
    "SRM",
    get_all_srms(),
    accept_new_options=True,
)

if srms:
    data = get_data(srms)
    if data:
        for table_group, tables in TABLEGROUP_DBNAMES_TABLENAMES_MAPPING.items():
            with st.expander(table_group, expanded=False):
                tabs = st.tabs(list(tables.values()))

                for tab, name in zip(tabs, tables, strict=True):
                    if (data_ := get_in(name, data, default=None)) is not None:
                        with tab:
                            st.dataframe(  # pyright: ignore[reportUnknownMemberType]
                                cast("pd.DataFrame", data_),
                                width="content",
                                hide_index=True,
                            )
