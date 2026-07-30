"""Data entry by upload excel file."""

import streamlit as st

from nist_gas_srm import read_excel

st.title("📋 Data upload portal")

if "srm_file" not in st.session_state:
    st.session_state.srm_file = None

# Input widgets
upload_file = st.file_uploader("Excel file to upload", type=".xls")

if upload_file is not None:
    st.session_state.srm_file = read_excel.SRMExcelFile(upload_file)


# 3. Process the submitted form data
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
            st.dataframe(func(), use_container_width=True)

    if submit_to_database:
        st.info("uploaded data")
