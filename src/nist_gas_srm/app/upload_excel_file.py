"""Data entry by upload excel file."""

from datetime import UTC, datetime

import pandas as pd
import streamlit as st

from nist_gas_srm import read_excel

st.title("📋 Data upload portal")

# * Initialize an empty starting template -------------------------------------
if "srm_file" not in st.session_state:
    st.session_state.srm_file = None

if "srm_metadata" not in st.session_state:
    st.session_state.srm_metadata = pd.DataFrame(
        [
            {
                "name": "a name",
                "srm_id": 1,
                "batch_id": "X",
                "lot_id": "X",
                "timestamp": datetime.now(UTC),
            }
        ],
    )

# * Input widgets -------------------------------------------------------------
upload_file = st.file_uploader("Excel file to upload", type=".xls")

edited_df = st.data_editor(
    st.session_state.srm_metadata,
    num_rows="fixed",  # Enables add/delete row buttons
    width="stretch",
    hide_index=True,
)


if upload_file is not None:
    st.session_state.srm_file = read_excel.SRMExcelFile(upload_file)


# * Tabbed data viewer/editor -------------------------------------------------
if st.session_state.srm_file is not None:
    submit_to_database = st.button("Upload to database")
    data = st.session_state.srm_file

    tabs_mapping = {
        "Ratio data": data.ratio_data,
        "Vendor data": data.vendor_data,
        "Standards": data.standards_data,
        "Ratio analysis": data.ratio_analysis_random_effects,
        "Past lot standards": data.past_lot_standards,
        "Additional lot standards": data.additional_lot_standards,
    }

    tabs = st.tabs(list(tabs_mapping.keys()))

    for tab, func in zip(
        tabs,
        tabs_mapping.values(),
        strict=True,
    ):
        with tab:
            st.dataframe(func(), width="content", hide_index=True, placeholder="-")

    if submit_to_database:
        st.info("uploaded data")
