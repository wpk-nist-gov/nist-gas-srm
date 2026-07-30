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
        "SRM values": data.srm_values,
        "Standards values": data.standards_values,
        "Additional lot standards": data.additional_lot_standards,
        "Cylinder results": data.cylinder_results,
        "Ananalysis function coefficients": data.analysis_function_coefficients,
        "Correlation coefficients": data.correlation_coefficients,
        "Outliers": data.outliers,
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
                x="name",
                y="value",
                error_y="confidence_level_95",
                title="Cylinder reulsts",
            )
            st.plotly_chart(fig)  # pyright: ignore[reportUnknownMemberType]
