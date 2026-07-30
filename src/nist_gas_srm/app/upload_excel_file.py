"""Data entry by upload excel file."""

import streamlit as st

from nist_gas_srm import read_excel

st.title("📋 Data upload portal")
# Input widgets
upload_file = st.file_uploader("Excel file to upload", type=".xls")

# 3. Process the submitted form data
if upload_file is not None:
    submit_to_database = st.button("Upload to database")
    tabs = st.tabs([
        "Ratio data",
        "Vendor data",
        "Standards",
        "Ratio analysis",
        "Past lot standards",
        "Additional lot standards",
    ])

    data = st.session_state.srm = read_excel.SRMExcelFile(upload_file)

    for tab, func in zip(
        tabs,
        [
            data.ratio_data,
            data.vendor_data,
            data.standards_data,
            data.ratio_analysis_random_effects,
            data.past_lot_standards,
            data.additional_lot_standards,
        ],
        strict=True,
    ):
        with tab:
            st.dataframe(func(), use_container_width=True)

    if submit_to_database:
        st.info("uploaded data")
