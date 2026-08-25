"""View certified data"""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from nist_gas_srm.core import basemodels, excel_interface

st.title("Certified values")


DBNAMES_TABLENAMES_MAPPING = {
    "srm_values": "SRM values",
    "standards_values": "Standards values",
    "additional_lot_standards": "Certified additional lot standards",
    "cylinder_results": "Cylinder results",
    "analysis_function_coefficients": "Analysis function coefficients",
    "correlation_coefficients": "Correlation coefficients",
    "outliers": "Outliers",
}

if (excelfile := st.session_state.get("srm_file")) is not None:
    tabs = st.tabs(list(DBNAMES_TABLENAMES_MAPPING.values()))
    for tab, name in zip(tabs, DBNAMES_TABLENAMES_MAPPING, strict=True):
        data_ = excel_interface.excel_to_dataframe_by_name(
            name, excelfile, model=basemodels.RCertCreateComplete
        )

        with tab:
            st.dataframe(data_, width="content", hide_index=True)

        if name == "cylinder_results" and data_ is not None:
            # plot of Cylinder results
            fig = px.scatter(  # pyright: ignore[reportUnknownMemberType]
                data_,
                x="Sample",
                y="Value",
                error_y="95% CI",
                title="Cylinder reulsts",
            )
            st.plotly_chart(fig)  # pyright: ignore[reportUnknownMemberType]
