"""Data entry by upload excel file."""

import streamlit as st

from nist_gas_srm import read_excel

st.title("📋 Data upload portal")

if "srm" not in st.session_state:
    st.session_state.srm = None

# Input widgets
upload_file = st.file_uploader("Excel file to upload", type=".xls")

if upload_file is not None:
    st.session_state.srm = read_excel.SRMExcelFile(upload_file)


# 3. Process the submitted form data
if st.session_state.srm is not None:
    submit_to_database = st.button("Upload to database")
    tabs = st.tabs([
        "Ratio data",
        "Vendor data",
        "Standards",
        "Ratio analysis",
        "Past lot standards",
        "Additional lot standards",
    ])

    data = st.session_state.srm

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
