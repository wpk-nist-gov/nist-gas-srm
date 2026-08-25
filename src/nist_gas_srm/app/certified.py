"""View certified data"""

from __future__ import annotations

from typing import TYPE_CHECKING

import plotly.express as px
import streamlit as st

if TYPE_CHECKING:
    from collections.abc import Callable

    import pandas as pd


st.title("Certified values")

if (srm_file := st.session_state.get("srm_file")) is not None:
    data = srm_file.rcert
    tabs_mapping: dict[str, Callable[[], pd.DataFrame | None]] = {
        "SRM values": data["srm_values"].excel_to_dataframe,
        "Standards values": data["standards_values"].excel_to_dataframe,
        "Additional lot standards": data["additional_lot_standards"].excel_to_dataframe,
        "Cylinder results": data["cylinder_results"].excel_to_dataframe,
        "Ananalysis function coefficients": data[
            "analysis_function_coefficients"
        ].excel_to_dataframe,
        "Correlation coefficients": data["correlation_coefficients"].excel_to_dataframe,
        "Outliers": data["outliers"].excel_to_dataframe,
    }

    tabs = st.tabs(list(tabs_mapping.keys()))

    for tab, (name, func) in zip(
        tabs,
        tabs_mapping.items(),
        strict=True,
    ):
        data_ = func()
        with tab:
            st.dataframe(data_, width="content", hide_index=True)

        if name == "Cylinder results" and data_ is not None:
            # plot of Cylinder results
            fig = px.scatter(  # pyright: ignore[reportUnknownMemberType]
                data_,
                x="Sample",
                y="Value",
                error_y="95% CI",
                title="Cylinder reulsts",
            )
            st.plotly_chart(fig)  # pyright: ignore[reportUnknownMemberType]
