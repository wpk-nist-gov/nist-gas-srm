"""View existing data"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import httpx
import pandas as pd
import streamlit as st

from nist_gas_srm import basemodels, excel
from nist_gas_srm.client import crud
from nist_gas_srm.core.utils import get_in
from nist_gas_srm_frontend._utils import (
    FASTAPI_URL,
    TABLEGROUP_DBNAMES_TABLENAMES_MAPPING,
    get_all_srms,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any


def get_data(srm_query: list[str]) -> dict[str, Any]:
    with httpx.Client(base_url=FASTAPI_URL) as client:
        response = crud.get_srms(
            client=client,
            srm_query=srm_query,
            complete=True,
        )

        json = response.json().get("data", [])

        dataframes = excel.interface.json_to_dict_of_dataframes(
            json,
            model=basemodels.srm.SRMCompleteCreate,
            normalize=True,
        )

        # add in metadata
        dataframes["metadata"] = pd.DataFrame([
            {k: v for k, v in d.items() if not isinstance(v, dict)} for d in json
        ])

        return excel.interface.clean_normalized_dataframe(dataframes)


def plot_cylinder_results(data: pd.DataFrame) -> None:
    import plotly.express as px

    fig = px.scatter(  # pyright: ignore[reportUnknownMemberType]
        data,
        x="Sample",
        y="Value",
        error_y="95% CI",
        title="Cylinder results",
        color="srm_name",
    )

    st.plotly_chart(fig)  # pyright: ignore[reportUnknownMemberType]


srms = st.multiselect(
    "SRM",
    get_all_srms(include_subtypes=False),
    accept_new_options=True,
)


tablegroup_dbnames_tablenames_mapping = {
    "Metadata": {"metadata": "SRM info"},
    **TABLEGROUP_DBNAMES_TABLENAMES_MAPPING,
}


tablegroup_plot_mapping: dict[str, dict[str, Callable[[pd.DataFrame], None]]] = {
    "RCertification": {"rcert.cylinder_results": plot_cylinder_results}
}


if srms and (data := get_data(srms)):
    for table_group, tables in tablegroup_dbnames_tablenames_mapping.items():
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

                        if (
                            plot_func := get_in(
                                (table_group, name),
                                tablegroup_plot_mapping,
                                split=None,
                                default=None,
                            )
                        ) is not None:
                            plot_func(data_)
